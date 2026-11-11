# Timeline Replay 0.5.0 — November 11, 2026

Six more canvas styles, Style/Pacing picker, both-part updates, HyperFrames version check, per-family estimates, Skyline reframed.

- **CT114 real data, 0.4.0** (HOST8; 6 cores, 12 GiB, 3 workers): Orbit all-time 60 s 1080p 274 s (check 123, render 148); Galaxy all-time 60 s 237 s (101/133); Skyline 7 days 30 s 44 s (8/36). Social on the same data: 372 s and 100 s. All verified by ffprobe, gate 0 errors. HOST8's contact sheet showed a Skyline framing defect (city in the left/centre, detached row labels), fixed in 0.5.0.
- **Development PC, 0.5.0:** 49 Python tests pass in repeated runs; the Desktop harness covers the Style picker and both-part update link; the seek harness passes for Social, multi-profile and all canvas styles; lane visibility passes. HyperFrames check, 0 errors and 0 runtime and lint warnings (2 known craft warnings): all 12 paces at 1.1k events 1080p; river, pulse, clock, neural, rain, ridgelines and skyline at 20k events; neural, river and skyline at 4K. Frame draw at 20k events: 2–6 ms for the new styles. Not yet measured: the six new styles and the reframed Skyline rendered on CT114 with real data.

# Timeline Replay 0.4.0 — November 11, 2026

Galaxy and Skyline paces. Development PC: 47 Python tests pass; 1 failure in about 25 repeated runs, not reproduced in 12 runs under parallel render load and not captured (the earlier clock-patching flake is fixed, so this is a different, unidentified test). The Desktop, seek (Social, multi-profile, Orbit, Galaxy, Skyline) and lane-visibility harnesses pass. HyperFrames check: 0 errors, 0 runtime warnings, 0 lint warnings (2 known craft warnings) for Social, Orbit, Galaxy and Skyline at 1.1k events, Galaxy and Skyline at 20k events, Skyline at 8k, and Galaxy and Skyline at 4K. The composition sits about 3 lines under HyperFrames' 300-line lint threshold, so 0.5.0 must ship per-pace code. Frame draw time at 20k events in headless Chromium: Galaxy about 4 ms, Skyline about 2 ms. Not yet measured: Galaxy and Skyline MP4s rendered on CT114 with real data.

# Timeline Replay 0.3.0 — November 11, 2026

Orbit pace, host setup check, test fixes. Development PC: 47 Python tests pass in repeated runs (the clock-patching test no longer fails under load). The Desktop harness (version notice with a 9.9.9 host), the seek harness (Social, multi-profile and Orbit replays) and the lane-visibility check pass. HyperFrames check (0 errors, 0 runtime warnings; 2 known craft warnings) on Orbit at 1.1k events (1080p and 4K), 8k events and 20k events (1080p), and on Social 1080p. HyperFrames snapshot confirms the Orbit canvas draws in the export path. Orbit draws a frame in about 13 ms at 20k events in headless Chromium. Not yet measured: an Orbit MP4 rendered on CT114 with real data.

# Timeline Replay 0.2.18 — November 11, 2026

