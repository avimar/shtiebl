# Handoff: restructure shtiebl — sub pages, user profiles, richer threads

You are picking this up cold. Read this file fully, then `README.md`, then skim `index.html`.
The user has approved every decision below; don't re-ask them. Work in `C:\Users\Admin\coding\shtiebl`
(Windows, use the PowerShell tool; Python and Node are available).

## The short version

shtiebl is a static Reddit look-alike where real Torah (Yom Kippur, Sukkos, Simchas Torah…) is
told as Reddit posts and comment threads, every line sourced to Sefaria. Live at
https://avimar.github.io/shtiebl/ (GitHub Pages from `main` of `avimar/shtiebl`: **pushing = publishing**).

Today all content is JS data inside `index.html`. The job:

1. Move content into per-post files + a users file + a subs file. Drop the Warm/Deadpan tones.
2. Add `#/r/<Sub>` pages.
3. Add `#/u/<user>` profile pages (bio, posts, all their comments, each linking into its thread).
4. Record every image's prompt + model in a manifest so any image can be regenerated or tweaked.
5. Content pass: more flavor comments, side discussions, ~20 more comment images.

**Each step is useful alone. Commit + push after each one that passes the checks.**

## Decisions already made (don't re-litigate)

| Decision | Chosen |
|---|---|
| Tones | **Spicy only.** Delete Warm, Deadpan, the tone switcher, and the `SPICY` override layer (its text *is* the Spicy text now). Git history keeps the old ones. |
| User bios | **Yes** — short in-character bios on profiles (e.g. u/Rashi: "11th-c. France. Wine merchant. Explains everything in five words."). |
| New images | **Snapshot HD only** (`img/snapshot_gpt/`). Keep the old style sets (cartoon, `snapshot/`, `cinematic/`) and the picture switcher working, but **generate nothing new for them**. Missing images in those styles must fall back to the Snapshot HD image (today the fallback is cartoon — change it). |
| Image provenance | Record prompt + model + quality per image in `img/manifest.json` so it can be regenerated. |
| Build step / database | **None.** Static files, loaded by the page directly. No search, no real voting, no login. |
| Permalinks | Keep `#/p/<post id>` working unchanged (links are already shared). |

## Today vs. after

| | Today | After |
|---|---|---|
| Content | JS objects in `index.html`: `SUBS`, `HOLIDAYS`, `TONES`, `POSTS` (titles/hooks per tone), `THREADS` (2 blocks), `SPICY` overrides | `content/subs.js`, `content/users.js`, `content/posts/<id>.js` (one file = whole post + comments), `content/index.js` (ordered list of post ids) |
| Users | plain strings on comments (`a:"Rashi"`), badges per comment (`f` flair, `adm`, `op`, `flav`) | `users.js` entries: `{name, avatar, flair, bio, admin?}`; comments reference `by:` |
| Click a sub | nothing | `#/r/AmITheRasha` → sub header (icon, name, the "aka" real subreddit) + filtered feed |
| Click a user | nothing | `#/u/Rashi` → bio, their posts, their comments with "in r/X › post title" linking to `#/p/<id>/c/<cid>` (thread scrolls to + briefly highlights that comment) |
| Images | `img/prompts.json` (scene prompts + style prefixes), no record of which model made which file | plus `img/manifest.json`: per file → style, full prompt, model, quality, date |

## Current code map (index.html)

Line numbers drift; grep for the names.

| Thing | Name in index.html |
|---|---|
| Subs, holidays, tone blurbs | `SUBS`, `HOLIDAYS`, `TONES` |
| Posts (fields: `id, sub, hol, by, age, v, c, aw, verdict, t{spicy,warm,dry}, h{…}, body, src`) | `POSTS` |
| Threads for calf/kgama/yonah/tablets (`op` = replacement body, `cm` = comments) | `THREADS` |
| Spicy v2 titles/hooks — **these are the canonical Spicy text** | `SPICY` |
| Threads for the other 17 posts | `Object.assign(THREADS, {…})` |
| Comment fields: `a` user, `f` flair, `v` votes, `x` HTML, `s` source, `img`, `adm`, `op`, `flav`, `k` replies | `comment()` renderer |
| Sefaria linker (citation text → sefaria.org URL; unparsed → Sefaria search) | `SEF_NAMES`, `SEF_RE`, `linkSources()` |
| Image path + fallback | `imgSrc()`, `imgFallback()` |
| Navigation, scroll memory, permalinks, share toast | `go()`, `backToFeed()`, `routeFromHash()`, `share()`, `toast()` |
| Countdown dates | `DATES` |

