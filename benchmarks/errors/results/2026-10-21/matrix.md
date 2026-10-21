# Error-prevention results, run 20261021T000041Z

Cases and tools from commit `be0ce457a578d94a488fe178102c1e8b4ede1db3`.

## How each mistake ended

| Outcome | Citry | Django + HTMX + Alpine | Rusty + HTMX + Alpine | Jinja + HTMX + Alpine | django-unicorn | django-components + HTMX + Alpine | FastHTML | ReactPy | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Static/IDE error | 28 | 6 | 6 | 5 | 12 | 6 | 20 | 23 | 39 | 43 |
| Static/IDE warning | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| Runtime error | 11 | 15 | 17 | 26 | 13 | 20 | 10 | 10 | 3 | 4 |
| Runtime warning | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| N/A or prevented | 2 | 11 | 13 | 12 | 8 | 9 | 14 | 7 | 5 | 6 |
| Missed | 20 | 30 | 26 | 19 | 29 | 27 | 18 | 21 | 14 | 8 |

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

| Mistake | Citry | Django + HTMX + Alpine | Rusty + HTMX + Alpine | Jinja + HTMX + Alpine | django-unicorn | django-components + HTMX + Alpine | FastHTML | ReactPy | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (caught/total) | (40/60) | (21/51) | (23/49) | (31/50) | (25/54) | (26/53) | (30/48) | (34/55) | (43/57) | (48/56) |
| **Names: components, inputs, slots, variables** | (17/17) | (5/15) | (7/13) | (12/13) | (5/14) | (9/16) | (11/12) | (12/14) | (12/15) | (14/14) |
| Misspelled component name | E | R | R | R | R | R | E | E | E | E |
| Misspelled input name | E | M | M | R | M | R | E | R | E | E |
| Missing required input | E | M | M | R | M | R | E | R | E | E |
| Misspelled slot name | E | M | n/a | n/a | n/a | R | E | R | M | E |
| Undefined template variable | E | M | M | R | M | M | E | E | E | E |
| Misspelled attribute on a template object | E | M | R | R | M | M | E | E | E | E |
| Unknown translation message key | E | M | M | n/a | M | M | n/a | n/a | n/a | n/a |
| Misspelled template directive | R | M | M | M | C | M | M | n/a | E | n/a |
| Misspelled input on a browser-side component | E | R | R | R | M | R | n/a | R | E | E |
| Missing required input on a browser-side component | E | n/a | n/a | n/a | M | n/a | n/a | R | E | E |
| Required slot left unfilled | E | M | n/a | R | n/a | R | E | R | M | E |
| Slot fill reads a misspelled slot-data field | R | n/a | n/a | R | n/a | M | E | E | E | E |
| Template reads a misspelled state field | E | M | M | R | M | M | E | E | E | E |
| Browser code reads a misspelled server value | E | R | R | R | R | R | n/a | M | M | E |
| Link to a route that does not exist | R | R | R | R | R | R | R | M | Rw | E |
| Translation message given a missing or misnamed argument | E | M | R | n/a | M | M | n/a | n/a | n/a | n/a |
| Unknown template filter or helper function | E | R | R | R | R | R | E | E | E | E |
| **Types** | (8/9) | (3/7) | (3/7) | (5/8) | (4/8) | (5/8) | (7/7) | (4/8) | (7/9) | (7/9) |
| Wrong-typed input written in markup | E | M | M | M | M | R | n/a | n/a | E | E |
| Wrong-typed input computed in code | E | E | E | E | E | E | E | M | E° | E |
| Wrong-typed operation in a template expression | E | M | M | R | M | M | E | E | M | M |
| Wrong-typed input on a browser-side component | M | n/a | n/a | n/a | M | n/a | n/a | M | E | E |
| Slot fill uses slot data as the wrong type | R | n/a | n/a | R | n/a | M | E | R | E | E |
| State field given a value of the wrong type | E | M | M | M | E | M | E | E | E | E |
| Component input given a value outside its allowed choices | E | M | M | M | M | R | E | M | E | E |
| Loop over a value that is not a list | E | R | R | R | R | R | E | E | E | E |
| Link passes a route parameter of the wrong type | R | R | R | R | R | R | R | M | M | M |
| **Template and script syntax** | (5/5) | (4/5) | (4/5) | (4/5) | (3/5) | (4/5) | (3/4) | (5/6) | (5/5) | (5/6) |
| Syntax error in a browser expression | R | R | R | R | R | R | R | E | C | E |
| Syntax error in component JavaScript | E | E | E | R | n/a | E | R | E | E | E |
| Unclosed element in a template | E° | C | C | C | C | C | E | E | E | E° |
| Misspelled path to a template or component file | n/a | R | R | R | R | R | n/a | E | n/a | E |
| Repeated browser element without a key | R | n/a | n/a | n/a | M | n/a | n/a | Rw | C | C |
| Two-way binding on an element with no value | R | M | M | M | M | M | M | M | E | M |
| **HTML and CSS** | (5/13) | (4/13) | (4/13) | (4/13) | (5/13) | (4/13) | (3/13) | (3/13) | (9/13) | (10/13) |
| Invalid HTML attribute value | Ew | M | M | M | M | M | M | M | E | E |
| Misspelled HTML attribute name | M | M | M | M | M | M | M | M | E | E |
| Misspelled HTML element | M | M | M | M | M | M | E | E | E | E |
| Misspelled CSS class | M | M | M | M | M | M | M | M | M | M |
| CSS reads a misspelled variable the server sets | M | M | M | M | M | M | M | M | E | M |
| Misspelled path to a stylesheet, script or image | R | R | R | R | R | R | R | R | B | R |
| Block element inside a paragraph | R | M | M | M | M | M | M | M | C | R |
| Image without alt text | M | C | C | C | C | C | M | M | M | E |
| Misspelled ARIA attribute | M | M | M | M | C | M | M | M | E | Cw |
| Invalid ARIA attribute value | E | M | M | M | M | M | M | M | E | E |
| Same attribute written twice on one element | E | C | C | C | C | C | E | C | E | E |
| Two elements share an id | M | C | C | C | C | C | M | M | M | M |
| Boolean attribute given the text "false" | M | M | M | M | M | M | M | M | M | E |
| **Events and server requests** | (3/12) | (3/8) | (3/8) | (4/8) | (6/11) | (3/8) | (4/9) | (9/11) | (8/12) | (10/11) |
| Misspelled server handler name | E | R | R | R | M | R | R | E | E° | E |
| State field typo in an update handler | E | M | M | R | M | M | E | E | E | E |
| Misspelled field in a request payload | M | R | R | R | R | R | R | E | M | E |
| Child emits an event the parent does not listen for | E | M | M | M | E | M | M | E | E | E |
| Child component changes an input it received | M | P | P | P | M | P | n/a | C | C | C |
| Parent listens for a misspelled event | M | M | M | M | E° | M | M | R | E | E |
| Event sent with a payload of the wrong type | M | n/a | n/a | n/a | E | n/a | n/a | n/a | n/a | n/a |
| Misspelled browser event name on an element | M | M | M | M | M | M | M | M | M | E |
| Request payload field of the wrong type | M | P | P | P | P | P | P | E | M | E |
| Request payload leaves out a required field | M | R | R | R | R | R | R | E | R | E |
| Browser reads a misspelled field of the server's reply | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | E | n/a |
| Form field name differs from what the server reads | M | M | M | M | M | M | M | M | M | M |
| Handler declares arguments the event does not send | M | n/a | n/a | n/a | E° | n/a | M | E° | E° | E |
| **Server and browser** | (2/4) | (2/3) | (2/3) | (2/3) | (2/3) | (1/3) | (2/3) | (1/3) | (2/3) | (2/3) |
| Server-only value read in browser code | E | R | R | R | R | M | R | M | R | R |
| Server and browser render different content | M | n/a | n/a | n/a | n/a | n/a | n/a | n/a | R | R |
| Server passes browser code a value the browser cannot receive | R | R | R | R | R | R | R | R | n/a | n/a |
| Server sends a secret to the browser | M | M | M | M | M | M | M | M | M | M |
