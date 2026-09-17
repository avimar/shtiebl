---
name: shtiebl-post
description: Write new shtiebl content — a Reddit-style post with its comment thread and Snapshot HD pictures, every line sourced to Sefaria. Use when asked for more posts, more comments, side discussions or comment images on the shtiebl site.
---

# Write shtiebl posts

Real Torah told as Reddit posts. **The facts are Chazal's; only the packaging is ours.**
File layout, field names and the image commands are in `README.md`. Read it first.

## The voice (the part that makes it worth reading)

**Take the metaphor or mashal Chazal already built, and say it in modern idiom.** The user's favorite lines all do this:

| Line | What Chazal already said |
|---|---|
| "It's not a feast, it's a date." | Rashi Bamidbar 29:36: "make me a small meal so I can enjoy you" |
| Nineveh king holding the beam: "Look at the effort we went through!! … FOUND IT" | Taanis 16a: they tore down palaces to return one stolen beam |
| "I don't 'stay up.' I *get kept* up." | Mishna Yoma 1:7: the young kohanim kept him awake |

- Loud for its own sake (ALL CAPS, "??") is weaker. Use the recipe instead.
- Recurring characters cross-talk: Rashi correcting people, Aharon being defensive, the Nineveh king showing off, random_cow. Reuse existing users (`content/users.js`) before inventing new ones.
- **Don't rewrite an existing post's title or hook.** Show the user the proposed wording and ask first. New posts get new titles freely.

## Rules (non-negotiable)

1. Every post and every non-flavor comment has a `src`, and the text there **really says it**. Read the source (Sefaria API: `https://www.sefaria.org/api/v3/texts/<Ref>`); a ref that merely exists is not enough.
2. u/HaMelech (ADMIN) speaks **only** verbatim pesukim / Chazal, cited. Never invented words for Him. God is never shown in an image.
3. Invented lines are `flavor: true`. Invented lines for real sages must not contradict what they actually held.
4. No lashon hara. Affectionate, never mocking Torah or the sages.
5. No profanity, including in real-subreddit names (`aka`). Leave `aka: ""` rather than quote a crude sub name.
6. **Gemara (any daf ref, incl. Rashi/Tosafos on the daf) links to the passage, not the page:** write `Shabbos 87a:5` (the Sefaria segment number; ranges like `Sotah 13b:9–14a:2`). Find the number by fetching the daf from the Sefaria API and matching the text. `tools/check.py` fails on a bare daf.
7. Halacha claims: say whose opinion it is (Shulchan Aruch, Rema, Mishna Berura…) and cite the siman.
8. A link to another thread is a real link: `<a href="#/r/<Sub>/<id>">…</a>` (add `/c/<cid>` for one comment). Never `onclick="go(…)"`: that can't be Ctrl-clicked or copied.

## Steps

1. Pick the Torah first (a real, surprising, sourced fact), then the sub and the joke. Subs live in `content/subs.js`; add one if needed (icon, color, clean `aka`).
2. Write `content/posts/<id>.js` (copy the shape of an existing post, e.g. `content/posts/yonah.js`). Aim for **6–12 comments, 1–3 comment images**, with at least one reply chain.
3. Add the id to `POST_ORDER` in `content/index.js` (it controls feed order; group it with its holiday). Add new users to `content/users.js` with avatar, flair and a one-line in-character bio.
4. New book name in a `src`? Add it to `SEF_NAMES` in `index.html`. Unknown Sefaria name: `https://www.sefaria.org/api/name/<text>`.
5. Pictures (one set, `img/snapshot_gpt/`): add scene keys to `img/prompts.json` (`<id>` for the post, `c_<name>` for comments), then

       python img/gen_images.py snapshot <ids...> --as snapshot_gpt --fal-model openai/gpt-image-2.5/flare/text-to-image --quality low

   Make the picture the **punchline** of the title, not a generic illustration (e.g. a kid aiming a lulav at the shul router, not "kid holding four minim"). **No women unless the scene can't work without one** (the site keeps only two mothers and the Kohen's wife): prefer men and boys, and end the scene prompt with "Every person in the picture is a man or a boy; no women or girls anywhere." (the shared suffix alone isn't enough). Faces and poses should serve the joke; nothing the scene doesn't call for. **Look at every image** (Read the .jpg), **zooming into the background**: small figures there are where women slip in. Check for modest dress, married women's hair covered, no crosses/church domes, no God. Redo a bad one with `--count 3 --force`, then `--pick N`. If an otherwise good image has one local glitch (a head lost in a coffin), try an edit first: `python "C:\Users\Admin\Marcus Personal Sync\ADM Obsidian\.claude\skills\make-image\scripts\make_image.py" "<what to fix>" --edit img/snapshot_gpt/<id>.png -o <new.png>` (GPT Image edit, low, ~$0.004), then record it in `img/manifest.json`. To swap it in: `recycle` the old png, put the new one in its place, set its modified time to now (`Copy-Item` keeps the old time, and then `img/optimize.py` skips it), run `python img/optimize.py`. When writing the manifest from Python, use `json.dumps(..., ensure_ascii=False, indent=1) + "\n"` like `gen_images.py` does (`img/prompts.json` uses `indent=2`); any other indent rewrites the whole file in the diff.
   If Avi likes part of a picture (a face, a pose), edit out the problem instead of regenerating; a new take loses the part he liked.
   Many pictures to approve? Build one local before/after page (current picture + takes, a radio per row, a "copy choices" button). Save the picks in `localStorage`, and never rebuild or reopen the page while he is marking: a reload wiped his picks once.
6. `python tools/check.py` must pass (it checks users, images, links, Sefaria refs, scrolling).

**Many threads at once:** work in batches (e.g. by holiday), **one batch at a time**. All batches write the shared `img/prompts.json` and `img/manifest.json`. A background subagent per batch works well. Tell it to read this skill, not to change titles or hooks, not to commit, and to report a table plus the claims it's unsure of. Then review it yourself: a contact sheet of the new images, 4–5 refs read on Sefaria (for a doubtful word, check the commentary too, e.g. Rashi), `check.py`, then commit the batch's files by name.
7. Commit only when asked to; pushing publishes the site.

## Budget
GPT Image low ≈ $0.004 per image. Never omit `--quality low` (fal bills high, ~9×). Don't use Gemini or higher quality without asking.
