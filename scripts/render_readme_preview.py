"""Build the README preview from the deterministic MVP demo images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "demo" / "output" / "assets"
OUTPUT = ROOT / "docs" / "assets" / "readme-preview.jpg"

CANVAS_SIZE = (1600, 1000)
BACKGROUND = "#F3F4F1"
INK = "#202422"
MUTED = "#656B68"
LINE = "#D3D7D2"
PAPER = "#FFFFFF"
ACCENT = "#E95D45"
SUCCESS = "#2B7A5B"


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def cover(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as source:
        return ImageOps.fit(source.convert("RGB"), size, Image.Resampling.LANCZOS)


def label(
    draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str
) -> None:
    x, y = xy
    draw.rounded_rectangle((x, y, x + 118, y + 35), radius=4, fill=color)
    draw.text((x + 12, y + 7), text, fill=PAPER, font=font(17, bold=True))


def case_study(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    title: str,
    subtitle: str,
    before: Path,
    after: Path,
) -> None:
    width = 740
    draw.rectangle((x, y, x + width, y + 405), fill=PAPER, outline=LINE, width=2)
    draw.text((x + 24, y + 20), title, fill=INK, font=font(25, bold=True))
    draw.text((x + 24, y + 55), subtitle, fill=MUTED, font=font(18))

    image_y = y + 92
    image_size = (337, 211)
    canvas.paste(cover(before, image_size), (x + 24, image_y))
    canvas.paste(cover(after, image_size), (x + 379, image_y))
    label(draw, (x + 38, image_y + 162), "BEFORE", INK)
    label(draw, (x + 393, image_y + 162), "FITTED", SUCCESS)

    draw.line((x + 24, y + 326, x + width - 24, y + 326), fill=LINE, width=2)
    draw.text(
        (x + 24, y + 350),
        "Light-aware exposure + white balance adaptation",
        fill=MUTED,
        font=font(17),
    )


def main() -> None:
    expected = {
        "reference": ASSETS / "reference.jpg",
        "dark": ASSETS / "target-dark-cool.jpg",
        "dark_fitted": ASSETS / "fitted-dark-cool.jpg",
        "green": ASSETS / "target-bright-green.jpg",
        "green_fitted": ASSETS / "fitted-bright-green.jpg",
    }
    missing = [str(path) for path in expected.values() if not path.is_file()]
    if missing:
        raise SystemExit(
            "Missing demo images. Run `python scripts/dev.py demo` first:\n"
            + "\n".join(missing)
        )

    canvas = Image.new("RGB", CANVAS_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, 1600, 120), fill=INK)
    draw.text((48, 25), "Chameleon.lr", fill=PAPER, font=font(42, bold=True))
    draw.text(
        (405, 40),
        "adaptive style transfer for Lightroom Classic",
        fill="#CCD1CD",
        font=font(21),
    )
    draw.rounded_rectangle((1322, 33, 1552, 83), radius=4, fill=ACCENT)
    draw.text((1363, 47), "MVP  /  REAL OUTPUT", fill=PAPER, font=font(16, bold=True))

    reference_size = (1512, 300)
    reference_xy = (44, 150)
    canvas.paste(cover(expected["reference"], reference_size), reference_xy)
    draw.rectangle(
        (
            reference_xy[0],
            reference_xy[1],
            reference_xy[0] + reference_size[0],
            reference_xy[1] + reference_size[1],
        ),
        outline=PAPER,
        width=3,
    )
    label(draw, (70, 176), "REFERENCE", ACCENT)
    draw.text(
        (70, 389),
        "Styled baseline selected in Lightroom",
        fill=PAPER,
        font=font(21, bold=True),
    )

    case_study(
        canvas,
        draw,
        x=44,
        y=478,
        title="Dark + cool target",
        subtitle="Different exposure and white balance",
        before=expected["dark"],
        after=expected["dark_fitted"],
    )
    case_study(
        canvas,
        draw,
        x=816,
        y=478,
        title="Bright + green target",
        subtitle="Independent per-photo fitting",
        before=expected["green"],
        after=expected["green_fitted"],
    )

    draw.text(
        (44, 929),
        "Deterministic demo images | Physical Develop Settings remain the authoritative output",
        fill=MUTED,
        font=font(18),
    )
    draw.text((1438, 929), "GPL-3.0", fill=INK, font=font(18, bold=True))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, "JPEG", quality=92, optimize=True, progressive=True)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
