# Error-prevention results, run 20261021T182412Z

Cases and tools from commit `d4d3b2c4acbe5042724a73df65cb7fa0ba69fb98`, benchmark inputs tree `b8de898cf6bef8b758b16fb0cc6c1e17d7691b5e`.

Citry: citry 0.6.0 and citry-lsp 0.2.0 built from this repository at commit `d4d3b2c4acbe5042724a73df65cb7fa0ba69fb98`, not a published release.

## How each mistake ended

| Outcome | Citry | Django + HTMX + Alpine | Rusty + HTMX + Alpine | Jinja + HTMX + Alpine | Tetra | django-unicorn | django-components + HTMX + Alpine | FastHTML | ReactPy | Reflex | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Static/IDE error | 47 | 6 | 6 | 5 | 8 | 12 | 6 | 20 | 24 | 38 | 39 | 44 |
| Static/IDE warning | 7 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| Runtime error | 2 | 15 | 17 | 27 | 16 | 13 | 21 | 10 | 10 | 4 | 3 | 4 |
| Runtime warning | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 |
| N/A or prevented | 2 | 11 | 13 | 12 | 6 | 8 | 9 | 15 | 7 | 9 | 5 | 6 |
| Missed | 5 | 31 | 27 | 19 | 32 | 30 | 27 | 18 | 21 | 12 | 14 | 8 |

## Every mistake

| Code | Meaning |
| --- | --- |
| E | reported in the editor |
| C | reported by a command-line check, type check or linter |
| B | reported by the production build |
| R | reported at runtime by a server error, an error response or a browser error (Rw: only a warning) |
| w | after a letter: that stage gave only a warning, such as Ew for a warning in the editor |
| M | missed: nothing reports it |
| ? | the runtime check was skipped and no tool reported it |
| P | the framework's design prevents the mistake |
| - | no case was written for this framework |
| n/a | the mistake has no natural equivalent in this framework |
| ! | the clean app reported problems in this run, so the cell is unreliable |
| ~ | a tool timed out or skipped this case, so it may have caught the mistake earlier |
| ° | the report points away from the change, and the case explains why it still counts |

