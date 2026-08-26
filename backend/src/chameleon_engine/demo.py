"""Self-contained visual demonstration of the adaptive fitting pipeline."""

from __future__ import annotations

import html
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance

from . import __version__
from .features import ImageFeatures, extract_features
from .models import FitRequest
from .service import fit_request


class DemoError(ValueError):
    """Raised when demo output cannot be created safely."""


@dataclass(frozen=True)
class DemoArtifacts:
    report_path: Path
    request_path: Path
    response_path: Path
    metrics_path: Path


def _multiply_rgb(image: Image.Image, red: float, green: float, blue: float) -> Image.Image:
    return image.convert(
        "RGB",
        (
            red,
            0,
            0,
            0,
            0,
            green,
            0,
            0,
            0,
            0,
            blue,
            0,
        ),
    )


def _make_scene() -> Image.Image:
    width, height = 960, 600
    image = Image.new("RGB", (width, height), "#d9e3e4")
    draw = ImageDraw.Draw(image)

    for y in range(0, 390):
        ratio = y / 389
        color = (
            round(225 - 36 * ratio),
            round(235 - 30 * ratio),
            round(234 - 20 * ratio),
        )
        draw.line((0, y, width, y), fill=color)
    for y in range(390, height):
        ratio = (y - 390) / (height - 390)
        color = (round(120 - 28 * ratio), round(91 - 22 * ratio), round(68 - 16 * ratio))
        draw.line((0, y, width, y), fill=color)

    draw.rectangle((80, 70, 365, 330), fill="#edf4f2", outline="#738887", width=8)
    draw.line((222, 74, 222, 326), fill="#90a2a0", width=6)
    draw.line((84, 198, 361, 198), fill="#90a2a0", width=6)
    draw.rectangle((105, 95, 198, 174), fill="#b9d9df")
    draw.rectangle((246, 95, 339, 174), fill="#9cc8d2")
    draw.rectangle((105, 222, 198, 304), fill="#a9ced5")
    draw.rectangle((246, 222, 339, 304), fill="#86bbc7")

    draw.ellipse((425, 235, 625, 525), fill="#3d7770", outline="#244f4a", width=7)
    draw.rectangle((451, 292, 599, 468), fill="#4e8c82")
    draw.ellipse((451, 420, 599, 512), fill="#4e8c82")
    draw.ellipse((462, 260, 588, 320), fill="#73a99d")

    leaves = [
        ((505, 266), (457, 128), "#355f47"),
        ((520, 260), (512, 104), "#2f6c50"),
        ((535, 268), (585, 125), "#47775a"),
        ((490, 280), (415, 175), "#527f5e"),
        ((550, 283), (638, 185), "#2f6548"),
    ]
    for start, end, color in leaves:
        draw.line((*start, *end), fill="#31483b", width=8)
        ex, ey = end
        draw.ellipse((ex - 30, ey - 18, ex + 30, ey + 18), fill=color)

    draw.rectangle((655, 348, 865, 510), fill="#efe8d8", outline="#594d43", width=5)
    swatches = ["#b64235", "#d88734", "#e1c14f", "#4d8b61", "#397aa0", "#75548f"]
    for index, color in enumerate(swatches):
        column = index % 3
        row = index // 3
        left = 680 + column * 58
        top = 372 + row * 58
        draw.rectangle((left, top, left + 40, top + 40), fill=color)

    draw.ellipse((300, 410, 430, 540), fill="#d69a31", outline="#8c5d1e", width=5)
    draw.ellipse((205, 430, 322, 548), fill="#a74738", outline="#702b26", width=5)
    draw.rectangle((75, 505, 885, 535), fill="#634b3b")
    draw.rectangle((75, 535, 885, 557), fill="#47372d")
    return image


def _save_inputs(asset_directory: Path) -> dict[str, Path]:
    neutral = _make_scene()
    reference = ImageEnhance.Color(
        ImageEnhance.Contrast(_multiply_rgb(neutral, 1.08, 1.0, 0.92)).enhance(1.12)
    ).enhance(1.16)
    dark_cool = ImageEnhance.Brightness(_multiply_rgb(neutral, 0.78, 0.94, 1.18)).enhance(0.56)
    bright_green = ImageEnhance.Brightness(_multiply_rgb(neutral, 1.02, 1.12, 0.82)).enhance(1.28)

    paths = {
        "reference": asset_directory / "reference.jpg",
        "dark-cool": asset_directory / "target-dark-cool.jpg",
        "bright-green": asset_directory / "target-bright-green.jpg",
    }
    reference.save(paths["reference"], quality=94, subsampling=0)
    dark_cool.save(paths["dark-cool"], quality=94, subsampling=0)
    bright_green.save(paths["bright-green"], quality=94, subsampling=0)
    return paths