Desktop/host version notice with an Update Desktop page button (Hermes' Desktop-only install link); composition code is unchanged. Development PC: 46 Python tests pass. The Desktop harness now also covers the notice: the link opened, the fallback with copy-link when it can't open, no button when the page is newer, and no install request from the plugin. The seek and lane-visibility harnesses pass. HyperFrames check on the medium Social 1080p stress fixture: 0 errors, 0 runtime warnings, 2 known craft warnings. The Desktop button itself needs a check in a real Desktop connected to a remote host.

# Timeline Replay 0.2.17 — November 11, 2026

Intro text in the page header and Settings → About, and an MIT LICENSE; composition code is unchanged. Development PC: 46 Python tests pass; the Desktop harness (now also asserting the intro text), seek and lane-visibility harnesses pass; HyperFrames check on the medium Social 1080p stress fixture: 0 errors, 0 runtime warnings, 2 known craft warnings.

# Timeline Replay 0.2.16 — November 11, 2026

An estimate and README release; composition code is unchanged. Development PC: 46 Python tests pass, including a regression test built from HOST8's CT114 render-stats rows (all-time check now 235 s against 234–235 s actual, previously 160 s). The Desktop, seek and lane-visibility harnesses pass, and the HyperFrames check on the medium Social 1080p stress fixture (1,159 events, 7 lanes) has 0 errors and 0 runtime warnings, with the 2 known craft warnings. Correction: the 0.2.15 note below says 46 Python tests, but that release had 44; the 2 new tests bring the count to 46.

# Timeline Replay 0.2.15 — November 11, 2026

An estimate and README release; visual code is unchanged from 0.2.14, whose gate results apply. 46 Python tests, the Desktop harness and the seek harness pass. The README resolution table and the 50k figures are HOST8's CT114 measurements of 0.2.14.

# Timeline Replay 0.2.14 — November 11, 2026

| Check | Result |
| --- | --- |
| HyperFrames gate | 0 errors and 0 runtime warnings: Social at 720p / 1080p / 1440p / 4K (data-width/height 1280×720 … 3840×2160, no root-zoom lint), Balanced 11-profile at 720p, Linear 1080p, demo. Craft warnings only. |
| Lane visibility | Social and Linear 7-profile and the demo at 1080p: every lane inside the plot. |
| Frames | handoff/frames-0.2.14/ (Social at 720p and 1440p). |
| Tests | 46 Python (new: resolution and zoom in the export only, bundle and job titles, invalid resolution/limit rejected, `source_names`). The Desktop harness now covers the settings page (4 pages render) and checks that a Settings default (720p, 50k) reaches the build request. Seek harnesses pass. |

Not verified here: real renders at each resolution (BeginFrame path, timings, ffprobe sizes) and the settings page inside real Desktop and Webapp. Both belong to the CT114 test.

# Timeline Replay 0.2.13 — November 11, 2026

| Check | Result |
| --- | --- |
| Lane visibility (tests/lanes_visible_check.mjs, real browser) | Every lane label and lane row inside its plot and the frame: Social/Balanced/Linear at 7 and 11 lanes, Social `lanes=4`, demo. |
| HyperFrames gate | 0 errors and **0 runtime warnings**: Social 7/11, Balanced 7/11 (one screen, compact), Linear 7/11, Social `lanes=4`, demo. Craft warnings only. |
| Tests | 43 Python (new: display name from profile.yaml, "Default" fallback); Desktop and seek harnesses. |
| Frames | handoff/frames-0.2.13/ (Balanced 11 on one screen, Linear 7, Social 11). |

# Timeline Replay 0.2.12 — November 10, 2026

| Check | Result |
| --- | --- |
| Performance (local, 11 profiles / 20k events, Social 64 s) | Animated elements: 2,522 (0.2.11) to **1,372** (0.2.8 3-chapter: 1,949). HyperFrames check wall time: 86 s to **65 s** on this PC. Host numbers come from CT114. |
| HyperFrames gate | 0 errors: Social 7 / 10 / 11 (20k), Social lanes=4, Balanced 7, Balanced 10 lanes=all, Linear 7, demo. Craft warnings only. |
| Tests | 42 Python (new: estimates prefer the same screen density); Desktop and seek harnesses. |
| Frames | handoff/frames-0.2.12/ (7-profile at 12 s, 11-profile at 45 s). |

# Timeline Replay 0.2.11 — November 10, 2026

| Check | Result |
| --- | --- |
| HyperFrames 0.9.23 gate | **0 errors in every section**: Social 7 profiles (stacked, 1 chapter), Social 10 profiles, Social all-time 11 profiles / 20k events (stacked, rotating cards), Social with `lanes=4` (chapters), Balanced 7, Balanced 10 with `lanes=all`, Linear 7, demo. Craft warnings only: small auxiliary text and silent film, plus counter-tick `line_unread` notes on the 20k fixture where stats update every 0.5 s by design. |
| Frames reviewed | handoff/frames-0.2.11/: 7-profile Social at 1.2/12/32.5 s, 11-profile all-time at 20/45/62 s, `lanes=4` at 6 s, and a 0.2.6 "before" frame (3-chapter all-time). |
| Python tests | 41 passed (new: `lanes` option validation and settings). |
| Desktop / seek harnesses | Passed. The 12-profile seek fixture is now 1 chapter in Social. |

# Timeline Replay 0.2.10 — November 10, 2026

| Check | Result |
| --- | --- |
| CSP reproduction (local chrome-headless-shell, real demo replay.html in a sandboxed srcdoc frame) | Under the exact Webapp policy from Sonny's console: **replay does not run**, with 1 "Executing inline script violates … script-src" message. Under the gateway guest-shell policy (`_GUEST_SOURCES`): **replay runs**, 0 CSP messages. |
| Desktop harness | Browser host renders `SDK.SandboxedFrame` with a `data:text/html` src containing the replay; Electron UA renders the direct `srcdoc` iframe. |
| Python tests / seek | 40 passed / passed. |

Not verified here: the real gateway guest shell relaying a 5 MB document and the Loop messages. That belongs to the CT114 Webapp test.

# Timeline Replay 0.2.9 — November 10, 2026

40 Python tests pass (new: warm-up ETA with a mocked clock). The Desktop harness passes. README sizing figures are HOST8's CT114 measurements from 0.2.5–0.2.8, not development-PC runs.

# Timeline Replay 0.2.8 — November 10, 2026

39 Python tests pass (new: `serving_profile` in status, profile label resolution). The Desktop harness now also covers the other-profile state: the message names the Desktop profile, and **Switch to Default profile** runs `ctx.runAction('profile.default')`. Visual code is unchanged from 0.2.7.

# Timeline Replay 0.2.7 — November 10, 2026

| Check | Result |
| --- | --- |
| Python tests | **38 passed**. New: completed jobs expose `video_path`; slim preview without origin, with the Loop control and a `loop:false` default; low-memory note at 8192 MB and none at 12288 MB. |
| Desktop harness | Passed, now with an SDK mock for `MessageTextContent`/`captureGatewayFileDownload` and `ctx.storage`. |
| Real browser (HyperFrames' local chrome-headless-shell via puppeteer-core; no downloads, no server) | Demo at 4×: Play once stops at 30.0 s with **Replay**; turning Loop on restarts and keeps playing (6.1 s into the next pass); 0 page errors. The 20k all-time preview (5.2 MB) loads and builds 1,949 animations in about 0.4 s, so building the page is not the Webapp bottleneck. |
| Seek harnesses | Passed. |

Not verified here: the MEDIA player and download inside real Desktop and Webapp, and the Webapp preview over the network. Both belong to the CT114/Webapp test.

# Timeline Replay 0.2.6 — November 10, 2026

36 Python tests pass. New: `@hf-progress` capture and encode parsing; the render-rate fit reproduces CT114's 20k render at about 187 s; mixed live/history finale shares. The Desktop and seek harnesses pass. The HyperFrames gate reports 0 errors on medium Social, all-time Social and the demo.

# Timeline Replay 0.2.5 — November 10, 2026

35 Python tests pass. New: CT114's multi-worker lines and the encode label; a silent 3.5 s check stage where the ticker keeps `elapsed` moving. The Desktop and seek harnesses pass. Visual code is unchanged from 0.2.4, so the 0.2.4 HyperFrames gate results apply. Real multi-worker renders are tested on CT114.

# Timeline Replay 0.2.4 — November 10, 2026

33 Python tests pass (new: vendor-prefix stripping, empty fallback, sublinear check fit against the CT114 points). The Desktop and seek harnesses pass. The HyperFrames gate reports 0 errors on medium Social/Balanced, large Social, all-time Social (fixture now includes a vendor-prefixed model) and the demo. Reviewed the finale snapshot. The switch debounce is not yet checked against real CT114 history.

# Timeline Replay 0.2.3 — November 10, 2026

32 Python tests pass. New tests: versions agree across version.py, plugin.yaml, manifest and plugin.js; a stale `client_api` is rejected; bundle.json records the version; the worker override works; frame-based % is used; no ETA once check samples finish. The Desktop harness now also covers the setup toggle closing, the version label and `client_api`. Seek harnesses pass. The HyperFrames gate reports 0 errors on medium Social, all-time Social and the demo. Not exercised: the stale-version banner against a real host update, and multi-worker rendering. Both belong to the CT114 test.

# Timeline Replay 0.2.2 — November 10, 2026

| Check | Measured result |
| --- | --- |
| HyperFrames 0.9.23 check | **ok=true, 0 errors in every section** on medium Social 34 s / Balanced 36 s / Linear 30 s, large (10 profiles, 8k events) Social 64 s, all-time (11 profiles, 20k events, 72 days, 3 chapters) Social 68 s, and the demo. All fixtures include model/provider switches. Craft: two warnings each (small auxiliary text, silent film). |
| Snapshot review | All-time fixture at 6 s, 22.2 s and 66 s: compressed axis with real-clock ticks, chapter counters, model readouts on cards and lanes, chapter card, models line in the finale. |
| Python tests | **30 passed.** New: progress parsing plus a real `
`-progress child process through `_stream`; provider sanitizing that keeps ids unchanged; the models toggle; the learned estimate after a completed job. |
| Seek / Desktop harness | Both seek fixtures 901 frame steps plus reverse seeks; Desktop harness passed. |

Not verified here: live progress against a real HyperFrames render, `billing_provider`/token columns on CT114's state.db, and the encoded MP4. These belong to the CT114 test.

# Timeline Replay 0.2.1 layout-gate fix — November 10, 2026

| Check | Measured result |
| --- | --- |
| Reproduction | Before the fix, local HyperFrames 0.9.23 `check` on real-shaped synthetic fixtures (`tests/stress_fixture.py`) reproduced the CT114 classes. Social, 7 profiles: 7 layout errors (pop overlap, end tick occluded). Balanced: 5 (also clipped lane labels). 10-profile Social: 18 (also a clipped profile card and a label covered by a burst). |
| After the fix | **ok=true, 0 errors in lint/runtime/layout/motion/contrast** for medium Social 34 s, medium Balanced 36 s, medium Linear 30 s, large Social 64 s and the public demo. Craft keeps warnings only: small auxiliary text and a silent film (47 small-text warnings on the 10-profile fixture). |
| Python tests | **27 passed**, including new tests: a failed check is summarized and blocks render; a stale `running` job becomes `interrupted` when the render lock is free and stays `running` while it is held. |
| Seek / Desktop harness | Both seek fixtures passed 1,021 frame steps plus reverse seeking; the Desktop behavior harness passed. |

Limits: the fixtures are synthetic and rendered with Windows fonts. Text fitting uses the renderer's own fonts at build time, so it should hold on Linux, but that is unverified until the CT114 check passes. No MP4 was encoded on the development PC.

# Timeline Replay 0.2.0 validation — November 10, 2026

This is a tested code package, not a claim that the updated plugin has been installed in the user's live Desktop app.

| Check | Measured result |
| --- | --- |
| Python tests | **25 passed**: prior metadata/privacy/storage checks plus all-time range selection, days/CLI flags, pacing monotonicity, gap shortening, render configuration persistence, reviewable setup without installation, bounded latest-event selection and the terminal HUD. |
| Hermes admission validator | **16/16 passed, zero warnings**, including SDK surface, declared hooks/tools, isolated registration, security scan and no core overrides. |
| API routes | In-process FastAPI tests passed status, five prerequisite checks, setup-request generation, pure sample preview with no bundle write, normal demo/preview/export routes and rejected unsupported actions/sources. |
| Desktop behavior harness | Passed native SDK control usage, initial sample loading, all-time/Social/30-second/history build payload, setup request drafted without installation, and disabled video export before readiness. |
| Seek harness | **1,021 frame steps each** for a 34-second four-lane Social sample and a twelve-lane/three-chapter fixture, plus reverse seeks, chapter visibility and real-time/presentation-time round trips. |
| Real browser, standalone replay | Passed playback controls, repeated backward seeking, paused reduced-motion finale, 390px viewport fit, zero page errors and zero HTTP(S) requests. |
| Desktop design fixture | Browser-checked dark/light theme variables, responsive width, embedded sample playback and zero page errors. The fixture uses the actual component source with a mocked SDK; it is not an automated run inside live Hermes Desktop. |
| HyperFrames composition check | **ok=true**; lint, runtime, layout, motion and contrast each had zero errors and zero warnings on the final Social fixture. Samples at 0, 2.5, 8, 15 and 30.8 seconds. |
| Visual review | Inspected the Desktop layout and activity-stage screenshots; corrected text clipping/contrast and intentional intro-overlay layout annotations. |

The craft audit retains **two warnings**: dense auxiliary labels below the generic phone-video font-size floor, and a silent film. Primary counters/profile names are larger; the current export has no audio. The intro intentionally overlays the underlying scene and is marked for that layout relationship. Informational occlusion findings during that opening are expected.

Tested renderer: **HyperFrames 0.9.23**, using only an existing installation. No dependency downloads or MP4 encoding were performed on the development/main PC. Encoder command construction, limited environment, file locking and completion/failure verification remain covered with mocks. A real new-version MP4 still needs a smoke test on the installed Hermes host.

Native APIs were checked against installed Hermes source commit `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19` in NousResearch/hermes-agent. No shared engine/configuration was modified, no live profile was enabled, no service was restarted and no inference endpoint was contacted.

## Target-host acceptance

1. Replace the installed code with 0.2.0, preserving `plugin-data/timeline-replay` and enrolled sources.
2. Restart/rescan the test gateway/Desktop plugin and confirm the new native controls follow the selected app theme.
3. Open Video setup. Confirm detected prerequisites, prepare the missing-tools request, and review/send it if installation is needed. Recheck readiness afterward.
4. Compare Social and Linear previews for a small real range, then test days/all-available with coverage notes visible.
5. Render a 15- or 30-second Social cut on that host and inspect the encoded video.
6. Test `hermes replay watch`, plus a CLI build/render using the same profiles and pacing.
