"""Compose the mod.io icon and logo from a transparent dice render.

Usage: python make_mod_logo.py <dice.png> <output_folder>

Render the dice first with render_icon.py at 1024 pixels.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BACKGROUND = (20, 18, 24)
GLOW = (255, 170, 40)
TITLE = (255, 196, 64)
FONT = "C:/Windows/Fonts/impact.ttf"


def scene(width, height, dice, dice_height, centre):
    """Dark background with a warm glow behind the dice."""
    image = Image.new("RGB", (width, height), BACKGROUND)
    trimmed = dice.crop(dice.getbbox())
    scale = dice_height / trimmed.height
    trimmed = trimmed.resize((round(trimmed.width * scale), dice_height), Image.LANCZOS)
    left = centre[0] - trimmed.width // 2
    top = centre[1] - trimmed.height // 2

    glow = Image.new("L", (width, height), 0)
    radius = round(dice_height * 0.62)
    ImageDraw.Draw(glow).ellipse((centre[0] - radius, centre[1] - radius, centre[0] + radius, centre[1] + radius), fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(dice_height / 6))
    image.paste(Image.new("RGB", (width, height), GLOW), (0, 0), glow)
    image.paste(trimmed, (left, top), trimmed)
    return image


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    dice = Image.open(sys.argv[1]).convert("RGBA")
    out = Path(sys.argv[2])

    scene(1024, 1024, dice, 760, (512, 512)).save(out / "LuckyDice_Icon.png")

    logo = scene(1280, 720, dice, 520, (360, 360))
    draw = ImageDraw.Draw(logo)
    font = ImageFont.truetype(FONT, 170)
    draw.text((680, 170), "LUCKY", font=font, fill=TITLE)
    draw.text((680, 350), "DICE", font=font, fill=TITLE)
    logo.save(out / "LuckyDice_Logo.png")


main()
