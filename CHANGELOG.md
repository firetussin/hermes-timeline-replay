# Changes

## 0.3.0 — November 11, 2026

Update the Desktop page too (it changed). On a remote host, the page's **Update Desktop page** button does this.

- **New pace: Orbit.** A turning 3D ring: each profile owns a colour sector of a flattened torus; every event shoots out as a ray when the replay reaches its real time, outward only (tilted up to ~40° above or below the ring, never into the centre), with ray length ranked by tokens, else duration, else the average. The camera sways and rolls slightly. Beside it: live counters, per-profile live counts, an activity line, model share, a callout on the newest notable event, and a token stream by profile. One canvas drawn purely from replay time (player seek and HyperFrames `hf-seek`); up to 3,600 rays, one per several events above that. Choose it under Pacing, in Settings → Playback, or with `--pace orbit`.
- **Host setup check:** `hermes replay dependencies` and Settings → About warn when `<HERMES_HOME>/desktop-plugins` isn't writable by Hermes (CT114 had it root-owned, so the Webapp page silently failed to install). README has a Troubleshooting section.
- **Tests:** the render-ETA test no longer patches the global clock (it failed intermittently under load); the seek harness is pace-aware; Orbit builds are covered.
- **README:** Orbit section, Troubleshooting, and a credit for the visualization that inspired Orbit.

## 0.2.18 — November 11, 2026

Update the Desktop page too (it changed).

- **Desktop/host version notice:** with a remote Hermes host, updating the host never updated the Desktop copy, and the old notice's Reload just reloaded the same old page. When the host is newer, the page header and Settings → About now show the two versions and an **Update Desktop page** button. It opens Hermes' Desktop-only install link (`hermes://plugin-desktop/install?…&force=1`), so Hermes' install dialog opens with only Desktop selected and nothing installs until you confirm. If the link can't be opened, the notice shows the Install from Git steps and a copy-link button. When the page is newer than the host, it says to update the host instead.
- **README:** a "Keeping Desktop in step with a remote host" section and a Disclosures line for the update link.

## 0.2.17 — November 11, 2026

- **Explains itself in the app:** a short intro under the page title and as the first row of Settings → Plugins → Timeline Replay → About (what it does; metadata only, no prompts, transcripts or tool results).
- **License:** MIT (`LICENSE`).

## 0.2.16 — November 11, 2026

- **Estimates:** the all-time check was still estimated at 160 s when CT114 had two identical exports taking 234 s. Check time now comes straight from recent exports with a similar event count (within ±15%, median of the newest three), narrowed to the same layout, worker count and lane density. The power-law fit only covers sizes the host hasn't exported yet, and only its newest rows. New stats rows record a layout version, so rows from the older chapter layout stop counting once newer ones exist.
- **README:** removed the stale "1920×1080 only" and "four lanes per chapter" lines and a development-run note; resolution cost figures now match the CT114 table.

## 0.2.15 — November 11, 2026

- **Estimates:**
  - Learned history keeps the last 50 exports instead of 10, so a run of small test renders no longer evicts the large ones. This is the likely cause of the 50k all-time check being estimated at 159 s against 236 s actual.
  - Before a resolution has its own rows, render time scales by pixels^0.7 (measured on CT114) instead of linearly: the 4K prior had said 238 s against 182 s actual.
- **"4k"** (also "uhd", "720", "1080", "1440", "2160") is accepted as a resolution alias.
- After a build, the page shows how many events the replay holds next to the limit, so it's clear when a higher limit isn't binding.
- **README:** a "What it does" overview, the CT114 resolution table, current test commands, and a Thanks section crediting Nous Research and Hermes Agent, HyperFrames by HeyGen, FFmpeg, Chromium and Puppeteer, Node.js, Python, SQLite, React, Sonny, the HOST8 maintenance agent and Claude Code.

## 0.2.14 — November 11, 2026

Sonny's requests via HOST8.

