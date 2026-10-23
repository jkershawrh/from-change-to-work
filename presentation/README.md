# From change to work — aerospace hangar edition

The 5:26 story is packaged at `/show/` with the dashboard `/`, the transfer workbench `/?actions=1&mode=live`, and the authenticated APIs. Run the repository root setup/demo scripts. The app extends the canonical `demo-story-starter`; `?guided=1` retains its guided renderer.

The latest film is `film/from-change-to-work-announced.mp4`. The seven-chapter business story keeps its varied production, package, recovery, module and pilot compositions. The delivery chapter now uses an actual 3D causal event flow; the opening uses the three user-approved Blender views. Local execution appears in the optimized C-17 hangar scene with the original articulated simulator robot. Aircraft attribution is available in Evidence & scope and models/approved-aircraft/ATTRIBUTION.txt.

## Inspection and controls

The audience sees three fully framed responsibilities: engineering, delivery and the receiving cell. Open **Inspect the engineering detail** for the seven-event selector and source checks. Hover exposes checks and repository source. The result-return path is labeled. The authenticated observer remains separate from execution. The dispatcher binds action intent; the executor independently fetches the signed bundle. This is a causal process view, not a claim that bundle bytes transit the dispatcher.

The robot chapter has cinematic, hangar-wide, cell and detail camera presets, orbit, blueprint, exploded edge layers and a visual exploded robot assembly. The retained joint pose remains separate from illustrative assembly offsets. Hangar scenery includes an airframe, fasteners, fixtures, trusses, crane, floor markings, shelving, tooling and service assets. Local environment lighting and font textures need no external art service.

Space plays/pauses, arrows change chapter, P opens presenter notes, and F requests fullscreen. Captions, deep links, reduced-motion stills and narrow rehearsal remain available. Story gestures and media export never issue robot execution requests. Current-session observations require an explicit authenticated read and do not replace an independent audit.

## Saved narration

`audio/voice-profile.json` pins the saved Kersh profile from the two-week visibility strategy: Eleven v3, stability 0.5, similarity 0.8, style 0.3, speaker boost enabled, speed 1.0. This edition locally edits the retained cinema-02 take: it removes the personal introduction/disclaimer, replaces six-second chapter holds with 0.55-second gaps, and shortens the ending hold to 2.2 seconds. It performs no new provider generation or account voice-setting change.

The active script and editorial checks are under `audio/cinema-06/`. The source alignment stays under `audio/cinema-02/`; `public/audio/cinema-06/plan.json`, captions and edited audio ship with the private handoff. All captions and event cues share the edited audio clock. Ordinary setup needs no provider key. Never delete a generation-intent record to force another request or put a provider key in browser code. Objective checks do not claim subjective listening.

## Repeatable film export

With the combined demo running, use these commands from the repository root:

```bash
AERIS_FILM_OUTPUT=.production/cinema-07-final node scripts/record_story.mjs
AERIS_TITLE_OUTPUT=.production/cinema-06-title-final node scripts/capture_story_title.mjs
.venv/bin/python scripts/encode_story.py --edition cinema-07 --source .production/cinema-07-final/story-picture.webm --opening-title .production/cinema-06-title-final/opening-title.png --ffmpeg /path/to/ffmpeg
```

Recording captures the shared process illustrations, actual WebGL hangar/event flow and export typography at the story's natural runtime. Encoding combines the locally edited narration and speech-ducked original piano/pad score, fully decodes the MP4 and retains representative frames. Camera geometry and logos keep their aspect ratio. Its own successful media report enables the current download. The result is a narrated retained-evidence story, not a new execution or hardware proof.

## Verification and history

Root `scripts/check.sh` covers software tests, blueprint validation, builds and offline assets. `npm --prefix presentation run test:visual` checks the chapters/reveals at presentation, laptop and mobile sizes, media clock, observations, hover/focus, spatial event controls and robot views. The current visual/media evidence is `verification/cinema-07/`. Earlier cinema-01 through cinema-05 artifacts remain unchanged history. Reused module names remain in source provenance; audience branding stays neutral.


## Reproduce the local audio edit

Decode `public/audio/cinema-02/kersh-raw.mp3` to `audio/cinema-02/raw-decoded.wav` using FFmpeg, mono 44.1 kHz signed 16-bit PCM. Run from the repository root with fresh output folders:

```sh
.venv/bin/python -B scripts/edit_story_audio.py --out .production/audio-06-rebuild --metadata .production/audio-06-rebuild-metadata
```

The script refuses existing output directories. It uses saved character alignment to remove the complete personal passage and to place spoken event cues, adds only short chapter gaps and edge fades, and never requests a new voice generation or changes speaking speed. Retained source audio and earlier film editions remain historical evidence.

## Opening title

A zero-time link opens the full-screen aircraft title cover before Act 1. Watch and presenter controls enter the existing story; no title gesture issues an action request. The live story lasts 5:26. The movie adds a four-second title card with the quiet original bed and hides interactive buttons, for a 5:30 total. The body narration, captions and event clock move together by that four-second movie offset. The title card is captured from the actual cover component. Earlier movie editions remain history.


## Caption-free musical edition

The current film burns no captions into the picture. Interactive captions start off and remain optional for accessibility. The original Kersh narration is byte-identical to cinema-06. Cinema-07 adds an original 78 BPM pad/piano score, with speech ducking, midrange energy for ordinary speakers, and a target music RMS about 19 dB below active voice. The previous quiet drone was about 34 dB below voice.

Decoded review images now feed the export directly from the same scene clock. The exporter never samples a React canvas for the opening two chapters, so a new heading cannot be captured over the previous scene's image. Live plates also switch decoded images synchronously before paint.

To rebuild the score into fresh folders:

```sh
.venv/bin/python -B scripts/score_story.py --out .production/score-rebuild-001 --metadata .production/score-metadata-001
.venv/bin/python -B scripts/verify_story_music.py
```

The independent music verifier checks the shipped cinema-07 sources. After encoding, run `scripts/verify_score_export.py --work .production/cinema-07-final --ffmpeg /path/to/ffmpeg` to verify the actual AAC mix and sample the former caption region. The recorder waits for the preloaded 3D asset to be attached behind the title cover; visibility is expected only after playback starts.

Exports contain no decorative playback bar. Working controls belong to the interactive presentation and the viewer’s video player. The current encoder clears the recorded transport strip while retaining the aircraft attribution; future browser recordings omit it directly.

The end-to-end final review and retained chapter-entry repairs are documented in `docs/FINAL_VIDEO_REVIEW.md` (from the repository root). Current handoff evidence is under `verification/cinema-08/`. Audio remains the unchanged cinema-07 mix.

The current cinema-09 opening announces the title using the unchanged Kersh profile. The main narration and music come from the existing lossless cinema-07 mix; the reviewed cinema-08 body visuals remain intact. The voice-production/disclaimer footer is absent. `scripts/announce_story_export.py --ffmpeg /path/to/ffmpeg` reproduces the movie from retained sources without making another provider request. Its retained raw opener is generated once, with intent and alignment recorded under `presentation/audio/cinema-09/`. Current verification is `verification/cinema-09/`.
