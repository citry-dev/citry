# Error-prevention results, run 20261020T215449Z

Cases and tools from commit `c1378f5790debeb63fb82f2bdf85d4c61f4251f1`.

## How each mistake ended

| Outcome | Citry | Django + HTMX + Alpine | Rusty + HTMX + Alpine | Jinja + HTMX + Alpine | django-unicorn | django-components + HTMX + Alpine | FastHTML | ReactPy | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Static/IDE error | 24 | 3 | 3 | 2 | 7 | 3 | 17 | 19 | 25 | 34 |
| Static/IDE warning | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Runtime error | 7 | 12 | 14 | 20 | 10 | 17 | 9 | 10 | 6 | 4 |
| Runtime warning | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| N/A or prevented | 2 | 9 | 11 | 10 | 8 | 7 | 13 | 7 | 5 | 6 |
| Missed | 15 | 25 | 21 | 17 | 24 | 22 | 10 | 13 | 12 | 5 |

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
| (caught/total) | (32/47) | (15/40) | (17/38) | (22/39) | (17/41) | (20/42) | (26/36) | (29/42) | (32/44) | (38/43) |
| **Names: components, inputs, slots, variables** | (16/16) | (4/14) | (6/12) | (8/12) | (4/13) | (8/15) | (10/11) | (11/13) | (11/14) | (13/13) |
| Misspelled component name | E | R | R | R | R | R | E | E | R | E |
| Misspelled input name | E | M | M | R | M | R | E | R | E | E |
| Missing required input | E | M | M | M | M | R | E | R | E | E |
| Misspelled slot name | E | M | n/a | n/a | n/a | R | E | R | M | E |
| Undefined template variable | E | M | M | R | M | M | E | E | E | E |
| Misspelled attribute on a template object | E | M | R | M | M | M | E | E | E | E |
| Unknown translation message key | E | M | M | n/a | M | M | n/a | n/a | n/a | n/a |
| Misspelled template directive | R | M | M | M | C | M | M | n/a | R | n/a |
| Misspelled input on a browser-side component | E | R | R | R | M | R | n/a | R | E | E |
| Missing required input on a browser-side component | E | n/a | n/a | n/a | M | n/a | n/a | R | E | E |
| Required slot left unfilled | E | M | n/a | R | n/a | R | E | R | M | E |
| Slot fill reads a misspelled slot-data field | R | n/a | n/a | M | n/a | M | E | E | E | E |
| Template reads a misspelled state field | E | M | M | R | M | M | E | E | E | E |
| Browser code reads a misspelled server value | E | R | R | R | R | R | n/a | M | M | E |
| Link to a route that does not exist | R | R | R | R | R | R | R | M | Rw | R |
| Translation message given a missing or misnamed argument | E | M | R | n/a | M | M | n/a | n/a | n/a | n/a |
| **Types** | (6/7) | (1/5) | (1/5) | (3/6) | (2/6) | (3/6) | (5/5) | (3/6) | (6/7) | (6/7) |
| Wrong-typed input written in markup | E | M | M | M | M | R | n/a | n/a | E | E |
| Wrong-typed input computed in code | E | E | E | E | E | E | E | M | E° | E |
| Wrong-typed operation in a template expression | E | M | M | R | M | M | E | E | M | M |
| Wrong-typed input on a browser-side component | M | n/a | n/a | n/a | M | n/a | n/a | M | E | E |
| Slot fill uses slot data as the wrong type | R | n/a | n/a | R | n/a | M | E | R | E | E |
| State field given a value of the wrong type | E | M | M | M | E | M | E | E | E | E |
| Component input given a value outside its allowed choices | E | M | M | M | M | R | E | M | E | E |
| **Template and script syntax** | (3/3) | (4/4) | (4/4) | (4/4) | (3/3) | (4/4) | (3/3) | (4/4) | (3/3) | (4/4) |
| Syntax error in a browser expression | R | R | R | R | R | R | R | E | C | E |
| Syntax error in component JavaScript | E | E | E | R | n/a | E | R | E | E | E |
| Unclosed element in a template | E° | C | C | C | C | C | E | E | E | E° |
| Misspelled path to a template or component file | n/a | R | R | R | R | R | n/a | E | n/a | E |
| **HTML and CSS** | (2/6) | (1/6) | (1/6) | (1/6) | (1/6) | (1/6) | (2/6) | (2/6) | (4/6) | (4/6) |
| Invalid HTML attribute value | Ew | M | M | M | M | M | M | M | E | E |
| Misspelled HTML attribute name | M | M | M | M | M | M | M | M | M | E |
| Misspelled HTML element | M | M | M | M | M | M | E | E | R | E |
| Misspelled CSS class | M | M | M | M | M | M | M | M | M | M |
| CSS reads a misspelled variable the server sets | M | M | M | M | M | M | M | M | E | M |
| Misspelled path to a stylesheet, script or image | R | R | R | R | R | R | R | R | B | R |
| **Events and server requests** | (3/11) | (3/8) | (3/8) | (4/8) | (5/10) | (3/8) | (4/8) | (8/10) | (6/11) | (9/10) |
| Misspelled server handler name | E | R | R | R | M | R | R | E | E° | E |
| State field typo in an update handler | E | M | M | R | M | M | E | E | E | E |
| Misspelled field in a request payload | M | R | R | R | R | R | R | E | M | E |
| Child emits an event the parent does not listen for | E | M | M | M | E | M | M | E | E | E |
| Child component changes an input it received | M | P | P | P | M | P | n/a | C | C | C |
| Parent listens for a misspelled event | M | M | M | M | E° | M | M | R | M | E |
| Event sent with a payload of the wrong type | M | n/a | n/a | n/a | E | n/a | n/a | n/a | n/a | n/a |
| Misspelled browser event name on an element | M | M | M | M | M | M | M | M | M | E |
| Request payload field of the wrong type | M | P | P | P | P | P | P | E | M | E |
| Request payload leaves out a required field | M | R | R | R | R | R | R | E | R | E |
| Browser reads a misspelled field of the server's reply | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | E | n/a |
| Form field name differs from what the server reads | M | M | M | M | M | M | M | M | M | M |
| **Server and browser** | (2/4) | (2/3) | (2/3) | (2/3) | (2/3) | (1/3) | (2/3) | (1/3) | (2/3) | (2/3) |
| Server-only value read in browser code | E | R | R | R | R | M | R | M | R | R |
| Server and browser render different content | M | n/a | n/a | n/a | n/a | n/a | n/a | n/a | R | R |
| Server passes browser code a value the browser cannot receive | R | R | R | R | R | R | R | R | n/a | n/a |
| Server sends a secret to the browser | M | M | M | M | M | M | M | M | M | M |
