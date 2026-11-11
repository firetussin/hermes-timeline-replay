# Hermes Timeline Replay

Build a reusable Hermes plugin, not a video tied to the original livestream references.

- Input: metadata recorded by Hermes hooks, selected profile session databases read-only, or explicit JSON event exports.
- Output: private standalone interactive HTML, deterministic HyperFrames composition, and optional local MP4 on the installed Hermes machine.
- Design: navy background, coral clock, gold milestones, colored profile/agent lanes, time bands, real counters, a caption ticker and final totals.
- Controls: play/pause, restart, speed and scrub; reduced-motion starts at the final state. No external fonts or media required.
- Default duration: 60 seconds of replay and an 8-second closing card. Multiple lane pages replay the full time range in sequential chapters.
- Data integrity: no invented events, delivery claims or success verdicts; missing timestamps/status/durations remain unknown. Synthetic demonstration data is explicitly labeled.
- Privacy: no prompt bodies, tool arguments/results, process command lines or raw private paths in captured metadata or published pages. Selected profile names are human-readable; session identifiers are pseudonymous.
- Scope: local prototype, no publication, no live profile installation, no service changes, no inference calls. Rendering runs on the machine where the user installs the plugin. No video rendering on the development PC.
- Workflow: application development; use the HyperFrames core/WAAPI contract for generated compositions. The supplied brief fixes the creative direction and authorizes an autonomous testable first version.

## Revision 0.2.0

User feedback: use native Desktop theme/components, offer dependency setup from the HUD, support days/all available, and make the exported replay lively for X. Implemented preview-first UI, a targeted setup request, Social/Balanced/Linear modes, event-driven animated profile stage, a 30-second Social default plus four-second finale, and CLI parity/live watch. No live dependency installs or video renders on the main PC.