- **Settings → Plugins → Timeline Replay** (`ctx.registerSettingsPage`, with a `SETTINGS_PLUGINS_AREA` fallback for older hosts). Built from ToggleRow/ListRow/SegmentedControl and stored per user in `ctx.storage`.
  - **Playback** (landing page): default pace, Lanes per screen, Play once/Loop, models & providers.
  - **Build:** default range, length, history, default profiles (by display name), timezone.
  - **Export:** resolution, render workers (Auto/1–4, saved on the Hermes host), event limit with impact notes, host performance notes.
  - **About:** page, loaded and installed versions, API, backend profile, renderer readiness.
  
  The main page starts from these defaults, follows changes live, and keeps its quick per-build controls. A line under the build buttons shows the export resolution and event limit, with a link to Settings.
- **Event limit:** 20k (default), 50k or 100k per replay, via `events_limit` or `--events-limit`. Session rows scale with it (max(2,000, limit/10)). Capture retention is unchanged (20k events / 30 days per profile), so higher caps mostly help history imports. The notes state the cost: check ≈ events^0.45, previews ~5 MB per 20k events.
- **Resolution:** 720p, 1080p (default), 1440p or 4K, via `resolution` or `--resolution`. The composition root is the real output size and each scene zooms its 1920×1080 layout; HyperFrames honours zoom on descendants and flags zoom on the root. This keeps native capture and BeginFrame, where HyperFrames' own `--resolution` supersamples through screenshot capture. ffprobe verifies the chosen size. bundle.json and job.json record it, and estimates learn per resolution (pixel-scaled from 1080p until learned).
- **Exports list:** rows read "Video ready · Hermes activity · Last 7 days · Social · 34 s · 7 profiles", with the created time as secondary text and the bundle id in a tooltip. The same titles appear on running and failed rows.
- **Source picker** shows display names ("Default" instead of "current").

## 0.2.13 — November 11, 2026

From Sonny's feedback via HOST8.

- **No chapters by default in any pace.** Auto now stacks up to 16 lanes in Balanced and Linear too; previously 8, so 11 profiles split into 8 + 3. Balanced and Linear get the same compact fixed layout as Social, minus the signal band: lanes get 654 px (rows up to 80 px, 100 px for ≤4 lanes). "4" remains the explicit chapter look.
- **Real profile names, not "current".** "current" is only the internal key for this backend's own Hermes home. Viewers now see Hermes' presentation `display_name` from that profile's `profile.yaml`, else the profile name ("Default" for the root profile), in lanes, cards, captions, the finale and the counts. The CLI and UI keep `current` as the selector.
- **Lane visibility check.** New `tests/lanes_visible_check.mjs` (real browser, local puppeteer-core and Chromium) asserts every lane label and lane row sits inside its plot and the frame, at every chapter. It passes for Social, Balanced and Linear at 4, 7, 10 and 11 lanes, and with `lanes=4` and `lanes=all`. While writing it, it caught a Social script error in this build's band change (fixed before release).
- **Signal band:** the hub and card cluster move left (hub at x 740), so the tool/model readout gets 560 px instead of 330.
- Fixed before release: two Social hub keyframes used `${hubX}` in plain strings, so the browser rejected them (runtime console warnings in the gate). They are template literals now. The release gate now also requires **0 runtime warnings**, not only 0 errors.
- **Lighter check:** lane row boxes, gridlines and night bands are also marked `data-layout-ignore` (no text). Axis ticks stay audited.
- Not done: Sonny's optional "cards circle the hub" idea. He was unsure, so the 2×2 rotation stays for now.

## 0.2.12 — November 10, 2026

From the CT114 0.2.11 renders. Stacking worked on real data, but exports were 40–50% slower (7d 85 → 125 s, all-time 307 → 440 s), because every lane's dots and effects were on screen for every check sample and frame.

