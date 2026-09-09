# Measure the public simple API

The public runtime now has validation and integration work that the earlier
prototypes did not perform. Measure it directly before borrowing their gains.

Use the existing large page, its data callbacks and its templates. The candidate
adds `simple = True` to Button, Icon and HeroIcon at class definition, makes their
callbacks static and removes the unused `self` parameter. Reject the fixture if
any selected callback starts using its instance. HeroIcon retains the existing
`pure = True` declaration in both Citry variants. No runtime method is patched
during timing, and no experimental rendering adapter is installed.

Run all six permutations of ordinary Citry, simple Citry and the existing Django
scenario in fresh processes, 80 warmed renders after six initial renders per
process. Report the actual second render separately. Keep normal garbage
collection and retain every timed HTML result until timing ends. Vary Citry's
fixed-width IDs on each render. Exclude loading the scenario, collecting inputs,
instrumentation and output checks from rendering time.

After timing, count the three callbacks and capture complete ownership snapshots
and browser manifests. Check every timed Citry output with the existing
application-content projection, which validates manifests and removes ownership
markers and replaces generated IDs with stable names. Require matching projected output between ordinary
and simple variants and unchanged callback/call counts; require 342 ordinary and
146 simple identities. Ownership graphs intentionally differ. Django remains
the vendored scenario using django-components' HTML-attribute helper; its output
and feature set differ, so timing does not establish equivalent full behavior.

Record raw timings, output sizes and hashes, activation evidence, source hashes
and the native artifact hash. Reject changing sources, missing activation,
invalid manifests or different Citry application output. This first public-API
measurement is diagnostic; it does not replace broader feature qualification or
update the adopted historical timeline. Investigate the measured gap before
choosing the next optimization.

The public API also covers one Icon inserted as a Python value. The earlier
prototype selected only the 40 Icon tags; the public fixture executes 41 Icon
callbacks and removes 196 identities in total, including that Python value.

Callback counts and complete ownership snapshots come from one observed render
after timing in each Citry worker. Every timed Citry HTML result is checked and
its emitted manifests validated, but callbacks and server records are not
independently instrumented during timing. The native artifact is the retained
release build used by the accepted repeat-render baseline; its SHA-256 is
`321af83391e96c3770513de105b53f51e0cb2af60ea254857faa85b8fc9f71c7`.
