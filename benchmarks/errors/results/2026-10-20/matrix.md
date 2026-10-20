# Error-prevention results, run 20261020T194609Z

Cases and tools from commit `4253e96baa5aa1cf06a24271643a6c9da4a940ae`.

## How each mistake ended

| Outcome | Citry | Django + HTMX + Alpine | Rusty + HTMX + Alpine | Jinja + HTMX + Alpine | FastHTML | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Static/IDE error | 23 | 3 | 3 | 2 | 17 | 23 | 34 |
| Static/IDE warning | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Runtime error | 5 | 10 | 11 | 18 | 7 | 6 | 2 |
| Runtime warning | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| N/A or prevented | 2 | 9 | 11 | 9 | 12 | 4 | 5 |
| Missed | 13 | 22 | 19 | 15 | 8 | 11 | 3 |

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

| Mistake | Citry | Django + HTMX + Alpine | Rusty + HTMX + Alpine | Jinja + HTMX + Alpine | FastHTML | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| (caught/total) | (29/42) | (13/35) | (14/33) | (20/35) | (24/32) | (29/40) | (36/39) |
| **Names: components, inputs, slots, variables** | (14/14) | (3/12) | (4/10) | (7/11) | (9/10) | (10/13) | (12/12) |
| Misspelled component name | E | R | R | R | E | R | E |
| Misspelled input name | E | M | M | R | E | E | E |
| Missing required input | E | M | M | M | E | E | E |
| Misspelled slot name | E | M | n/a | n/a | E | M | E |
| Undefined template variable | E | M | M | R | E | E | E |
| Misspelled attribute on a template object | E | M | R | M | E | E | E |
| Unknown translation message key | E | M | M | n/a | n/a | n/a | n/a |
| Misspelled template directive | R | M | M | M | M | R | n/a |
| Misspelled input on a browser-side component | E | R | R | R | n/a | E | E |
| Missing required input on a browser-side component | E | n/a | n/a | n/a | n/a | E | E |
| Required slot left unfilled | E | M | n/a | R | E | M | E |
| Slot fill reads a misspelled slot-data field | R | n/a | n/a | M | E | E | E |
| Template reads a misspelled state field | E | M | M | R | E | E | E |
| Browser code reads a misspelled server value | E | R | R | R | n/a | M | E |
| **Types** | (6/7) | (1/5) | (1/5) | (3/6) | (5/5) | (6/7) | (6/7) |
| Wrong-typed input written in markup | E | M | M | M | n/a | E | E |
| Wrong-typed input computed in code | E | E | E | E | E | E° | E |
| Wrong-typed operation in a template expression | E | M | M | R | E | M | M |
| Wrong-typed input on a browser-side component | M | n/a | n/a | n/a | n/a | E | E |
| Slot fill uses slot data as the wrong type | R | n/a | n/a | R | E | E | E |
| State field given a value of the wrong type | E | M | M | M | E | E | E |
| Component input given a value outside its allowed choices | E | M | M | M | E | E | E |
| **Template and script syntax** | (3/3) | (4/4) | (4/4) | (4/4) | (3/3) | (3/3) | (4/4) |
| Syntax error in a browser expression | R | R | R | R | R | C | E |
| Syntax error in component JavaScript | E | E | E | R | R | E | E |
| Unclosed element in a template | E° | C | C | C | E | E | E° |
| Misspelled path to a template or component file | n/a | R | R | R | n/a | n/a | E |
| **HTML and CSS** | (1/4) | (0/4) | (0/4) | (0/4) | (1/4) | (2/4) | (3/4) |
| Invalid HTML attribute value | Ew | M | M | M | M | E | E |
| Misspelled HTML attribute name | M | M | M | M | M | M | E |
| Misspelled HTML element | M | M | M | M | E | R | E |
| Misspelled CSS class | M | M | M | M | M | M | M |
| **Events and server requests** | (3/10) | (3/7) | (3/7) | (4/7) | (4/7) | (6/10) | (9/9) |
| Misspelled server handler name | E | R | R | R | R | E° | E |
| State field typo in an update handler | E | M | M | R | E | E | E |
| Misspelled field in a request payload | M | R | R | R | R | M | E |
| Child emits an event the parent does not listen for | E | M | M | M | M | E | E |
| Child component changes an input it received | M | P | P | P | n/a | C | C |
| Parent listens for a misspelled event | M | M | M | M | M | M | E |
| Event sent with a payload of the wrong type | M | n/a | n/a | n/a | n/a | n/a | n/a |
| Misspelled browser event name on an element | M | M | M | M | M | M | E |
| Request payload field of the wrong type | M | P | P | P | P | M | E |
| Request payload leaves out a required field | M | R | R | R | R | R | E |
| Browser reads a misspelled field of the server's reply | n/a | n/a | n/a | n/a | n/a | E | n/a |
| **Server and browser** | (2/4) | (2/3) | (2/3) | (2/3) | (2/3) | (2/3) | (2/3) |
| Server-only value read in browser code | E | R | R | R | R | R | R |
| Server and browser render different content | M | n/a | n/a | n/a | n/a | R | R |
| Server passes browser code a value the browser cannot receive | R | R | R | R | R | n/a | n/a |
| Server sends a secret to the browser | M | M | M | M | M | M | M |