def _request_payload(paths: dict[str, Path]) -> dict[str, Any]:
    reference_settings = {
        "Contrast2012": 24,
        "Highlights2012": -35,
        "Shadows2012": 28,
        "Whites2012": 12,
        "Blacks2012": -18,
        "Texture": 8,
        "Clarity2012": 6,
        "Vibrance": 18,
        "Saturation": -4,
        "HueAdjustmentOrange": -6,
        "SaturationAdjustmentBlue": -12,
        "ToneCurveName2012": "Custom",
        "ToneCurvePV2012": [0, 0, 48, 40, 128, 139, 210, 224, 255, 255],
    }
    return {
        "schema_version": 1,
        "request_id": "mvp-demo-001",
        "reference": {
            "id": "reference",
            "preview_path": str(paths["reference"].resolve()),
            "develop_settings": reference_settings,
            "metadata": {"file_name": "reference.jpg", "file_format": "JPEG", "iso": 200},
        },
        "targets": [
            {
                "id": "dark-cool",
                "preview_path": str(paths["dark-cool"].resolve()),
                "develop_settings": {"Exposure2012": 0, "Temperature": 4800, "Tint": -8},
                "metadata": {
                    "file_name": "target-dark-cool.jpg",
                    "file_format": "JPEG",
                    "iso": 800,
                },
            },
            {
                "id": "bright-green",
                "preview_path": str(paths["bright-green"].resolve()),
                "develop_settings": {"Exposure2012": 0, "Temperature": 6200, "Tint": 14},
                "metadata": {
                    "file_name": "target-bright-green.jpg",
                    "file_format": "JPEG",
                    "iso": 100,
                },
            },
        ],
        "options": {
            "strength": 1.0,
            "adapt_exposure": True,
            "adapt_white_balance": True,
        },
    }


def _clamp_multiplier(value: float) -> float:
    return max(0.55, min(1.8, value))


def _render_approximation(
    source_path: Path, destination_path: Path, settings: dict[str, Any], diagnostics: dict[str, Any]
) -> None:
    with Image.open(source_path) as source:
        image = source.convert("RGB")

    exposure_delta = float(diagnostics["exposure_delta_ev"])
    temperature_delta = float(diagnostics["temperature_delta"])
    tint_delta = float(diagnostics["tint_delta"])
    red = _clamp_multiplier(math.exp(temperature_delta / 3600 + tint_delta / 140))
    green = _clamp_multiplier(math.exp(-tint_delta / 140))
    blue = _clamp_multiplier(math.exp(-temperature_delta / 3600 + tint_delta / 140))
    image = _multiply_rgb(image, red, green, blue)
    image = ImageEnhance.Brightness(image).enhance(2**exposure_delta)

    contrast = float(settings.get("Contrast2012", 0))
    vibrance = float(settings.get("Vibrance", 0))
    saturation = float(settings.get("Saturation", 0))
    image = ImageEnhance.Contrast(image).enhance(max(0.2, 1 + contrast / 200))
    image = ImageEnhance.Color(image).enhance(max(0.0, 1 + vibrance / 250 + saturation / 150))
    image.save(destination_path, quality=94, subsampling=0)


def _feature_gap(reference: ImageFeatures, candidate: ImageFeatures) -> dict[str, float]:
    color_distance = math.sqrt(
        sum((reference.rgb_mean[index] - candidate.rgb_mean[index]) ** 2 for index in range(3))
    )
    return {
        "luma_median": round(abs(reference.luma_median - candidate.luma_median), 4),
        "rgb_mean": round(color_distance, 4),
    }


def _format_setting(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, list):
        return "[" + ", ".join(f"{float(item):g}" for item in value) + "]"
    return str(value)


