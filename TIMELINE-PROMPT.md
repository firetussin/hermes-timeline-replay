# Reusable Hermes activity timeline brief

Use this brief with a coding agent or adapt it into a plugin task. It contains no references to personal videos, specific computers or Claude artifacts.

```text
Create an animated timeline replay of recorded Hermes Agent activity across the
profiles and agents I explicitly select. Provide a private standalone HTML player
and a deterministic composition that can be rendered to MP4 on the Hermes host.

INPUT
- Profiles: <explicit profile labels or approved profile directories>
- Time range: <last N hours/days, or all available recorded history>
- Display timezone: <IANA zone; default America/Chicago>
- Title: <short replay title>
- Replay length: <default 30 seconds plus a 4-second Social finale>
- Pacing: <Social, Balanced or Linear; default Social>

DATA
Use actual recorded events only. Prefer supported Hermes observer hooks for new
activity and read-only session database metadata for historical activity. Support
an explicit versioned JSON import for other hosts. Do not scan arbitrary machines
or profiles, use SSH automatically, or change running services.

Keep profile identity, session/agent identity, parent-child correlation and time
provenance separate. Record session/turn events, tool calls, model usage and
delegation when those fields exist. Do not read transcript bodies, command
arguments, tool results, credentials, hidden prompts or private paths into the
artifact. Pseudonymize raw session IDs. Use explicitly chosen safe display labels.

Preserve missing timestamps, durations, statuses and usage as unknown. A session
ending is not proof the task succeeded; a write_file call is not proof of delivery.
Do not invent reviews, decisions, outputs or completion counts. Mark synthetic
fixtures prominently. Reconcile counts, deduplicate capture/history overlap and
include coverage, truncation and unavailable-source notes.

VISUAL EXPERIENCE
- A navy 16:9 stage with a coral run clock, gold milestones and distinct profile
  colors. Use bundled/system fonts and no required network assets.
- Profile and agent/session lanes on a shared real-time axis; show delegation
  events and parent relationships when recorded.
- Duration bars only for measured or explicitly paired intervals; point marks
  for events with unknown duration. Differentiate known errors and unknown results.
- Running counters from observed events: profiles, sessions, tools, known errors
  and recorded tokens. Include other totals only when supported by real evidence.
- Timezone-aware labels and local-night bands. Do not label quiet gaps as outages.
- A moving playhead and 10–15 representative captions derived from actual events.
- In Social mode, emphasize active profile cards, event packets, impact rings,
  counter hits and milestone cards. Compress quiet gaps while preserving truthful
  timestamps and event order; clearly label the compressed pacing.
- A final card with exact observed totals and important coverage qualifications.
- Keep every selected lane visible through labeled chapters or explicit grouping.
  Do not silently discard overflow events or profiles.
- Play/Pause, Restart, Speed and Scrub; reduced-motion starts paused at the end.

RENDERING
Use a seek-safe HyperFrames composition. The same time value must reproduce the
same visual state, including after a backward seek. Embed sanitized data and local
assets. Keep interactive playback clocks out of the video composition.

Preview before encoding. Render only after an explicit user action, on the machine
where the plugin is installed, using preinstalled local dependencies. Do not render
on my main PC, spend API credits, install render engines or publish automatically.
Show dependency readiness in Desktop and CLI. If something is missing, prepare a
targeted installation request for the user to review with their Hermes agent.
Support the same ranges, pacing and export via CLI, plus a lightweight terminal
activity watch that needs no video dependencies.
Use argument-list subprocesses, bounded concurrency and truthful job progress.
Verify video existence, dimensions, frame rate and duration before claiming success.

DELIVERABLES
An installable Hermes plugin using documented extension APIs; a synthetic demo;
private HTML and MP4 export; metadata/provenance JSON; meaningful offline tests;
clear installation and target-host smoke-test instructions. Follow local AGENTS.md.
Distinguish tested behavior from implemented-but-unverified integration.
```
