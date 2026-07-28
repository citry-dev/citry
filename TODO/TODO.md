# Citry

Citry (short for "Component tree") is a package for serializing tree structures (think HTML)
Citry - your frontend's favourite templating engine.

Write to your bio/CV that you can large open source multi-language ecosystems.

Best templating framework for AI agents. The "Pydantic for templating"
- citry catches huge number of errors statically, providing early feedback.
- best ux/devexp

<!-- TODO - ADD "DEV" MODE DURING WHICH WE'LL BE COLLECTING TELEMETRY FROM RUNTIME.
            AND GATE-KEEP TUTORIALS, ASKING PEOPLE TO LOG IN AND ENABLE TRACKING
            FOR THEM TO ACCESS THE TUTORIALS.

            THE WHOLE PREMISE IS SO THAT WE CAN TRACK THE ERROR RATE OF PEOPLE'S PROJECTS
            AND SEE HOW IT CHANGES OVER TIME, SO THAT WE CAN SEE IF WE'RE WRITING SAFER CODE OR NOT.

            BUT FOR THIS TO BE IDEAL, WE'D WANT ALSO THE COMPILER / IDE TO TRACK ERRORS.

            BECAUSE ONE THING IS ERRORS AT RUNTIME (e.g. by overloading Python's error handling),
            BUT GETTING TO A RUNNABLE VERSION COULD BE PREFACED WITH 10 CHANGES, WHICH THE USER
            HAD TO FIX WITH THE FEEDBACK FROM COMPILER (think Rust compiler).

            (When running Python runtime, is it technically possible to intercept error handling,
            so as to intercept errors that come from running other parts of the code?)

            SO IF WE TRACKED BOTH, WE COULD OPTIMIZE FOR MINIMIZING ERROR RATE / IMPROVING DEV SPEED.

            THIS COULD BE GENERALIZED INTO A STANDALONE SERVICE THAT WOULD:
            1. INTERCEPT PYTHON RUNTIME ERROR AND SEND THEM TO OUR SERVERS (WHEN OUR TELEMETRY PACKAGE
               IS INSTALLED).
            2. VSCODE EXT THAT WOULD AGAIN COLLECT ERRORS FROM OTHER LANGUAGE SERVERS AND SEND IT TO OUR
               SERVER IF THE ERROR RELATES TO OUR PACKAGE.
            3. SERVER/SERVICE THAT WOULD COLLECT AND TRACK THE ERRORS.
            4. PACKAGE/PROJECT SPECIFIC VIEW/DASHBOARD - THIS IS WHAT PACKAGE AUTHOR COULD SHARE/SHOW
               TO THEIR USERBASE.
            5. SOME WAY TO ISOLATE TO REPORT ONLY PACKAGE-RELEVANT ERRORS TO MAINTAINERS.
            6. DEVS WOULD BE NUDGED TO LOG IN - GRANT ACCESS VIA GITHUB/GITLAB/BITBUCKET/GOOGLE/OTHER.
            6. 
-->

# AlpineJS

### “Bridge” attributes are just normal names

Things like:

```html
<div c-:class="'{ open: is_open }'">
```

are not special cases — they follow the same rules:

* Attribute name is `c-:class`.
* The framework strips the first `c-`, so the *target* attribute name is `:class`.
* It evaluates the value as Python.
* Final HTML:

  ```html
  <div :class="{ open: is_open }">
  ```

Now Vue/Alpine can pick that up.
