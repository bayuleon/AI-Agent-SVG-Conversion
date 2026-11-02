---
name: raster-to-svg
description: Trace local raster art with source-integrity evidence.
version: 0.2.0
author: Package contributors, Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [vector, raster, svg, local]
    related_skills: []
---
# Raster to SVG Skill

Trace authorized local artwork through an external VTracer executable. No model,
API key, image generation, network access or Adobe approval guarantee is required
or provided. This standalone draft is not an installed skill.

## When to Use
- Prepare an explicitly authorized local raster-to-SVG experiment and evidence.
- Do not use for automatic semantic reconstruction, uploading, or reopening a
  rejected repair. Sharing this package gives a Manager no permission to generate
  assets or change any project contract.

## Prerequisites
- Read the current project contract before acting; its permissions take priority.
- Python 3.10+ and separately supplied VTracer 1.0.0-alpha.4; see requirements.md.
- Read references/settings-quality.md and inventory the source's real objects,
  pale surfaces, holes, thin supports and background before tracing.
- Use read_file/search_files for local documents, vision_analyze for the actual
  source where available; do not claim semantic preflight from a hash or color.

## How to Run
Use terminal with a quoted user-supplied Python executable and paths:
`terminal(command='python scripts/trace.py "input.png" "output.svg" --report "trace.json" --vtracer "vtracer"', timeout=180)`.
Resolve script location from this package; the command assumes its root is the
current directory. Accept absolute user paths; never replace them with a local
contributor path. On Windows prefer a quoted native absolute Python path.

## Quick Reference
- Baseline: precision 5, simplify 0.8; other recipe fields are fixed.
- Experimental only: `--precision 6 --simplify 0.4`; not always better.
- `--timeout 120`: per tracing process; help/version each capped at 10 seconds.
- Existing output/report paths are always rejected; no overwrite option exists.
- Report precedes SVG: candidate_validated is not proof of SVG publication.

## Procedure
1. Confirm scope/rights and source inventory; record unresolved pale/background
   ambiguity manually outside this package. Criterion: source-specific checklist.
2. Choose one bounded experiment; preserve source and baseline. Criterion: new
   output/report paths and authorized recipe.
3. Invoke the wrapper; criterion: exit zero, actual version and supported flags,
   matching before/after SHA-256, vector-only safe XML, output hash and runtime.
4. Compare aligned native source and SVG plus relevant 400% regions; see reference.
   Criterion: coverage and unresolved defects recorded, not a self-issued pass.
5. Hand off exact output/report to an independent reviewer as the final gate.
   Criterion: independent decision before delivery; never arbitrary upload.
6. Repair only items independently marked fix, once with explicit authorization;
   preserve baseline and submit the saved repair for independent reassessment.
   If still failing/rejected, stop; no renamed retry to evade the limit.

## Pitfalls
- Exclusive hardlink publication fails closed on unsupported filesystems.
- Publication is atomic per file, not a two-file transaction. Reports are immutable;
  verify exit code and output hash separately. See README.md for failure semantics.
- Smoothness, path count, technical validity and recognition do not prove fidelity.
- Pale foreground can merge into background; no global color/background mask is
  automatically correct. Do not blanket-whiten or invent missing geometry.
- XML checks intentionally accept a conservative geometry-only subset; this is
  not a complete browser security sanitizer or proof of editability/visual quality.
- Untrusted executable/input is outside the sandbox guarantee; run only trusted
  local tools. Hash checks detect mutation but cannot prevent a malicious binary.
- Native Windows was exercised. Other OSes are design targets, not tested claims.

## Verification
Use terminal to run `python -m unittest discover -s tests -v` and
`python scripts/trace.py --help`. Tests mock subprocess and do not establish real
image quality. A live trace must use an authorized existing input and external
binary, with evidence outside the distributable. No images, binaries, credentials,
private paths or local logs belong in a shared archive. Authored material is MIT
licensed; see LICENSE and LICENSE_POLICY.md. Await independent audit before release.