- **Leaner stacked screens.**
  - Event dots, bars and lane flashes move into one decorative layer, and sparks, rings, packets, card glows and hub waves are marked too. HyperFrames' `data-layout-ignore` means the layout audit never walks them; they carry no text.
  - Dot buckets per lane scale with the lane count (budget ~700 per screen: 160 per lane at 4 lanes, unchanged, ~63 at 11).
  - Burst spacing scales with lanes/4, and stacked Social uses 4 sparks per burst instead of 7.
  - On the 11-profile / 20k fixture, animated elements fell from 2,522 to 1,372, below the 0.2.8 three-chapter build's 1,949. The local layout check went from 86 s to 65 s.
- **Estimates by screen density.** bundle.json records `screen_lanes`. Learned rows store it, and estimates prefer exports with similar density (≤4, 5–8, 9+ lanes), the way they already prefer the same worker count. Older rows are used as a fallback.
- **Hub readout** fits its 330 px slot (no mid-word cut). **Card swap-in** animates brightness only, so slots keep a fixed width in every frame. **Packets** end at the stats strip's edge instead of entering a card. The **"RECORDED EVENT SIGNALS"** label is gone from compact Social; the legend explains the signals.

## 0.2.11 — November 10, 2026

Sonny: Social is the most entertaining pace but split profiles into chapters, and the layout wasted space at the top and in the middle.

- **Social stacks every profile on one screen.** Up to 16 lanes before chapters (previously 4 per chapter). Rows size themselves to the lane area: up to 100 px for ≤4 lanes, 80 px otherwise, 30 px minimum. The model sub-line shows from 40 px rows. All the Social energy is kept: pops, sparks, rings, packets, hub, variable speed.
- **Compact Social layout (fixed positions, 1080p):**
  - one title row with the clock beside it;
  - a slim stats strip;
  - the legend on one line;
  - a 110 px signal band;
  - the "Recorded moment" caption directly under the lanes.
  
  The lane area grew from about 190 px to 544 px. Blocks are absolutely positioned, so host fonts cannot push them.
- **Signal band:** the hub sits with four card slots in a tight cluster around it, not at the frame edges. With more than four lanes the cards show the four most active profiles in each stretch of the replay. A profile keeps its slot while it stays in the top four, and newcomers flash in. Lanes always show every profile. Only profiles on a card send a signal packet; the hub pulses for every event.
- **Lanes per screen option:** Auto (default; Social up to 16, Balanced/Linear 8), 4 (the old chapter look), All (up to 16 for every pace). Available as a Desktop selector (remembered per user), `--lanes auto|4|all` in the CLI and `lanes` in the tool; recorded in bundle.json.
- The milestone pop is smaller in Social and sits above the clock card. The card glow is softer (contrast ≥ 4.5:1 for the model line). The hub label reads "EVENTS".

## 0.2.10 — November 10, 2026

- **Webapp preview fixed (CSP).** The browser-hosted Webapp serves its page with `script-src 'self' blob: 'wasm-unsafe-eval'` plus fixed hashes (hermes_cli/webapp_page_policy.py). A `srcdoc` iframe inherits that policy, so the replay's inline scripts never ran (Sonny's Firefox console: "blocked an inline script … srcdoc"). Native Desktop has no such policy, which is why it worked there. In the Webapp the preview now uses the SDK's `SandboxedFrame` with a `data:text/html` URL. The SDK re-serves that through the gateway guest shell (`/assets/webapp-guest.html`, guest policy with inline scripts and styles, opaque sandbox), as documented for this case. Electron Desktop keeps the direct `srcdoc` frame, which avoids Chromium's ~2 MB navigation URL cap for large replays. The data URL is encoded once per document (memoized), so polling never reloads it. The Loop `postMessage` bridge works through the shell (`event.source === ref.current.contentWindow`, post to `parent`).

## 0.2.9 — November 10, 2026

