# Error-prevention results, run 20261020T090617Z

## How each mistake ended

| Outcome | Citry | Django + HTMX + Alpine | Jinja + HTMX + Alpine | FastHTML | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- |
| Error before running | 16 | 3 | 2 | 11 | 13 | 18 |
| Warning before running | 1 | 0 | 0 | 0 | 0 | 0 |
| Error at runtime | 3 | 5 | 10 | 5 | 5 | 2 |
| Warning at runtime | 0 | 0 | 0 | 0 | 0 | 0 |
| Missed, page wrong | 4 | 13 | 8 | 3 | 5 | 2 |
| Missed, no visible change | 0 | 2 | 1 | 1 | 0 | 0 |
| Does not apply | 0 | 1 | 3 | 4 | 1 | 2 |

## Every mistake

| Code | Meaning |
| --- | --- |
| E | reported in the editor |
| C | reported by a command-line check, type check or linter |
| B | reported by the production build |
| R | reported at runtime: a server error, an error response, or a browser error or warning |
| w | after a stage letter: that stage gave only a warning; after the comma: the first error, if any |
| S | nothing reports it, and the page looks or behaves differently |
| N | nothing reports it, and the page looks the same |
| ? | the runtime check was skipped and no tool reported it |
| P | the framework's design prevents the mistake |
| - | no case was written for this framework |
| n/a | the mistake has no natural equivalent in this framework |
| ! | the unchanged app reported problems in this run, so the cell is unreliable |
| ~ | a tool timed out or skipped this case, so it may have caught the mistake earlier |
| ° | the report points away from the change, and the case explains why it still counts |

| Mistake | Citry | Django + HTMX + Alpine | Jinja + HTMX + Alpine | FastHTML | Nuxt (TypeScript) | Next.js (TypeScript) |
| --- | --- | --- | --- | --- | --- | --- |
| **Names: components, inputs, slots, variables** | | | | | | |
| Misspelled component name | E | R | R | E | R | E |
| Misspelled input name | E | S | R | E | E | E |
| Missing required input | E | S | S | E | E | E |
| Misspelled slot name | E | S | n/a | E | S | E |
| Undefined template variable | E | S | R | E | E | E |
| Misspelled attribute on a template object | E | S | S | E | E | E |
| Unknown translation message key | E | S | n/a | n/a | n/a | n/a |
| Misspelled template directive | R | S | S | n/a | R | n/a |
| **Types** | | | | | | |
| Wrong-typed input written in markup | E | S | S | n/a | E | E |
| Wrong-typed input computed in code | E | N | E | E | E° | E |
| Wrong-typed operation in a template expression | E | S | R | E | S | S |
| **Template and script syntax** | | | | | | |
| Syntax error in a browser expression | R | R | R | R | C | E |
| Syntax error in component JavaScript | E | E | R | R | E | E |
| Unclosed element in a template | E | C | C | E | E | E° |
| **HTML and CSS** | | | | | | |
| Invalid HTML attribute value | Ew, N | N | N | N | E | E |
| Misspelled HTML attribute name | S | S | S | S | S | E |
| Misspelled HTML element | S | C | S | E | R | E |
| Misspelled CSS class | S | S | S | S | S | S |
| **Events and server requests** | | | | | | |
| Misspelled server handler name | E | R | R | R | E° | E |
| State field typo in an update handler | E | S | R | E | E | E |
| Misspelled field in a request payload | S | R | R | R | S | E |
| Child emits an event the parent does not listen for | E | S | S | S | E | E |
| **Server and browser** | | | | | | |
| Server-only value read in browser code | E | R | R | R | R | R |
| Server and browser render different content | R | n/a | n/a | n/a | R | R |