When merging a post: title/hook = `SPICY[id]` (fallback `t.spicy`/`h.spicy`); body = `THREADS[id].op` **if present** for the thread view but `POSTS.body` for the feed card (today the thread view swaps in `op`). Keep both: `body` (feed) and `op` (thread, optional).

## Navigation behavior that must survive (it was tuned with the user)

| Situation | Behavior |
|---|---|
| Tap a post in the feed | Thread opens scrolled so only the bottom ~quarter of the image shows (they already saw it). Short threads get bottom padding on `body` (not the column — the sidebar is taller) so the scroll is possible. |
| Shared link / reload of `#/p/<id>` | Opens at the **top** (whole post visible). |
| Back to feed (top and bottom links), logo, browser Back | Return to the exact feed spot. Logo on the feed = jump to top. |
| Share | Copies `…/#/p/<id>` and shows toast "Link copied to clipboard" (clipboard API with `execCommand` fallback). |
| Phones (≤700px) | One-row header: logo + ⚙ button labelled with current picture emoji; tapping opens switchers + dark mode. Holiday chips scroll sideways. After dropping tones, the ⚙ label is just the picture emoji. |

New routes should reuse the same machinery: `#/r/<sub>` and `#/u/<user>` are "feed-like" views (remember scroll anchor when leaving to a thread; Back returns there).

## The build, in 5 steps

### Step 1 — Restructure + drop tones (no visible change except the tone switcher is gone)

- Write a **one-off** Node/Python script that loads the current `index.html` data and emits the new files (don't hand-copy 21 posts). Throw the script away after; don't commit it.
- File shape:

```js
// content/posts/tablets.js
post({
  id: "tablets", sub: "AmITheRasha", by: "Moshe_Rabbeinu", hol: "st", age: "3,338 yr",
  votes: "112k", comments: "12.4k", awards: "🏆🏆🏆💎", verdict: "NTR (ADMIN)",
  title: "AITR for SMASHING the tablets my Boss wrote HIMSELF?",
  hook: "…", img: "tablets",
  body: `<p>…</p>`,            // feed card
  op: `<p>…</p>`,              // optional: longer body in thread view
  src: "Shemos 32:19 · Shabbos 87a · Rashi, Devarim 34:12",
  thread: [
    { by: "HaMelech", x: `…`, src: "Shabbos 87a", replies: [
      { by: "Resh_Lakish", x: `…`, src: "Shabbos 87a" } ] },
    { by: "Aharon_HaKohen", flair: "OP's brother", x: `…`, img: "c_aharon", src: "Rashi, Shemos 32:5" },
    { by: "Moshe_Rabbeinu", x: `Didn't expect that reply, ngl.`, flavor: true },
  ],
});
```

```js
// content/users.js
users({
  HaMelech:       { admin: true, avatar: "👑", flair: "ADMIN", bio: "…pesukim and Chazal only…" },
  Rashi:          { avatar: "📜", flair: "Parshan · verified", bio: "11th-c. France. Wine merchant. Explains everything in five words." },
  Moshe_Rabbeinu: { avatar: "🧔", flair: "Leader · verified", bio: "…" },
  …
});
```

- `op` badge = comment `by` equals the post's `by` (computed, not stored). Per-comment `flair` overrides the user's default.
- `content/index.js` = `POST_ORDER = ["melech", "dirshu", …]` (keeps today's feed order). `index.html` loads `subs.js`, `users.js`, `index.js`, then injects `<script src="content/posts/<id>.js">` for each id, then renders once all loaded. A post file that throws → skip it and show a red banner naming it.
- Delete: tone switcher HTML, `TONES`, `tonebar`, `t`/`h` per-tone fields, `SPICY`, `localStorage shtiebl-tone`.
- Every user referenced must exist in `users.js`. Generic one-offs (u/still_in_bed) get an entry too, with a one-line bio.
- **Done when:** the check script (below) passes and the feed/threads look like today's Spicy view.

### Step 2 — `#/r/<Sub>` pages

- Sub names (post meta + sidebar "Top communities") become links.
- Page: sub header (icon, `r/Name`, "aka r/realname", post count) + filtered feed. Holiday chips still apply within it.
- **Done when:** r/AmITheRasha shows its 4 posts; Back from a thread returns to the sub page spot.

### Step 3 — `#/u/<user>` profiles