| Mistake | Citry | Django + HTMX + Alpine | Rusty + HTMX + Alpine | Jinja + HTMX + Alpine | Tetra | django-unicorn | django-components + HTMX + Alpine | FastHTML | ReactPy | Reflex | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (caught/total) | (56/61) | (21/52) | (23/50) | (32/51) | (25/57) | (25/55) | (27/54) | (30/48) | (35/56) | (42/54) | (44/58) | (49/57) |
| **Names: components, inputs, slots, variables** | (18/18) | (5/16) | (7/14) | (13/14) | (7/17) | (5/15) | (10/17) | (11/12) | (13/15) | (15/16) | (13/16) | (15/15) |
| Misspelled component name | E | R | R | R | C | R | R | E | E | E | E | E |
| Misspelled input name | E | M | M | R | R | M | R | E | R | E | E | E |
| Missing required input | E | M | M | R | R | M | R | E | R | E | E | E |
| Misspelled slot name | E | M | n/a | n/a | M | n/a | R | E | R | E | M | E |
| Undefined template variable | E | M | M | R | M | M | M | E | E | E | E | E |
| Misspelled attribute on a template object | E | M | R | R | M | M | M | E | E | C | E | E |
| Unknown translation message key | E | M | M | n/a | M | M | M | n/a | n/a | n/a | n/a | n/a |
| Misspelled template directive | E | M | M | M | M | C | M | M | n/a | E | E | n/a |
| Misspelled input on a browser-side component | E | R | R | R | R | M | R | n/a | R | E | E | E |
| Missing required input on a browser-side component | E | n/a | n/a | n/a | n/a | M | n/a | n/a | R | E | E | E |
| Required slot left unfilled | E | M | n/a | R | M | n/a | R | E | R | E | M | E |
| Slot fill reads a misspelled slot-data field | E | n/a | n/a | R | M | n/a | M | E | E | E | E | E |
| Template reads a misspelled state field | E | M | M | R | M | M | M | E | E | E | E | E |
| Browser code reads a misspelled server value | E | R | R | R | R | R | R | n/a | M | E | M | E |
| Link to a route that does not exist | Ew | R | R | R | R | R | R | R | M | M | Rw | E |
| Translation message given a missing or misnamed argument | E | M | R | n/a | M | M | M | n/a | n/a | n/a | n/a | n/a |
| Descendant reads a shared value that no ancestor provides | R | M | M | R | M | M | R | n/a | E | E | Rw | E |
| Unknown template filter or helper function | E | R | R | R | C | R | R | E | E | E | E | E |
| **Types** | (9/9) | (3/7) | (3/7) | (5/8) | (4/8) | (4/8) | (5/8) | (7/7) | (4/8) | (7/8) | (7/9) | (7/9) |
| Wrong-typed input written in markup | E | M | M | M | M | M | R | n/a | n/a | n/a | E | E |
| Wrong-typed input computed in code | E | E | E | E | E | E | E | E | M | E | E° | E |
| Wrong-typed operation in a template expression | E | M | M | R | M | M | M | E | E | E | M | M |
| Wrong-typed input on a browser-side component | E | n/a | n/a | n/a | n/a | M | n/a | n/a | M | E | E | E |
| Slot fill uses slot data as the wrong type | E | n/a | n/a | R | M | n/a | M | E | R | E | E | E |
| State field given a value of the wrong type | E | M | M | M | E | E | M | E | E | E | E | E |
| Component input given a value outside its allowed choices | E | M | M | M | M | M | R | E | M | E | E | E |
| Loop over a value that is not a list | E | R | R | R | R | R | R | E | E | C | E | E |
| Link passes a route parameter of the wrong type | R | R | R | R | R | R | R | R | M | M | M | M |
| **Template and script syntax** | (5/5) | (4/5) | (4/5) | (4/5) | (3/6) | (3/5) | (4/5) | (3/4) | (5/6) | (5/6) | (5/5) | (5/6) |
| Syntax error in a browser expression | E | R | R | R | R | R | R | R | E | E | C | E |
| Syntax error in component JavaScript | E | E | E | R | Bw° | n/a | E | R | E | E | E | E |
| Unclosed element in a template | E° | C° | C° | C | M | C° | C° | E | E° | E | E | E° |
| Misspelled path to a template or component file | n/a | R | R | R | R | R | R | n/a | E | E | n/a | E |
| Repeated browser element without a key | E | n/a | n/a | n/a | M | M | n/a | n/a | Rw | M | C | C |
| Two-way binding on an element with no value | E | M | M | M | M | M | M | M | M | C° | E | M |
| **HTML and CSS** | (12/13) | (4/13) | (4/13) | (4/13) | (4/13) | (5/13) | (4/13) | (3/13) | (3/13) | (6/13) | (9/13) | (10/13) |
| Invalid HTML attribute value | E | M | M | M | M | M | M | M | M | E | E | E |
| Misspelled HTML attribute name | E | M | M | M | M | M | M | M | M | M | E | E |
| Misspelled HTML element | E | M | M | M | M | M | M | E | E | E | E | E |
| Misspelled CSS class | M | M | M | M | M | M | M | M | M | M | M | M |
| CSS reads a misspelled variable the server sets | Ew | M | M | M | M | M | M | M | M | M | E | M |
| Misspelled path to a stylesheet, script or image | Ew | R | R | R | R | R | R | R | R | M | B | R |
| Block element inside a paragraph | E | M | M | M | M | M | M | M | M | R | C | R |
| Image without alt text | Ew | C | C | C | C | C | C | M | M | M | M | E |
| Misspelled ARIA attribute | E | M | M | M | M | C | M | M | M | R | E | Cw |
| Invalid ARIA attribute value | E | M | M | M | M | M | M | M | M | M | E | E |
| Same attribute written twice on one element | E | C | C | C | C | C | C | E | C | E | E | E |
| Two elements share an id | E | C | C | C | C | C | C | M | M | M | M | M |
| Boolean attribute given the text "false" | E | M | M | M | M | M | M | M | M | E | M | E |
| **Events and server requests** | (10/12) | (3/8) | (3/8) | (4/8) | (5/10) | (6/11) | (3/8) | (4/9) | (9/11) | (9/9) | (8/12) | (10/11) |
| Misspelled server handler name | E | R | R | R | R | M | R | R | E | E | E° | E |
| State field typo in an update handler | E | M | M | R | M | M | M | E | E | R | E | E |
| Misspelled field in a request payload | E | R | R | R | n/a | R | R | R | E | P | M | E |
| Child emits an event the parent does not listen for | E | M | M | M | M | E | M | M | E | E | E | E |
| Child component changes an input it received | E | P | P | P | P | M | P | n/a | C | C | C | C |
| Parent listens for a misspelled event | Ew | M | M | M | M | E° | M | M | R | E | E | E |
| Event sent with a payload of the wrong type | M | n/a | n/a | n/a | R | E | n/a | n/a | n/a | n/a | n/a | n/a |
| Misspelled browser event name on an element | Ew | M | M | M | M | M | M | M | M | C | M | E |
| Request payload field of the wrong type | E | P | P | P | R | P | P | P | E | P | M | E |
| Request payload leaves out a required field | E | R | R | R | R | R | R | R | E | E | R | E |
| Browser reads a misspelled field of the server's reply | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | E | n/a |
| Form field name differs from what the server reads | E | M | M | M | M | M | M | M | M | R | M | M |
| Handler declares arguments the event does not send | M | n/a | n/a | n/a | C | E° | n/a | M | E° | E° | E° | E |
| **Server and browser** | (2/4) | (2/3) | (2/3) | (2/3) | (2/3) | (2/3) | (1/3) | (2/3) | (1/3) | (0/2) | (2/3) | (2/3) |
| Server-only value read in browser code | E | R | R | R | R | R | M | R | M | M | R | R |
| Server and browser render different content | M | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | R | R |
| Server passes browser code a value the browser cannot receive | Ew° | R | R | R | R | R | R | R | R | P | n/a | n/a |
| Server sends a secret to the browser | M | M | M | M | M | M | M | M | M | M | M | M |
