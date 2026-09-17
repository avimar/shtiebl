# shtiebl — Torah edutainment as a Reddit mock-up

**Live:** https://avimar.github.io/shtiebl/ (GitHub Pages, served from `main`, so pushing is publishing).
Locally, open `index.html` in a browser. It is one file with no build step.

- **Permalinks:** `#/p/<post id>` opens that thread. **Share** copies the permalink and shows "Link copied to clipboard".
- **Navigation:** Back to feed (top and bottom of a thread), the logo, and the browser's Back button all return to your spot in the feed. On the feed, the logo scrolls to the top.

- **Tone switcher** (🌶 Spicy / 🤗 Warm / 🎩 Deadpan) changes only each post's title and opening line. The facts and sources stay the same.
- **Holiday chips** filter the feed: Aseres Yemei Teshuva, Yom Kippur, Sukkos, Shemini Atzeres/Simchas Torah.
- **Every post opens a thread** with nested comments. Threads live in `THREADS`, keyed by post id.
- **Images:** the site loads `img/[<style>/]<id>.jpg`. Comment images are `c_*`, attached with `img:"c_name"`. The `.png` originals are local only (gitignored). `img/optimize.py` makes the `.jpg` copies and runs automatically after `gen_images.py`.
- **Picture switcher** (Snapshot HD, the default, / Snapshot FLUX / Cartoon / Movie; Vintage was tried and dropped) swaps image sets. A missing image falls back to the cartoon.
- **Sources link to Sefaria.** `linkSources()` maps the citation names to Sefaria refs (the `SEF_NAMES` table). Anything it can't parse becomes a Sefaria search link. When you add a new book name, add it to the table.

## Images
Scene prompts and the per-style prefixes are in `img/prompts.json`. To generate:

    python img/gen_images.py <snapshot|cartoon|cinematic> [id ...] [--count 3] [--force]

- Snapshot HD = the same prompts through GPT Image 2.5 at low quality (~$0.004 each; the command is in the script's docstring). It follows instructions far better than FLUX. Everything else runs on FLUX schnell (~$0.003). **The budget is to stay cheap**: redo a bad image with `--count 3` and pick the best take by hand. Don't move up to Gemini.
- **FLUX can't handle negatives.** Writing "no crosses" put crosses *in*. Describe what you want (a Jewish setting, a wound white turban, a flat-topped Second Temple facade). Still check every batch for crosses, church domes and short sleeves.
- Spicy tone v2 lives in the `SPICY` override object, which replaces `t.spicy` and `h.spicy`.

## Content rules (enforced by hand)
1. Every post and comment has a `src`.
2. `adm` (ADMIN / HaMelech) comments quote only Tanach or Chazal.
3. Invented lines get `flav:1` and show a grey FLAVOR badge.

## Adding content
Edit the `POSTS` array (`t` = title per tone, `h` = hook per tone, `body`, `src`) and `THREADS` in the `<script>` block. Countdown dates live in `DATES`. Update them each season with `hdate`.
