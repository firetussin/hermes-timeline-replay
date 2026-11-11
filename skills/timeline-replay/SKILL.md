---
name: timeline-replay
description: Create private animated replays of selected Hermes agent and profile activity and export them to local video.
---

Use the `timeline_replay` tool when the user asks to replay agent activity over time.
Call `status` first to learn the explicitly enrolled profile labels and all render prerequisites. Start with `demo`
for a first installation test. A real `build` takes selected profiles, hours, timezone,
title, seconds and pace. Use pace=social for a shareable cut, balanced for gentler motion,
or linear for uniformly spaced real time. Use days or range=all when the user asks for
more than a day; explain reported event/history limits. Set history=true for earlier saved metadata.

The build produces HTML and a render bundle, not a video. Show the preview and coverage
notes. Only call `render` for its bundle ID after the user requests encoding. It runs
on the connected Hermes host; keep its gateway running. Poll `jobs` and claim completion
only when state=complete. `/replay jobs` can attach the verified MP4.

Use action=setup to prepare a targeted dependency installation request. It does not install
anything. Review missing prerequisites, reuse existing tools, and honor the user's scope
before installing. The UI drafts the request into the user's chat; it never submits it.
The CLI also supports `hermes replay watch` for a live metadata-only terminal HUD.

Never infer success, delivery, review verdicts or outages from missing metadata. Missing
outcomes are unknown. Demo events are synthetic. Do not use other tools to find private
transcripts or automatically enroll profiles. Enrollment and JSON import are operator
terminal actions documented in the README. Do not install dependencies, publish, SSH
or use cloud rendering as a fallback without the user's explicit scope.
