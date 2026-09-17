"""Batch-generate shtiebl images on fal (FLUX schnell ~$0.003 each; GPT Image low ~$0.004).

    python gen_images.py <style> [id ...] [--count N] [--force]

style = cartoon | cinematic | snapshot (see prompts.json "_styles").
cartoon writes img/<id>.png; the other styles write img/<style>/<id>.png.
No ids = every scene. Existing files are skipped unless --force.
--as DIR --fal-model M --quality low = same style prompts via another model, e.g. Snapshot HD:
    gen_images.py snapshot --as snapshot_gpt --fal-model openai/gpt-image-2.5/flare/text-to-image --quality low
--count N > 1 writes <id>-1.png..<id>-N.png to pick from by hand.
"""
import argparse, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
MAKE = Path(r"C:\Users\Admin\Marcus Personal Sync\ADM Obsidian\.claude\skills\make-image\scripts\make_image.py")

ap = argparse.ArgumentParser()
ap.add_argument("style")
ap.add_argument("ids", nargs="*")
ap.add_argument("--count", type=int, default=1)
ap.add_argument("--force", action="store_true")
ap.add_argument("--as", dest="as_dir", help="write to img/<AS>/ instead of img/<style>/ (e.g. same style, other model)")
ap.add_argument("--fal-model", help="fal model id (default: FLUX schnell)")
ap.add_argument("--quality", help="passed through; GPT Image needs 'low' or it bills at high")
a = ap.parse_args()

P = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
prefix = P["_styles"][a.style]
out_dir = HERE / a.as_dir if a.as_dir else (HERE if a.style == "cartoon" else HERE / a.style)
out_dir.mkdir(exist_ok=True)
ids = a.ids or [k for k in P if not k.startswith("_")]

def run(i):
    out = out_dir / f"{i}.png"
    if a.count == 1 and out.exists() and not a.force:
        return f"skip {i}"
    prompt = prefix + P[i].replace("{kg}", P["_kg"]) + P["_suffix"]
    cmd = [sys.executable, str(MAKE), prompt, "--fal", "-o", str(out)]
    if a.count > 1:
        cmd += ["-c", str(a.count)]
    if a.fal_model:
        cmd += ["--fal-model", a.fal_model]
    if a.quality:
        cmd += ["--quality", a.quality]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return f"{'ok  ' if r.returncode == 0 else 'FAIL'} {a.style}/{i}" + ("" if r.returncode == 0 else "\n" + r.stderr[-300:])

with ThreadPoolExecutor(6) as ex:
    for line in ex.map(run, ids):
        print(line, flush=True)

from optimize import optimize   # web .jpg copies; the site loads those, not the .png
print(f"optimized {optimize()} image(s) to .jpg")
