# Error-prevention results, run 20261020T175743Z

Cases and tools from commit `60e9fc263512744a094532ba2e3d65958ed569db`.

## How each mistake ended

| Outcome | Citry | Django + HTMX + Alpine | Jinja + HTMX + Alpine | FastHTML | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- |
| Static/IDE error | 20 | 3 | 2 | 14 | 16 | 27 |
| Static/IDE warning | 1 | 0 | 0 | 0 | 0 | 0 |
| Runtime error | 4 | 9 | 16 | 7 | 6 | 2 |
| Runtime warning | 0 | 0 | 0 | 0 | 0 | 0 |
| N/A or prevented | 2 | 4 | 6 | 8 | 4 | 5 |
| Missed | 10 | 21 | 13 | 8 | 11 | 3 |

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

| Mistake | Citry | Django + HTMX + Alpine | Jinja + HTMX + Alpine | FastHTML | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- |
| (caught/total) | (25/35) | (12/33) | (18/31) | (21/29) | (22/33) | (29/32) |
| **Names: components, inputs, slots, variables** | (11/11) | (2/11) | (6/9) | (8/9) | (7/10) | (9/9) |
| Misspelled component name | E | R | R | E | R | E |
| Misspelled input name | E | M | R | E | E | E |
| Missing required input | E | M | M | E | E | E |
| Misspelled slot name | E | M | n/a | E | M | E |
| Undefined template variable | E | M | R | E | E | E |
| Misspelled attribute on a template object | E | M | M | E | E | E |
| Unknown translation message key | E | M | n/a | n/a | n/a | n/a |
| Misspelled template directive | R | M | M | M | R | n/a |
| Required slot left unfilled | E | M | R | E | M | E |
| Template reads a misspelled state field | E | M | R | E | E | E |
| Browser code reads a misspelled server value | E | R | R | n/a | M | E |
| **Types** | (4/4) | (1/4) | (2/4) | (3/3) | (3/4) | (3/4) |
| Wrong-typed input written in markup | E | M | M | n/a | E | E |
| Wrong-typed input computed in code | E | E | E | E | E° | E |
| Wrong-typed operation in a template expression | E | M | R | E | M | M |
| State field given a value of the wrong type | E | M | M | E | E | E |
| **Template and script syntax** | (3/3) | (4/4) | (4/4) | (3/3) | (3/3) | (4/4) |
| Syntax error in a browser expression | R | R | R | R | C | E |
| Syntax error in component JavaScript | E | E | R | R | E | E |
| Unclosed element in a template | E | C | C | E | E | E° |
| Misspelled path to a template or component file | n/a | R | R | n/a | n/a | E |
| **HTML and CSS** | (1/4) | (0/4) | (0/4) | (1/4) | (2/4) | (3/4) |
| Invalid HTML attribute value | Ew | M | M | M | E | E |
| Misspelled HTML attribute name | M | M | M | M | M | E |
| Misspelled HTML element | M | M | M | E | R | E |
| Misspelled CSS class | M | M | M | M | M | M |
| **Events and server requests** | (3/9) | (3/7) | (4/7) | (4/7) | (5/9) | (8/8) |
| Misspelled server handler name | E | R | R | R | E° | E |
| State field typo in an update handler | E | M | R | E | E | E |
| Misspelled field in a request payload | M | R | R | R | M | E |
| Child emits an event the parent does not listen for | E | M | M | M | E | E |
| Parent listens for a misspelled event | M | M | M | M | M | E |
| Event sent with a payload of the wrong type | M | n/a | n/a | n/a | n/a | n/a |
| Misspelled browser event name on an element | M | M | M | M | M | E |
| Request payload field of the wrong type | M | P | P | P | M | E |
| Request payload leaves out a required field | M | R | R | R | R | E |
| Browser reads a misspelled field of the server's reply | n/a | n/a | n/a | n/a | E | n/a |
| **Server and browser** | (3/4) | (2/3) | (2/3) | (2/3) | (2/3) | (2/3) |
| Server-only value read in browser code | E | R | R | R | R | R |
| Server and browser render different content | R | n/a | n/a | n/a | R | R |
| Server passes browser code a value the browser cannot receive | R | R | R | R | n/a | n/a |
| Server sends a secret to the browser | M | M | M | M | M | M |
