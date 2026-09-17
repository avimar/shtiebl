"""Make web copies: every img/**/*.png -> sibling .jpg (max 1200px wide, q82).

The site loads only the .jpg files; the .png originals stay local (.gitignore'd).
Runs automatically at the end of gen_images.py. Skips jpgs newer than their png.
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent

def optimize():
    n = 0
    for png in HERE.rglob("*.png"):
        jpg = png.with_suffix(".jpg")
        if jpg.exists() and jpg.stat().st_mtime >= png.stat().st_mtime:
            continue
        im = Image.open(png).convert("RGB")
        if im.width > 1200:
            im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
        im.save(jpg, "JPEG", quality=82, optimize=True, progressive=True)
        n += 1
    return n

if __name__ == "__main__":
    print(f"optimized {optimize()} image(s)")
