# shtiebl — Torah edutainment as a Reddit mock-up

**Live:** https://avimar.github.io/shtiebl/ (GitHub Pages, served from `main`, so pushing is publishing).
Locally, open `index.html` in a browser. There is no build step. The page loads the content files directly.

- **Permalinks:** `#/p/<post id>` opens that thread at the top, showing the whole post. Only a tap from the feed skips past most of the image, since that reader already saw it. **Share** copies the permalink and shows "Link copied to clipboard".
- **Sub pages:** `#/r/<Sub>` shows that community's header and only its posts. Tap any `r/…` name to go there.
- **Navigation:** each list view (feed, sub page) saves its scroll spot in its own history entry when you leave it. The thread's "← Back to …" links (top and bottom) and the browser's Back button return to that exact spot. The logo goes to the feed; on the feed it scrolls to the top.
- **Holiday chips** filter the feed: Aseres Yemei Teshuva, Yom Kippur, Sukkos, Shemini Atzeres/Simchas Torah.
- **Images:** the site loads `img/[<style>/]<id>.jpg`. Comment images are `c_*`, attached with `img: "c_name"`. The `.png` originals are local only (gitignored). `img/optimize.py` makes the `.jpg` copies and runs automatically after `gen_images.py`.
- **Picture switcher** (Snapshot HD, the default, / Snapshot FLUX / Cartoon / Movie) swaps image sets. A missing image falls back to the cartoon.
- **Sources link to Sefaria.** `linkSources()` in `index.html` maps the citation names to Sefaria refs (the `SEF_NAMES` table). Anything it can't parse becomes a Sefaria search link. When you add a new book name, add it to the table.

## Content files

| File | Holds |
|---|---|
| `content/index.js` | `POST_ORDER`: the feed order. Each id loads `content/posts/<id>.js`. |
| `content/posts/<id>.js` | One whole post and its comments: `post({id, sub, by, hol, age, votes, comments, awards, verdict, title, hook, img, body, op, src, thread})`. `body` shows in the feed; `op` (optional) replaces it in the thread. |
| `content/users.js` | Every username: `{avatar, flair, bio, admin?}`. |
| `content/subs.js` | The communities: `{icon, color, aka}`. |

A comment is `{by, flair?, votes, x, src?, img?, flavor?, replies?}`. The OP badge is automatic (the comment's `by` is the post's `by`). A comment's `flair` overrides the user's default. If a post file is missing or throws, the page shows a red banner naming it and renders the rest.

To add a post: write `content/posts/<id>.js`, add the id to `POST_ORDER`, and add any new users to `users.js`. Countdown dates live in `DATES` in `index.html`. Update them each season with `hdate`.

## Content rules
1. Every post and comment has a `src`, and the source really says it.
2. The ADMIN (u/HaMelech) quotes only Tanach or Chazal.
3. Invented lines get `flavor: true` and show a grey FLAVOR badge.

## Before you push

    python tools/check.py            # full check, about 2 minutes
    python tools/check.py --quick    # skips the scroll test and the Sefaria lookups

It checks for page errors, broken images in every style, source boxes without links, unknown users, the feed ↔ thread scroll behavior, the phone header, and that every Sefaria link resolves. Needs Playwright with Edge (`channel="msedge"`).

## Images
Scene prompts and the per-style prefixes are in `img/prompts.json`. To generate:

    python img/gen_images.py <snapshot|cartoon|cinematic> [id ...] [--count 3] [--force]

- Snapshot HD = the same prompts through GPT Image 2.5 at low quality (~$0.004 each; the command is in the script's docstring). It follows instructions far better than FLUX. Everything else runs on FLUX schnell (~$0.003). **The budget is to stay cheap**: redo a bad image with `--count 3` and pick the best take by hand. Don't move up to Gemini.
- **FLUX can't handle negatives.** Writing "no crosses" put crosses *in*. Describe what you want (a Jewish setting, a wound white turban, a flat-topped Second Temple facade). Still check every batch for crosses, church domes and short sleeves.
