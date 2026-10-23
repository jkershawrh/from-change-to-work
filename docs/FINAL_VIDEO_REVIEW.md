# Final movie review and handoff

The current download is `presentation/public/film/from-change-to-work-announced.mp4`. It adds a five-second spoken title opening: “From change to work. A Red Hat and Intel robotics story.” The approved Kersh profile is unchanged. The voice-production/disclaimer footer has been removed from the movie and interactive presentation; the required aircraft credit remains. The interactive title waits for its announcement to finish before entering the story. Current checks are under `verification/cinema-09/`; the review below describes the retained cinema-08 body used for this edit. The interactive story is `/show/`; the root dashboard leads to the real transfer workbench. The source repository is https://github.com/jkershawrh/from-change-to-work. Read `AGENTS.md` and `docs/AGENT_START.md` for agent-assisted setup and hardware due diligence.

The story follows one business problem: an approved engineering change must become accountable work at the receiving cell. The sequence is the waiting cell, an approved work package, remote delivery/local acceptance, work after a central data-plane cut, explicit recovery, reuse for another task, and one bounded customer pilot. Delivery does not become remote control of the robot. The film distinguishes illustrative factory scenes, retained simulator execution and proposed hardware acceptance.

The review inspected the encoded movie across its full 5:30 runtime, with one-second contact sheets and eight samples per second around all six chapter handoffs. Every encoded frame was decoded and scanned for unexpected dark frames and transport-strip contamination. Narration text was compared with the seven timed chapter texts; five-second decoded audio windows were correlated with the source mix. Music level, clipping, chapter holds and the opening title offset were checked. These are visual inspection and objective audio checks; subjective listening is not claimed.

The close transition review found brief stale WebGL frames at the architecture opening and a camera reset at the disconnect opening. The final cut replaces only those entry intervals with stable matching frames from the same recorded chapter. The AAC stream is copied byte for byte; narration, music and timing are unchanged. `verification/cinema-08/encoded-media.json` records the source movie hash, repair intervals, frame identities and audio stream hash. The earlier movie and before-review evidence remain available.

Future recording now rejects a WebGL frame whose rendered chapter identity differs from the export chapter. At a chapter change the camera snaps to its new pose; ordinary within-scene camera movement still eases. New unit contracts and a browser check cover scene identity. Media success is not execution acceptance, a new hardware proof or certification.

The export retains Red Hat and Intel logos and attribution. It has no burned-in captions or decorative playback bar. Interactive controls and optional captions remain available in the live presentation. The source voice and voice profile remain unchanged; no new voice-provider request was made.

To reproduce the reviewed repair from the retained cinema-07 movie:

```bash
.venv/bin/python scripts/repair_story_export.py --ffmpeg /path/to/ffmpeg
.venv/bin/python scripts/review_story_export.py --ffmpeg /path/to/ffmpeg --movie presentation/public/film/from-change-to-work-final.mp4 --out verification/my-fresh-final-review
```

The review command requires a fresh output directory. Source film and original evidence are not overwritten. Hosted CI has previously been blocked before any steps ran by the GitHub account billing/spending restriction; local media checks and hosted status remain separate.

A browser assertion still expected the opening hangar at story second 12, although the approved scene schedule has reached the cell by then. The check now waits for the loaded story clock, verifies the correct 12-second cell, then explicitly seeks to second 1 to verify the hangar. The original failing run is retained in `verification/cinema-08/browser.log`; it was a stale timing expectation, not a change to the approved scene schedule.

The readiness marker is published from inside the resolved 3D asset boundary after two animation frames. A stronger regression also reads actual canvas contrast, preventing an empty background from passing as a ready scene. The targeted final browser run passed all three checks. Final picture comparison inspected 8,131 frames outside the declared repairs; the minimum structural similarity was 0.999601. Final audio measured −18.5 LUFS integrated and −0.7 dBFS true peak, with no detected silent interval longer than 250 ms at −60 dBFS.
