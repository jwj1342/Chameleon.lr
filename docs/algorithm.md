# Baseline Algorithm

> Part of the [Chameleon.lr documentation](README.md).

The initialized engine is a deterministic baseline, not a trained model. It makes the full
Lightroom-to-engine-to-Lightroom workflow testable before datasets and evaluation criteria
are fixed.

For each rendered JPEG it computes:

- luminance mean, standard deviation, P10, median, and P90;
- shadow and highlight clipping fractions;
- mean HSV saturation;
- mean RGB channels.

Style controls such as contrast, highlights/shadows, HSL, tone curves, and color grading are
copied from the reference and blended against each target by the requested strength. Exposure
is estimated from the log2 ratio of reference and target median luminance, capped at three EV.
Temperature and tint use bounded log-chromaticity differences as a conservative heuristic.

## Known limitations

- Lightroom's thumbnail is the currently rendered result, not linear scene-referred RAW data.
- A single edited reference does not reveal the exact before/after transform that created the
  style. Higher-quality training should capture paired unedited/edited states or use multiple
  examples.
- RGB thumbnail statistics are not a substitute for camera-profile-aware color science.
- Temperature/tint response depends on camera profile and file type; the current mapping is a
  bounded starting point, not a calibrated physical model.
- Similar-looking global histograms can hide different local or semantic content.

The next algorithm milestone should introduce a reproducible dataset and perceptual evaluation
suite before adding a learned model. Useful metrics include luminance-histogram distance,
Delta E on matched neutral/color regions, clipping rate, parameter smoothness across a shoot,
and photographer acceptance rate.
