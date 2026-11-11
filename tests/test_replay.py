import hashlib
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("timeline_test", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
plugin = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = plugin
spec.loader.exec_module(plugin)
from timeline_test import core, rendering, visuals, service, presentation, dependencies
from timeline_test.demo import make_demo


def event(t=100, kind="tool", **kw):
    return core.normalize(dict(time=t, kind=kind, session="worker-a", tool="terminal", **kw), "Research")


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def history_db(self):
        path = self.home / "state.db"
        with closing(sqlite3.connect(path)) as db:
            db.executescript("""
              CREATE TABLE sessions(id TEXT, started_at REAL, ended_at REAL, parent_session_id TEXT, model TEXT, system_prompt TEXT, cwd TEXT);
              CREATE TABLE messages(id INTEGER, session_id TEXT, timestamp REAL, role TEXT, tool_name TEXT, active INTEGER, content TEXT, tool_calls TEXT);
              INSERT INTO sessions VALUES('worker-a',100,200,NULL,'test-model','SECRET PROMPT','/private/project');
              INSERT INTO messages VALUES(1,'worker-a',120,'tool','terminal',1,'sk-private-secret','private argv');
              INSERT INTO messages VALUES(2,'worker-a',130,'tool','read_file',0,'hidden compressed content','');
            """)
        return path

    def test_strict_metadata_projection_and_pseudonyms(self):
        e = event(args={"command": "cat /private/token"}, result="sk-test-credential", prompt="PRIVATE")
        raw = json.dumps(e)
        self.assertNotIn("private", raw)
        self.assertNotIn("PRIVATE", raw)
        self.assertNotIn("worker-a", raw)
        self.assertEqual(e["status"], "unknown")
        self.assertIsNone(e["duration"])

    def test_timezones_and_invalid_time(self):
        self.assertEqual(core.timestamp("2026-11-01T01:30:00-05:00")+3600, core.timestamp("2026-11-01T01:30:00-06:00"))
        for value in ("2026-11-01T01:30:00", float("nan"), None):
            with self.assertRaises(ValueError):
                core.timestamp(value)

    def test_labels_reject_paths_and_secrets(self):
        for value in ("/private/path", r"C:\private\data", "https://host/?token=secret", "sk-test-key"):
            self.assertEqual(core.label(value), "unknown")

    def test_unknown_outcome_does_not_become_success(self):
        model = core.replay([event(), event(110, status="error"), event(120, status="success")], timezone_name="UTC")
        self.assertEqual(model["totals"]["unknown_status"], 1)
        self.assertEqual(model["totals"]["errors"], 1)
        self.assertEqual(model["totals"]["tools"], 3)

    def test_history_is_read_only_and_excludes_transcripts(self):
        db = self.history_db()
        before = hashlib.sha256(db.read_bytes()).hexdigest()
        events, warnings = core.read_history(self.home, "Research", 90, 210)
        self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), before)
        self.assertEqual([e["kind"] for e in events], ["session_start", "session_end", "tool"])
        self.assertTrue(all(e["status"] == "unknown" for e in events))
        self.assertIsNone(events[-1]["duration"])
        self.assertNotIn("SECRET", json.dumps(events))
        self.assertNotIn("private", json.dumps(events))
        self.assertIn("stored message times", " ".join(warnings))

    def test_capture_and_history_never_double_count_session(self):
        self.history_db()
        with patch("timeline_test.core.time.time", return_value=150):
            core.append(dict(kind="tool", time=120, session="worker-a", tool="terminal", id="call-a"), "local", self.home)
        events, warnings = core.collect(["current"], 90, 210, True, self.home)
        self.assertEqual(len(events), 1)
        self.assertIn("avoid duplicate", " ".join(warnings))

    def test_sources_require_operator_enrollment(self):
        with self.assertRaises(ValueError):
            core.collect(["unapproved"], 0, 200, home=self.home)
        self.history_db()
        core.enroll("research", self.home, self.home)
        self.assertIn("research", core.sources(self.home))
        with self.assertRaises(ValueError):
            core.enroll("../escape", self.home, self.home)

    def test_zero_length_and_empty_data(self):
        self.assertEqual(core.replay([event()], timezone_name="UTC")["span"], 1)
        with self.assertRaises(ValueError):
            core.replay([], timezone_name="UTC")

    def test_many_sessions_group_without_dropping_events(self):
        events = [core.normalize(dict(time=100+i, kind="tool", session=str(i)), "one") for i in range(40)]
        model = core.replay(events, timezone_name="UTC")
        self.assertEqual(len(model["lanes"]), 1)
        self.assertEqual(len(model["events"]), 40)
        self.assertEqual(model["totals"]["sessions"], 40)

    def test_export_is_private_and_has_render_contract(self):
        result = service.run(dict(action="demo", timezone="UTC", seconds=30), self.home)
        self.assertTrue(result["demo"])
        path = rendering.bundle_path(result["bundle"], self.home)
        html = (path / "index.html").read_text()
        self.assertIn('data-duration="30"', html)
        self.assertIn('data-composition-id="timeline-replay"', html)
        self.assertNotIn('<script src=', html)
        self.assertNotIn('claude.ai', html)
        data = json.loads((path / "events.json").read_text())
        self.assertTrue(data["demo"])
        self.assertEqual(data["totals"]["tools"], 22)
        self.assertIn("SYNTHETIC", data["warnings"][0])

    def test_script_embedding_cannot_break_out(self):
        data = make_demo("UTC")
        data["title"] = '</script><script>bad()</script>'
        page = visuals.html(data)
        self.assertNotIn(data["title"], page)
        self.assertIn('\\u003c/script', page)

    def test_traversal_bundle_rejected(self):
        for bad in ("../secrets", "123", "a"*16+"/../../", None):
            with self.assertRaises(ValueError):
                rendering.bundle_path(bad, self.home)

    def test_missing_renderer_fails_before_spawning(self):
        result = service.run(dict(action="demo", timezone="UTC"), self.home)
        with patch.dict(os.environ, {}, clear=True), patch("timeline_test.rendering.shutil.which", return_value=None), patch("timeline_test.rendering.subprocess.run") as spawn:
            with self.assertRaises(ValueError):
                rendering.start(result["bundle"], self.home)
            spawn.assert_not_called()

    def test_render_lock_excludes_parallel_workers(self):
        lock = rendering._acquire(self.home)
        try:
            with self.assertRaises(ValueError):
                rendering._acquire(self.home)
        finally:
            lock.close()
        rendering._acquire(self.home).close()

    def test_renderer_marks_complete_only_after_probe(self):
        result = service.run(dict(action="demo", timezone="UTC"), self.home)
        folder = rendering.bundle_path(result["bundle"], self.home)
        job = dict(id=result["bundle"], state="running")
        lock = rendering._acquire(self.home)
        calls = []
        def fake_stream(argv, **kw):
            calls.append((argv, kw))
            if 'render' in argv:
                kw['on_text']('53%  Streaming frame 10/60')
                (folder/'timeline.mp4').write_bytes(b'fixture-only-not-a-real-video')
            else:
                kw['on_text']('[hyperframes] check: samples 3/9')
            return 0
        class Probe:
            stdout = json.dumps({'format':{'duration':'60.0'},'streams':[{'codec_type':'video','width':1920,'height':1080,'r_frame_rate':'30/1'}]})
        with patch.dict(os.environ, {'OPENAI_API_KEY':'must-not-leak'}), patch('timeline_test.rendering._stream',side_effect=fake_stream),patch('timeline_test.rendering.subprocess.run',return_value=Probe()),patch('timeline_test.rendering.shutil.which',return_value='ffprobe'):
            rendering._worker(result['bundle'],folder,['hyperframes'],job,lock)
        self.assertEqual(job['state'],'complete',job.get('error'))
        self.assertEqual(calls[0][0][1],'check')
        self.assertEqual(calls[1][0][1],'render')
        self.assertNotIn('OPENAI_API_KEY',calls[0][1]['env'])
        self.assertNotIn('progress',job)
        est = rendering.estimate(30, self.home)
        self.assertIsNotNone(est)
        self.assertIn('previous export',est['basis'])

    def test_bad_video_probe_never_claims_completion(self):
        result = service.run(dict(action="demo", timezone="UTC"), self.home)
        folder = rendering.bundle_path(result['bundle'],self.home)
        job = dict(id=result['bundle'],state='running')
        lock = rendering._acquire(self.home)
        class BadProbe:
            stdout=json.dumps({'format':{'duration':'1.0'},'streams':[]})
        def fake_stream(argv, **kw):
            if 'render' in argv:
                (folder/'timeline.mp4').write_bytes(b'x')
            return 0
        with patch('timeline_test.rendering._stream',side_effect=fake_stream),patch('timeline_test.rendering.subprocess.run',return_value=BadProbe()),patch('timeline_test.rendering.shutil.which',return_value='ffprobe'):
            rendering._worker(result['bundle'],folder,['hyperframes'],job,lock)
        self.assertEqual(job['state'],'failed')

    def test_failed_check_is_summarized_and_blocks_render(self):
        result = service.run(dict(action="demo", timezone="UTC"), self.home)
        folder = rendering.bundle_path(result['bundle'],self.home)
        job = dict(id=result['bundle'],state='running')
        lock = rendering._acquire(self.home)
        calls = []
        def fake_stream(argv, **kw):
            calls.append(argv)
            kw['stdout'].write(json.dumps({'ok':False,'lint':{'errorCount':0,'warningCount':0,'findings':[]},
                'layout':{'errorCount':2,'warningCount':0,'findings':[{'severity':'error','code':'content_overlap','selector':'#p > div','text':'10 TOOL CALLS','times':[0.5]}]}}))
            return 1
        with patch('timeline_test.rendering._stream',side_effect=fake_stream),patch('timeline_test.rendering.shutil.which',return_value='ffprobe'):
            rendering._worker(result['bundle'],folder,['hyperframes'],job,lock)
        self.assertEqual(len(calls),1)
        self.assertEqual(job['state'],'failed')
        self.assertIn('layout 2 errors',job['error'])
        self.assertEqual(job['check']['sections']['layout']['errors'],2)
        self.assertEqual(job['check']['first_errors'][0]['code'],'content_overlap')

    def test_stale_running_job_reports_interrupted_when_lock_is_free(self):
        result = service.run(dict(action="demo", timezone="UTC"), self.home)
        folder = rendering.bundle_path(result['bundle'],self.home)
        (folder/'job.json').write_text(json.dumps(dict(id=result['bundle'],state='running')))
        self.assertEqual(rendering.status(self.home)[0]['state'],'interrupted')
        lock = rendering._acquire(rendering.data_dir(self.home))
        try:
            self.assertEqual(rendering.status(self.home)[0]['state'],'running')
        finally:
            lock.close()

    def test_progress_parsing_and_real_stream(self):
        state = {}
        self.assertTrue(rendering.parse_progress('[hyperframes] check: samples 3/9', 'checking', state))
        self.assertEqual((state['step'], state['steps'], state['label']), (3, 9, 'Checking layout 3/9'))
        state = {}
        self.assertTrue(rendering.parse_progress('\u2588\u2588 5%  Compiling composition', 'rendering', state))
        self.assertEqual(state['label'], 'Compiling composition')
        self.assertNotIn('percent', state)
        rendering.parse_progress('53%  Streaming frame 582/1140', 'rendering', state)
        self.assertEqual((state['frame'], state['frames']), (582, 1140))
        # A real child process: \r-separated progress reaches the parser and the log, without a shell.
        import io, sys
        seen, log = [], io.StringIO()
        code = rendering._stream([sys.executable, '-c', "import sys;sys.stdout.write('10%  Streaming frame 1/10\\r50%  Streaming frame 5/10\\r100%  Render complete\\n')"],
                                 cwd=self.home, env=dict(os.environ), log=log, on_text=seen.append)
        self.assertEqual(code, 0)
        self.assertEqual(len(seen), 3)
        self.assertIn('Render complete', log.getvalue())

    def test_history_tokens_and_provider_without_changing_ids(self):
        e1 = core.normalize(dict(kind='model', time=1794175200, session='s', model='deepseek-v4', provider='openrouter', id='a'), 'p', 'capture')
        e0 = core.normalize(dict(kind='model', time=1794175200, session='s', model='deepseek-v4', id='a'), 'p', 'capture')
        self.assertEqual(e1['id'], e0['id'])
        self.assertEqual(e1['provider'], 'openrouter')
        bad = core.normalize(dict(kind='model', time=1794175200, session='s', model='m', provider='https://10.0.0.5/v1', id='b'), 'p', 'capture')
        self.assertEqual(bad['provider'], '')

    def test_model_layer_toggle(self):
        events = [core.normalize(dict(kind='model', time=1794175200+i*600, session='s', model=m, provider='nous', id=f'm{i}'), 'Researchbot', 'demo')
                  for i, m in enumerate(['hermes-4', 'hermes-4', 'deepseek-v4', 'hermes-4'])]
        model = core.replay(events, 'Models', 'UTC', [], demo=True)
        on = visuals.html(model, 20, interactive=False, pace='social', models=True)
        off = visuals.html(model, 20, interactive=False, pace='social', models=False)
        self.assertIn('"models":true', on)
        self.assertIn('"models":false', off)
        self.assertIn('data-duration="20"', on)

    def test_versions_agree_and_stale_clients_are_rejected(self):
        from pathlib import Path
        import re as _re
        pkg = Path(__file__).resolve().parents[1]
        loaded = sys.modules['timeline_test.version'].VERSION
        self.assertEqual(sys.modules['timeline_test.version'].installed_version(), loaded)
        self.assertIn(f'"version": "{loaded}"', (pkg/'dashboard'/'manifest.json').read_text(encoding='utf-8'))
        self.assertIn(f"UI_VERSION='{loaded}'", (pkg/'desktop'/'plugin.js').read_text(encoding='utf-8'))
        status = service.run(dict(action='status'), self.home)
        self.assertEqual((status['version'], status['restart_required']), (loaded, False))
        self.assertEqual(service.run(dict(action='jobs', client_api=1), self.home)['version'], loaded)
        with self.assertRaises(ValueError):
            service.run(dict(action='jobs', client_api=99), self.home)
        built = service.run(dict(action='demo', timezone='UTC', seconds=15), self.home)
        info = json.loads((rendering.bundle_path(built['bundle'], self.home)/'bundle.json').read_text())
        self.assertEqual(info['version'], loaded)

    def test_workers_configurable_and_progress_uses_frames(self):
        with patch.dict(os.environ, {'TIMELINE_REPLAY_WORKERS': '3'}):
            self.assertEqual(rendering.render_workers(self.home), 3)
        with patch.dict(os.environ, {'TIMELINE_REPLAY_WORKERS': ''}):
            self.assertTrue(1 <= rendering.render_workers(self.home) <= 4)
        state = {}
        rendering.parse_progress('25%  Streaming frame 9/1020', 'rendering', state)
        self.assertEqual(state['percent'], 1)
        state = {}
        rendering.parse_progress('[hyperframes] check: samples 9/9', 'checking', state)
        self.assertEqual(state['label'], 'Analysing layout results')
        self.assertNotIn('eta_seconds', state)

    def test_vendor_prefixed_models_and_sublinear_check_estimate(self):
        e = core.normalize(dict(kind='session_start', time=1794175200, session='s', model='anthropic/claude-haiku-5.5', id='x'), 'p', 'history')
        self.assertEqual(e['model'], 'claude-haiku-5.5')
        e = core.normalize(dict(kind='session_start', time=1794175200, session='s', model='oamazonasgabriel/lfm2.5-2.6b:q4_k_m-8gbGPU', id='y'), 'p', 'history')
        self.assertEqual(e['model'], 'lfm2.5-2.6b:q4_k_m-8gbGPU')
        e = core.normalize(dict(kind='session_start', time=1794175200, session='s', model='https://bad host/<x>', id='z'), 'p', 'history')
        self.assertEqual(e['model'], '')
        rows = [dict(events=1159, check=52), dict(events=20000, check=190)]
        self.assertAlmostEqual(rendering.check_time(rows, 20000), 190, delta=5)
        self.assertAlmostEqual(rendering.check_time(rows[:1], 20000), 190, delta=25)

    def test_multi_worker_progress_and_encode_phase(self):
        state = {}
        self.assertTrue(rendering.parse_progress('Capturing frame 182/1020 (2 workers)', 'rendering', state))
        self.assertEqual((state['frame'], state['frames'], state['percent']), (182, 1020, 18))
        self.assertNotIn('eta_seconds', state)  # warm-up: no early rate-based ETA
        self.assertTrue(rendering.parse_progress('\u2588\u2588 60%  Capturing frame 594/1020 (2 workers)', 'rendering', state))
        self.assertEqual(state['frame'], 594)
        self.assertTrue(rendering.parse_progress('Encoding video', 'rendering', state))
        self.assertEqual((state['label'], state['percent']), ('Encoding video', 99))
        self.assertNotIn('eta_seconds', state)

    def test_progress_refreshes_without_new_output(self):
        result = service.run(dict(action="demo", timezone="UTC", seconds=15), self.home)
        folder = rendering.bundle_path(result['bundle'], self.home)
        job = dict(id=result['bundle'], state='running')
        lock = rendering._acquire(rendering.data_dir(self.home))
        seen = []
        def slow_stream(argv, **kw):
            if 'check' in argv:
                kw['stdout'].write(json.dumps({'ok': True}))
                kw['on_text']('[hyperframes] check: samples 7/9')
                import time as _t
                for _ in range(7):  # silent for ~3.5 s: the ticker must keep elapsed moving
                    _t.sleep(.5)
                    seen.append(json.loads((folder/'job.json').read_text())['progress']['elapsed'])
                return 1
            return 0
        with patch('timeline_test.rendering._stream', side_effect=slow_stream), patch('timeline_test.rendering.shutil.which', return_value='ffprobe'):
            rendering._worker(result['bundle'], folder, ['hyperframes'], job, lock)
        self.assertGreater(max(seen), min(seen))

    def test_machine_progress_render_fit_and_session_shares(self):
        state = {}
        self.assertTrue(rendering.parse_progress('@hf-progress {"code":"capture","done":1005,"total":1020,"pct":69}', 'rendering', state))
        self.assertEqual((state['frame'], state['frames']), (1005, 1020))
        self.assertTrue(rendering.parse_progress('@hf-progress {"code":"encode","pct":99}', 'rendering', state))
        self.assertEqual(state['label'], 'Encoding video')
        rows = [dict(events=1159, check=41, wall=116, video=34), dict(events=20000, check=190, wall=377, video=64)]
        self.assertAlmostEqual(rendering.render_rate(rows, 20000)*64, 187, delta=8)
        # Finale shares: a live-captured profile and history profiles are counted per session.
        events = [core.normalize(dict(kind='model', time=1794175200+i, session='live', model='gpt-6.1-sol', provider='openai-codex', id=f'l{i}'), 'Default', 'capture') for i in range(50)]
        events += [core.normalize(dict(kind='session_start', time=1794175300+i, session=f'h{i}', model='anthropic/claude-haiku-5.5', provider='anthropic', id=f'h{i}'), 'Researchbot', 'history') for i in range(3)]
        html = visuals.html(core.replay(events, 'x', 'UTC', [], demo=True), 20, interactive=False, pace='social')
        self.assertIn('MODELS BY SESSION', html)

    def test_completed_job_exposes_video_path_and_slim_preview(self):
        result = service.run(dict(action="demo", timezone="UTC", seconds=15), self.home)
        folder = rendering.bundle_path(result['bundle'], self.home)
        (folder/'timeline.mp4').write_bytes(b'fixture-only')
        (folder/'job.json').write_text(json.dumps(dict(id=result['bundle'], state='complete')))
        job = rendering.status(self.home)[0]
        self.assertTrue(job['video_path'].endswith('timeline.mp4'))
        html = (folder/'replay.html').read_text(encoding='utf-8')
        self.assertNotIn('"origin"', html)
        self.assertIn('id="loop"', html)
        self.assertIn('"loop":false', html)

    def test_host_note_for_unwritable_desktop_plugins(self):
        deps = sys.modules['timeline_test.dependencies']
        (self.home / 'desktop-plugins').mkdir(exist_ok=True)
        with patch('timeline_test.dependencies.os.access', return_value=False):
            notes = deps.host_notes(self.home)
        self.assertTrue(notes and 'desktop-plugins' in notes[0] and 'chown' in notes[0])
        with patch('timeline_test.dependencies.os.access', return_value=True):
            self.assertEqual(deps.host_notes(self.home), [])
        self.assertIn('host', deps.inspect(self.home))

    def test_low_memory_note_is_non_blocking(self):
        with patch('timeline_test.dependencies.memory_total_mb', return_value=8192):
            notes = sys.modules['timeline_test.dependencies'].performance_notes()
        self.assertTrue(any('low-memory profile' in n for n in notes))
        with patch('timeline_test.dependencies.memory_total_mb', return_value=12288):
            notes = sys.modules['timeline_test.dependencies'].performance_notes()
        self.assertFalse(any('low-memory profile' in n for n in notes))

    def test_status_names_serving_profile(self):
        status = service.run(dict(action='status'), self.home)
        self.assertIn('serving_profile', status)
        self.assertEqual(core.profile_label(self.home / 'profiles' / 'Research'), 'Research')
        self.assertEqual(core.profile_label(self.home), 'default')

    def test_render_eta_waits_for_warm_up(self):
        clock = iter([0, 1, 6, 16])
        state = {}
        # Fake only the rendering module's clock: patching time.monotonic globally lets any other
        # thread consume the four values and made this test fail intermittently under load.
        import time as real_time, types
        fake = types.SimpleNamespace(**{k: getattr(real_time, k) for k in dir(real_time) if not k.startswith('_')})
        fake.monotonic = lambda: next(clock)
        with patch('timeline_test.rendering.time', fake):
            rendering.parse_progress('Capturing frame 3/1000', 'rendering', state)    # t=0: warm-up, slow frames
            rendering.parse_progress('Capturing frame 20/1000', 'rendering', state)   # t=1: 2% done, too early
            self.assertNotIn('eta_seconds', state)
            rendering.parse_progress('Capturing frame 60/1000', 'rendering', state)   # t=6: >=5% and >=5 s, baseline
            rendering.parse_progress('Capturing frame 260/1000', 'rendering', state)  # t=16: 20 fps after warm-up
        self.assertEqual(state['fps'], 20.0)
        self.assertEqual(state['eta_seconds'], 37)

    def test_lanes_per_screen_option(self):
        out = service.run(dict(action='demo', timezone='UTC', seconds=15, lanes='4'), self.home)
        self.assertEqual(out['lanes'], '4')
        html = (rendering.bundle_path(out['bundle'], self.home)/'index.html').read_text(encoding='utf-8')
        self.assertIn('"lanes":"4"', html)
        self.assertIn('social-compact', html)
        with self.assertRaises(ValueError):
            service.run(dict(action='demo', timezone='UTC', lanes='9'), self.home)

    def test_estimate_prefers_same_screen_density(self):
        rows = [dict(video=34, wall=85, check=41, events=1118, workers=3, screen_lanes=4),
                dict(video=34, wall=125, check=73, events=1118, workers=3, screen_lanes=7)]
        folder = rendering.data_dir(self.home); folder.mkdir(parents=True, exist_ok=True)
        (folder/'render-stats.json').write_text(json.dumps(rows))
        dense = rendering.estimate(34, self.home, events=1118, workers=3, screen_lanes=7)
        sparse = rendering.estimate(34, self.home, events=1118, workers=3, screen_lanes=4)
        self.assertAlmostEqual(dense['seconds'], 125, delta=3)
        self.assertAlmostEqual(sparse['seconds'], 85, delta=3)

    def test_estimate_uses_matching_large_exports_for_check(self):
        # CT114 render-stats after the 0.2.15 seed export: older, smaller-check rows in the
        # 9+ lane band and many 1.1k rows used to pull the all-time check down to 160 s.
        old = [dict(video=64, wall=307, check=150, events=20000, workers=3, screen_lanes=11, at=1),
               dict(video=64, wall=290, check=140, events=20000, workers=2, screen_lanes=11, at=2),
               dict(video=64, wall=300, check=160, events=17000, workers=3, screen_lanes=11, at=3)]
        small = [dict(video=34, wall=w, check=c, events=1118, workers=3, screen_lanes=7, height=h, at=10+i)
                 for i, (w, c, h) in enumerate([(80.6, 52.7, 720), (99.4, 53.0, 1080), (121.7, 53.7, 1440), (182.0, 54.5, 2160)])]
        big = [dict(video=64, wall=372.0, check=235.2, events=23277, workers=3, screen_lanes=11, height=1080, at=20),
               dict(video=64, wall=370.6, check=234.4, events=23277, workers=3, screen_lanes=11, height=1080, at=21)]
        folder = rendering.data_dir(self.home); folder.mkdir(parents=True, exist_ok=True)
        (folder/'render-stats.json').write_text(json.dumps(old + small + big))
        est = rendering.estimate(64, self.home, events=23277, workers=3, screen_lanes=11, height=1080)
        self.assertAlmostEqual(est['check_seconds'], 235, delta=2)
        self.assertAlmostEqual(est['seconds'], 372, delta=12)  # render part comes from the render fit
        # Sizes not exported yet still fall back to the fit; 1.1k stays near its own rows.
        self.assertAlmostEqual(rendering.estimate(34, self.home, events=1118, workers=3, screen_lanes=7, height=1080)['check_seconds'], 53, delta=2)
        self.assertGreater(rendering.estimate(64, self.home, events=50000, workers=3, screen_lanes=11, height=1080)['check_seconds'], 235)

    def test_new_stats_rows_record_layout(self):
        folder = rendering.data_dir(self.home); folder.mkdir(parents=True, exist_ok=True)
        rendering._record_stats(folder, 34, 100, 50, 1118, 3, 7, 1080)
        row = json.loads((folder/'render-stats.json').read_text())[-1]
        self.assertEqual(row['layout'], rendering.LAYOUT)

    def test_current_shows_real_profile_name(self):
        self.assertEqual(core.profile_display_name(self.home), 'Default')
        (self.home/'profile.yaml').write_text('display_name: "Sonny HQ"\n', encoding='utf-8')
        self.assertEqual(core.profile_display_name(self.home), 'Sonny HQ')
        sub = self.home/'profiles'/'Research'; sub.mkdir(parents=True)
        self.assertEqual(core.profile_display_name(sub), 'Research')

    def test_resolution_titles_and_limits(self):
        out = service.run(dict(action='demo', timezone='UTC', seconds=15, resolution='720p'), self.home)
        folder = rendering.bundle_path(out['bundle'], self.home)
        html = (folder/'index.html').read_text(encoding='utf-8')
        self.assertIn('data-width="1280" data-height="720"', html)
        self.assertIn('zoom:0.666667', html)
        self.assertNotIn('zoom', (folder/'replay.html').read_text(encoding='utf-8').split('</style>')[0].split('.intro-copy')[-1])
        info = json.loads((folder/'bundle.json').read_text())
        self.assertEqual((info['width'], info['height'], info['resolution']), (1280, 720, '720p'))
        self.assertIn('Synthetic demo', info['title'])
        (folder/'job.json').write_text(json.dumps(dict(id=out['bundle'], state='failed')))
        self.assertIn('Synthetic demo', rendering.status(self.home)[0]['title'])
        with self.assertRaises(ValueError):
            service.run(dict(action='demo', timezone='UTC', resolution='8k'), self.home)
        with self.assertRaises(ValueError):
            service.run(dict(action='demo', timezone='UTC', events_limit=12345), self.home)
        status = service.run(dict(action='status'), self.home)
        self.assertEqual(status['source_names']['current'], 'Default')
        self.assertEqual(status['event_limits'], [20000, 50000, 100000])

    def test_bounds_fail_without_exports(self):
        for args in (dict(action="demo", seconds=999), dict(action="build", hours=float("nan")),dict(action="build", profiles="all")):
            with self.assertRaises(ValueError):
                service.run(args, self.home)

    def test_all_time_retains_limits_and_uses_available_history(self):
        with patch('timeline_test.service.core.collect',return_value=([event()],[])) as collect:
            out=service.run(dict(action='build',range='all',history=True,timezone='UTC',seconds=15),self.home)
        self.assertEqual(collect.call_args.args[1],0)
        self.assertTrue(collect.call_args.args[3])
        self.assertIn('All available history',' '.join(out['warnings']))

    def test_cli_ranges_and_pacing(self):
        ns=service.parser().parse_args(['build','--days','14','--history','--pace','balanced'])
        self.assertEqual(ns.days,14)
        self.assertEqual(ns.pace,'balanced')
        ns=service.parser().parse_args(['build','--all-time'])
        self.assertTrue(ns.all_time)
        self.assertEqual(ns.seconds,30)
        for pace in ('social','balanced','linear','orbit'):
            result=service.run(dict(action='demo',pace=pace,timezone='UTC',seconds=30),self.home)
            self.assertEqual(result['duration'],30)  # requested length is the whole video
        orbit=service.run(dict(action='demo',pace='orbit',timezone='UTC',seconds=30),self.home)
        composition=(rendering.bundle_path(orbit['bundle'],self.home)/'index.html').read_text(encoding='utf-8')
        self.assertIn('"pace":"orbit"',composition)
        self.assertIn('hf-seek',composition)  # canvas layer redraws from HyperFrames time
        self.assertEqual(orbit['pace'],'orbit')

    def test_mapping_is_monotonic_and_shortens_quiet_gaps(self):
        model=core.replay([event(t) for t in (100,101,102,10000)],timezone_name='UTC')
        social=presentation.anchors(model,'social')
        linear=presentation.anchors(model,'linear')
        self.assertEqual(social[0],{'real':0,'screen':0})
        self.assertEqual(social[-1]['screen'],1)
        self.assertTrue(all(a['real']<b['real'] and a['screen']<b['screen'] for a,b in zip(social,social[1:])))
        self.assertLess(social[-1]['screen']-social[-2]['screen'],linear[-1]['screen']-linear[-2]['screen'])
        self.assertEqual(len(model['events']),4)

    def test_setup_is_a_reviewable_request_not_an_install(self):
        report={'ready':False,'items':[{'label':'HyperFrames','ready':False}]}
        with patch('timeline_test.dependencies.inspect',return_value=report),patch('timeline_test.dependencies.subprocess.run') as spawn:
            result=dependencies.setup_request(self.home)
        spawn.assert_not_called()
        self.assertIn('Install only missing',result['prompt'])
        self.assertIn('connected Hermes host',result['prompt'])
        self.assertIn('--prefix',result['prompt'])
        self.assertFalse(core.data_dir(self.home).exists())

    def test_configured_paths_persist_without_gateway_environment_changes(self):
        cli=self.home/'hyperframes.mjs';cli.write_text('// fixture')
        browser=self.home/'chrome';browser.write_text('fixture')
        dependencies.configure(str(cli),str(browser),self.home)
        with patch.dict(os.environ,{},clear=True),patch('timeline_test.rendering.shutil.which',return_value='node'):
            self.assertEqual(rendering.renderer_command(self.home),['node',str(cli)])
        self.assertEqual(dependencies.browser_path(self.home),str(browser))

    def test_global_event_limit_keeps_latest_and_warns(self):
        rows=[event(t) for t in (1,2,3,4,5)]
        with patch('timeline_test.core.EVENT_LIMITS',(3,)),patch('timeline_test.core.read_store',return_value=(rows,[])):
            events,warnings=core.collect(['current'],0,10,home=self.home,limit=3)
        self.assertEqual([e['time'] for e in events],[5,4,3])
        self.assertIn('newest 3',' '.join(warnings))

    def test_terminal_hud_is_metadata_only(self):
        from timeline_test.terminal import snapshot
        with patch('timeline_test.terminal.core.collect',return_value=([event(status='success')],[])):
            result=snapshot(['Research'],minutes=1,home=self.home)
        self.assertEqual(result['profiles'][0]['tools'],1)
        self.assertEqual(result['profiles'][0]['recent'],'terminal')
        self.assertNotIn('args',json.dumps(result))

    def test_native_registration_and_recorded_hook_shapes(self):
        class Context:
            hooks = {}
            tools = {}
            commands = {}
            def get_config(self, key, default=None):
                return default
            def register_hook(self, name, handler):
                self.hooks[name] = handler
            def register_tool(self, **kw):
                self.tools[kw["name"]] = kw
            def register_command(self, name, **kw):
                self.commands[name] = kw
            def register_cli_command(self, **kw):
                pass
        ctx = Context()
        plugin.register(ctx)
        with patch("timeline_test.core.active_home", return_value=self.home):
            ctx.hooks["pre_llm_call"](session_id="one", turn_id="t1", user_message="secret prompt")
            ctx.hooks["post_tool_call"](session_id="one", tool_call_id="tc1", tool_name="terminal", result="private output", args={"command":"secret"}, status="success", duration_ms=200)
            ctx.hooks["post_llm_call"](session_id="one", turn_id="t1", assistant_response="private response")
            ctx.hooks["on_session_end"](session_id="one", completed=True)
            ctx.hooks["subagent_start"](parent_session_id="one", child_session_id="two", child_goal="PRIVATE")
            events,_=core.read_store(self.home, 0, 253402300799)
        self.assertEqual(len(events), 4)
        self.assertEqual(sum(e["kind"]=="turn_end" for e in events), 1)
        self.assertNotIn("secret", json.dumps(events))
        self.assertNotIn("PRIVATE", json.dumps(events))
        self.assertEqual(len(ctx.hooks), 8)
        self.assertIn("replay", ctx.commands)


if __name__ == "__main__":
    unittest.main()