def _settings_table(current: dict[str, Any], proposed: dict[str, Any]) -> str:
    preferred_order = [
        "Exposure2012",
        "Temperature",
        "Tint",
        "Contrast2012",
        "Highlights2012",
        "Shadows2012",
        "Whites2012",
        "Blacks2012",
        "Texture",
        "Clarity2012",
        "Vibrance",
        "Saturation",
    ]
    remaining = sorted(set(proposed) - set(preferred_order))
    rows = []
    for key in [*preferred_order, *remaining]:
        if key not in proposed:
            continue
        rows.append(
            "<tr>"
            f"<th>{html.escape(key)}</th>"
            f"<td>{html.escape(_format_setting(current.get(key)))}</td>"
            f"<td>{html.escape(_format_setting(proposed[key]))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _report_html(request: dict[str, Any], response: dict[str, Any], metrics: dict[str, Any]) -> str:
    result_by_id = {result["photo_id"]: result for result in response["results"]}
    sections = []
    for target in request["targets"]:
        identifier = target["id"]
        result = result_by_id[identifier]
        diagnostics = result["diagnostics"]
        metric = metrics["targets"][identifier]
        title = target["metadata"]["file_name"]
        settings_table = _settings_table(target["develop_settings"], result["develop_settings"])
        sections.append(
            f"""
            <section class="target">
              <div class="section-heading">
                <div>
                  <p class="eyebrow">Target {html.escape(identifier)}</p>
                  <h2>{html.escape(title)}</h2>
                </div>
                <div class="confidence">
                  <span>Confidence</span>
                  <strong>{diagnostics["confidence"] * 100:.0f}%</strong>
                </div>
              </div>
              <div class="image-grid">
                <figure>
                  <img src="assets/target-{html.escape(identifier)}.jpg"
                       alt="Target before fitting">
                  <figcaption>Environment-light input</figcaption>
                </figure>
                <figure>
                  <img src="assets/fitted-{html.escape(identifier)}.jpg"
                       alt="Approximate fitted preview">
                  <figcaption>Feature-matched preview approximation</figcaption>
                </figure>
              </div>
              <div class="metrics">
                <div>
                  <span>Exposure correction</span>
                  <strong>{diagnostics["exposure_delta_ev"]:+.2f} EV</strong>
                </div>
                <div>
                  <span>Median-luma gap</span>
                  <strong>{metric["before"]["luma_median"]:.3f}
                    -> {metric["after"]["luma_median"]:.3f}</strong>
                </div>
                <div>
                  <span>Mean-RGB gap</span>
                  <strong>{metric["before"]["rgb_mean"]:.3f}
                    -> {metric["after"]["rgb_mean"]:.3f}</strong>
                </div>
              </div>
              <div class="settings">
                <h3>Proposed Develop Settings</h3>
                <table>
                  <thead><tr><th>Setting</th><th>Current</th><th>Proposed</th></tr></thead>
                  <tbody>{settings_table}</tbody>
                </table>
              </div>
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Chameleon.lr MVP Demo</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
      background: #f3f5f4;
      color: #17201d;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; }}
    header, section, footer {{ padding: 36px max(24px, calc((100vw - 1120px) / 2)); }}
    header {{
      background: #17201d;
      color: #f8fbf9;
      padding-top: 48px;
      padding-bottom: 48px;
    }}
    h1 {{
      margin: 4px 0 10px;
      font-size: 48px;
      line-height: 1.05;
      letter-spacing: 0;
    }}
    h2, h3, p {{ margin-top: 0; }}
    h2 {{ font-size: 24px; letter-spacing: 0; }}
    h3 {{ font-size: 17px; letter-spacing: 0; }}
    .eyebrow {{
      color: #64c59a;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0;
      margin-bottom: 8px;
    }}
    header p {{ max-width: 720px; color: #c8d4cf; line-height: 1.6; margin-bottom: 0; }}
    .reference {{ background: #fff; }}
    .reference-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(260px, .7fr);
      gap: 28px;
      align-items: center;
    }}
    img {{ display: block; width: 100%; height: auto; border-radius: 6px; }}
    .reference img, figure img {{ aspect-ratio: 8 / 5; object-fit: cover; }}
    .target {{ border-top: 1px solid #ccd4d0; }}
    .section-heading {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 20px;
      margin-bottom: 20px;
    }}
    .confidence {{ text-align: right; }}
    .confidence span, .metrics span {{
      display: block;
      color: #63706a;
      font-size: 12px;
      margin-bottom: 4px;
    }}
    .confidence strong {{ font-size: 24px; color: #236b50; }}
    .image-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    figure {{ margin: 0; }}
    figcaption {{ margin-top: 9px; color: #56625d; font-size: 13px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1px;
      background: #cbd3cf;
      margin: 26px 0;
      border: 1px solid #cbd3cf;
    }}
    .metrics div {{ min-height: 78px; background: #fff; padding: 16px; }}
    .metrics strong {{ font-size: 16px; }}
    .settings {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; font-size: 13px; }}
    th, td {{
      border-bottom: 1px solid #e0e5e2;
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}
    thead th {{ background: #e8eeeb; color: #46524d; }}
    tbody th {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 600; }}
    footer {{ background: #e4e9e6; color: #48554f; line-height: 1.6; }}
    footer a {{ color: #175f46; font-weight: 700; }}
    @media (max-width: 720px) {{
      header, section, footer {{ padding-left: 18px; padding-right: 18px; }}
      h1 {{ font-size: 34px; }}
      .reference-layout, .image-grid, .metrics {{ grid-template-columns: 1fr; }}
      .section-heading {{ align-items: start; }}
    }}
  </style>
</head>
<body>
  <header>
    <p class="eyebrow">Chameleon.lr {html.escape(__version__)}</p>
    <h1>Adaptive style fitting</h1>
    <p>A deterministic MVP run across two exposure and white-balance conditions.
      The same versioned JSON contract is used by the Lightroom plug-in.</p>
  </header>
  <main>
    <section class="reference">
      <div class="reference-layout">
        <img src="assets/reference.jpg" alt="Styled reference scene">
        <div>
          <p class="eyebrow">Style reference</p>
          <h2>One look, different light</h2>
          <p>The engine reads this rendered preview and its allowlisted Develop Settings,
            then derives target-specific exposure and white-balance corrections.</p>
        </div>
      </div>
    </section>
    {"".join(sections)}
  </main>
  <footer>
    <strong>Demo boundary:</strong> fitted images are a feature-space approximation for
    inspection, not a Lightroom rendering. The authoritative MVP output is the proposed slider
    JSON in <a href="response.json">response.json</a>; inspect the matching
    <a href="request.json">request.json</a> and <a href="metrics.json">metrics.json</a>.
  </footer>
</body>
</html>
"""


def create_demo(output_directory: Path, *, force: bool = False) -> DemoArtifacts:
    output_directory = output_directory.resolve()
    if output_directory.exists() and not output_directory.is_dir():
        raise DemoError(f"output path is not a directory: {output_directory}")
    if output_directory.exists() and any(output_directory.iterdir()) and not force:
        raise DemoError(
            f"output directory is not empty: {output_directory}; pass --force to update it"
        )

    asset_directory = output_directory / "assets"
    asset_directory.mkdir(parents=True, exist_ok=True)
    paths = _save_inputs(asset_directory)
    request_payload = _request_payload(paths)
    request = FitRequest.from_dict(request_payload)
    response = fit_request(request)
    if response["status"] != "ok":
        raise DemoError(f"demo fit failed: {response['errors']}")

    request_path = output_directory / "request.json"
    response_path = output_directory / "response.json"
    metrics_path = output_directory / "metrics.json"
    request_path.write_text(json.dumps(request_payload, indent=2) + "\n", encoding="utf-8")
    response_path.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")

    reference_features = extract_features(paths["reference"])
    targets_by_id = {target["id"]: target for target in request_payload["targets"]}
    metrics: dict[str, Any] = {"request_id": request.request_id, "targets": {}}
    for result in response["results"]:
        identifier = result["photo_id"]
        fitted_path = asset_directory / f"fitted-{identifier}.jpg"
        _render_approximation(
            Path(targets_by_id[identifier]["preview_path"]),
            fitted_path,
            result["develop_settings"],
            result["diagnostics"],
        )
        metrics["targets"][identifier] = {
            "before": _feature_gap(reference_features, extract_features(paths[identifier])),
            "after": _feature_gap(reference_features, extract_features(fitted_path)),
        }
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    report_path = output_directory / "index.html"
    report_path.write_text(_report_html(request_payload, response, metrics), encoding="utf-8")
    return DemoArtifacts(report_path, request_path, response_path, metrics_path)
