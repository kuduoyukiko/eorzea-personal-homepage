"""Remove the neutral item-slot plate from the original FFXIV crystal icons."""

from pathlib import Path
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "static" / "images" / "soul-crystals"
OUTPUT = ROOT / "static" / "images" / "soul-crystals-cutout"


def extract(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    pixels = list(image.getdata())
    seeds = []
    for red, green, blue, alpha in pixels:
        spread = max(red, green, blue) - min(red, green, blue)
        light = max(red, green, blue)
        seeds.append(255 if alpha and (spread >= 24 or light >= 205) else 0)

    seed = Image.new("L", image.size)
    seed.putdata(seeds)
    # Grow from the coloured/glowing crystal core across its dark rim, then
    # softly close tiny gaps without reintroducing the outer slot plate.
    matte = seed.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    matte = matte.filter(ImageFilter.GaussianBlur(0.45))
    matte = Image.composite(matte, Image.new("L", image.size), image.getchannel("A"))
    image.putalpha(matte)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image.resize((320, 320), Image.Resampling.LANCZOS).save(OUTPUT / path.name)


if __name__ == "__main__":
    for icon in sorted(SOURCE.glob("*.png")):
        extract(icon)
        print(icon.name)
