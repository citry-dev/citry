# Writing user-facing text

A reader opens a Citry page because they want to get something done: update
part of the page, validate a form, fix an error. If the page opens with a
list of capabilities, uses words they have not learned yet, or puts a rare
rule before the common case, they give up or guess. This guide shows how to
write text that gets them to their answer.

Use it for anything a Citry user reads: pages under `docs_site/content/`,
package READMEs, public docstrings, error messages, and changelog entries.
The sentence-level rules (plain words, actions over nouns, one-line
definitions of project terms) live in the House style section of
[`CLAUDE.md`](../../CLAUDE.md#house-style). This guide covers how to build a
page from those sentences. The plan for the docs site as a whole, including
page types and voice, is
[`docs/design/docs_content.md`](../design/docs_content.md).

The model page is
[`docs_site/content/events/actions.md`](../../docs_site/content/events/actions.md).
When in doubt, read it and do what it does.

## Open with the goal

Start each page with the reader's problem and when they would use the
feature. Then show how. A list of everything the feature can do comes only
after that, if at all.

The same applies to each section: its first sentence says what the reader
gets from it.

## Go from common to rare

Order the page from what most readers need to what few readers need. Do the
same inside each section. The first example shows the usual case; options,
limits, and rare cases come later.

A page that shows off features, such as a landing page or README, orders
them by value to the reader (for Citry, a Python or web engineer): core
capabilities first, then validation, then speed-ups. Do not drop a valuable
feature because of a weak caveat. Show it and state the caveat honestly.
Show only what is actually built.

## Use plain words

Name things the way a first-time reader would, following the House style
rules in `CLAUDE.md`. A term the page needs gets its one-sentence
definition at its first use on that page, not in another page.

Keep internals out. Private names, cache key formats, debug attributes, and
plans for later releases belong in code comments, contributor guides, or
the tracking issue. If you cannot describe a limitation without naming an
internal, the API needs a public name first.

## Cut what nobody needs

Cut restatements, hedges, and explanations of how Citry works inside when
the reader does not need them to act. Keep sentences short, one point per
paragraph, and examples small.

Keep the facts a reader needs, above all the error modes: what fails, and
what the reader sees when it does ("the call fails and nothing on the page
changes").

## Move edge cases last

A paragraph packed with conditions and exceptions stops the reader in the
middle of the page. Cut it hard first. Then move what remains to the end of
its section or page:

- A single aside goes in a note or warning block.
- When a whole section is edge cases, give each case its own `###`
  subheading instead of stacking notes. The "Fix binding problems" section
  of [`events/bindings.md`](../../docs_site/content/events/bindings.md)
  does this.

One exception: keep a prerequisite, security requirement, or data-loss risk
next to the step it affects, even when few readers hit it.

## Lead with the symptom

Describe a gotcha by what the reader will see ("the second render shows
stale text"), not by its internal cause. Mention the cause only when the
reader needs it to act.

When you warn against a mistake, show the reader's natural first attempt,
say in plain words why it breaks, then show the fix. Pair the wrong and
right examples, with comments on the lines that matter.

## Keep facts correct

Shortening a rule is where facts go wrong. Before you cut or reword a
rule, check it against the source code, not against the old wording. When
you rewrite a page, compare every fact with the previous version
(`git show <rev>:path`) and keep each one, or remove it on purpose.

## Write short headings

A heading says what the section helps the reader do. A reader skimming
the page should know from the heading alone whether the section applies
to them, so avoid vague headings such as "Notes" or "Caveats".

Keep a heading to about four words and 24 characters. The "On this page"
sidebar cuts longer headings off, and the words that get cut are usually
the ones that tell sections apart. A longer heading is fine when the
cut-off end is still obvious.

When you shorten a heading that other pages link to, keep its old anchor
by writing it in braces after the heading, as in
`## Swap in a component { #swap-in-a-different-component }`. Then update
any link text elsewhere that quotes the old heading, so a reader who
follows the link finds the title they clicked.

The `heading_length` check, which runs with the other docs checks in
`python -m docs_site build-check`, lists every `##` and `###` heading over
24 characters with its file and line. It reports and never fails the build.

## Keep examples focused

These rules apply to reader-facing examples, including example source
files that the docs build imports or runs. Production components and
generated scaffolds follow
[`component-authoring.md`](component-authoring.md).

- Keep code lines at 70 characters or fewer, and pick the fence language
  by the rules in [`CLAUDE.md`](../../CLAUDE.md#house-style).
- Show the smallest fragment that makes the point. A template fragment
  often says more than a full component class.

### Empty Kwargs and Slots

Leave out an empty `Kwargs` when the component neither uses nor discusses
inputs, and an empty `Slots` when it neither uses nor discusses slots.
Leaving a schema out lets the component accept any name. Declaring an
empty one rejects every name, so keep it when that rejection is part of the
lesson.

Data methods still receive both `kwargs` and `slots`, so keep both
parameters and drop only the annotations that name a missing schema.

Keep the explicit schemas in two places: Getting Started examples after
the first install check, where the walkthrough teaches component inputs
and slots, and Examples recipes, where an empty schema shows on purpose
that the component takes no kwargs or slots.

## Write docstrings

A public docstring becomes the API reference entry for that symbol, so
its reader is someone calling it for the first time. The section names,
the one-sentence first line, and the cross-reference syntax are in the
"Writing docstrings" section of
[`development.md`](../../docs_site/content/community/development.md#writing-docstrings).
On top of those:

- Under `Args:`, say what each value controls, and its default when it
  matters.
- Under `Returns:`, say what the caller gets.
- Under `Raises:`, say *when* each error happens, so the caller can avoid
  it.
- End with a small `Example:` that shows the usual call.

## Write error messages

The reader of an error message is in the middle of something and wants to
get back to it. Each message says three things:

1. What happened, naming the value the reader wrote.
2. Why it is not allowed, in one plain clause.
3. What to do next, naming the fix.

A message such as "Invalid name" leaves the reader to work out all three.
This one, from `actions.Dispatch`, says all three:

```text
actions.Dispatch: event names starting with 'citry:' are reserved
for the citry runtime; got 'citry:saved'. Pick another name (the
convention is prefixing with the component name, e.g.
'MyCard:submit').
```

Keep internals out of the message, the same as on a page. When there are
several possible fixes, name the most likely one first.

## Write code comments

Comments explain intent, not mechanics. The rule and an example are in
the "Inline comments explain intent" bullet of
[`CLAUDE.md`](../../CLAUDE.md#code-conventions).

## Write changelog entries

What belongs in a changelog and how to phrase an entry are in
[`CLAUDE.md`](../../CLAUDE.md#what-belongs-in-the-changelog).

## Before and after

These pairs come from the rewrite of the Events pages. The "before" text
is accurate; it is just hard to use.

### Start where they are

Before, the intro of `events/actions.md` listed capabilities:

> An event handler can rerender its calling component, return data,
> dispatch a browser event, change browser history, or navigate. Return one
> result for one effect, or a list when effects must happen in order.

After, it starts where the reader is:

> Your Python handler ran. Now the page should change: show the new data,
> swap in a confirmation, tell other browser code what happened, change the
> URL, or send a file. What the handler returns decides what the browser
> does next.

### Replace a coined term

Before, the page used "calling component" and "calling instance", terms it
never defined:

> A Render action updates one component on the page or an explicit marker
> in place. Omitting `target` selects the calling instance.

After, it names the thing in plain words instead:

> Return the component with its new inputs. Citry renders it on the server
> and the browser updates the component whose handler ran, in place.

### Cut a dense rule

Before, one paragraph in the middle of the page carried every condition:

> One response may update several independent targets when their Render
> actions form one contiguous group. Every action in that group must be
> immediate and blocking: omit `delay` or use `0`, and do not set
> `wait=False`. Otherwise the call fails and nothing on the page changes:
> the browser rejects a response that puts another action between two
> Renders, defers one of them, targets the same component instance twice,
> or targets both a component and a component inside it. The handler has
> already run by then, so any database writes it made stay. The server
> does not check the order or targets of these Render actions, so assert
> the returned list in a test of the handler.

After, a short note near the end of the page:

> You can update several separate parts of the page in one response by
> returning several Renders next to each other. Otherwise the call fails
> and nothing on the page changes.

The error mode stayed, and the note opens with what the reader can do.
The published note adds one plain sentence listing the cases that fail.
The remark about server checks and the testing advice went.

### Shorten a heading

| Before | After |
|---|---|
| Replace the calling component with a different component | Swap in a component |
| Dispatch a browser event | Notify browser code |
| Preserve identity in rendered lists | Keep list items matched |

Each "after" heading names what the reader wants to do, in words they
already have.

## Review a page cold

The writer cannot see what a first-time reader misses. Before you call a
new or substantially rewritten page done, have a separate agent read it as
a first-time reader would, using the reviewer saved in
[`.claude/agents/docs-cold-reader.md`](../../.claude/agents/docs-cold-reader.md).
Give it the changed pages and the commit before your change (for example
`main`) to compare facts against. It reports what is unclear, out of order,
too dense, or full of jargon, which headings are too long, and which facts
changed, then reviews the prose line by line. It does not edit the page.
