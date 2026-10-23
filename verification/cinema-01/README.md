# Cinematic demo acceptance

The source-matched final simulator capture and independent audit are in `final-session/`, `final-capture.log` and `final-audit.log`. The earlier complete integrated session is retained separately. The final task count is 736 control ticks and 7,360 physics substeps; it is local simulation only.

`browser-release.log` retains all six passing cinematic browser tests: three viewport/reveal rehearsals, voice clock/seeking with no actuation, authenticated source-bound payoff, and a verified nonempty MP4 stream. `browser-integrated.log` retains the seven dashboard/workbench checks. `final-transfer-workflow.log` repeats the actual challenge on the exact final source freeze.

`encoded-media.json`, `encoded-decode.log` and eight `encoded-frames/` retain the media check. Representative first, architecture and final frames were visually inspected. The complete 367.12-second 1080p/25fps movie has a decoded nonempty AAC track. Entire original narration timing is retained; no subjective listening is claimed. The voice profile exactly matches the latest saved Kersh settings from the two-week visibility strategy.

Failed playback readiness and the obsolete rendering rehearsal remain retained. Source/proof history was not rewritten. The Rust executor, controller and simulator source are unchanged. See result.json for the scoped rubric; current Intel/Red Hat hardware, production, physical and real-time gates are not promoted by this film.
