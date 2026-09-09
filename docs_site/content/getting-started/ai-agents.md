---
title: AI coding agents
description: Point your coding agent at Citry's documentation and give it the setup and verification commands for your project.
---

# AI coding agents

You can use a coding agent with Citry by giving it the documentation index and
your project's setup instructions. You do not need to install a Citry skill.

## Point the agent to `llms.txt`

Citry has an agent-friendly version of this website which is in plain markdown
at [llms.txt](/llms.txt).

An agent can retrieve the pages needed for its task without loading the whole site.

Test it out on a simple task:

```text
Context:
Use https://citry.dev/llms.txt for Citry documentation.
Read this project's README for setup and test commands.

Task:
Add a filter to the project list using a Python Citry Event.
Check the result in a browser and run the project tests.
```

## Using agent instructions in projects

For a hands-on example, see the [Citry starter projects]({{ repo_url }}/tree/{{ repo_edit_branch }}/examples/starters){: target="_blank" rel="noopener"}.

Each project includes `AGENTS.md` with project-specific paths, documentation pointers, and
verification commands. Their `CLAUDE.md` imports that file for Claude Code.

## Set up an existing project

Create `AGENTS.md` in the project root, or merge this section into the file
you already maintain:

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

Add your component directories, test and run commands, etc.

### Codex

Put `AGENTS.md` at the project root and start a new Codex session in that
project.
See [Codex's AGENTS.md guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md){: target="_blank" rel="noopener"}
for how global and nested instructions combine.

### Claude Code

Create `CLAUDE.md` beside `AGENTS.md` with this import, or add the import to
your existing `CLAUDE.md`:

```text
@AGENTS.md
```

Claude Code supports file imports in its project instructions. See
[Claude Code's memory guide](https://code.claude.com/docs/en/memory){: target="_blank" rel="noopener"}.

### Other agents

Use your tool's project-instructions setting to include `AGENTS.md`, or ask
the agent to read it at the start of the task. You can also paste the snippet directly into a prompt.

## `llms-full.txt`

Start with [llms.txt](/llms.txt). It is an index of guides and API references,
with links to their Markdown versions. An agent can retrieve the pages needed
for its task without loading the whole site.

[llms-full.txt](/llms-full.txt) combines documentation into one text export.
Use it when your tool works better with an attached document or needs a local
copy. It is much larger, and a saved copy can become outdated.

## Versioning

Check the installed version in the same environment that runs the app:

```console
python -c "from importlib.metadata import version; print(version('citry'))"
```

Compare the result with the version shown by the documentation.

If an example uses an API absent
from your installation, inspect the installed package and the
[release notes](/releases/) before changing dependencies.

Keep the project's lockfile and compatibility requirements in mind.

## Check the setup

Ask the agent to identify the installed Citry version, locate a guide relevant
to your task, and state the project's verification command before editing.

If it cannot retrieve documentation, provide the relevant Markdown pages
directly. After the change, review its test results and exercise browser
interactions that matter to your application.
