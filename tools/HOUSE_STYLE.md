# Walking the American Way: house style

Walking the American Way retells the stories of the Dhammapada commentary (the *Dhammapada-aṭṭhakathā*) one at a time, each moved to a moment in American history between 1492 and today. "American" is meant broadly: Indigenous nations before and after contact, Spanish, French, Dutch and Russian colonies, the borderlands, the Caribbean and territories, immigrant neighborhoods, the frontier, cities, suburbs, the present. Across the whole series, cover the full cultural and religious range of American life. The stories should not cluster in one region, era, faith or kind of person.

Also read `/home/claude/series/SEEDS.md`, the editor's wish list of images and worlds, and use a seed when it fits.

Three finished stories set the standard. Read at least one in full before writing:
- `/home/claude/series/the-mustard-seed.html` (8.13, Philadelphia 1918). This is also your HTML template.
- `/home/claude/series/stand-still.html` (13.6, Missouri 1864)
- `/home/claude/series/little-wayland.html` (2.3, Alabama 1959)

## The work, in order

1. **Check the master list first.** Run `python3 /home/claude/series/claim.py --list`. Your story numbers are assigned to you, but the setting is your choice, and it must not repeat what's already there. Avoid any community, region or decade already used, and any teacher type or scripture that's becoming common. As soon as you've chosen, claim it:
   `python3 /home/claude/series/claim.py NUM --title "..." --setting "Place, State" --year YYYY --community "..." --teacher "..." --scripture "..." --status writing --agent YOURNAME`
   Check the list again before each new story; other agents are writing at the same time.
2. **Read the source.** Fetch `https://ancient-buddhist-texts.net/English-Texts/Dhamma-Verses-Comm/CC-SS.htm` (chapter and story, zero-padded: 1.5 is `01-05.htm`, 24.6 is `24-06.htm`). Read the whole story, including any past-life stories and every verse.
3. **Choose the setting.** Pick the American moment where the story's core lands hardest, the way the purity verses landed in Jim Crow Alabama or the mustard seed in the flu autumn of 1918. Find the setting where the story's central image or situation turns real and specific. Don't take the first period that comes to mind; consider three and pick the strongest.
4. **Research the period** with web search until the material details are right: what people ate, wore, earned, worked at, feared; real events, laws and places. Don't invent a fact about a real event. Fictional towns and people are fine.
5. **Write the story** (word count and structure below).
6. **Verify.** Every scripture quotation must be checked verbatim against a public-domain source you fetched. Every Background link must be checked with a fetch or search. Every verifiable historical claim gets checked too.
7. **Build the page** from the template and save it as `/home/claude/series/<slug>.html`.
8. **Write the metadata** to `/home/claude/series/meta/<slug>.json` (format below).
9. **Mark it done:** `python3 /home/claude/series/claim.py NUM --status done`.

Don't publish anything, and don't edit `index.html`, other agents' files, `claim.py` or `build_index.py`. The lead assembles and publishes.

## Fidelity to the source

- Keep every major episode and turn of the commentary story, in order. Transpose them; don't drop them. Each Dhammapada verse the story ends on must have a real place in the retelling.
- **The Buddha figure** is a teacher who belongs to the time and place. Examples so far: a Black itinerant teacher, an Irish nun, a Dunkard elder. Vary the type widely across the series: women and men, young and old, clergy and laypeople, every faith and none. Never write a white savior who rescues people of color. The teacher speaks little, and what they say matters.
- **Miracles** (multiplying bodies, flying, coal turning to gold, radiant visions) are told plainly, as neighborhood legend or witness testimony. Don't explain them away and don't make a show of them; let them stand the way they stand in a folktale. This is the house style.
- **Past-life frames** (jātakas, karmic backstory) are either dropped or turned into something that rhymes inside the story: a family story, a porch tale, a memory, a story the teacher tells about "the same boy as always." Don't use literal reincarnation unless the community in the story actually believes in it.
- **Pāli verses become real scripture**, quoted verbatim, from the tradition that fits the characters: the Bible (KJV, Douay-Rheims, the 1917 JPS Tanakh), the Qur'an (Pickthall 1930), the Book of Mormon, the Bhagavad Gita (Arnold 1885 or Besant), the Tao Te Ching (Legge), the Book of Common Prayer, hymns published before 1929, and so on. KJV and Douay-Rheims are already heavily used; reach past them when the community allows (other Bible translations, Qur'an, Tanakh, Book of Mormon, Gita, Tao Te Ching, Kardec, hymnals, catechisms, the community's own public-domain sacred or devotional texts). Choose verses whose meaning matches the Dhammapada verse closely. The fit should hit the reader. Use only public-domain translations, quote them exactly, and cite them inline in the verse block as `— Book ch:v`. Never invent scripture, and never put a misquotation in a character's mouth. **Indigenous sacred words, songs and ceremonies are not quoted or invented.** In an Indigenous setting, carry the teaching through the teacher's own plain words, or through Christian or other scripture the community actually used in that period, and handle that relationship honestly.

