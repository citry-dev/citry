---
title: Install Citry
description: Install Citry in a Python environment, then render a small component to confirm everything works.
---

# Install Citry

Install Citry, then render one small component to confirm it works. You do
not need a web framework or a server yet.

## Check your Python version

Citry supports Python 3.10 through 3.14. Check the version you are about to
use:

```sh
python --version
```

If that command does not work, try `python3 --version` on macOS or Linux, or
`py --version` on Windows.

If the version is outside that range, install a supported Python version
first. The [Compatibility page](/about/compatibility/) has the full platform
details.

## Install the package

Install Citry into your environment:

```sh
python -m pip install citry
```

Or, inside an existing `uv` project:

```sh
uv add citry
```

## Check the installation

Save this complete example as `hello.py`. It uses Citry's
[`Component`][citry.Component] base class:

```citry
from citry import Component

class Hello(Component):
    template = """
      <p>Hello from Citry!</p>
    """

print(Hello())
```

Run the file:

```sh
python hello.py
```

If you added Citry with `uv`, run `uv run python hello.py` instead.

The command prints `Hello from Citry!` inside an HTML `<p>` element. Python
can now import Citry and render a component.

!!! note "The output has an extra attribute"

    Citry adds an attribute to the opening tag, and its value can change
    each time. That extra text is expected.

## Fix installation problems

If running `hello.py` reports `No module named 'citry'`, the install command
and the file probably used different Python environments.

If pip reports that no compatible package is available, check your Python
version first.

If pip tries to build Citry's compiled core package (`citry-core`) from
source and the build fails,
see [Compatibility](/about/compatibility/#building-from-source) for the
platform and Rust requirements.

## Add editor support

If you use VS Code, install the
[Citry extension from the Visual Studio
Marketplace](https://marketplace.visualstudio.com/items?itemName=citry-dev.citry).
It adds highlighting, completion, navigation, diagnostics, and formatting for
Citry code inside Python files. The [VS Code setup guide](/ide/vscode/) shows
how to point it at your project's Python environment and components.

## Set up a coding agent

If you use a coding agent, the optional
[AI coding agents guide](/getting-started/ai-agents/) shows how to point it
at these docs and give it project instructions. Citry's starter projects
already include these instruction files, and you can add them to an existing
project.

## Next steps

Citry is installed and ready to render HTML. Next,
[build a reusable card](/getting-started/your-first-component/) with an option,
content of your choice, and its own styles.
