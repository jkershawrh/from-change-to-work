# Scene handoff, captions and music correction

The user reported a glitch at the end of Scene 1, unwanted captions and inaudible music in the downloaded movie. The prior export sampled a live React canvas immediately after advancing story state. At the chapter boundary, the next heading appeared before that canvas had switched images. The retained contact sheet covers movie seconds 39–44 and shows the stale image beneath the next heading.

The exporter now synchronously selects pre-decoded image assets from its own frame clock for the first two chapters. A regression test checks the last frame before the boundary and the first frames after it. The interactive canvas also uses pre-decoded images and a layout effect, so the scene image changes before browser paint.

The exported film has no burned-in captions. Interactive captions are off by default and remain available through the explicit CC control. Caption sidecars are retained for accessibility and source timing; they are not overlaid on the movie.

The old bed was a very quiet low-frequency drone. The new original 78 BPM score combines warm pads, soft piano arpeggios and a gentle pulse, with a D minor / B-flat / F / C progression. It is ducked during speech and returns between phrases. Source checks measure music about 19 dB below active narration, rather than the earlier 34 dB. Most musical energy is in the audible midrange. The narration file, voice profile, wording and speaking speed are unchanged; there are no provider requests.

Local unit, scene-boundary and browser checks are scoped to this presentation revision. Source music checks verify unchanged narration, music level, midrange energy and no clipping. Export verification checks the actual AAC residual against the score, full video/audio decode, and the former caption region. These objective checks do not claim subjective listening, new execution proof or hardware acceptance.

The first recording attempt stopped because the strengthened title cover correctly hid the already-loaded robot stage. The recorder had been waiting for visibility. It now waits for the matching ready element to be attached, then begins the story normally. The failure is retained in `verification/cinema-07/recording.log`; final recording uses a fresh output directory.

The full-screen opening, Red Hat × Intel logos, shortened chapter gaps and private handoff remain intact. Software/media success does not qualify a robot, a new Intel/Red Hat host, timing or production savings.

The MP4 has no decorative timeline, time readout or chapter transport. The interactive demo retains its working controls; an MP4 player supplies real playback controls. For this capture, encoding masks only the already-recorded transport strip at y957–1037, retaining the attribution footer. The recorder also omits that strip for future captures. A decoded-frame check verifies the former transport region is clear.

The first final-package browser check detected an older production manifest copied by a build started before encoding completed. That failed check is retained in `browser-final.log`. The package was rebuilt after encoding, and its manifest and MP4 hashes were compared with the completed source before rerunning the checks.