## Who teaches, and where

Wisdom is everywhere. The Buddha figure can be anyone or anything the story earns: a bird, a child, a chatbot, a YouTuber, an OnlyFans creator, a psychic, a stripper, a cop, a drag queen, an atheist podcaster. Nothing is too recent and no community is off limits: Wiccans, pagans, New Agers, atheists, the Rainbow Gathering, militias, preppers, megachurches, the left, the right and the center are all fair game. Write every one of them from inside, with the same dignity and seriousness as a Dunkard elder or an Irish nun. No caricature, no sneer, no picking a political side.

Don't be afraid of ordinary people either. The series leans toward communities at the margins and toward dramatic history; it also needs boring white people, written just as closely: a Methodist insurance agent in Omaha, a Lutheran dental hygienist, a cul-de-sac in 1997, a bowling league, a regional sales manager, an HOA board, a retired shop teacher who mows at 7 a.m. The Dhamma lives in the dull places too, and an ordinary life rendered exactly is as strange as any other.

Mahayana echoes are welcome too. The bodhisattvas are innumerable: a figure who could leave and stays to help, a vow to come back for everyone, Guanyin or Jizo or Kannon in a Chinese, Japanese or Vietnamese household, an unexpected helper who might be a bodhisattva in disguise. Use them as quiet callbacks, never as lectures.

**When a community has no book,** use what it actually holds sacred or wise, in public domain if quoted (Thoreau, Whitman, Emerson, Ingersoll, the Declaration, a pre-1929 hymn or folk song, a Mahayana sutra in an old translation), or let the teacher's own words carry the verse. Never invent text and pass it off as a real quotation.

## Decades

The series is badly skewed toward the present: the 2010s and 2020s already have more than forty stories, and 1492–1680, 1700–1730 and 1800–1810 have almost none. **Until further notice, don't set a new story after 2000.** Prefer the empty decades: the 1490s through the 1670s (Columbus, Spanish Florida and New Mexico, Jamestown, Plymouth, New Netherland, the Pueblo Revolt), the 1700s–1720s, and the 1800s. Run `python3 /home/claude/series/claim.py --list` and count before choosing.

## Borders

The map draws no political borders. A story can cross them: people coming to or leaving the United States, through Canada, Mexico, the Caribbean, or across the Pacific and Atlantic. Put the main setting in lat/lon and any journey stops in the optional "route" list, and the map draws the journey as a dashed line.

## Cross-references

The series is getting dense, and the stories should start talking to each other quietly. Read `/home/claude/series/MOTIFS.md` before you write. Where your source story shares a figure, object or event with one already written (the same disciple, the same cow, a sequel), consider an echo: a recurring object, a family name, a legend someone half-remembers, a place seen again a century later. Keep it subtle enough that a reader who hasn't read the other story loses nothing. When you plant something future stories could use, add a line to MOTIFS.md.

## Opening, structure and length

- **Title:** two to four words, concrete, from inside the story (*Little Wayland*, *The Mustard Seed*, *Stand Still*).
- **Epigraph:** a scripture line from the story, with its citation.
- **Opening line:** a "Thus have I heard" in the language and idiom of the people telling it, plus the place, and nothing more. Examples in use: *Now this is how I heard it,* on Hackberry Street. / *Così ho sentito dire,* on the stoops below Washington Avenue. / *So hab ich's gehört,* on Big Creek. Leave out who told it and any extra clause.
- **Three to eight sections** (fewer for a short story), numbered with Roman numerals and titled (`I. The Road`), each with a dateline (*Cass County, Missouri · autumn 1864*).
- **Length:** let the source decide. A rich, episodic source (many turns, a past-life frame, several verses) may run 4,000 to 6,000 words. A slight one (a paragraph and a verse) should be 1,500 to 3,000. Never pad to reach a number. A short story that lands beats a long one that sags.
- **Watch the series' tics:** neighbors arriving with "a ham," strings of "and... and... and," endings where smoke goes straight up, a stranger who is never seen again. Each has been used; find your own.