- **README host sizing, measured.** CT114 at 2 cores/8 GiB/1 worker: ≈210 s (7d) and ≈500 s (all-time). At 4/8/2: ≈118 s and ≈377 s, both low-memory screenshot. At 6/12/3: 85 s and 307 s with BeginFrame parallel streaming. Above 8 GiB, BeginFrame works under software GL and is clearly faster; check time scales with cores.
- **Render ETA warm-up.** The first frames are slow (browser and encoder start), so the frame rate is measured only after max(5% of frames, 5 s). Until then the ETA counts down from the learned render time, or none is shown. CT114 had shown 261 s left at frame 3/1020 when about 40 s remained.
- The "Step 1/2 · / Step 2/2 ·" prefix is added by the Desktop UI on purpose. job.json labels stay plain.

## 0.2.8 — November 10, 2026

- **Which profile.** The header shows "Profile: Default · N sources · v0.2.8" from the backend's own `serving_profile` (status also reports `has_data`). When the current Desktop profile has no Timeline Replay backend, the page explains that exports live in the profile where the plugin is enabled, usually Default, and that nothing is missing. If the app offers the `profile.default` action, a **Switch to Default profile** button runs it. An empty list says exports are kept per profile.
- **Exports refresh by themselves.** Every 3 s while a job runs, every 20 s otherwise, and on window focus. Exports started elsewhere (Webapp, another device, an agent's `/replay render`) now appear without pressing Refresh.

## 0.2.7 — November 10, 2026

From Sonny's reports via HOST8.

- **Watch and download exports.** Each finished export has **Watch** and **Download MP4**. Watch plays inline through Hermes' own MEDIA player (`MessageTextContent` with `MEDIA:<path>`), so authentication and range streaming are handled by the host for local and remote gateways, with no plugin video URL or credentials. Download uses the SDK's `captureGatewayFileDownload`, so the native save dialog applies. Jobs now report `video_path`, the absolute path on the Hermes host.
- **Loop / Play once.** A toggle in the preview header, remembered per user with `ctx.storage`. Play once is the default: the HTML replay stops at the finale and its button reads **Replay**. The choice reaches the preview through `postMessage` (the sandboxed preview has no storage of its own), and the replay's own Loop button reports back. Exported MP4s in the player follow the same setting.
- **Preview loading.** Shows "Loading preview…", allows 180 s, and gives a **Retry preview** on failure instead of nothing. Embedded preview data is smaller: compact JSON, no per-event origin, 12-character ids (the 20k all-time preview drops from 6.3 MB to 5.2 MB). The bundle's events.json keeps everything.
- **Host sizing.** New README section on the HyperFrames low-memory profile (≤ 8 GiB, container limit counts), workers and the CT114 timings. Video setup shows non-blocking notes for low memory and for software GL without `/dev/dri`.

## 0.2.6 — November 10, 2026

From the CT114 0.2.5 run, where progress, ETA and the model fix were confirmed.

- **Finale shares fixed.** Shares were taken from API-call events whenever any existed, so the one live-captured profile hid the other ten ("gpt-6.1-sol 100%"). Shares are now counted per session: each (profile, session, model) counts once, from capture or history alike. The line reads "MODELS BY SESSION: …". Providers are tallied the same way and always shown when any are recorded.
- **Machine-readable progress.** `@hf-progress {"code":"capture","done":N,"total":M}` lines are used first, and `encode`/`assemble` become labels. The text wording is kept as a fallback.
- **Steps.** Progress reads "Step 1/2 · Checking…" and "Step 2/2 · Rendering frame…". A label carries across the stage boundary, so no sample is just `{elapsed}`.
- **Render estimate.** Seconds per video second are fitted against event count (`a·events^b`, b 0–0.6, default 0.1). Heavy compositions render slower per frame: about 13.7 fps at 1.1k events against 11.5 fps at 20k on CT114.

## 0.2.5 — November 10, 2026

From the CT114 0.2.3 run. With 2 workers, render time fell from about 150 s to 75 s, but progress broke.

- **Multi-worker progress.** HyperFrames prints "Capturing frame N/M (K workers)" with several workers and "Streaming frame N/M" with one. Both wordings now give frame/frames, percent and an ETA. After capture, encoding or finishing lines ("Encoding…", "Render complete") show as the label at 99% with no ETA claimed.
- **Live refresh.** A progress ticker rewrites job.json every 2.5 s while a stage runs, so elapsed, check percent and the render countdown keep moving between HyperFrames output lines.

## 0.2.4 — November 10, 2026

From the CT114 0.2.2 results.

- **Fixed the literal "model".** History stores vendor-prefixed ids (`anthropic/claude-haiku-5.5`, `oamazonasgabriel/lfm2.5-2.6b:q4_k_m-8gbGPU`). These are now reduced to the model name, the same as live capture. Unusable values become empty and are left out of readouts, switches and the finale. The vendor is not reused as the provider: `billing_provider` and the live `provider` stay the only source.
- **Fewer, steadier switch markers.** A lane groups many sessions, so a model run only counts as a switch when it spans two or more sessions or at least an hour. Detours of one session and back are not drawn, and neighbouring runs of the same model merge. Readouts follow the same runs.
- **Finale.** Shows the top 4 models by usage share, then "+N more", with providers on their own line. Shares come from API-call events when present, otherwise from session records.
- **ETA.** Check time is fitted sublinearly (`a·events^b` in log space, b clamped to 0.2–1.0; 0.45 with only one size seen). CT114's 52 s at 1.1k and 190 s at 20k events are matched within a few seconds; before, 20k was estimated at 959 s. Check estimates use every export; render estimates still prefer exports with the same worker count.

## 0.2.3 — November 10, 2026

From the CT114 0.2.2 run and Sonny's requests (via HOST8).

- **Video setup toggles.** The header button opens and closes the panel (`aria-expanded`, pressed style, "Hide video setup"); Escape also closes it. When the renderer is ready the button reads "Video ready".
- **Versions and stale code.** The header shows `v0.2.3`. Status reports the loaded `version`, the on-disk `installed_version`, `api` and `restart_required`. Every response carries `version`/`api`, and bundle.json/job.json record the version that built and rendered them. Desktop polls status every 60 s and on focus. It shows a Reload banner when the host version differs, and a restart notice when Hermes still has an older copy loaded. Requests carry `client_api`; an incompatible page gets a clear "Reload the page" error and its Build/Export buttons are disabled. Pages from 0.2.0–0.2.2 (API 1) still work.
- **Honest progress.** The render % now follows frames (`frame/frames`), not HyperFrames' overall figure. The check no longer shows a sample-based ETA. Once samples finish it reads "Analysing layout results"; with a learned check time it shows % and an ETA that covers the remaining check plus the expected render. Past the learned time it shows "elapsed · finishing" instead of "0 s left".
- **Render workers.** Automatic by default: half the cores, at least 1, at most 4 (2 on a 4-core CT114). Override with `hermes replay setup --workers N` (0 = automatic) or `TIMELINE_REPLAY_WORKERS`. The worker count is recorded per export, and estimates prefer exports made with the same count.

## 0.2.2 — November 10, 2026

From the CT114 0.2.1 run (HOST8 viewing notes) and Sonny's requests.

- **Export progress and ETA.** check/render output streams into `job.json` `progress` (stage, percent, frame/total, elapsed, ETA). Exports shows "Checking layout 3/9" or "Rendering frame N/M · 53% · ~1 min left" with a bar. After the first export, a build shows "Export ≈ N min on this host". The estimate is learned per host: check time scales with event count, encoding with video length. When an export is already running, a second one gets that export's progress instead of a bare refusal.
- **Models & providers (toggle, default on).** Capture records the provider label and the model that actually answered (`response_model`). Endpoint URLs are never stored, and provider stays out of event ids. History reads `billing_provider`. Profile cards and lane labels show the current model. Recorded switches get a marker and a ticker line, and the finale lists models and providers. Desktop has a "Show models & providers" checkbox; the CLI has `--no-models`.
- **Tokens:** history imports session input+output token totals, counted at session end. Previously only live-captured calls had tokens, so the counter sat at 0 for imported history.
- **Video length is the whole video.** The finale comes out of the requested seconds and is capped at 30%.
- **Chapters:** counters cover the chapter's profiles ("Profiles here / 11", "Tool calls here"). A chapter card explains that each chapter replays the full range. Captions and milestone pops use only that chapter's lanes. Milestones add 2,500, 10,000 and 20,000.
- **Compressed axis for Social/Balanced.** Positions use presentation time, so quiet weeks shrink and the playhead moves evenly. Ticks still print the real clock. Linear is unchanged.
- **Visual fixes:** packets launch from the card edge; card text sits above the glow; the milestone pop moved off the clock; the intro text clears before the backdrop dissolves; no pops under the intro or chapter cards; long model names don't shrink below 10 px; captions don't flash at chapter ends.

## 0.2.1 — November 10, 2026

Fixes real-data MP4 exports failing the `hyperframes check` layout gate (reported from CT114 for Social and Balanced bundles; Linear shares the code).

- Tool-count milestone pops no longer stack. Thresholds that land within one pop lifetime (1.8 s) collapse into the highest one reached, shown at its own recorded time.
- The last axis tick no longer wraps into the plot (it had zero width at `left:100%`). Ticks never wrap, and the first and last ticks align inward.
- Lane labels show the profile name with a small `ALL AGENTS` / `AGENT abc123` line under it. Names are fitted with canvas text metrics: shrink first, then add an ellipsis. Host font differences (Linux `system-ui`) can no longer overflow. The same fitting covers profile cards, the title, the ticker and the activity readout.
- Event rings and sparks render in a clipped effects layer, so they can't cover lane labels or ticks.
- Render jobs run `check --json` into `check.json`. A failed check records per-section error counts and the first errors in `job.json` (`check`), and the error message names them. The render step does not start.
- Job status: a persisted `running` job becomes `interrupted` when no process holds the render lock. It stays `running` while the lock is held. The Desktop panel shows "Export interrupted".
- Added `tests/stress_fixture.py`: real-shaped synthetic fixtures (7 profiles / ~1,160 events and 10 profiles / ~8,060 events over 7 days, long profile names) for the layout gate.

## 0.2.0 — November 10, 2026

- Replaced the full-width setup form with a preview-first Desktop layout using Hermes SDK buttons/inputs and app theme variables. Added profile chips, connection recovery, sample motion and exports/status areas.
- Added 24-hour, 7-day, 30-day, custom-day and all-available selections. Read-only imports now favor recent records within explicit limits; combined overflow is capped visibly rather than silently presented as complete.
- Added Social/Balanced/Linear pacing. Social includes an animated profile/event-feed stage, signal packets, rings/sparks, lane flashes, counter impacts, matching delegation links, tool-count milestones and a larger finale. Real timestamps and inverse seek mapping are preserved.
- Added five-part video readiness and a targeted setup request that can be drafted into Hermes chat or copied. No installation happens on panel open. Added persistent renderer/browser path configuration and npm Windows-shim resolution; configured browser selection reaches the worker environment.
- Added CLI days/all-time/pace flags and a read-only live terminal HUD.
- Initial synthetic preview is a pure route with no profile reads or render-bundle writes. Stored previews are cleared when the active profile changes.
- Expanded tests and rebuilt the public synthetic fixtures. Existing capture schema, plugin ID and storage namespace are unchanged.

## 0.1.0

Initial metadata capture, selected-profile history import, standalone HTML, Desktop page and explicit local MP4 pipeline. The original 0.1.0 ZIP remains available separately.
