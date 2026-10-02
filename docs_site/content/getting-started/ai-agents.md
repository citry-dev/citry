---
title: AI coding agents
description: Point your coding agent at Citry's documentation and give it the setup and verification commands for your project.
---

# AI coding agents

A coding agent writes better Citry code when it can read the Citry docs and
knows how to run and test your project. Give it two things: the link to
Citry's documentation index, and a project instructions file. You do not
need to install a Citry skill or plugin.

## Point the agent to `llms.txt`

[llms.txt](/llms.txt) is an index of this site's guides and API references,
with a link to a plain Markdown version of each page. An agent reads the
index, then fetches only the pages its task needs.

Try it on a small task:

```text
Context:
Use https://citry.dev/llms.txt for Citry documentation.
Read this project's README for setup and test commands.

Task:
Add a filter to the project list using a Python Citry Event.
Check the result in a browser and run the project tests.
```

## Add project instructions

Many agents, such as Codex, read an `AGENTS.md` file in the project root at
the start of each session. Create one, or add this section to yours:

```markdown
## Citry

Read README.md for project setup and verification commands.
Use https://citry.dev/llms.txt to find relevant Citry guides
and API references. Fetch the linked Markdown pages as needed.
Check APIs against the installed Citry version and preserve
the project's dependency constraints.
Run the project tests after changes. For browser behavior,
also exercise the affected interaction in a browser.
```

Then add what is specific to your project, such as where components live
and the commands that run and test the app.

The [Citry starter projects]({{ repo_url }}/tree/{{ repo_edit_branch }}/examples/starters){: target="_blank" rel="noopener"}
already include an `AGENTS.md` with these pointers, project paths, and test
commands, plus a `CLAUDE.md` that imports it.

### Codex

Put `AGENTS.md` in the project root and start a new Codex session in that
project. [Codex's AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md){: target="_blank" rel="noopener"}
explains how global and nested instruction files combine.

### Claude Code

Claude Code reads `CLAUDE.md`. Create it beside `AGENTS.md` with this line,
or add the line to your existing `CLAUDE.md`:

```text
@AGENTS.md
```

The line imports `AGENTS.md`. See
[Claude Code's memory guide](https://code.claude.com/docs/en/memory){: target="_blank" rel="noopener"}
for how imports work.

### Other agents

Use your tool's project instructions setting to include `AGENTS.md`, or ask
the agent to read it at the start of the task. You can also paste the
snippet into a prompt.

## Check the setup

Before the agent edits anything, ask it to:

1. report the installed Citry version;
2. find a Citry guide relevant to your task; and
3. state the command that tests the project.

If it cannot fetch the documentation, give it the relevant Markdown pages
directly. After the change, review its test results and try the browser
interactions that matter to your app yourself.

## Match the docs to your installed version

The docs describe one Citry version, and your project may use another. Check
the installed version in the same environment that runs the app:

```console
python -c "from importlib.metadata import version; print(version('citry'))"
```

Compare it with the version shown on this site. If an example uses an API
that your installation lacks, check the installed package and the
[release notes](/releases/) before changing dependencies, and keep the
project's lockfile and version constraints in mind.

## Use `llms-full.txt` for a single file

[llms-full.txt](/llms-full.txt) puts the whole documentation in one text
file. Use it when your tool works better with an attached document or needs
a local copy. It is much larger than `llms.txt`, and a saved copy goes out of
date as the docs change.