## Prose

- Close third person, plain and concrete, in the cadence of the time and place. Avoid dialect spelling and caricature; voice comes through word choice and rhythm, not apostrophes.
- Dialogue in `<em>` with no quotation marks, as in the template.
- Period detail does real work: prices, tools, foods, jobs, laws, weather. Fold one or two facts only this period would have into the plot, the way the mustard plasters of 1918 did.
- Let images recur and pay off (the handkerchief, the gold, the chimneys). End on a concrete image, not a moral.
- Avoid mannered devices: stacks of em dashes, "not X but Y," colon reveals, stock phrases. Don't explain the parallel to the source in the story; the Background section does that.
- Treat cruelty and violence with weight. Don't make them gratuitous, and don't flinch from them when the source doesn't.
- Real public figures may appear only in the distance, never with invented dialogue. No real private individuals.
- Treat every community with respect. Show people's dignity and full lives, not just their suffering.

## The page

Copy `the-mustard-seed.html` and change it:
- Keep the fonts (IM Fell English for display, Spectral for body), the column, the type scale and all the structural classes: `.series` nav, `h1`, `.epigraph`, `.heard`, sections with `h2` and `.dateline`, `.verse`, `.brk`, `details.bg`, `footer` with `.pager`.
- **Give the page its own palette and atmosphere.** Choose four to six tokens in `:root` drawn from the story's world, using a single committed theme, light or dark. Write a small canvas effect tied to the story's central image (the series so far has fireflies, votive flames, and a moon crossed by clouds). It must stay subtle behind the text, respect `prefers-reduced-motion` with a static frame, cap devicePixelRatio at 2, and never block reading. Don't reuse an effect another story already has.
- The `.series` nav reads `Walking the American Way` (linking to index.html) on the left and `Commentary N.N · <Pāli name>` on the right.
- Only Google Fonts may load from outside. No remote images or scripts; everything is inline.
- **Background** (a collapsed `<details class="bg">` placed just before the footer) has three parts:
  1. *The verse* (or *The verses*): each Dhammapada verse in F. Max Müller's 1881 translation, verbatim from `https://www.gutenberg.org/files/2017/2017.txt`, cited `Dhammapada N, tr. F. Max Müller (1881)`.
  2. One paragraph summarizing the original commentary story, with links to `the full commentary story` (its ancient-buddhist-texts page) and to a Wikipedia or similar page on the main figure, if one exists.
  3. A heading for the place and period, then two paragraphs of historical context with links to Wikipedia or other stable sites (national park, state archive, university encyclopedia), each one verified.
- **Footer:** `After the story of <name> from the Dhammapada commentary (verse N). <a href="...">The original</a>. Scripture from <translation(s)>. Written by <your exact model name, e.g. Claude Opus 5.5>.` followed by an empty `<div class="pager"></div>`, which the lead's build script fills in.
- Drop cap selector must be `section > .dateline + p::first-letter` (the template had a bug; already fixed there).
- Before finishing, check that the HTML parses with every tag closed (`python3 -c "import html.parser"` with a quick checker is enough) and grep it for `http` to confirm the only outside loads are Google Fonts.

## Metadata file

`/home/claude/series/meta/<slug>.json`:
```json
{"num": "1.1", "title": "…", "place": "City, State", "year": "1871", "source": "Cakkhupāla",
 "file": "<slug>.html", "accent": "#hex", "glow": "#hex",
 "logline": "One sentence, under 25 words, concrete, no spoilers of the ending.",
 "model": "<your model name>", "lat": 00.00, "lon": -00.00,
 "route": [[lat, lon], ...]}   // optional: other places the story travels to, in order
```

## Report back

When all your stories are done, reply with one line per story: number, title, setting and year, word count, teacher figure, scripture used, and anything you couldn't verify.
