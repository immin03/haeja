# The Emperor's Diary (EN) — packaging spec for a US audience

Owner decision 2026-11-11 01:58 KST. Applies to every English longform on @EmperorsDiary-en.
Build packaging for a US audience from scratch. Do not adapt the Korean thumbnail, title or description style.

## Thumbnails (3 A/B variants, 1280×720 PNG, under 2 MB)
- Text: 3–5 English words max, heavy bold sans-serif, with a shadow or backing so it stays legible.
- Keep the lower-right corner empty (YouTube's duration stamp sits there). Keep key elements away from the edges so a mobile crop does not cut them.
- One focal point: a face filling about 1/4–1/3 of the frame. Use Marcus Aurelius (statue or portrait style art) or the story's central person, with a clear, genuine expression. No exaggerated meme faces.
- Dark cinematic background with high contrast. Accent color: gold, teal or orange. Avoid a red/white/black palette, which blends into YouTube's UI.
- Use at most 1–2 visual cues, for example one arrow or one circle.
- Test at phone-feed size (about 360×202) before finalizing.
- Each variant changes ONE element. For example: A = emperor face + text, B = betrayer/scene face + same text, C = A's image with different wording.
- Do not copy the Korean thumbnail wording or Korean text; the words follow the US research (samples/round2/thumb_research.md: viewer's situation first, 4–9 words in two sizes, white + yellow/gold).
- COIN EMBLEM (owner 2026-11-11 09:30, overrides the earlier small-badge layout of v1–v3): do it the way the Korean channel does (docs/emperor/long/ep04_a.jpg). The Aurelius coin is LARGE — about half the left side (diameter ≈ 640–680 px on 1280×720), warm gold, softly blended (screen) into the dark background, with the words sitting on top of it. Never a small logo badge in a corner. Reference build: make_thumb_en4.py (samples/round3/).
- Korean thumbnails share: dark painterly figure, heavy white text + one yellow/gold line, one small subtitle line, text grouped on one side.

## Title
- Under 70 characters, with the main keyword early.
- Patterns that work for top US Stoic channels: a numbered list or a direct command, plus a transformational payoff and curiosity.
- Use 1–2 words in CAPS for emphasis. End with "| Stoicism" or "| Marcus Aurelius".
- Propose 3 options and pick the best. Example direction: "3 Stoic Ways to WIN Against Someone Who Betrayed You | Marcus Aurelius".

## Description
- Put the target keyword (Marcus Aurelius / Stoicism / the topic) in the first two sentences.
- Follow with a short, hooky summary, then chapters with timestamps.
- Include one subscribe CTA.
- Source line: "Meditations quotes adapted from George Long's public-domain translation."
- Add the AI/altered-content disclosure, as the channel already does.
- End with 3–5 hashtags: #Stoicism #MarcusAurelius #Meditations + 1 topic tag.

## Tags
stoicism, marcus aurelius, meditations, stoic philosophy, stoic wisdom, plus topic tags (e.g. betrayal, how to deal with betrayal, revenge, forgiveness).

## Language
US English spelling throughout. No Korean anywhere: not in the video, the thumbnail, the title, the description or the tags.

## Other fixed choices
- Voices: `voices_en.json` (narrator Ron, Marcus Aurelius Robert at tempo 0.87, general Carl, rebel Rusty).
- Render: `longform_en.py` (the same template engine as the Korean cut, with English fonts and strings).
- Modern-day scenes use Western people and settings.
