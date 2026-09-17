# shtiebl — Torah edutainment as a Reddit mock-up

**Live:** https://avimar.github.io/shtiebl/ (GitHub Pages, served from `main`, so pushing is publishing).
Locally, open `index.html` in a browser. There is no build step. The page loads the content files directly.

- **Permalinks:** `#/r/<Sub>/<post id>` opens that thread. Threads always open at the top, and a blue bar in the header ("← Back to …") plus a darker page background show you're inside one. Add `/c/<cid>` to jump to one comment and flash it (`cid` = position path, e.g. `2.0` = 3rd comment's 1st reply; it shifts if comments are inserted above). Old `#/p/<post id>` links still work. **Share** copies the permalink and shows "Link copied to clipboard".
- **Sub pages:** `#/r/<Sub>` shows that community's header and only its posts. Tap any `r/…` name to go there.
- **Profiles:** `#/u/<user>` shows avatar, flair, bio, every comment (each links to its spot in the thread) and the user's posts. Tap any `u/…` name to go there.
- **Navigation:** each list view (feed, sub page, profile) saves its scroll spot in its own history entry when you leave it. The thread's "← Back to …" links (top and bottom) and the browser's Back button return to that exact spot. The logo goes to the feed; on the feed it scrolls to the top. In-site links are real `<a href="#/…">` links (Ctrl-click and copy work); one click handler sends plain clicks through `go()`. In content files, link to another thread as `<a href="#/r/<Sub>/<id>">`.
- **Holiday chips** filter the feed: Aseres Yemei Teshuva, Yom Kippur, Sukkos, Shemini Atzeres/Simchas Torah.
- **Images:** the site loads `img/[<style>/]<id>.jpg`. Comment images are `c_*`, attached with `img: "c_name"`. The `.png` originals are local only (gitignored). `img/optimize.py` makes the `.jpg` copies and runs automatically after `gen_images.py`.
- **Picture switcher** (Snapshot HD, the default, / Snapshot FLUX / Cartoon / Epic) swaps image sets. A missing image falls back to Snapshot HD.
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
1. Every post and comment has a `src`, and the source really says it. Gemara refs name the Sefaria line: `Shabbos 87a:5`, `Sotah 13b:9–14a:2` (check.py fails on a bare daf).
2. The ADMIN (u/HaMelech) quotes only Tanach or Chazal.
3. Invented lines get `flavor: true` and show a grey FLAVOR badge.

## Before you push

    python tools/check.py            # full check, about 2 minutes
    python tools/check.py --quick    # skips the scroll test and the Sefaria lookups

It checks for page errors, broken images in every style, source boxes without links, unknown users, the feed ↔ thread scroll behavior, the phone header, and that every Sefaria link resolves. Needs Playwright with Edge (`channel="msedge"`).

## Images
Scene prompts and the per-style prefixes are in `img/prompts.json`. `img/manifest.json` records, for every `.png` original, the style, scene, full prompt sent, model, quality and date, so any image can be regenerated or tweaked.

**New images are Snapshot HD only** (GPT Image 2.5 via fal, quality low, ~$0.004 each). The Snapshot FLUX, Cartoon and Epic sets are kept but not extended: a missing image in those styles falls back to the Snapshot HD one.

    python img/gen_images.py snapshot <id> --as snapshot_gpt --fal-model openai/gpt-image-2.5/flare/text-to-image --quality low --count 3
    python img/gen_images.py snapshot <id> --as snapshot_gpt --pick 2     # keep take 2, recycle the others

- Never drop `--quality low`: fal bills GPT Image at high (~9×) otherwise. Without `--fal-model` the script uses FLUX schnell.
- New comment images get a `c_` scene key in `prompts.json`. `--prompt-override "<scene>"` tries a different scene for one image without editing the shared prompt (the manifest still records the full prompt).
- Look at every take before publishing: as few women as possible (say "men and boys only" in the scene when it can do without them), modest dress (long sleeves and skirts, married women's hair covered), no crosses or church domes, God never depicted. **FLUX can't handle negatives** ("no crosses" put crosses *in*), so describe what you want instead.