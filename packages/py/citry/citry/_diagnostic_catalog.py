"""Generated from packages/protocol/diagnostics/v1/catalog.json. Do not edit."""

# ruff: noqa: E501, Q000
# fmt: off

from __future__ import annotations

from typing import Final

SCHEMA_VERSION: Final = 1
DOCUMENTATION_BASE_URL: Final = 'https://citry.dev'

PARSE_SYNTAX = 'citry.parse.syntax'
PARSE_VALUE = 'citry.parse.value'
PARSE_CONFIGURATION = 'citry.parse.configuration'
TEMPLATE_UNKNOWN_VARIABLE = 'citry.template.unknown-variable'
TEMPLATE_UNKNOWN_COMPONENT = 'citry.template.unknown-component'
TEMPLATE_MARKER_NAME_INVALID = 'citry.template.marker-name-invalid'
TEMPLATE_ALPINE_ATTRIBUTE = 'citry.template.alpine-attribute'
TEMPLATE_ALPINE_CLOAK = 'citry.template.alpine-cloak'
TEMPLATE_INVALID_ATTRIBUTE_VALUE = 'citry.template.invalid-attribute-value'
JS_DATA_UNSUPPORTED_TYPE = 'citry.js-data.unsupported-type'
JS_DATA_PUBLIC_NAME_COLLISION = 'citry.js-data.public-name-collision'
VUE_UNKNOWN_VARIABLE = 'citry.vue.unknown-variable'
VUE_PYTHON_VARIABLE = 'citry.vue.python-variable'
CSP_INCOMPATIBLE_BROWSER_CODE = 'citry.csp.incompatible-browser-code'
COMPONENT_JS_UNKNOWN_VARIABLE = 'citry.component-js.unknown-variable'
COMPONENT_JS_UNKNOWN_MEMBER = 'citry.component-js.unknown-member'
BROWSER_INVALID_STATE_BINDING_TARGET = 'citry.browser.invalid-state-binding-target'
BROWSER_UNKNOWN_STATE_FIELD = 'citry.browser.unknown-state-field'
BROWSER_UNKNOWN_SERVER_EVENT = 'citry.browser.unknown-server-event'
BROWSER_UNDECLARED_EMIT = 'citry.browser.undeclared-emit'
BROWSER_UNDECLARED_COMPONENT_EVENT = 'citry.browser.undeclared-component-event'
BROWSER_MISSING_COMPONENT_PROP = 'citry.browser.missing-component-prop'
BROWSER_INCOMPATIBLE_COMPONENT_PROP = 'citry.browser.incompatible-component-prop'
CHECK_TEMPLATE_DECLARATION = 'citry.check.template-declaration'
CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED = 'citry.check.template-language-unsupported'
CHECK_TEMPLATE_VALUE_INVALID = 'citry.check.template-value-invalid'
CHECK_TEMPLATE_FILE_NOT_FOUND = 'citry.check.template-file-not-found'
CHECK_TEMPLATE_FILE_UNREADABLE = 'citry.check.template-file-unreadable'
CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE = 'citry.check.template-namespace-unavailable'
CHECK_PYTHON_SOURCE_UNREADABLE = 'citry.check.python-source-unreadable'
I18N_CATALOG_INVALID = 'citry.i18n.catalog-invalid'
I18N_UNKNOWN_MESSAGE = 'citry.i18n.unknown-message'
I18N_ARGUMENT_INVALID = 'citry.i18n.argument-invalid'
I18N_CROSS_LANGUAGE_FALLBACK = 'citry.i18n.cross-language-fallback'
I18N_CLIENT_MESSAGE_INVALID = 'citry.i18n.client-message-invalid'
FORMAT_SYNTAX = 'citry.format.syntax'
FORMAT_SUPPRESSION = 'citry.format.suppression'
FORMAT_INVARIANT = 'citry.format.invariant'
FORMAT_UNSUPPORTED = 'citry.format.unsupported'
FORMAT_PROVIDER_INVALID = 'citry.format.provider-invalid'
FORMAT_EMBEDDED_SUPPRESSED = 'citry.format.embedded-suppressed'
FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED = 'citry.format.embedded-language-unsupported'
FORMAT_EMBEDDED_INTERPOLATION_UNSUPPORTED = 'citry.format.embedded-interpolation-unsupported'
FORMAT_PROVIDER_UNAVAILABLE = 'citry.format.provider-unavailable'
FORMAT_HOST_SYNTAX = 'citry.format.host-syntax'
FORMAT_INELIGIBLE = 'citry.format.ineligible'
FORMAT_STALE_DOCUMENT = 'citry.format.stale-document'
FORMAT_CANCELLED = 'citry.format.cancelled'

