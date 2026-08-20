---
title: Install Citry
url: https://citry.dev/v/0.4.1/getting-started/installation/
description: "Install Citry in a Python environment, then render a small component to confirm everything works."
---
# Install Citry

Let's install Citry. You do not need a web framework or a server yet.

## Before you start

Citry supports Python 3.10 through 3.14. Check the version you are about to
use:


```sh
python --version
```


If that command does not work, try `python3 --version` on macOS or Linux, or
`py --version` on Windows.

If the version is outside the supported range, install a supported
Python version before continuing. The [Compatibility
page](/about/compatibility/) has the full platform details.

## Installation

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
[`Component`](/v/0.4.1/reference/component/#citry-component) base class:


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


(If you added Citry with `uv`, run `uv run python hello.py` instead.)

The command should print `Hello from Citry!` inside an HTML `<p>` element.

You have now confirmed that Python can import Citry and render a component.

!!! note

    Citry adds an attribute to the opening tag, and its value can change each time.
    That extra text is expected.

## Troubleshoot

If running `hello.py` reports `No module named 'citry'`, the install command
and the file probably used different Python environments.

If pip reports that no compatible package is available, check your Python
version first.

If pip tries to compile the core package and the build fails,
see [Compatibility](/v/0.4.1/about/compatibility/#building-from-source) for the
platform and Rust requirements.

## Next steps

Citry is installed and ready to render HTML. Next,
[build a reusable card](/v/0.4.1/getting-started/your-first-component/) with an option,
content of your choice, and its own styles.