- Usernames on posts and comments become links.
- Page: avatar, name, flair, bio; "Posts" list (feed cards); "Comments" list — each shows the comment text (trimmed), and a context line `in r/Sub › post title` linking to `#/p/<id>/c/<cid>`.
- `cid` = path index generated at render (e.g. `2.0.1`). Acceptable that it shifts when comments are inserted (only a shared comment link degrades to the thread).
- `#/p/<id>/c/<cid>`: open thread, scroll that comment into view (below the sticky header), flash a highlight ~1.5s.
- **Done when:** u/Rashi lists all his comments across threads and each jump lands on the right comment.

### Step 4 — Image manifest (prompt + model per file)

- Extend `img/gen_images.py` so every generated file appends/updates an entry in `img/manifest.json`:
  `"snapshot_gpt/c_beam.png": {"style":"snapshot","scene":"c_beam","prompt":"<full prompt sent>","model":"openai/gpt-image-2.5/flare/text-to-image","quality":"low","date":"2026-09-17"}`.
- Add `--prompt-override "<text>"` (or a `prompts.json` per-image override key) so one image can be tweaked without editing the shared scene prompt.
- **Backfill** existing entries (best known):

| Files | Model | Quality | Notes |
|---|---|---|---|
| `img/snapshot_gpt/*` | `openai/gpt-image-2.5/flare/text-to-image` (fal) | low | style `snapshot`; `snap` and `c_floor` were retried once (transient fal errors) |
| `img/snapshot/*` | `fal-ai/flux/schnell` | — | `akiva`, `lev`, `roast` picked from 3 takes |
| `img/cinematic/*` | `fal-ai/flux/schnell` | — | `bulls`, `roast` picked from 3 takes |
| `img/*.png` (cartoon) | `fal-ai/flux/schnell` | — | except `roast`, `snap`, `thread`, `clouds`, `c_ark` = `google/gemini-3.1-flash-image` (OpenRouter) with hand-written detailed prompts; `happy`, `c_beam` picked from 3 FLUX takes |

  The exact old cartoon prompts differ from today's `prompts.json` (the style prefix/suffix changed since). Record the *current* prompt with `"prompt_note": "approximate — original prompt not recorded"`.
- New comment images get a scene key in `prompts.json` (prefix `c_`) and are generated **only** in Snapshot HD:
  `python img/gen_images.py snapshot c_newthing --as snapshot_gpt --fal-model openai/gpt-image-2.5/flare/text-to-image --quality low`
- Change the page fallback: missing `img/<style>/<id>.jpg` → `img/snapshot_gpt/<id>.jpg` → hide.
- **Done when:** every `.png` under `img/` has a manifest entry, and regenerating one image by name works.

### Step 5 — Content pass (ongoing)

Goal per thread: **6–12 comments, 1–3 comment images**, more flavor replies and cross-talk between recurring characters (Rashi correcting people, Aharon being defensive, the Nineveh king showing off, random_cow). Add side discussions on related Torah (e.g. under the Yonah thread: why we read it on Yom Kippur; under Sukkos: ushpizin, the sukkah on a wagon/ship, Hoshana Rabbah).