DIAGNOSTICS: Final = {'citry.browser.incompatible-component-prop': {'code': 'citry.browser.incompatible-component-prop',
                                               'constant': 'BROWSER_INCOMPATIBLE_COMPONENT_PROP',
                                               'defaultSeverity': 'error',
                                               'documentationPath': '/ide/diagnostics/#citry.browser.incompatible-component-prop',
                                               'examples': [{'language': 'citry-html',
                                                             'source': '<c-card :count="\'many\'" />',
                                                             'title': 'Wrong literal type'}],
                                               'messages': {'default': "Vue prop '{name}' expects {expected}, but this "
                                                                       'binding is {actual}.'},
                                               'parameters': {'actual': 'Proven authored value type.',
                                                              'expected': "Child component's accepted Vue prop type.",
                                                              'name': 'Authored native Vue prop name.'},
                                               'summary': 'A native Vue binding value has a proven type that the '
                                                          'declared child prop type does not accept.',
                                               'surfaces': ['check', 'lsp'],
                                               'title': 'Incompatible Vue prop',
                                               'when': 'A resolved component receives a native :prop or v-bind:prop '
                                                       'value with a proven literal, JsData, or loop-binding type that '
                                                       'is incompatible with its statically declared Vue prop type.'},
 'citry.browser.invalid-state-binding-target': {'code': 'citry.browser.invalid-state-binding-target',
                                                'constant': 'BROWSER_INVALID_STATE_BINDING_TARGET',
                                                'defaultSeverity': 'error',
                                                'documentationPath': '/ide/diagnostics/#citry.browser.invalid-state-binding-target',
                                                'examples': [{'language': 'citry-html',
                                                              'source': '<head :c-query></head>',
                                                              'title': 'Binding on a non-control element'}],
                                                'messages': {'default': '{detail}'},
                                                'parameters': {'detail': 'Explanation of the unsupported binding '
                                                                         'target.'},
                                                'summary': 'A State binding is attached to an element or input type '
                                                           'that cannot support it.',
                                                'surfaces': ['check', 'lsp'],
                                                'title': 'Invalid State binding target',
                                                'when': 'A statically known target cannot hold a bound value or '
                                                        'support the requested binding direction or update event.'},
 'citry.browser.missing-component-prop': {'code': 'citry.browser.missing-component-prop',
                                          'constant': 'BROWSER_MISSING_COMPONENT_PROP',
                                          'defaultSeverity': 'error',
                                          'documentationPath': '/ide/diagnostics/#citry.browser.missing-component-prop',
                                          'examples': [{'language': 'citry-html',
                                                        'source': '<c-card />',
                                                        'title': 'Missing required prop'}],
                                          'messages': {'default': "Required Vue prop '{name}' is missing for <{tag}>."},
                                          'parameters': {'name': 'Required child Vue prop name.',
                                                         'tag': 'Resolved native component tag.'},
                                          'summary': 'A component call omits a required prop declared by the child '
                                                     "component's Vue props option.",
                                          'surfaces': ['check', 'lsp'],
                                          'title': 'Missing required Vue prop',
                                          'when': 'A resolved registered <c-*> call has no native Vue binding for a '
                                                  'prop marked required: true, and no dynamic binding could supply '
                                                  'it.'},
 'citry.browser.undeclared-component-event': {'code': 'citry.browser.undeclared-component-event',
                                              'constant': 'BROWSER_UNDECLARED_COMPONENT_EVENT',
                                              'defaultSeverity': 'warning',
                                              'documentationPath': '/ide/diagnostics/#citry.browser.undeclared-component-event',
                                              'examples': [{'language': 'citry-html',
                                                            'source': '<c-Lane @drop-tsak="moveTask($event)"></c-Lane>',
                                                            'title': 'Misspelled child event'}],
                                              'messages': {'default': "Component '{component}' does not declare event "
                                                                      "'{name}' in its emits option."},
                                              'parameters': {'component': 'Component tag, lowercased, including the c- '
                                                                          'prefix.',
                                                             'name': 'Authored event name.'},
                                              'summary': 'A template listens on a child component tag for an event the '
                                                         "child's emits option does not declare.",
                                              'surfaces': ['check', 'lsp'],
                                              'title': 'Listener for an event the child component does not declare',
                                              'when': 'A @name or v-on:name listener on a Citry component tag names an '
                                                      "event that the child component's emits option does not declare "
                                                      'and no on<Event> prop accepts, and the name cannot be a native '
                                                      'DOM event because it contains a hyphen, a colon, or an '
                                                      "uppercase letter. Vue passes such a listener to the child's "
                                                      'root element, where it fires only if that element dispatches a '
                                                      'DOM event with this name, so a misspelled event name goes '
                                                      "unnoticed. Citry checks only when the child's emits option is "
                                                      'an array of string literals or an object with static keys.'},
 'citry.browser.undeclared-emit': {'code': 'citry.browser.undeclared-emit',
                                   'constant': 'BROWSER_UNDECLARED_EMIT',
                                   'defaultSeverity': 'error',
                                   'documentationPath': '/ide/diagnostics/#citry.browser.undeclared-emit',
                                   'examples': [{'language': 'javascript',
                                                 'source': '$component({\n'
                                                           "  emits: ['drop-task'],\n"
                                                           '  methods: {\n'
                                                           "    drop() { this.$emit('drop-tsak'); },\n"
                                                           '  },\n'
                                                           '});',
                                                 'title': 'Misspelled event in a method'},
                                                {'language': 'citry-html',
                                                 'source': '<button @click="$emit(\'close\')">Close</button>',
                                                 'title': 'Undeclared event in the template'}],
                                   'messages': {'default': "Event '{name}' is not declared in this component's emits "
                                                           'option.'},
                                   'parameters': {'name': 'Authored event name.'},
                                   'summary': "Browser code emits a Vue event that the component's emits option does "
                                              'not declare.',
                                   'surfaces': ['check', 'lsp'],
                                   'title': 'Undeclared emitted event',
                                   'when': 'Component JavaScript calls this.$emit or component.$emit, or a Vue '
                                           "expression in the component's template calls $emit, with a string literal "
                                           "that is not in the component's emits option and has no matching on<Event> "
                                           'prop. Citry checks only when the emits option is an array of string '
                                           'literals or an object with static keys; a component without emits may emit '
                                           'any name, as in Vue.'},
 'citry.browser.unknown-server-event': {'code': 'citry.browser.unknown-server-event',
                                        'constant': 'BROWSER_UNKNOWN_SERVER_EVENT',
                                        'defaultSeverity': 'error',
                                        'documentationPath': '/ide/diagnostics/#citry.browser.unknown-server-event',
                                        'examples': [{'language': 'citry-html',
                                                      'source': '<button @click="sendEvent(\'missing\')">Run</button>',
                                                      'title': 'Unknown literal event'},
                                                     {'language': 'citry-html',
                                                      'source': '<button @c-click="missing">Run</button>',
                                                      'title': 'Unknown declarative handler'},
                                                     {'language': 'citry-html',
                                                      'source': '<span x-show="$loading(\'missing\')">Saving</span>',
                                                      'title': 'Unknown loading handler'}],
                                        'messages': {'default': "Server event '{name}' is not declared by this "
                                                                'component.'},
                                        'parameters': {'name': 'Authored server-event wire name.'},
                                        'summary': 'A literal browser event reference names no effective handler on '
                                                   'the component that owns it.',
                                        'surfaces': ['check', 'lsp'],
                                        'title': 'Unknown server event',
                                        'when': 'An Vue expression or component JavaScript calls sendEvent, '
                                                '$sendEvent, $loading, or $error with an unknown non-empty string '
                                                'literal, or a declarative @c-* binding names an unknown handler.'},
 'citry.browser.unknown-state-field': {'code': 'citry.browser.unknown-state-field',
                                       'constant': 'BROWSER_UNKNOWN_STATE_FIELD',
                                       'defaultSeverity': 'error',
                                       'documentationPath': '/ide/diagnostics/#citry.browser.unknown-state-field',
                                       'examples': [{'language': 'citry-html',
                                                     'source': '<input :c-missing_field.debounce="refresh">',
                                                     'title': 'Unknown field in a State binding'}],
                                       'messages': {'default': "State field '{name}' is not a public field of this "
                                                               'component.'},
                                       'parameters': {'name': 'Authored State field name, without prefix or '
                                                              'modifiers.'},
                                       'summary': 'A State binding names a field that the owning component does not '
                                                  'expose publicly.',
                                       'surfaces': ['check', 'lsp'],
                                       'title': 'Unknown State binding field',
                                       'when': 'A :c-* binding names a field absent from a known public State schema. '
                                               'Bindings with unknown component ownership or an unknown State schema '
                                               'are not checked.'},
 'citry.check.python-source-unreadable': {'code': 'citry.check.python-source-unreadable',
                                          'constant': 'CHECK_PYTHON_SOURCE_UNREADABLE',
                                          'defaultSeverity': 'error',
                                          'documentationPath': '/ide/diagnostics/#citry.check.python-source-unreadable',
                                          'messages': {'default': 'Citry could not analyze this Python source: '
                                                                  '{detail}'},
                                          'parameters': {'detail': 'Python source failure detail.'},
                                          'summary': 'Static checking could not read, decode, or parse a Python source '
                                                     'file.',
                                          'surfaces': ['check'],
                                          'title': 'Python source could not be analyzed',
                                          'when': 'Static discovery reaches a Python file that cannot be read, '
                                                  'decoded, or parsed.'},
 'citry.check.template-declaration': {'code': 'citry.check.template-declaration',
                                      'constant': 'CHECK_TEMPLATE_DECLARATION',
                                      'defaultSeverity': 'error',
                                      'documentationPath': '/ide/diagnostics/#citry.check.template-declaration',
                                      'messages': {'default': "Citry could not inspect this component's template "
                                                              'declaration: {detail}'},
                                      'parameters': {'detail': 'Inspection failure detail.'},
                                      'summary': "The checker could not safely inspect or identify a component's "
                                                 'template declaration.',
                                      'surfaces': ['check'],
                                      'title': 'Template declaration unavailable',
                                      'when': "The selected component's template or template_file declaration raises "
                                              'during inspection or cannot be identified safely.'},
 'citry.check.template-file-not-found': {'code': 'citry.check.template-file-not-found',
                                         'constant': 'CHECK_TEMPLATE_FILE_NOT_FOUND',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.check.template-file-not-found',
                                         'examples': [{'language': 'citry',
                                                       'source': 'class Card(Component):\n'
                                                                 '    template_file = "missing.html"',
                                                       'title': 'Missing template file'}],
                                         'messages': {'default': "Template file '{path}' was not found. Searched: "
                                                                 '{locations}.'},
                                         'parameters': {'locations': 'Locations searched by Citry.',
                                                        'path': 'Authored template_file value.'},
                                         'summary': 'No template file exists at any location resolved from '
                                                    'template_file.',
                                         'surfaces': ['check'],
                                         'title': 'Template file not found',
                                         'when': 'Component.template_file points to a path that does not exist in the '
                                                 'component directory or any configured template directory.'},
 'citry.check.template-file-unreadable': {'code': 'citry.check.template-file-unreadable',
                                          'constant': 'CHECK_TEMPLATE_FILE_UNREADABLE',
                                          'defaultSeverity': 'error',
                                          'documentationPath': '/ide/diagnostics/#citry.check.template-file-unreadable',
                                          'messages': {'default': 'Citry could not read this template file: {detail}'},
                                          'parameters': {'detail': 'File-system or decoding failure detail.'},
                                          'summary': 'The resolved template file could not be opened or decoded as '
                                                     'UTF-8.',
                                          'surfaces': ['check'],
                                          'title': 'Template file could not be read',
                                          'when': 'Citry resolves Component.template_file but cannot open the file or '
                                                  'decode it as UTF-8.'},
 'citry.check.template-language-unsupported': {'code': 'citry.check.template-language-unsupported',
                                               'constant': 'CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED',
                                               'defaultSeverity': 'error',
                                               'documentationPath': '/ide/diagnostics/#citry.check.template-language-unsupported',
                                               'messages': {'default': 'Citry cannot check template_lang with a {type} '
                                                                       'value. This template was skipped.'},
                                               'parameters': {'type': 'Runtime type of the non-None template_lang '
                                                                      'value.'},
                                               'summary': 'The checker only analyzes native Citry templates and '
                                                          'skipped a declaration with another language.',
                                               'surfaces': ['check'],
                                               'title': 'Unsupported template language',
                                               'when': 'A component sets template_lang to a non-None value; citry '
                                                       'check currently analyzes only native Citry templates.'},
 'citry.check.template-namespace-unavailable': {'code': 'citry.check.template-namespace-unavailable',
                                                'constant': 'CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE',
                                                'defaultSeverity': 'error',
                                                'documentationPath': '/ide/diagnostics/#citry.check.template-namespace-unavailable',
                                                'messages': {'default': "Citry could not inspect this template's "
                                                                        'variables: {detail}'},
                                                'parameters': {'detail': 'Namespace inspection failure detail.'},
                                                'summary': 'The checker could not determine the variables supplied to '
                                                           'a component template.',
                                                'surfaces': ['check'],
                                                'title': 'Template variables unavailable',
                                                'when': "citry check cannot inspect the component's declared or "
                                                        'inferred template data namespace.'},
 'citry.check.template-value-invalid': {'code': 'citry.check.template-value-invalid',
                                        'constant': 'CHECK_TEMPLATE_VALUE_INVALID',
                                        'defaultSeverity': 'error',
                                        'documentationPath': '/ide/diagnostics/#citry.check.template-value-invalid',
                                        'examples': [{'language': 'citry',
                                                      'source': 'class Card(Component):\n'
                                                                '    template = build_template()',
                                                      'title': 'Non-string inline template'}],
                                        'messages': {'file': 'Component.template_file must be a string or Path. This '
                                                             'template was skipped.',
                                                     'inline': 'Component.template must be a string. This template was '
                                                               'skipped.'},
                                        'parameters': {},
                                        'summary': 'A template or template_file declaration has a value type the '
                                                   'checker cannot use.',
                                        'surfaces': ['check'],
                                        'title': 'Invalid template declaration value',
                                        'when': 'Component.template is not a string, or Component.template_file is '
                                                'neither a string nor a pathlib.Path.'},
 'citry.component-js.unknown-member': {'code': 'citry.component-js.unknown-member',
                                       'configurableSeverity': True,
                                       'constant': 'COMPONENT_JS_UNKNOWN_MEMBER',
                                       'defaultSeverity': 'error',
                                       'documentationPath': '/ide/diagnostics/#citry.component-js.unknown-member',
                                       'examples': [{'language': 'javascript',
                                                     'source': '$component(({ component }) => {\n'
                                                               '  console.log(component.missing_field);\n'
                                                               '});',
                                                     'title': 'Misspelled js_data() key in a callback'}],
                                       'messages': {'default': "Component instance member '{name}' is not defined by "
                                                               'this component.'},
                                       'parameters': {'name': 'Authored member name.'},
                                       'summary': 'Component JavaScript reads a name that the component instance does '
                                                  'not have.',
                                       'surfaces': ['check', 'lsp'],
                                       'title': 'Unknown component instance member',
                                       'when': 'Component JavaScript reads this.<name> inside a Vue Options method, '
                                               'computed value, data() function, lifecycle hook, provide() function, '
                                               'or watch handler, or reads component.<name> inside an onServerRender '
                                               'callback, and the name is not a js_data() key, prop, data() key, setup '
                                               'binding, method, computed value, or injection. Citry checks only when '
                                               "every owning component's JavaScript data is closed (a closed JsData "
                                               'schema or a complete inferred js_data() return) and every Vue Options '
                                               'section is known from the source. Names that start with $ or _, '
                                               'bracket reads such as component[key], and names the source may assign '
                                               'as a property are not checked, and nothing is checked when the source '
                                               'writes computed members, copies names in with Object.assign, declares '
                                               'a class, or merges other options in with mixins or extends. A plugin '
                                               'property without a $ prefix, such as this.axios, is reported.'},
 'citry.component-js.unknown-variable': {'code': 'citry.component-js.unknown-variable',
                                         'configurableSeverity': True,
                                         'constant': 'COMPONENT_JS_UNKNOWN_VARIABLE',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.component-js.unknown-variable',
                                         'examples': [{'language': 'javascript',
                                                       'source': '$component(({ component }) => {\n'
                                                                 '  component.ready = settings.ready;\n'
                                                                 '});',
                                                       'title': 'Undeclared name in a callback'}],
                                         'messages': {'default': "Component JavaScript variable '{name}' is not "
                                                                 'defined.'},
                                         'parameters': {'name': 'Authored JavaScript variable name.'},
                                         'summary': 'A free identifier inside a $component initializer is absent from '
                                                    'its lexical scope and configured globals.',
                                         'surfaces': ['check', 'lsp'],
                                         'title': 'Unknown component JavaScript variable',
                                         'when': 'A $component initializer references a name that was not declared '
                                                 'locally, destructured from the callback context, supplied by the '
                                                 'JavaScript or browser environment, or configured as a lint-only '
                                                 'component JavaScript global.'},
 'citry.csp.incompatible-browser-code': {'code': 'citry.csp.incompatible-browser-code',
                                         'configurableSeverity': True,
                                         'constant': 'CSP_INCOMPATIBLE_BROWSER_CODE',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.csp.incompatible-browser-code',
                                         'examples': [{'language': 'citry-html',
                                                       'source': '<button @click="items.map(item => '
                                                                 'item.id)">Save</button>',
                                                       'title': 'Move an arrow function into Component.js'}],
                                         'messages': {'default': 'The configured browser security policy cannot accept '
                                                                 '{detail} here. Move complex logic to Component.js '
                                                                 'and call a component method from the template.'},
                                         'parameters': {'detail': 'The unsupported directive, host, token, or '
                                                                  'operation.'},
                                         'summary': 'A Citry browser expression or asset conflicts with the configured '
                                                    'browser security policy.',
                                         'surfaces': ['check', 'lsp'],
                                         'title': 'Browser code is incompatible with strict CSP',
                                         'when': 'The selected Citry application configures CSP warning or strict mode '
                                                 'and a source-classifiable browser expression or asset violates that '
                                                 'policy.'},
 'citry.format.cancelled': {'code': 'citry.format.cancelled',
                            'constant': 'FORMAT_CANCELLED',
                            'defaultSeverity': 'information',
                            'documentationPath': '/ide/diagnostics/#citry.format.cancelled',
                            'messages': {'default': '{detail}'},
                            'parameters': {'detail': 'Cancellation explanation.'},
                            'summary': 'The editor cancelled a formatting operation before Citry could apply it.',
                            'surfaces': ['vscode'],
                            'title': 'Formatting cancelled',
                            'when': 'The editor or user cancels a format request before Citry applies its edits.'},
 'citry.format.embedded-interpolation-unsupported': {'code': 'citry.format.embedded-interpolation-unsupported',
                                                     'constant': 'FORMAT_EMBEDDED_INTERPOLATION_UNSUPPORTED',
                                                     'defaultSeverity': 'warning',
                                                     'documentationPath': '/ide/diagnostics/#citry.format.embedded-interpolation-unsupported',
                                                     'examples': [{'language': 'citry-html',
                                                                   'source': '<script>\n'
                                                                             '  const title = "{{ title }}";\n'
                                                                             '</script>',
                                                                   'title': 'Citry interpolation inside JavaScript'}],
                                                     'messages': {'default': '{detail}'},
                                                     'parameters': {'detail': 'Interpolation explanation.'},
                                                     'summary': 'A JavaScript or CSS region contains Citry '
                                                                'interpolation that cannot be safely delegated yet.',
                                                     'surfaces': ['formatter', 'lsp', 'vscode'],
                                                     'title': 'Embedded interpolation unsupported',
                                                     'when': 'An embedded JavaScript or CSS region contains Citry '
                                                             'interpolation, which cannot yet be mapped safely through '
                                                             'an external formatter.'},
 'citry.format.embedded-language-unsupported': {'code': 'citry.format.embedded-language-unsupported',
                                                'constant': 'FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED',
                                                'defaultSeverity': 'warning',
                                                'documentationPath': '/ide/diagnostics/#citry.format.embedded-language-unsupported',
                                                'messages': {'default': '{detail}'},
                                                'parameters': {'detail': 'Unsupported language explanation.'},
                                                'summary': 'Citry recognized an embedded region but cannot delegate '
                                                           'its declared language.',
                                                'surfaces': ['formatter', 'lsp', 'vscode'],
                                                'title': 'Embedded language unsupported',
                                                'when': 'An embedded script or style region declares a language for '
                                                        'which Citry has no formatter provider.'},
 'citry.format.embedded-suppressed': {'code': 'citry.format.embedded-suppressed',
                                      'constant': 'FORMAT_EMBEDDED_SUPPRESSED',
                                      'defaultSeverity': 'information',
                                      'documentationPath': '/ide/diagnostics/#citry.format.embedded-suppressed',
                                      'messages': {'default': '{detail}'},
                                      'parameters': {'detail': 'Suppression explanation.'},
                                      'summary': 'A fmt directive deliberately prevented formatting of a JavaScript or '
                                                 'CSS region.',
                                      'surfaces': ['formatter', 'lsp', 'vscode'],
                                      'title': 'Embedded formatting suppressed',
                                      'when': 'A fmt:off or fmt:skip directive covers an embedded JavaScript or CSS '
                                              'region.'},
 'citry.format.host-syntax': {'code': 'citry.format.host-syntax',
                              'constant': 'FORMAT_HOST_SYNTAX',
                              'defaultSeverity': 'error',
                              'documentationPath': '/ide/diagnostics/#citry.format.host-syntax',
                              'messages': {'default': '{detail}'},
                              'parameters': {'detail': 'Python syntax explanation.'},
                              'summary': 'A Python file containing component assets could not be parsed before '
                                         'formatting.',
                              'surfaces': ['formatter', 'lsp', 'vscode'],
                              'title': 'Invalid Python host syntax',
                              'when': 'A format command targets a Python file whose current source has invalid Python '
                                      'syntax.'},
 'citry.format.ineligible': {'code': 'citry.format.ineligible',
                             'constant': 'FORMAT_INELIGIBLE',
                             'defaultSeverity': 'error',
                             'documentationPath': '/ide/diagnostics/#citry.format.ineligible',
                             'messages': {'default': '{detail}'},
                             'parameters': {'detail': 'Eligibility explanation.'},
                             'summary': "The selected document, position, or asset is outside Citry's proven "
                                        'formatting scope.',
                             'surfaces': ['formatter', 'lsp', 'vscode'],
                             'title': 'Document is not eligible for formatting',
                             'when': 'Citry cannot prove that the selected document or cursor position belongs to a '
                                     'supported Citry template, script, or style region.'},
 'citry.format.invariant': {'code': 'citry.format.invariant',
                            'constant': 'FORMAT_INVARIANT',
                            'defaultSeverity': 'error',
                            'documentationPath': '/ide/diagnostics/#citry.format.invariant',
                            'messages': {'default': '{detail}'},
                            'parameters': {'detail': 'Formatter-provided explanation.'},
                            'summary': 'The formatter refused to write output after an internal span, structure, or '
                                       'idempotence check failed.',
                            'surfaces': ['formatter', 'lsp', 'vscode'],
                            'title': 'Formatter safety check failed',
                            'when': "Formatting output fails one of Citry's safety checks, so Citry refuses to apply "
                                    'the edit.'},
 'citry.format.provider-invalid': {'code': 'citry.format.provider-invalid',
                                   'constant': 'FORMAT_PROVIDER_INVALID',
                                   'defaultSeverity': 'error',
                                   'documentationPath': '/ide/diagnostics/#citry.format.provider-invalid',
                                   'messages': {'default': '{detail}'},
                                   'parameters': {'detail': 'Provider validation failure detail.'},
                                   'summary': "A JavaScript or CSS formatter response failed Citry's source-bound "
                                              'validation.',
                                   'surfaces': ['formatter', 'lsp', 'vscode'],
                                   'title': 'Embedded formatter returned invalid output',
                                   'when': 'A delegated JavaScript or CSS formatter returns an edit that does not '
                                           'match the requested embedded region.'},
 'citry.format.provider-unavailable': {'code': 'citry.format.provider-unavailable',
                                       'constant': 'FORMAT_PROVIDER_UNAVAILABLE',
                                       'defaultSeverity': 'warning',
                                       'documentationPath': '/ide/diagnostics/#citry.format.provider-unavailable',
                                       'messages': {'default': '{detail}'},
                                       'parameters': {'detail': 'Provider availability detail.'},
                                       'summary': 'No JavaScript or CSS formatter returned a usable result for a '
                                                  'delegated region.',
                                       'surfaces': ['formatter', 'lsp', 'vscode'],
                                       'title': 'Embedded formatter unavailable',
                                       'when': 'Citry asks the editor to format embedded JavaScript or CSS, but no '
                                               'installed provider returns an edit.'},
 'citry.format.stale-document': {'code': 'citry.format.stale-document',
                                 'constant': 'FORMAT_STALE_DOCUMENT',
                                 'defaultSeverity': 'error',
                                 'documentationPath': '/ide/diagnostics/#citry.format.stale-document',
                                 'messages': {'default': '{detail}'},
                                 'parameters': {'detail': 'Stale-document explanation.'},
                                 'summary': 'Formatting was discarded because its source-bound plan no longer matches '
                                            'the current document.',
                                 'surfaces': ['lsp', 'vscode'],
                                 'title': 'Document changed during formatting',
                                 'when': 'The document changes after Citry prepares a format plan but before the '
                                         'editor can apply it.'},
 'citry.format.suppression': {'code': 'citry.format.suppression',
                              'constant': 'FORMAT_SUPPRESSION',
                              'defaultSeverity': 'error',
                              'documentationPath': '/ide/diagnostics/#citry.format.suppression',
                              'examples': [{'language': 'citry-html',
                                            'source': '{# fmt: on #}\n<div></div>',
                                            'title': 'Unmatched formatter enable directive'}],
                              'messages': {'default': '{detail}'},
                              'parameters': {'detail': 'Formatter-provided explanation.'},
                              'summary': 'A fmt directive is unmatched or appears in a context where its requested '
                                         'scope is invalid.',
                              'surfaces': ['formatter', 'lsp', 'vscode'],
                              'title': 'Invalid formatter directive',
                              'when': 'A fmt:on, fmt:off, or fmt:skip directive has no valid matching scope at its '
                                      'authored position.'},
 'citry.format.syntax': {'code': 'citry.format.syntax',
                         'constant': 'FORMAT_SYNTAX',
                         'defaultSeverity': 'error',
                         'documentationPath': '/ide/diagnostics/#citry.format.syntax',
                         'messages': {'default': '{detail}'},
                         'parameters': {'detail': 'Formatter-provided explanation.'},
                         'summary': 'Formatting stopped because the template does not parse.',
                         'surfaces': ['formatter', 'lsp', 'vscode'],
                         'title': 'Invalid template syntax',
                         'when': 'A format command receives a template with a Citry syntax error.'},
 'citry.format.unsupported': {'code': 'citry.format.unsupported',
                              'constant': 'FORMAT_UNSUPPORTED',
                              'defaultSeverity': 'error',
                              'documentationPath': '/ide/diagnostics/#citry.format.unsupported',
                              'messages': {'default': '{detail}'},
                              'parameters': {'detail': 'Formatter-provided explanation.'},
                              'summary': 'The formatter conservatively declined a valid template shape it cannot yet '
                                         'rewrite safely.',
                              'surfaces': ['formatter', 'lsp', 'vscode'],
                              'title': 'Formatting shape unsupported',
                              'when': "The template is valid, but its source shape is outside the formatter's "
                                      'currently supported rewrite rules.'},
 'citry.i18n.argument-invalid': {'code': 'citry.i18n.argument-invalid',
                                 'constant': 'I18N_ARGUMENT_INVALID',
                                 'defaultSeverity': 'error',
                                 'documentationPath': '/ide/diagnostics/#citry.i18n.argument-invalid',
                                 'messages': {'default': '{detail}'},
                                 'parameters': {'detail': 'Argument-contract explanation.'},
                                 'summary': 'A translation binding, formatter, parser, or rich-message call does not '
                                            'match its checked contract.',
                                 'surfaces': ['check', 'lsp'],
                                 'title': 'Invalid i18n argument',
                                 'when': 'A literal i18n call or $c-tr binding is malformed, has missing, unknown, or '
                                         'mistyped message inputs, uses an unknown named profile, or supplies the '
                                         'wrong <c-trans> values or fills.'},
 'citry.i18n.catalog-invalid': {'code': 'citry.i18n.catalog-invalid',
                                'constant': 'I18N_CATALOG_INVALID',
                                'defaultSeverity': 'error',
                                'documentationPath': '/ide/diagnostics/#citry.i18n.catalog-invalid',
                                'messages': {'default': '{detail}'},
                                'parameters': {'detail': 'Compiler-provided catalog error.'},
                                'summary': "A Fluent source unit failed Citry's production parser or i18n contract "
                                           'checks.',
                                'surfaces': ['check', 'lsp'],
                                'title': 'Invalid Fluent catalog source',
                                'when': 'A messages block or catalog file contains invalid Fluent syntax, an '
                                        'unsupported parameter type, or another source-level i18n error.'},
 'citry.i18n.client-message-invalid': {'code': 'citry.i18n.client-message-invalid',
                                       'constant': 'I18N_CLIENT_MESSAGE_INVALID',
                                       'defaultSeverity': 'error',
                                       'documentationPath': '/ide/diagnostics/#citry.i18n.client-message-invalid',
                                       'messages': {'default': '{detail}'},
                                       'parameters': {'detail': 'Client-message contract explanation.'},
                                       'summary': 'A message declared for browser use is missing or lacks complete '
                                                  'locale coverage.',
                                       'surfaces': ['check'],
                                       'title': 'Invalid client i18n message',
                                       'when': 'Component.I18n.client_messages names an unknown output or an output '
                                               'that would fall back across languages in a client-enabled subtree.'},
 'citry.i18n.cross-language-fallback': {'code': 'citry.i18n.cross-language-fallback',
                                        'constant': 'I18N_CROSS_LANGUAGE_FALLBACK',
                                        'defaultSeverity': 'error',
                                        'documentationPath': '/ide/diagnostics/#citry.i18n.cross-language-fallback',
                                        'messages': {'default': '{detail}'},
                                        'parameters': {'detail': 'Fallback coverage explanation.'},
                                        'summary': 'A plain translated string falls back to a different language '
                                                   'without a place to carry that language metadata.',
                                        'surfaces': ['check'],
                                        'title': 'Cross-language i18n fallback',
                                        'when': 'A text-only translation can select a source or fallback locale whose '
                                                'canonical language tag differs from the requested locale.'},
 'citry.i18n.unknown-message': {'code': 'citry.i18n.unknown-message',
                                'constant': 'I18N_UNKNOWN_MESSAGE',
                                'defaultSeverity': 'error',
                                'documentationPath': '/ide/diagnostics/#citry.i18n.unknown-message',
                                'messages': {'default': '{detail}'},
                                'parameters': {'detail': 'Unknown-message explanation.'},
                                'summary': 'A literal translation key is absent from the checked project catalog.',
                                'surfaces': ['check', 'lsp'],
                                'title': 'Unknown i18n message',
                                'when': 'A direct tr() call, <c-trans> tag, $c-tr binding, or bounded browser bind() '
                                        'call names a message value or attribute that no component or configured '
                                        'catalog package defines.'},
 'citry.js-data.public-name-collision': {'code': 'citry.js-data.public-name-collision',
                                         'constant': 'JS_DATA_PUBLIC_NAME_COLLISION',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.js-data.public-name-collision',
                                         'messages': {'conditional': "JsData field '{name}' conflicts with a reserved "
                                                                     'or component-defined public instance name when '
                                                                     'supplied.',
                                                      'default': "JsData field '{name}' conflicts with a reserved or "
                                                                 'component-defined public instance name.'},
                                         'parameters': {'name': 'JsData field name.'},
                                         'summary': 'A JsData field conflicts with a reserved or component-defined Vue '
                                                    'public instance name.',
                                         'surfaces': ['lsp'],
                                         'title': 'JsData field conflicts with a public instance name',
                                         'when': 'A source-proven JsData field uses a reserved browser-scope name or '
                                                 'the name of a public Vue Options property.'},
 'citry.js-data.unsupported-type': {'code': 'citry.js-data.unsupported-type',
                                    'constant': 'JS_DATA_UNSUPPORTED_TYPE',
                                    'defaultSeverity': 'warning',
                                    'documentationPath': '/ide/diagnostics/#citry.js-data.unsupported-type',
                                    'examples': [{'language': 'citry',
                                                  'source': 'class Card(Component):\n'
                                                            '    class JsData:\n'
                                                            '        selected_ids: set[int]',
                                                  'title': 'Unsupported set value'}],
                                    'messages': {'default': "JsData field '{name}' is not a clean JSON value: "
                                                            '{detail}. Browser tooling will treat its type as '
                                                            'unknown.'},
                                    'parameters': {'detail': 'Why the value is not a clean JSON type.',
                                                   'name': 'JsData field name.'},
                                    'summary': 'A declared or inferred JsData value cannot be represented safely by '
                                               "Citry's JSON wire format.",
                                    'surfaces': ['check', 'lsp'],
                                    'title': 'JsData field is not a JSON type',
                                    'when': 'A JsData field has a type that strict JSON serialization cannot carry, '
                                            'such as bytes, a set, a callable, or a date/time object without an '
                                            'explicit conversion.'},
 'citry.parse.configuration': {'code': 'citry.parse.configuration',
                               'constant': 'PARSE_CONFIGURATION',
                               'defaultSeverity': 'error',
                               'documentationPath': '/ide/diagnostics/#citry.parse.configuration',
                               'messages': {'default': '{detail}'},
                               'parameters': {'detail': 'Configuration failure detail.'},
                               'summary': 'Project-specific parser configuration could not be constructed or applied.',
                               'surfaces': ['check', 'lsp'],
                               'title': 'Template parser configuration failed',
                               'when': 'Citry cannot build the parser rules required by the selected application or '
                                       'component registry.'},
 'citry.parse.syntax': {'code': 'citry.parse.syntax',
                        'constant': 'PARSE_SYNTAX',
                        'defaultSeverity': 'error',
                        'documentationPath': '/ide/diagnostics/#citry.parse.syntax',
                        'examples': [{'language': 'citry-html',
                                      'source': '<section>\n  <p>Hello</p>',
                                      'title': 'Unclosed element'}],
                        'messages': {'default': '{detail}'},
                        'parameters': {'detail': 'Parser-provided explanation.'},
                        'summary': 'The Citry parser could not parse the template at the reported source range.',
                        'surfaces': ['parser', 'formatter', 'check', 'lsp'],
                        'title': 'Invalid template syntax',
                        'when': 'Citry encounters malformed template markup, an incomplete expression, or another '
                                'template grammar error.'},
 'citry.parse.value': {'code': 'citry.parse.value',
                       'constant': 'PARSE_VALUE',
                       'defaultSeverity': 'error',
                       'documentationPath': '/ide/diagnostics/#citry.parse.value',
                       'messages': {'default': '{detail}'},
                       'parameters': {'detail': 'Parser-provided explanation.'},
                       'summary': "The parser received a template value that cannot be represented by Citry's template "
                                  'model.',
                       'surfaces': ['parser', 'formatter', 'check', 'lsp'],
                       'title': 'Invalid template value',
                       'when': 'A parser API receives a value that it cannot convert into Citry template source or a '
                               'supported template value.'},
 'citry.template.alpine-attribute': {'code': 'citry.template.alpine-attribute',
                                     'configurableSeverity': True,
                                     'constant': 'TEMPLATE_ALPINE_ATTRIBUTE',
                                     'defaultSeverity': 'warning',
                                     'documentationPath': '/ide/diagnostics/#citry.template.alpine-attribute',
                                     'examples': [{'language': 'citry-html',
                                                   'source': '<div x-data="{ open: false }">\n'
                                                             '  <button x-on:click="open = !open">Menu</button>\n'
                                                             '</div>',
                                                   'title': 'Alpine state on an element'}],
                                     'messages': {'default': "'{name}' is an Alpine attribute. Citry uses Vue, so "
                                                             'nothing reads it. Replace it with its Vue form, or set '
                                                             "rule_alpine_attribute to 'ignore' if a library on the "
                                                             "page reads '{name}'."},
                                     'parameters': {'name': 'Attribute name as written in the template.'},
                                     'summary': 'An HTML element carries an Alpine x- attribute, which Citry renders '
                                                'unchanged and nothing in the browser reads.',
                                     'surfaces': ['check', 'lsp'],
                                     'title': 'Alpine attribute on an HTML element',
                                     'when': 'An attribute name on a plain HTML element or a <c-element> starts with '
                                             'x-, compared without regard to letter case, including elements inside '
                                             'nested templates. Citry uses Vue, so the attribute has no effect unless '
                                             'another library on the page reads it. Component tags are not checked, '
                                             'because an x- attribute there is a Python keyword argument. x-cloak is '
                                             'reported as citry.template.alpine-cloak instead.'},
 'citry.template.alpine-cloak': {'code': 'citry.template.alpine-cloak',
                                 'configurableSeverity': True,
                                 'constant': 'TEMPLATE_ALPINE_CLOAK',
                                 'defaultSeverity': 'error',
                                 'documentationPath': '/ide/diagnostics/#citry.template.alpine-cloak',
                                 'examples': [{'language': 'citry-html',
                                               'source': '<div x-cloak>{{ message }}</div>',
                                               'title': 'Leftover x-cloak'}],
                                 'messages': {'default': "Nothing in Citry removes 'x-cloak', so a '[x-cloak]' CSS "
                                                         "rule keeps this element hidden. Delete 'x-cloak' and its "
                                                         "'[x-cloak]' rule; the server-rendered HTML already shows the "
                                                         'content.'},
                                 'parameters': {},
                                 'summary': 'An HTML element carries x-cloak. Nothing in Citry removes it, so a '
                                            '[x-cloak] CSS rule keeps the element hidden.',
                                 'surfaces': ['check', 'lsp'],
                                 'title': 'x-cloak hides an element for good',
                                 'when': 'An attribute named x-cloak, compared without regard to letter case, sits on '
                                         'a plain HTML element or a <c-element>, including elements inside nested '
                                         'templates. Component tags are not checked.'},
 'citry.template.invalid-attribute-value': {'code': 'citry.template.invalid-attribute-value',
                                            'configurableSeverity': True,
                                            'constant': 'TEMPLATE_INVALID_ATTRIBUTE_VALUE',
                                            'defaultSeverity': 'warning',
                                            'documentationPath': '/ide/diagnostics/#citry.template.invalid-attribute-value',
                                            'examples': [{'language': 'citry-html',
                                                          'source': '<div draggable="treu">Drag me</div>',
                                                          'title': 'A misspelled keyword'},
                                                         {'language': 'citry-html',
                                                          'source': '<input type="datetime" name="start">',
                                                          'title': 'An input type the browser does not know'}],
                                            'messages': {'default': "'{value}' is not a valid value for '{attribute}' "
                                                                    'on <{element}>. Valid values: {allowed}.',
                                                         'empty': "'{attribute}' on <{element}> needs a value. Valid "
                                                                  'values: {allowed}.',
                                                         'suggestion': "'{value}' is not a valid value for "
                                                                       "'{attribute}' on <{element}>. Did you mean "
                                                                       "'{suggestion}'? Valid values: {allowed}.",
                                                         'target': "'{value}' is not a valid value for '{attribute}' "
                                                                   "on <{element}>. A name that starts with '_' must "
                                                                   'be one of: {allowed}.'},
                                            'parameters': {'allowed': 'The valid values, quoted and separated by '
                                                                      'commas.',
                                                           'attribute': 'Attribute name as written in the template.',
                                                           'element': 'Element name as written in the template.',
                                                           'suggestion': 'The valid value closest to the written one.',
                                                           'value': 'Attribute value as written in the template.'},
                                            'summary': 'A static HTML attribute that accepts only a fixed set of '
                                                       'keywords, such as draggable or type, has a value outside that '
                                                       'set, so the browser ignores it or falls back to a default.',
                                            'surfaces': ['check', 'lsp'],
                                            'title': 'Invalid value for an enumerated HTML attribute',
                                            'when': 'A plain HTML element has an attribute with a fixed set of '
                                                    'keywords in the HTML Standard, such as draggable, dir, hidden, '
                                                    'contenteditable, type on input, button, ol, or li, method on '
                                                    'form, loading, or crossorigin, and its written value is not one '
                                                    'of them. Keywords compare without regard to ASCII letter case, '
                                                    'except type on ol and li, where "a" and "A" are different '
                                                    'markers. An attribute that allows the empty string, such as '
                                                    'hidden or crossorigin, may be written with no value. For target, '
                                                    'formtarget, and the name of an iframe or object, only a name that '
                                                    'starts with an underscore is checked, because any other name is a '
                                                    'valid window name. Bound values (c-*, :attr), component tags, '
                                                    '<c-element>, custom elements with a hyphen, and elements inside '
                                                    '<svg> or <math> are not checked, and neither are attributes such '
                                                    'as sandbox or rel that take a list of tokens.'},
 'citry.template.marker-name-invalid': {'code': 'citry.template.marker-name-invalid',
                                        'constant': 'TEMPLATE_MARKER_NAME_INVALID',
                                        'defaultSeverity': 'error',
                                        'documentationPath': '/ide/diagnostics/#citry.template.marker-name-invalid',
                                        'messages': {'dynamic': 'Marker name must be a static literal.',
                                                     'extra': 'Marker accepts only its name attribute.',
                                                     'invalid': 'Marker name must match [A-Za-z][A-Za-z0-9_-]*.',
                                                     'missing': 'Marker requires a literal name attribute.',
                                                     'named_fill': 'Marker accepts only its default slot.'},
                                        'parameters': {},
                                        'summary': 'A component marker must have one valid literal name and may '
                                                   'contain only default slot content.',
                                        'surfaces': ['check', 'lsp'],
                                        'title': 'Invalid component marker',
                                        'when': 'A literal marker omits its name, uses a dynamic or invalid name, adds '
                                                'an extra attribute, or declares a named fill.'},
 'citry.template.unknown-component': {'code': 'citry.template.unknown-component',
                                      'constant': 'TEMPLATE_UNKNOWN_COMPONENT',
                                      'defaultSeverity': 'error',
                                      'documentationPath': '/ide/diagnostics/#citry.template.unknown-component',
                                      'examples': [{'language': 'citry-html',
                                                    'source': '<c-missing-card />',
                                                    'title': 'Unregistered component tag'}],
                                      'messages': {'default': 'Component <{tag}> is not registered.'},
                                      'parameters': {'tag': 'Authored component tag, including the c- prefix.'},
                                      'summary': 'A component tag is not registered in the selected Citry registry.',
                                      'surfaces': ['check', 'lsp'],
                                      'title': 'Unknown component',
                                      'when': 'A template uses a component tag whose name is absent from the selected '
                                              'application or library registry.'},
 'citry.template.unknown-variable': {'code': 'citry.template.unknown-variable',
                                     'configurableSeverity': True,
                                     'constant': 'TEMPLATE_UNKNOWN_VARIABLE',
                                     'defaultSeverity': 'error',
                                     'documentationPath': '/ide/diagnostics/#citry.template.unknown-variable',
                                     'examples': [{'language': 'citry-html',
                                                   'source': '<p>{{ missing_name }}</p>',
                                                   'title': 'Unknown name in an interpolation'},
                                                  {'language': 'citry-html',
                                                   'source': '<div c-title="missing_name"></div>',
                                                   'title': 'Unknown name in a dynamic attribute'}],
                                     'messages': {'allow-extra': "Template variable '{name}' is not declared. It may "
                                                                 'be supplied dynamically.',
                                                  'closed': "Template variable '{name}' is not available in this "
                                                            'template.',
                                                  'unknown': "Template variable '{name}' is not declared. Citry could "
                                                             'not determine whether it is supplied dynamically.'},
                                     'parameters': {'name': 'Authored variable name.'},
                                     'summary': 'A parser-proven root variable is not declared by every component that '
                                                'consumes the template.',
                                     'surfaces': ['check', 'lsp'],
                                     'title': 'Unknown template variable',
                                     'when': 'A name used in an interpolation or Python-valued template attribute is '
                                             'absent from the proven template data, configured globals, and lint-only '
                                             'variables.'},
 'citry.vue.python-variable': {'code': 'citry.vue.python-variable',
                               'configurableSeverity': True,
                               'constant': 'VUE_PYTHON_VARIABLE',
                               'defaultSeverity': 'warning',
                               'documentationPath': '/ide/diagnostics/#citry.vue.python-variable',
                               'examples': [{'language': 'citry-html',
                                             'source': '<li c-for="item in items" :title="item"></li>',
                                             'title': 'Python loop variable in a Vue binding'}],
                               'messages': {'attribute': "Vue reads '{name}' from browser state, but '{name}' is a "
                                                         'Python variable here. Use c-{attribute}="{name}" to pass the '
                                                         'Python value.',
                                            'browser': "Vue reads the component's browser value '{name}' here, not the "
                                                       "Python loop or slot variable '{name}'. Pass the Python value "
                                                       'with a c- attribute, or rename one of them.',
                                            'browser-attribute': "Vue reads the component's browser value '{name}' "
                                                                 "here, not the Python loop or slot variable '{name}'. "
                                                                 'Use c-{attribute}="{name}" for the Python value, or '
                                                                 'rename one of them.',
                                            'default': "Vue reads '{name}' from browser state, but '{name}' is a "
                                                       'Python variable here. Pass its value with a c- attribute or '
                                                       "loop with Vue's v-for instead."},
                               'parameters': {'attribute': 'HTML attribute name that a c- attribute can set from '
                                                           'Python.',
                                              'name': 'Python variable name read by the Vue expression.'},
                               'summary': 'A Vue expression reads a Python loop or slot variable, which the browser '
                                          'never sees, so the value is missing or wrong.',
                               'surfaces': ['check', 'lsp'],
                               'title': 'Python variable read by a Vue expression',
                               'when': 'A Vue expression inside a c-for loop or a c-fill binding reads that Python '
                                       'variable and the name is not a Vue v-for or slot alias. This includes a name '
                                       "that the component's browser data also defines, where Vue shows the browser "
                                       "value instead of the loop value. When the component's browser data is fully "
                                       'known and lacks the name, citry.vue.unknown-variable reports the read instead, '
                                       'unless that rule is set to ignore.'},
 'citry.vue.unknown-variable': {'code': 'citry.vue.unknown-variable',
                                'configurableSeverity': True,
                                'constant': 'VUE_UNKNOWN_VARIABLE',
                                'defaultSeverity': 'error',
                                'documentationPath': '/ide/diagnostics/#citry.vue.unknown-variable',
                                'examples': [{'language': 'citry-html',
                                              'source': '<button :disabled="submitting1">Save</button>',
                                              'title': 'Unknown name in a Vue expression'}],
                                'messages': {'default': "Vue variable '{name}' is not available in this component.",
                                             'python': "Vue variable '{name}' is not available in this component. "
                                                       "'{name}' is a Python variable here, which the browser never "
                                                       "sees; pass its value with a c- attribute or loop with Vue's "
                                                       'v-for.'},
                                'parameters': {'name': 'Authored Vue variable name.'},
                                'summary': "A free identifier in a Vue expression is absent from the component's "
                                           'proven browser scope.',
                                'surfaces': ['check', 'lsp'],
                                'title': 'Unknown Vue variable',
                                'when': 'A Vue expression references a root that is not supplied by JsData, an '
                                        'enclosing v-for alias, a Vue or Citry helper, a browser global, or configured '
                                        'lint-only Vue variables.'}}

EXTERNAL_CODE_PREFIXES: Final = [{'prefix': 'citry.python.',
  'provider': 'ty',
  'summary': 'Python semantic diagnostics retained from the pinned ty analyzer. The suffix and message remain '
             'provider-owned.'},
 {'prefix': 'citry.typescript.',
  'provider': 'TypeScript',
  'summary': 'TypeScript errors in component JavaScript and Vue template expressions, such as a wrong argument type, '
             "an unknown member, or a wrong argument count. The suffix is TypeScript's own error number, such as "
             "ts2322, and the message is TypeScript's. Citry drops a TypeScript error that one of its own diagnostics "
             'already reports.'}]

# fmt: on
