# Settings and source-aware review

## Evidence-derived starting point
A previous authorized whole-image experiment used VTracer 1.0.0-alpha.4:
color-cluster, cutout, spline, filter-speckle 1, color-precision 5,
simplify 0.8, optimize 0. These are a baseline recipe, not universal optima.
Precision 6 / simplify 0.4 is experimental and not always better. Increasing
precision can retain shades but increase fragments; simplifying can erase narrow
parts. Never rank candidates only by path count or reduced colors.

## Manual preflight
Inventory actual objects, pale faces, openings, negative spaces, bands, narrow
supports and frames in the original. Background is not defined by color alone.
Use geometry, continuity and structure; border connectivity is evidence, not a
universal mask. Foreground can touch borders; enclosed holes may be background.
Preserve cool-white foreground against warm canvas and thin structural links.
Do not apply blanket whitening, outlines, patches, or automatic semantic claims.
Record inspected regions, untouched regions and unresolved ambiguity honestly.
The wrapper records a manual-review reminder; it does not perform this inspection.

## Comparison protocol (manual, not bundled)
Use equivalent coordinates, coverage and composition at native size. At 400%
render SVG geometry directly at FOUR TIMES native dimensions (or an equivalent
bounded viewBox); compare source with nearest-neighbor fourfold enlargement.
A 400-pixel thumbnail or an enlarged rasterized SVG is NOT a direct 400% SVG
comparison. Disclose anti-aliasing and non-scaling-stroke differences. Inspect
holes, continuity, source color, pale boundaries, halos, seams and narrow parts.
No optional renderer/Pillow comparison is implemented in this bounded package;
those dependencies are not required. A separate trusted renderer and image viewer
would be necessary for that manual workflow.

## Gate
Technical XML/vector checks and preserved hashes are evidence, not quality passes.
Independent review remains the final gate; an authorized fix gets one repair and
independent reassessment. Stop if rejected/still failing. No publishing/uploading
permission is implied. No Adobe acceptance guarantee is possible.