**The voice recipe (the user's favorite lines follow it):** take the metaphor or mashal Chazal *already* built and say it in modern idiom.
- "It's not a feast, it's a date." = Rashi Bamidbar 29:36 ("make me a small meal so I can enjoy you").
- The Nineveh king holding up the beam: "Look at the effort we went through!! … FOUND IT" = Taanis 16a.
- "I don't 'stay up.' I *get kept* up." = Mishna Yoma 1:7.

Loud-for-its-own-sake (ALL CAPS + "??") is weaker. Use the recipe instead.

Images: ~20 new comment images, Snapshot HD only (~$0.004 each, ~$0.08 total). Good candidates are visual punchlines: the leaning study-hall walls, R' Shimon ben Gamliel's thumb-bow, Levi limping, the soggy kugel, the backup wife waiting in the wings, the esrog in its velvet box.

## Content rules (non-negotiable)

1. **Every post and non-flavor comment has a `src`**, and it must be real. `linkSources()` turns it into a Sefaria link; add new book names to `SEF_NAMES`. Verify new refs resolve: `https://www.sefaria.org/api/v3/texts/<Ref>` (see check script). Check the *content* claim against the text, not just that the ref exists.
2. **ADMIN (u/HaMelech) speaks only in verbatim pesukim / Chazal**, cited. Never put invented words in His mouth. God is never depicted in images.
3. **Invented lines are `flavor: true`** (grey FLAVOR badge). Invented lines for real sages must not contradict what they actually held.
4. No lashon hara; the tone is affectionate, not mocking of Torah or of the sages.
5. Still unverified from the earlier round — check when touching those threads: Gra on Shir HaShirim 1:4 (clouds return after YK), Rema OC 639:7 ("hedyot"), Rambam Avodas Yom HaKippurim 1:7 (reason for staying awake).

## Image rules (learned the hard way)

- **Default model** is the `/make-image` default: GPT Image 2.5 via fal at **quality low** (~$0.004). Never omit quality — fal bills GPT Image at `high` (~9×) by default. Don't use Gemini or higher quality without asking the user.
- **Modesty:** long sleeves, long skirts, high necklines, married women's hair covered. The shared `_suffix` in `prompts.json` handles most of it; still look.
- **No crosses / church domes.** FLUX can't do negatives ("no crosses" *added* crosses). Describe positively (Jewish setting, wound white turban, flat-topped Second Temple facade).
- **Always review** a contact sheet before publishing (render a grid HTML of the new files and screenshot it with Playwright via `channel="msedge"`; the bundled Chromium is not installed). Redo bad ones with `--count 3 --force` and pick by eye; recycle the losers with `recycle`.
- `.png` originals are gitignored; the site loads `.jpg` copies made by `img/optimize.py` (runs automatically at the end of `gen_images.py`).

## When things go wrong

| What breaks | What to do |
|---|---|
| Content script can't parse `index.html` data | Evaluate the `<script>` block in Node with stubbed `document`/`localStorage` and read the globals instead of regex-parsing. |
| A post file throws at load | Page shows a red banner naming the file and renders the rest. Fix the file. |
| A `by:` user isn't in `users.js` | Check script fails listing them. Add the user. |
| A Sefaria ref 404s / 400s | Look up the canonical name with `https://www.sefaria.org/api/name/<text>` (e.g. Mechilta = `Mekhilta_DeRabbi_Yishmael,_Tractate_Pischa.1`). If Sefaria doesn't have the book, leave it unparsed (it becomes a search link). |
| fal call fails | Usually transient — retry that one image. |
| Scroll position wrong in a new view | Remember: pad `body`, not the column; measure after `render()`; test with a real click only after scrolling the card into view yourself (Playwright's auto-scroll fakes offsets). |
| Anything looks off after push | `git revert` the commit and push; Pages redeploys in ~1 min. |

*Principle: nothing is pushed until the check script passes, and every step is its own commit.*

## The check script (run before every push)

Serve locally (`python -m http.server 8765 --directory C:\Users\Admin\coding\shtiebl`, then stop it) and with Playwright (`channel="msedge"`) verify:

- No `pageerror`s on `/`, every `#/p/<id>`, every `#/r/<sub>`, every `#/u/<user>`.
- Every `<img>` loads (`naturalWidth > 0`) in each picture style.
- Every `.src` box has at least one link.
- Every `by:` exists in `users.js`; every post id in `POST_ORDER` has a file and vice versa.
- Feed → thread opens with ~22–30% of the image visible; Back restores the card's offset within 2px (do this for every post, as the previous agent did).
- `#/p/<id>` fresh load → `scrollY == 0`.
- Phone viewport 412×915 `is_mobile=True`: header ≤ 50px closed.
- New Sefaria refs resolve via the v3 API (collect hrefs from the rendered pages).

Consider saving this as `tools/check.py` (commit it — it's the reusable part).

## Publishing

`git add -A; git commit; git push` from the repo root. End commit messages with:
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
Then poll until live, e.g. `curl -s https://avimar.github.io/shtiebl/?v=N | grep -q '<something new>'`.
Update `README.md` in the same commit when behavior or file layout changes (it's the usage doc — keep it short; history goes nowhere).

## Assumptions

| I'm assuming | Why | How it could be wrong |
|---|---|---|
| ~25 small script files load fine on Pages | few KB each, cached | Slightly slower first load on bad connections — acceptable |
| One Spicy voice is all we need | User said Spicy is the reason this is worthwhile | They may want a kids' version later; git has the Warm text |
| Comment ids by position are good enough | Only generated inside the site | A shared comment link lands on the thread, not the comment, after inserts |
| Old cartoon prompts can't be recovered exactly | Style prefix/suffix changed after they were made | Minor: regenerating a cartoon gives a slightly different look (and we're not regenerating those anyway) |

## Side effects *(skip this)*

- Profiles expose continuity: inconsistent flair/voice for a character becomes visible — fix it in `users.js`.
- More content = more sources to verify; the Sefaria links keep that to one click, but claims still need reading.
- Deleting Warm/Deadpan removes some good Shabbos-table lines from the live site; they're in git history (commit `b3d1989` and earlier).
