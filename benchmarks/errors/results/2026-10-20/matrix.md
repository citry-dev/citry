# Error-prevention results, run 20261020T094732Z

Cases and tools from commit `b0ef345dcc7a71e5ba7d68d0bbf7677f8a7348be`.

## How each mistake ended

| Outcome | Citry | Django + HTMX + Alpine | Jinja + HTMX + Alpine | FastHTML | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- |
| Static error | 16 | 3 | 2 | 11 | 13 | 18 |
| Static warning | 1 | 0 | 0 | 0 | 0 | 0 |
| Runtime error | 3 | 5 | 10 | 5 | 5 | 2 |
| Runtime warning | 0 | 0 | 0 | 0 | 0 | 0 |
| N/A or prevented by design | 0 | 1 | 3 | 3 | 1 | 2 |
| Missed | 4 | 14 | 8 | 4 | 5 | 2 |
| Missed, page unchanged | 0 | 1 | 1 | 1 | 0 | 0 |

## Every mistake

| Code | Meaning |
| --- | --- |
| E | reported in the editor |
| C | reported by a command-line check, type check or linter |
| B | reported by the production build |
| R | reported at runtime by a server error, an error response or a browser error (Rw: only a warning) |
| w | the stage before it gave only a warning; after the comma, the first stage that gave an error, or S or N |
| S | nothing reports it, and the page looks or behaves differently |
| N | nothing reports it, and the page looks the same |
| ? | the runtime check was skipped and no tool reported it |
| P | the framework's design prevents the mistake |
| - | no case was written for this framework |
| n/a | the mistake has no natural equivalent in this framework |
| ! | the clean app reported problems in this run, so the cell is unreliable |
| ~ | a tool timed out or skipped this case, so it may have caught the mistake earlier |
| ° | the report points away from the change, and the case explains why it still counts |

| Mistake | Citry | Django + HTMX + Alpine | Jinja + HTMX + Alpine | FastHTML | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- |
| (caught/total) | (20/24) | (8/23) | (12/21) | (16/21) | (18/23) | (20/22) |
| **Names: components, inputs, slots, variables** | (8/8) | (1/8) | (3/6) | (6/7) | (6/7) | (6/6) |
| Misspelled component name | E | R | R | E | R | E |
| Misspelled input name | E | S | R | E | E | E |
| Missing required input | E | S | S | E | E | E |
| Misspelled slot name | E | S | n/a | E | S | E |
| Undefined template variable | E | S | R | E | E | E |
| Misspelled attribute on a template object | E | S | S | E | E | E |
| Unknown translation message key | E | S | n/a | n/a | n/a | n/a |
| Misspelled template directive | R | S | S | S | R | n/a |
| **Types** | (3/3) | (1/3) | (2/3) | (2/2) | (2/3) | (2/3) |
| Wrong-typed input written in markup | E | S | S | n/a | E | E |
| Wrong-typed input computed in code | E | E | E | E | E° | E |
| Wrong-typed operation in a template expression | E | S | R | E | S | S |
| **Template and script syntax** | (3/3) | (3/3) | (3/3) | (3/3) | (3/3) | (3/3) |
| Syntax error in a browser expression | R | R | R | R | C | E |
| Syntax error in component JavaScript | E | E | R | R | E | E |
| Unclosed element in a template | E | C | C | E | E | E° |
| **HTML and CSS** | (1/4) | (0/4) | (0/4) | (1/4) | (2/4) | (3/4) |
| Invalid HTML attribute value | Ew, N | N | N | N | E | E |
| Misspelled HTML attribute name | S | S | S | S | S | E |
| Misspelled HTML element | S | S | S | E | R | E |
| Misspelled CSS class | S | S | S | S | S | S |
| **Events and server requests** | (3/4) | (2/4) | (3/4) | (3/4) | (3/4) | (4/4) |
| Misspelled server handler name | E | R | R | R | E° | E |
| State field typo in an update handler | E | S | R | E | E | E |
| Misspelled field in a request payload | S | R | R | R | S | E |
| Child emits an event the parent does not listen for | E | S | S | S | E | E |
| **Server and browser** | (2/2) | (1/1) | (1/1) | (1/1) | (2/2) | (2/2) |
| Server-only value read in browser code | E | R | R | R | R | R |
| Server and browser render different content | R | n/a | n/a | n/a | R | R |
