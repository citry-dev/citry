# Writing blog posts

Citry blog posts come in two voices. Pick one before you write.

- **Personal posts** speak in the maintainer's voice: a major release, a
  milestone, why the project exists, where it is going. They follow this
  guide.
- **Routine posts** report something that happened: an incident, a
  service change, a small release. They use the neutral voice of the docs
  and follow [`writing-docs.md`](writing-docs.md). The model routine post
  is
  [`2026-10-22-emsign-certificate-incident.md`](../../docs_site/content/blog/2026-10-22-emsign-certificate-incident.md).

The model personal post is
[`2026-11-16-citry-1-0-0.md`](../../docs_site/content/blog/2026-11-16-citry-1-0-0.md),
which the maintainer edited by hand to set this tone. Read it before
drafting a personal post, and match it.

## The voice

The maintainer's voice is sincere, honest, thoughtful, data-driven,
thankful, and concise. In practice:

- **Sincere.** Write in the first person and say how it feels when the
  feeling is real: "I've been waiting to write this post for a long
  time." Enthusiasm is welcome when the news earns it. One or two emoji
  per post at most, where the emotion peaks (the 1.0.0 post uses 🎉 at
  the release and ❤️ in the thanks).
- **Honest.** Give other projects credit ("ReactPy, Reflex, FastHTML... -
  and they succeeded to varying degree") and name the people the work builds on.
  Say where Citry is behind ("just behind Nuxt") and what it does not
  cover yet ("A new framework simply doesn't have the accumulated
  knowledge of an established one"), and link to the limits.
- **Thoughtful.** Explain why a feature matters, not only that it
  exists. Tie it to a real problem the reader has had, and to where the
  field is going. The 1.0.0 post's AI paragraphs are the example: AI
  speeds up attacks and defense alike, and an AI agent that gets clear
  errors can fix its own mistakes.
- **Data-driven.** Back each claim with one number and its comparison
  (257 ms, ahead of Next.js at 324 ms), or a chart. Link to the page
  that explains how it was measured. One strong number beats a table of
  them.
- **Thankful.** Thank the people who helped, invite readers to show what
  they build, and give the ways to get involved: sponsoring, Discord,
  GitHub issues, the roadmap.
- **Concise.** Short paragraphs. A one-line paragraph for emphasis
  ("Citry is fast. Really fast."). Details go behind a link.

## Structure

1. **Open with the news.** The first line says what happened. Put
   `pip install citry` right after it when the post is about a release.
2. **Tell the story.** Why this exists, from the maintainer's own
   experience: the problem as it felt at the time, what others tried,
   what was missing.
3. **What it means for the reader**, then thanks and the ways to get
   involved.
4. **One section per idea.** Each opens with a short claim, gives one
   concrete proof (a small code example, a chart, a number), and usually
   ends with a link to the full details.
5. **Practical details last**: versioning, upgrading, and who wrote it.

## Keep it at the reader's level

A personal post sells an idea to a person, so write about what they get,
not how Citry does it.

- **Benefits, not mechanics.** "A typo gets underlined right away" makes
  the point. Terminal output and "the command exits with status 1" do
  not; they belong in the docs.
- **Everyday words.** Say "whatever your users type shows up as text",
  not "escapes output" or "signs the State".
- **Round numbers that tell the story.** "Over the past year" reads
  better than "over eight to nine months" when the rough figure is true.
- **Write the commands people actually type:** `pip install citry`, not
  a pinned `python -m pip install "citry>=1.0.0,<2"`. Keep pins for the
  upgrade guides, unless readers must pin, as with `citry-ui` in the
  1.0.0 post.
- **No announcing.** Cut sentences such as "let me tell you why I'm so
  excited about it". Say the exciting thing instead.
- **No repeats between the description and the opening.** The front
  matter `description` shows as the subtitle right above the first line,
  so it must add something the opening does not say.
