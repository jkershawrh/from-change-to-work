# Aircraft visual review: three stills before the film

The procedural aircraft attempt was rejected by the user for its shape and visual execution. Its source and interrupted recording remain under the ignored `.production/rejected-procedural-aircraft-04/` and `.production/cinema-04/`; the rejected attempt is recorded in `verification/cinema-04/result.json`. No new film was published from that attempt. The working presentation source was restored to the preceding committed version.

This review instead uses an existing licensed C-17 asset, prepared in Blender. Deliverables are three 2560 × 1440 Cycles renders under `presentation/public/review/aircraft-01/`: a hangar establishing view, an aircraft/engine detail, and the robot positioning cell. These are authored review images, not photographs, inspection measurements or simulator execution proof. The user approved the aircraft with “Then move back to the demo because the plane looks good.” Cinema-05 integrates these views and the same prepared scene; narration and runtime execution authority remain unchanged.

## Source and modifications

The source GLB, creator/source/license attribution and its SHA-256 identity are under `presentation/assets/aircraft-review/`. The model is “c17 Globemaster with animation” by pilotcandle5470, supplied as an optimized viewer asset by AiZity under CC BY 4.0. Keep `ATTRIBUTION.txt` and the license link with any shared asset or rendered image.

The source catalogue asset has compressed Draco/meshopt geometry and embedded material textures. The conversion script decodes geometry for Blender without replacing the asset with a procedural plane. Four overlapping control-surface layers are hidden for rendering; named underlying panels and wide wing texture layers receive a neutral review topcoat, with duplicate-layer shadows suppressed. The neutral paint also removes source livery from wide skins; remaining component textures and source geometry are retained. The model is rescaled to an illustrative 53 m length; this is not manufacturing calibration. Its original control/gear configuration is presented on authored maintenance supports. It is a candidate visual prop, not an OEM-endorsed model.

The hangar, fixtures, maintenance jacks, lighting and camera views are authored scenery. The robot uses the repository's existing MJCF-derived mesh hierarchy and home joint pose. Raw OBJ vertices preserve the source axes, and the fixture includes workpiece support pads. No control program is run and no physical robot is contacted. Small camera/material choices do not establish physical feasibility or a safety acceptance envelope.

Two lower-detail alternatives were evaluated and rejected for close-up use: amvlab's A320 and Innerscene's regional jet. Candidate previews and iteration logs remain in ignored `.production/aircraft-review/`. Their presence is not a recommendation or a production asset qualification.

## Repeatable local rendering

Use a trusted Blender 4.5+ installation. Authoring here used Blender 4.5.15 LTS, mounted read-only from a signed macOS application; no system installation, kernel or driver change was made. The app image is not shipped in the repository. The renderer records the actual version in its report. The final review uses CPU rendering for the wide frame and Metal rendering of the same prepared scene for the other two frames. This is authoring hardware, not the Intel edge proof.

From the repository root:

```bash
npm ci --prefix tools/aircraft-assets
mkdir -p .production/aircraft-review
node scripts/visuals/decode_aircraft.mjs presentation/assets/aircraft-review/c17.glb .production/aircraft-review/decoded.glb
blender -b --threads 8 --python scripts/visuals/render_aircraft_review.py -- --asset .production/aircraft-review/decoded.glb --out .production/aircraft-review/render --width 2560 --samples 64
```

Use `--device METAL` on a supported Mac to render with its GPU, or keep the default CPU path. The output includes the editable scene, three PNGs and a per-view render report. Keep the large `.blend` file outside public assets; publish only the reviewed PNGs and report. Copy those four deliverables into `presentation/public/review/aircraft-01/`, then run:

```bash
.venv/bin/python -B scripts/visuals/verify_aircraft_review.py presentation/public/review/aircraft-01
.venv/bin/python -B -m unittest discover -s scripts/visuals -p 'test_aircraft_review.py'
```

The verifier checks source asset identity and attribution, embedded dependencies, complete PNG chunks/CRC/pixel data, named views, dimensions, image hashes and the no-motion scope. It does not judge realism, approve the design or establish render provenance attestation. CPU/GPU authoring performance is unrelated to Intel edge execution qualification.

## Scoped rubric

- **TDD:** retain the missing-deliverable failure before rendering and passing file-integrity/rejection tests after rendering.
- **EDD:** retain candidate rejection history, Blender logs, source hashes, actual camera/lens settings and image hashes. The stills remain authored scenery.
- **CDD:** pin the GLB/license identity and require exactly three distinct images; reject altered bytes, missing views and any physical-motion authority claim.
- **BDD:** inspect wide, detail and robot-cell views before deciding whether to integrate the asset or regenerate the film.
- **CBT:** exercise pinned asset → decoder → Blender import → actual Cycles rendering → independent artifact checks. This is an authoring boundary, not the central-to-edge execution boundary.

GREEN applies only to passing artifact checks. The aircraft review is user-approved; physical hardware, inspection quality and hard real time are outside this review. A software pass cannot make a weak image acceptable. Hosted CI account/billing status remains separate.

Cinema-05 integrates the approved scene, regenerates the film using the existing Kersh narration, and retains visual/media checks in `verification/cinema-05/`. Aircraft approval does not imply acceptance of every later camera or film edit.


## Browser scene export

Load the approved Blender scene and export static scenery without its posed robot. The browser adds the existing articulated simulator assembly, preserving retained joint samples and exploded inspection.

```sh
blender -b .production/aircraft-review/final/aircraft-review.blend --python scripts/visuals/export_approved_scene.py -- --out .production/cinema-05/scene-raw.glb
node scripts/visuals/optimize_approved_scene.mjs .production/cinema-05/scene-raw.glb presentation/public/models/approved-aircraft/scene.glb
```

The pinned glTF tools deduplicate, flatten, join and prune the exported geometry from 986 meshes to 34 meshes (12.6 MB). The browser asset is self-contained, with embedded textures and no decoder dependency. Preserve the source attribution beside it. glTF material conversion uses browser lighting; Cycles shader detail and lighting are retained in the opening image plates rather than claimed to be identical in WebGL.
