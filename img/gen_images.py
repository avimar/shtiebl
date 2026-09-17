"""Batch-generate shtiebl images on fal and record each one in img/manifest.json.

    python gen_images.py <style> [id ...] [--count N] [--force] [--prompt-override "..."]
    python gen_images.py <style> <id> --pick N [--as DIR]

style = cartoon | cinematic | snapshot (see prompts.json "_styles").
cartoon writes img/<id>.png; the other styles write img/<style>/<id>.png.
No ids = every scene. Existing files are skipped unless --force.

New images are Snapshot HD only (GPT Image 2.5, quality low, ~$0.004 each):
    gen_images.py snapshot c_newthing --as snapshot_gpt --fal-model openai/gpt-image-2.5/flare/text-to-image --quality low
Never drop --quality low: fal bills GPT Image at high (~9x) otherwise. Without --fal-model it is FLUX schnell.

--count N > 1 writes <id>-1.png..<id>-N.png. Look at them, then
--pick K makes take K the real <id>.png (moving its manifest entry) and recycles the other takes.
--prompt-override "full scene text" replaces the prompts.json scene for this run (one id only);
    the prefix/suffix still apply, and the manifest records the full prompt sent.
"""
import argparse, datetime, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
MAKE = Path(r"C:\Users\Admin\Marcus Personal Sync\ADM Obsidian\.claude\skills\make-image\scripts\make_image.py")
RECYCLE = Path.home() / ".claude" / "scripts" / "recycle.py"
MANIFEST = HERE / "manifest.json"
FLUX = "fal-ai/flux/schnell"

ap = argparse.ArgumentParser()
ap.add_argument("style")
ap.add_argument("ids", nargs="*")
ap.add_argument("--count", type=int, default=1)
ap.add_argument("--force", action="store_true")
ap.add_argument("--as", dest="as_dir", help="write to img/<AS>/ instead of img/<style>/ (e.g. same style, other model)")
ap.add_argument("--fal-model", help="fal model id (default: FLUX schnell)")
ap.add_argument("--quality", help="passed through; GPT Image needs 'low' or it bills at high")
ap.add_argument("--prompt-override", help="scene text to use instead of prompts.json (one id only)")
ap.add_argument("--pick", type=int, help="keep take N of a --count run as <id>.png; recycle the rest")
a = ap.parse_args()

P = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
out_dir = HERE / a.as_dir if a.as_dir else (HERE if a.style == "cartoon" else HERE / a.style)
out_dir.mkdir(exist_ok=True)
ids = a.ids or [k for k in P if not k.startswith("_")]
if (a.prompt_override or a.pick) and len(ids) != 1:
    sys.exit("--prompt-override and --pick need exactly one id")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
def key(path):
    return path.relative_to(HERE).as_posix()
def save_manifest():
    MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

if a.pick:
    i = ids[0]
    takes = sorted(out_dir.glob(f"{i}-[0-9]*.png"))
    keep = out_dir / f"{i}-{a.pick}.png"
    if keep not in takes:
        sys.exit(f"no take {keep.name}; have: {', '.join(t.name for t in takes)}")
    final = out_dir / f"{i}.png"
    def recycle(paths):
        existing = [str(p) for p in paths if p.exists()]
        if existing:
            subprocess.run([sys.executable, str(RECYCLE), *existing], check=True)
    recycle([t for t in takes if t != keep] + [final, final.with_suffix(".jpg")])
    keep.rename(final)
    recycle([t.with_suffix(".jpg") for t in takes])   # every take's web copy; the kept one is rebuilt below
    entry = manifest.pop(key(keep), {})
    for t in takes: manifest.pop(key(t), None)
    manifest[key(final)] = entry
    save_manifest()
    from optimize import optimize
    print(f"kept {keep.name} as {final.name}; optimized {optimize()} image(s) to .jpg")
    sys.exit()

def run(i):
    out = out_dir / f"{i}.png"
    if a.count == 1 and out.exists() and not a.force:
        return f"skip {i}", []
    scene = a.prompt_override or P[i]
    prompt = P["_styles"][a.style] + scene.replace("{kg}", P["_kg"]) + P["_suffix"]
    cmd = [sys.executable, str(MAKE), prompt, "--fal", "-o", str(out)]
    if a.count > 1:
        cmd += ["-c", str(a.count)]
    if a.fal_model:
        cmd += ["--fal-model", a.fal_model]
    if a.quality:
        cmd += ["--quality", a.quality]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return f"FAIL {a.style}/{i}\n" + r.stderr[-300:], []
    files = [out] if a.count == 1 else [out_dir / f"{i}-{n}.png" for n in range(1, a.count + 1)]
    entry = {"style": a.style, "scene": i, "prompt": prompt, "model": a.fal_model or FLUX,
             "quality": a.quality, "date": datetime.date.today().isoformat()}
    if a.prompt_override:
        entry["prompt_override"] = True
    return f"ok   {a.style}/{i}", [(key(f), entry) for f in files if f.exists()]

with ThreadPoolExecutor(6) as ex:
    for line, entries in ex.map(run, ids):
        print(line, flush=True)
        manifest.update(entries)
save_manifest()

from optimize import optimize   # web .jpg copies; the site loads those, not the .png
print(f"optimized {optimize()} image(s) to .jpg")
