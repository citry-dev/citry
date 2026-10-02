---
title: Fragments
description: Load a server-rendered component and its assets on demand.
---

# Fragments

Use this pattern to add a component to a page after it has loaded, for
example when the user opens a panel. The server renders the component
as an HTML fragment, a piece of HTML that is not a whole page. Your
JavaScript inserts it, and Citry loads the component's JavaScript and
CSS and starts it.

<c-example name="fragments" />

The lines to notice:

- The page loads `/citry/citry.js` up front. That script notices the
  inserted fragment and fetches its JavaScript and CSS.
- The button's script fetches the fragment and sets it as the
  `innerHTML` of an empty element. No other setup is needed.
- "(JS ran)" appears in the widget once its own script has started.

This docs site is static, so the example serves one prepared fragment,
and you reload the page to try again. To render and serve fragments from
your own routes, see [HTML fragments](/advanced/html-fragments/).
