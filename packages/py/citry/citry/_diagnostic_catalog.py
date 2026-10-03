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
I18N_RICH_MESSAGE_FALLBACK = 'citry.i18n.rich-message-fallback'
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
                                               'fix': 'Pass a value of the type the child declares, or change the '
                                                      "child's prop type.",
                                               'messages': {'default': "Vue prop '{name}' expects {expected}, but this "
                                                                       'binding is {actual}.'},
                                               'parameters': {'actual': 'Proven authored value type.',
                                                              'expected': "Child component's accepted Vue prop type.",
                                                              'name': 'Authored native Vue prop name.'},
                                               'summary': 'A Vue prop on a component tag gets a value of a type the '
                                                          'child component does not accept.',
                                               'surfaces': ['check', 'lsp'],
                                               'title': 'Incompatible Vue prop',
                                               'when': 'A :prop or v-bind:prop value on a component tag has a type '
                                                       'Citry knows, from a literal, JsData, or a loop binding, and '
                                                       "the child's declared Vue prop type does not accept it."},
 'citry.browser.invalid-state-binding-target': {'code': 'citry.browser.invalid-state-binding-target',
                                                'constant': 'BROWSER_INVALID_STATE_BINDING_TARGET',
                                                'defaultSeverity': 'error',
                                                'documentationPath': '/ide/diagnostics/#citry.browser.invalid-state-binding-target',
                                                'examples': [{'language': 'citry-html',
                                                              'source': '<head :c-query></head>',
                                                              'title': 'Binding on a non-control element'}],
                                                'fix': 'Bind a form control that holds a value, such as <input>, '
                                                       '<select>, or <textarea>. On a custom element, name its update '
                                                       'event with .on:<event>. To react to an event on another '
                                                       'element, use an @c-* binding instead.',
                                                'messages': {'default': '{detail}'},
                                                'parameters': {'detail': 'Explanation of the unsupported binding '
                                                                         'target.'},
                                                'summary': 'A :c-* State binding is on an element that has no value to '
                                                           'bind, such as a <div>, or an input type that cannot hold '
                                                           'one, such as a file input.',
                                                'surfaces': ['check', 'lsp'],
                                                'title': 'Invalid State binding target',
                                                'when': 'The element or input type cannot hold a bound value, or does '
                                                        "not support the binding's direction or update event."},
 'citry.browser.missing-component-prop': {'code': 'citry.browser.missing-component-prop',
                                          'constant': 'BROWSER_MISSING_COMPONENT_PROP',
                                          'defaultSeverity': 'error',
                                          'documentationPath': '/ide/diagnostics/#citry.browser.missing-component-prop',
                                          'examples': [{'language': 'citry-html',
                                                        'source': '<c-card />',
                                                        'title': 'Missing required prop'}],
                                          'fix': 'Pass the prop on the tag, such as :count="total".',
                                          'messages': {'default': "Required Vue prop '{name}' is missing for <{tag}>."},
                                          'parameters': {'name': 'Required child Vue prop name.',
                                                         'tag': 'Resolved native component tag.'},
                                          'summary': 'A component tag leaves out a Vue prop that the child component '
                                                     'marks as required.',
                                          'surfaces': ['check', 'lsp'],
                                          'title': 'Missing required Vue prop',
                                          'when': 'A registered <c-*> tag has no Vue binding for a prop the child '
                                                  'declares with required: true, and no spread binding could supply '
                                                  'it.'},
 'citry.browser.undeclared-component-event': {'code': 'citry.browser.undeclared-component-event',
                                              'constant': 'BROWSER_UNDECLARED_COMPONENT_EVENT',
                                              'defaultSeverity': 'warning',
                                              'documentationPath': '/ide/diagnostics/#citry.browser.undeclared-component-event',
                                              'examples': [{'language': 'citry-html',
                                                            'source': '<c-Lane @drop-tsak="moveTask($event)"></c-Lane>',
                                                            'title': 'Misspelled child event'}],
                                              'fix': "Correct the event name, or add it to the child's emits.",
                                              'messages': {'default': "Component '{component}' does not declare event "
                                                                      "'{name}' in its emits option."},
                                              'parameters': {'component': 'Component tag, lowercased, including the c- '
                                                                          'prefix.',
                                                             'name': 'Authored event name.'},
                                              'summary': 'A template listens on a child component for an event the '
                                                         'child does not declare, often because of a typo. The '
                                                         'listener usually never runs.',
                                              'surfaces': ['check', 'lsp'],
                                              'title': 'Listener for an event the child component does not declare',
                                              'when': 'An @name or v-on:name listener on a component tag names an '
                                                      "event that the child's emits does not list and no on<Event> "
                                                      "prop accepts. Vue then passes the listener to the child's root "
                                                      'element, where it runs only for a DOM event of that name. Only '
                                                      'names with a hyphen, a colon, or an uppercase letter are '
                                                      'reported, because a plain lowercase name such as click is '
                                                      "usually a DOM event. Citry checks only when the child's emits "
                                                      'is an array of strings or an object with plain keys.'},
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
                                   'fix': 'Correct the event name, or add it to emits.',
                                   'messages': {'default': "Event '{name}' is not declared in this component's emits "
                                                           'option.'},
                                   'parameters': {'name': 'Authored event name.'},
                                   'summary': "Browser code emits a Vue event that the component's emits option does "
                                              'not list, often because of a typo. Parents listening for the declared '
                                              'name never hear it.',
                                   'surfaces': ['check', 'lsp'],
                                   'title': 'Undeclared emitted event',
                                   'when': "this.$emit, component.$emit, or $emit in the component's template uses a "
                                           'name that emits does not list and no on<Event> prop declares. Citry checks '
                                           'only when emits is an array of strings or an object with plain keys. A '
                                           'component without emits may emit any name, as in Vue.'},
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
                                                      'source': '<span v-show="$loading(\'missing\')">Saving</span>',
                                                      'title': 'Unknown loading handler'}],
                                        'fix': 'Correct the name, or add a public method with that name to the '
                                               "component's Events class.",
                                        'messages': {'default': "Server event '{name}' is not declared by this "
                                                                'component.'},
                                        'parameters': {'name': 'Authored server-event wire name.'},
                                        'summary': 'Browser code names a server event that the component has no '
                                                   'handler for, often because of a typo.',
                                        'surfaces': ['check', 'lsp'],
                                        'title': 'Unknown server event',
                                        'when': 'A template or component JavaScript calls sendEvent, $sendEvent, '
                                                '$loading, or $error with a string that names no handler, or an @c-* '
                                                'binding names no handler.'},
 'citry.browser.unknown-state-field': {'code': 'citry.browser.unknown-state-field',
                                       'constant': 'BROWSER_UNKNOWN_STATE_FIELD',
                                       'defaultSeverity': 'error',
                                       'documentationPath': '/ide/diagnostics/#citry.browser.unknown-state-field',
                                       'examples': [{'language': 'citry-html',
                                                     'source': '<input :c-missing_field.debounce="refresh">',
                                                     'title': 'Unknown field in a State binding'}],
                                       'fix': "Correct the field name, or add the field to the component's State "
                                              'class.',
                                       'messages': {'default': "State field '{name}' is not a public field of this "
                                                               'component.'},
                                       'parameters': {'name': 'Authored State field name, without prefix or '
                                                              'modifiers.'},
                                       'summary': "A :c-* State binding names a field the component's State does not "
                                                  'have, often because of a typo.',
                                       'surfaces': ['check', 'lsp'],
                                       'title': 'Unknown State binding field',
                                       'when': 'A :c-* binding names a field that is not a public field of the '
                                               "component's State class. Bindings whose component or State class Citry "
                                               'cannot determine are not checked.'},
 'citry.check.python-source-unreadable': {'code': 'citry.check.python-source-unreadable',
                                          'constant': 'CHECK_PYTHON_SOURCE_UNREADABLE',
                                          'defaultSeverity': 'error',
                                          'documentationPath': '/ide/diagnostics/#citry.check.python-source-unreadable',
                                          'fix': 'Fix the Python syntax error or encoding problem in the file the '
                                                 'message names.',
                                          'messages': {'default': 'Citry could not analyze this Python source: '
                                                                  '{detail}'},
                                          'parameters': {'detail': 'Python source failure detail.'},
                                          'summary': 'A Python file could not be read or parsed, so its components '
                                                     'were not checked.',
                                          'surfaces': ['check'],
                                          'title': 'Python source could not be analyzed',
                                          'when': 'citry check --static reaches a Python file it cannot read, decode, '
                                                  'or parse.'},
 'citry.check.template-declaration': {'code': 'citry.check.template-declaration',
                                      'constant': 'CHECK_TEMPLATE_DECLARATION',
                                      'defaultSeverity': 'error',
                                      'documentationPath': '/ide/diagnostics/#citry.check.template-declaration',
                                      'fix': 'Read the error in the message and fix the declaration or the code it '
                                             'runs.',
                                      'messages': {'default': "Citry could not inspect this component's template "
                                                              'declaration: {detail}'},
                                      'parameters': {'detail': 'Inspection failure detail.'},
                                      'summary': "citry check could not read a component's template or template_file, "
                                                 'for example because computing it raised an error.',
                                      'surfaces': ['check'],
                                      'title': 'Template declaration unavailable',
                                      'when': "Reading the component's template or template_file declaration raises an "
                                              'error, or Citry cannot tell which declaration applies.'},
 'citry.check.template-file-not-found': {'code': 'citry.check.template-file-not-found',
                                         'constant': 'CHECK_TEMPLATE_FILE_NOT_FOUND',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.check.template-file-not-found',
                                         'examples': [{'language': 'citry',
                                                       'source': 'class Card(Component):\n'
                                                                 '    template_file = "missing.html"',
                                                       'title': 'Missing template file'}],
                                         'fix': 'Correct the path, or move the file to one of the searched locations '
                                                'the message lists.',
                                         'messages': {'default': "Template file '{path}' was not found. Searched: "
                                                                 '{locations}.'},
                                         'parameters': {'locations': 'Locations searched by Citry.',
                                                        'path': 'Authored template_file value.'},
                                         'summary': 'The file named in template_file does not exist in any place Citry '
                                                    'looks.',
                                         'surfaces': ['check'],
                                         'title': 'Template file not found',
                                         'when': "template_file points to a path that is not in the component's "
                                                 'directory or any configured template directory.'},
 'citry.check.template-file-unreadable': {'code': 'citry.check.template-file-unreadable',
                                          'constant': 'CHECK_TEMPLATE_FILE_UNREADABLE',
                                          'defaultSeverity': 'error',
                                          'documentationPath': '/ide/diagnostics/#citry.check.template-file-unreadable',
                                          'fix': "Check the file's permissions, and save it as UTF-8.",
                                          'messages': {'default': 'Citry could not read this template file: {detail}'},
                                          'parameters': {'detail': 'File-system or decoding failure detail.'},
                                          'summary': 'The template file exists, but Citry could not open it or read it '
                                                     'as UTF-8 text.',
                                          'surfaces': ['check'],
                                          'title': 'Template file could not be read',
                                          'when': 'Citry finds the template_file but cannot open it, or it is not '
                                                  'valid UTF-8.'},
 'citry.check.template-language-unsupported': {'code': 'citry.check.template-language-unsupported',
                                               'constant': 'CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED',
                                               'defaultSeverity': 'error',
                                               'documentationPath': '/ide/diagnostics/#citry.check.template-language-unsupported',
                                               'fix': 'Nothing to fix if the other language is intended. Check that '
                                                      "template with that language's own tools.",
                                               'messages': {'default': 'Citry cannot check template_lang with a {type} '
                                                                       'value. This template was skipped.'},
                                               'parameters': {'type': 'Runtime type of the non-None template_lang '
                                                                      'value.'},
                                               'summary': 'The component sets template_lang to another template '
                                                          'language. citry check reads only Citry templates, so it '
                                                          'skipped this one.',
                                               'surfaces': ['check'],
                                               'title': 'Unsupported template language',
                                               'when': "A component's template_lang is not None."},
 'citry.check.template-namespace-unavailable': {'code': 'citry.check.template-namespace-unavailable',
                                                'constant': 'CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE',
                                                'defaultSeverity': 'error',
                                                'documentationPath': '/ide/diagnostics/#citry.check.template-namespace-unavailable',
                                                'fix': 'Read the error in the message and fix the template data '
                                                       'declaration or the code it runs.',
                                                'messages': {'default': "Citry could not inspect this template's "
                                                                        'variables: {detail}'},
                                                'parameters': {'detail': 'Namespace inspection failure detail.'},
                                                'summary': 'citry check could not work out which variables a '
                                                           "component's template receives, so it cannot check them.",
                                                'surfaces': ['check'],
                                                'title': 'Template variables unavailable',
                                                'when': "Reading the component's declared or inferred template data "
                                                        'raises an error.'},
 'citry.check.template-value-invalid': {'code': 'citry.check.template-value-invalid',
                                        'constant': 'CHECK_TEMPLATE_VALUE_INVALID',
                                        'defaultSeverity': 'error',
                                        'documentationPath': '/ide/diagnostics/#citry.check.template-value-invalid',
                                        'examples': [{'language': 'citry',
                                                      'source': 'class Card(Component):\n'
                                                                '    template = build_template()',
                                                      'title': 'Non-string inline template'}],
                                        'fix': 'Set template to a string, or template_file to a string or Path.',
                                        'messages': {'file': 'Component.template_file must be a string or Path. This '
                                                             'template was skipped.',
                                                     'inline': 'Component.template must be a string. This template was '
                                                               'skipped.'},
                                        'parameters': {},
                                        'summary': "A component's template or template_file has a value of the wrong "
                                                   'type, so citry check skipped it.',
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
                                       'fix': 'Correct the name, or define it on the component. A plugin that adds a '
                                              'property to every component should give it a $ prefix, such as $api.',
                                       'messages': {'default': "Component instance member '{name}' is not defined by "
                                                               'this component.'},
                                       'parameters': {'name': 'Authored member name.'},
                                       'summary': 'Component JavaScript reads this.<name> or component.<name>, and the '
                                                  'component has no member with that name, often because of a typo. '
                                                  'The value is undefined in the browser.',
                                       'surfaces': ['check', 'lsp'],
                                       'title': 'Unknown component instance member',
                                       'when': 'The name is not a js_data() key, prop, data() key, setup binding, '
                                               'method, computed value, or injection. Citry checks only when it can '
                                               'see every js_data() key and every Vue Options section in the source. '
                                               'It skips names that start with $ or _, bracket reads such as '
                                               'component[key], and code that uses mixins, extends, Object.assign, a '
                                               'class, or computed member names.'},
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
                                         'fix': 'Declare or destructure the name, or read the value from the component '
                                                'instance. If a project script defines it as a global, declare it in '
                                                'component_js_globals, or change rule_unknown_component_js_variable.',
                                         'messages': {'default': "Component JavaScript variable '{name}' is not "
                                                                 'defined.'},
                                         'parameters': {'name': 'Authored JavaScript variable name.'},
                                         'summary': 'Code inside $component reads a name that is not declared there, '
                                                    'often a callback value you forgot to destructure. It fails in the '
                                                    'browser.',
                                         'surfaces': ['check', 'lsp'],
                                         'title': 'Unknown component JavaScript variable',
                                         'when': 'A name inside a $component initializer is not declared in that code, '
                                                 "destructured from the callback's argument, a JavaScript or browser "
                                                 'global, or a declared component_js_globals entry.'},
 'citry.csp.incompatible-browser-code': {'code': 'citry.csp.incompatible-browser-code',
                                         'configurableSeverity': True,
                                         'constant': 'CSP_INCOMPATIBLE_BROWSER_CODE',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.csp.incompatible-browser-code',
                                         'examples': [{'language': 'citry-html',
                                                       'source': '<button @click="items.map(item => '
                                                                 'item.id)">Save</button>',
                                                       'title': 'Move an arrow function into Component.js'}],
                                         'fix': "Move the logic into a method in the component's JavaScript and call "
                                                'that method from the template.',
                                         'messages': {'default': 'The configured browser security policy cannot accept '
                                                                 '{detail} here. Move complex logic to Component.js '
                                                                 'and call a component method from the template.'},
                                         'parameters': {'detail': 'The unsupported directive, host, token, or '
                                                                  'operation.'},
                                         'summary': 'Browser code in a template or asset is not allowed by the Content '
                                                    'Security Policy mode your application sets.',
                                         'surfaces': ['check', 'lsp'],
                                         'title': 'Browser code is incompatible with strict CSP',
                                         'when': 'The application sets security_csp to "warn" or "strict", and a '
                                                 'browser expression or asset does something that policy forbids.'},
 'citry.format.cancelled': {'code': 'citry.format.cancelled',
                            'constant': 'FORMAT_CANCELLED',
                            'defaultSeverity': 'information',
                            'documentationPath': '/ide/diagnostics/#citry.format.cancelled',
                            'fix': 'Nothing to fix. Run the format command again if needed.',
                            'messages': {'default': '{detail}'},
                            'parameters': {'detail': 'Cancellation explanation.'},
                            'summary': 'Formatting was cancelled before Citry applied it.',
                            'surfaces': ['vscode'],
                            'title': 'Formatting cancelled',
                            'when': 'The editor or you cancel a format request before Citry applies its edits.'},
 'citry.format.embedded-interpolation-unsupported': {'code': 'citry.format.embedded-interpolation-unsupported',
                                                     'constant': 'FORMAT_EMBEDDED_INTERPOLATION_UNSUPPORTED',
                                                     'defaultSeverity': 'warning',
                                                     'documentationPath': '/ide/diagnostics/#citry.format.embedded-interpolation-unsupported',
                                                     'examples': [{'language': 'citry-html',
                                                                   'source': '<script>\n'
                                                                             '  const title = "{{ title }}";\n'
                                                                             '</script>',
                                                                   'title': 'Citry interpolation inside JavaScript'}],
                                                     'fix': 'Pass the value through js_data() or css_data() instead of '
                                                            'interpolating it, or leave the region unformatted.',
                                                     'messages': {'default': '{detail}'},
                                                     'parameters': {'detail': 'Interpolation explanation.'},
                                                     'summary': 'A JavaScript or CSS region contains Citry '
                                                                'interpolation, such as {{ title }}, so it was left '
                                                                'unchanged.',
                                                     'surfaces': ['formatter', 'lsp', 'vscode'],
                                                     'title': 'Embedded interpolation unsupported',
                                                     'when': 'An embedded JavaScript or CSS region contains Citry '
                                                             'interpolation, which an external formatter cannot handle '
                                                             'safely.'},
 'citry.format.embedded-language-unsupported': {'code': 'citry.format.embedded-language-unsupported',
                                                'constant': 'FORMAT_EMBEDDED_LANGUAGE_UNSUPPORTED',
                                                'defaultSeverity': 'warning',
                                                'documentationPath': '/ide/diagnostics/#citry.format.embedded-language-unsupported',
                                                'fix': 'Nothing to fix. Format that region with its own tools.',
                                                'messages': {'default': '{detail}'},
                                                'parameters': {'detail': 'Unsupported language explanation.'},
                                                'summary': 'A <script> or <style> region declares a language Citry has '
                                                           'no formatter for, so it was left unchanged.',
                                                'surfaces': ['formatter', 'lsp', 'vscode'],
                                                'title': 'Embedded language unsupported',
                                                'when': 'An embedded script or style region declares a language that '
                                                        'no Citry formatter handles.'},
 'citry.format.embedded-suppressed': {'code': 'citry.format.embedded-suppressed',
                                      'constant': 'FORMAT_EMBEDDED_SUPPRESSED',
                                      'defaultSeverity': 'information',
                                      'documentationPath': '/ide/diagnostics/#citry.format.embedded-suppressed',
                                      'fix': 'Nothing to fix. Remove the directive if you want the region formatted.',
                                      'messages': {'default': '{detail}'},
                                      'parameters': {'detail': 'Suppression explanation.'},
                                      'summary': 'A fmt: off or fmt: skip comment kept a JavaScript or CSS region '
                                                 'unformatted, as requested.',
                                      'surfaces': ['formatter', 'lsp', 'vscode'],
                                      'title': 'Embedded formatting suppressed',
                                      'when': 'A fmt: off or fmt: skip directive covers an embedded JavaScript or CSS '
                                              'region.'},
 'citry.format.host-syntax': {'code': 'citry.format.host-syntax',
                              'constant': 'FORMAT_HOST_SYNTAX',
                              'defaultSeverity': 'error',
                              'documentationPath': '/ide/diagnostics/#citry.format.host-syntax',
                              'fix': 'Fix the Python syntax error, then format again.',
                              'messages': {'default': '{detail}'},
                              'parameters': {'detail': 'Python syntax explanation.'},
                              'summary': 'The Python file has a syntax error, so Citry could not find the component '
                                         'strings to format.',
                              'surfaces': ['formatter', 'lsp', 'vscode'],
                              'title': 'Invalid Python host syntax',
                              'when': 'A format command targets a Python file that is not valid Python.'},
 'citry.format.ineligible': {'code': 'citry.format.ineligible',
                             'constant': 'FORMAT_INELIGIBLE',
                             'defaultSeverity': 'error',
                             'documentationPath': '/ide/diagnostics/#citry.format.ineligible',
                             'fix': 'Place the cursor inside a template, js, or css string, or open the template file '
                                    'itself.',
                             'messages': {'default': '{detail}'},
                             'parameters': {'detail': 'Eligibility explanation.'},
                             'summary': 'The file or cursor position is not inside a Citry template, script, or style, '
                                        'so there is nothing to format.',
                             'surfaces': ['formatter', 'lsp', 'vscode'],
                             'title': 'Document is not eligible for formatting',
                             'when': 'Citry cannot tell that the document or cursor position belongs to a template, '
                                     'js, or css string, or a standalone Citry template.'},
 'citry.format.invariant': {'code': 'citry.format.invariant',
                            'constant': 'FORMAT_INVARIANT',
                            'defaultSeverity': 'error',
                            'documentationPath': '/ide/diagnostics/#citry.format.invariant',
                            'fix': 'The file is unchanged. Report the template and message as a Citry bug.',
                            'messages': {'default': '{detail}'},
                            'parameters': {'detail': 'Formatter-provided explanation.'},
                            'summary': "The formatter's own safety check failed, so it refused to change the file. "
                                       'Your template is not at fault.',
                            'surfaces': ['formatter', 'lsp', 'vscode'],
                            'title': 'Formatter safety check failed',
                            'when': "The formatted result fails one of Citry's safety checks, for example formatting "
                                    'it a second time would change it again.'},
 'citry.format.provider-invalid': {'code': 'citry.format.provider-invalid',
                                   'constant': 'FORMAT_PROVIDER_INVALID',
                                   'defaultSeverity': 'error',
                                   'documentationPath': '/ide/diagnostics/#citry.format.provider-invalid',
                                   'fix': 'The file is unchanged. Try another formatter for that language, or report '
                                          'the message.',
                                   'messages': {'default': '{detail}'},
                                   'parameters': {'detail': 'Provider validation failure detail.'},
                                   'summary': 'The JavaScript or CSS formatter returned a change that does not fit the '
                                              'code it was asked to format, so Citry discarded it.',
                                   'surfaces': ['formatter', 'lsp', 'vscode'],
                                   'title': 'Embedded formatter returned invalid output',
                                   'when': 'An external JavaScript or CSS formatter returns an edit outside the region '
                                           'Citry sent it.'},
 'citry.format.provider-unavailable': {'code': 'citry.format.provider-unavailable',
                                       'constant': 'FORMAT_PROVIDER_UNAVAILABLE',
                                       'defaultSeverity': 'warning',
                                       'documentationPath': '/ide/diagnostics/#citry.format.provider-unavailable',
                                       'fix': 'In VS Code, check that Prettier for VS Code is installed and enabled '
                                              'for the language, or disable it so Citry uses its own copy of Prettier.',
                                       'messages': {'default': '{detail}'},
                                       'parameters': {'detail': 'Provider availability detail.'},
                                       'summary': 'No JavaScript or CSS formatter answered, so that region was left '
                                                  'unchanged.',
                                       'surfaces': ['formatter', 'lsp', 'vscode'],
                                       'title': 'Embedded formatter unavailable',
                                       'when': 'Citry asks the editor to format embedded JavaScript or CSS, and no '
                                               'installed formatter returns an edit.'},
 'citry.format.stale-document': {'code': 'citry.format.stale-document',
                                 'constant': 'FORMAT_STALE_DOCUMENT',
                                 'defaultSeverity': 'error',
                                 'documentationPath': '/ide/diagnostics/#citry.format.stale-document',
                                 'fix': 'Run the format command again.',
                                 'messages': {'default': '{detail}'},
                                 'parameters': {'detail': 'Stale-document explanation.'},
                                 'summary': 'The document changed while Citry was formatting it, so the result was '
                                            'discarded.',
                                 'surfaces': ['lsp', 'vscode'],
                                 'title': 'Document changed during formatting',
                                 'when': 'The document changes after Citry prepares the edit and before the editor '
                                         'applies it.'},
 'citry.format.suppression': {'code': 'citry.format.suppression',
                              'constant': 'FORMAT_SUPPRESSION',
                              'defaultSeverity': 'error',
                              'documentationPath': '/ide/diagnostics/#citry.format.suppression',
                              'examples': [{'language': 'citry-html',
                                            'source': '{# fmt: on #}\n<div></div>',
                                            'title': 'Unmatched formatter enable directive'}],
                              'fix': 'Pair each fmt: off with a fmt: on in the same scope, or remove the stray '
                                     'directive.',
                              'messages': {'default': '{detail}'},
                              'parameters': {'detail': 'Formatter-provided explanation.'},
                              'summary': 'A fmt: on, fmt: off, or fmt: skip comment has no matching partner or sits '
                                         'where it cannot apply.',
                              'surfaces': ['formatter', 'lsp', 'vscode'],
                              'title': 'Invalid formatter directive',
                              'when': 'A formatter directive has no valid scope at the place it is written, such as a '
                                      'fmt: on without an earlier fmt: off.'},
 'citry.format.syntax': {'code': 'citry.format.syntax',
                         'constant': 'FORMAT_SYNTAX',
                         'defaultSeverity': 'error',
                         'documentationPath': '/ide/diagnostics/#citry.format.syntax',
                         'fix': 'Fix the syntax error, then format again.',
                         'messages': {'default': '{detail}'},
                         'parameters': {'detail': 'Formatter-provided explanation.'},
                         'summary': 'The template has a syntax error, so the formatter left it unchanged.',
                         'surfaces': ['formatter', 'lsp', 'vscode'],
                         'title': 'Invalid template syntax',
                         'when': 'A format command receives a template with a Citry syntax error.'},
 'citry.format.unsupported': {'code': 'citry.format.unsupported',
                              'constant': 'FORMAT_UNSUPPORTED',
                              'defaultSeverity': 'error',
                              'documentationPath': '/ide/diagnostics/#citry.format.unsupported',
                              'fix': 'Nothing to fix. Format that part by hand, or wrap it in fmt: off and fmt: on.',
                              'messages': {'default': '{detail}'},
                              'parameters': {'detail': 'Formatter-provided explanation.'},
                              'summary': 'The template is valid, but the formatter cannot rewrite this shape safely, '
                                         'so it left it unchanged.',
                              'surfaces': ['formatter', 'lsp', 'vscode'],
                              'title': 'Formatting shape unsupported',
                              'when': "The template's structure is outside what the formatter can rewrite."},
 'citry.i18n.argument-invalid': {'code': 'citry.i18n.argument-invalid',
                                 'constant': 'I18N_ARGUMENT_INVALID',
                                 'defaultSeverity': 'error',
                                 'documentationPath': '/ide/diagnostics/#citry.i18n.argument-invalid',
                                 'fix': "Match the arguments to the message's @param declarations, which hover shows, "
                                        'or correct the profile name.',
                                 'messages': {'default': '{detail}'},
                                 'parameters': {'detail': 'Argument-contract explanation.'},
                                 'summary': 'A translation call passes the wrong inputs: a missing, extra, or mistyped '
                                            'argument, an unknown format profile, or wrong <c-trans> values or fills.',
                                 'surfaces': ['check', 'lsp'],
                                 'title': 'Invalid i18n argument',
                                 'when': 'A literal i18n call or $c-tr binding is malformed, its message inputs do not '
                                         "match the message's @param declarations, it names an unknown formatter or "
                                         'parser profile, or a <c-trans> tag supplies the wrong values or fills.'},
 'citry.i18n.catalog-invalid': {'code': 'citry.i18n.catalog-invalid',
                                'constant': 'I18N_CATALOG_INVALID',
                                'defaultSeverity': 'error',
                                'documentationPath': '/ide/diagnostics/#citry.i18n.catalog-invalid',
                                'fix': 'Correct the Fluent source at the reported position. The message says what is '
                                       'wrong.',
                                'messages': {'default': '{detail}'},
                                'parameters': {'detail': 'Compiler-provided catalog error.'},
                                'summary': 'A messages block or Fluent catalog file has invalid Fluent syntax or '
                                           'another translation source mistake.',
                                'surfaces': ['check', 'lsp'],
                                'title': 'Invalid Fluent catalog source',
                                'when': 'A messages block or catalog file has invalid Fluent syntax, an unsupported '
                                        '@param type, or another source error.'},
 'citry.i18n.client-message-invalid': {'code': 'citry.i18n.client-message-invalid',
                                       'constant': 'I18N_CLIENT_MESSAGE_INVALID',
                                       'defaultSeverity': 'error',
                                       'documentationPath': '/ide/diagnostics/#citry.i18n.client-message-invalid',
                                       'fix': 'Correct the name in client_messages, or add the message.',
                                       'messages': {'default': '{detail}'},
                                       'parameters': {'detail': 'Client-message contract explanation.'},
                                       'summary': 'Component.I18n.client_messages names a message that does not exist, '
                                                  'so the browser cannot load it.',
                                       'surfaces': ['check'],
                                       'title': 'Unknown client i18n message',
                                       'when': 'Component.I18n.client_messages names a message ID that no component or '
                                               'configured catalog package defines.'},
 'citry.i18n.cross-language-fallback': {'code': 'citry.i18n.cross-language-fallback',
                                        'configurableSeverity': True,
                                        'constant': 'I18N_CROSS_LANGUAGE_FALLBACK',
                                        'defaultSeverity': 'warning',
                                        'documentationPath': '/ide/diagnostics/#citry.i18n.cross-language-fallback',
                                        'fix': 'Add the missing translations; the i18n coverage command lists them. To '
                                               'show fallback text with its own language, call self.i18n.resolve() and '
                                               "put its locale and direction on an element, as the i18n guide's "
                                               'Language direction and accessibility page shows. Set '
                                               'rule_i18n_cross_language_fallback to "error" to require complete '
                                               'translations, or to "ignore" to hide this warning.',
                                        'messages': {'default': '{detail}'},
                                        'parameters': {'detail': 'Fallback coverage explanation.'},
                                        'summary': 'A translation is missing for some locales, so this text appears in '
                                                   'another language there. The page still renders, but the text sits '
                                                   'inside an element marked with the requested language, so a screen '
                                                   'reader may read it with the wrong pronunciation.',
                                        'surfaces': ['check'],
                                        'title': 'Text from a fallback language',
                                        'when': 'A tr() call or self.i18n.tr() call with a literal message ID, or a '
                                                'message listed in Component.I18n.client_messages, has no translation '
                                                'in some selectable locale and resolves to another locale through the '
                                                "configured fallbacks or the message's source locale."},
 'citry.i18n.rich-message-fallback': {'code': 'citry.i18n.rich-message-fallback',
                                      'constant': 'I18N_RICH_MESSAGE_FALLBACK',
                                      'defaultSeverity': 'error',
                                      'documentationPath': '/ide/diagnostics/#citry.i18n.rich-message-fallback',
                                      'fix': 'Add a translation for each locale the finding lists. Plain text messages '
                                             'may fall back; only <c-trans> needs every translation.',
                                      'messages': {'default': '{detail}'},
                                      'parameters': {'detail': 'Fallback coverage explanation.'},
                                      'summary': 'A <c-trans> message has no translation in some locale. Rendering it '
                                                 'in that locale raises I18nRuntimeUnavailableError, because <c-trans> '
                                                 'adds no element that could mark text from a fallback language.',
                                      'surfaces': ['check'],
                                      'title': 'Rich message without a translation',
                                      'when': 'A <c-trans> tag names a message or attribute that has no translation in '
                                              'some selectable locale, so it would resolve to another locale through '
                                              "the configured fallbacks or the message's source locale."},
 'citry.i18n.unknown-message': {'code': 'citry.i18n.unknown-message',
                                'constant': 'I18N_UNKNOWN_MESSAGE',
                                'defaultSeverity': 'error',
                                'documentationPath': '/ide/diagnostics/#citry.i18n.unknown-message',
                                'fix': "Correct the message ID, or add the message to the component's messages or a "
                                       'catalog.',
                                'messages': {'default': '{detail}'},
                                'parameters': {'detail': 'Unknown-message explanation.'},
                                'summary': 'Code asks for a translation message that no catalog defines, often because '
                                           'of a typo in the message ID.',
                                'surfaces': ['check', 'lsp'],
                                'title': 'Unknown i18n message',
                                'when': 'A tr() call, <c-trans> tag, $c-tr binding, or browser bind() call with a '
                                        'literal ID names a message or attribute that no component or configured '
                                        'catalog package defines.'},
 'citry.js-data.public-name-collision': {'code': 'citry.js-data.public-name-collision',
                                         'constant': 'JS_DATA_PUBLIC_NAME_COLLISION',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.js-data.public-name-collision',
                                         'fix': 'Rename the JsData field, or rename the Vue Options entry it collides '
                                                'with.',
                                         'messages': {'conditional': "JsData field '{name}' conflicts with a reserved "
                                                                     'or component-defined public instance name when '
                                                                     'supplied.',
                                                      'default': "JsData field '{name}' conflicts with a reserved or "
                                                                 'component-defined public instance name.'},
                                         'parameters': {'name': 'JsData field name.'},
                                         'summary': 'A JsData field has the same name as something already on the '
                                                    'component instance in the browser, such as a prop, a method, or a '
                                                    'name Vue reserves.',
                                         'surfaces': ['lsp'],
                                         'title': 'JsData field conflicts with a public instance name',
                                         'when': 'A JsData field that Citry can see in the source uses a reserved '
                                                 'browser name or the name of a Vue Options entry, such as a prop, '
                                                 'method, or computed value.'},
 'citry.js-data.unsupported-type': {'code': 'citry.js-data.unsupported-type',
                                    'constant': 'JS_DATA_UNSUPPORTED_TYPE',
                                    'defaultSeverity': 'warning',
                                    'documentationPath': '/ide/diagnostics/#citry.js-data.unsupported-type',
                                    'examples': [{'language': 'citry',
                                                  'source': 'class Card(Component):\n'
                                                            '    class JsData:\n'
                                                            '        selected_ids: set[int]',
                                                  'title': 'Unsupported set value'}],
                                    'fix': 'Convert the value to JSON-friendly data in js_data(), such as a list, a '
                                           'string, or a dict of plain values, and change the JsData annotation to '
                                           'match.',
                                    'messages': {'default': "JsData field '{name}' is not a clean JSON value: "
                                                            '{detail}. Browser tooling will treat its type as '
                                                            'unknown.'},
                                    'parameters': {'detail': 'Why the value is not a clean JSON type.',
                                                   'name': 'JsData field name.'},
                                    'summary': 'A JsData field has a type that cannot be sent to the browser as JSON, '
                                               'such as a set or a date. Editor help treats the value as any.',
                                    'surfaces': ['check', 'lsp'],
                                    'title': 'JsData field is not a JSON type',
                                    'when': 'A declared or inferred JsData field has a type that strict JSON cannot '
                                            'carry, such as bytes, a set, a callable, a date or time, or a whole class '
                                            'instance.'},
 'citry.parse.configuration': {'code': 'citry.parse.configuration',
                               'constant': 'PARSE_CONFIGURATION',
                               'defaultSeverity': 'error',
                               'documentationPath': '/ide/diagnostics/#citry.parse.configuration',
                               'fix': 'Read the message for the rule that failed, and fix the application or extension '
                                      'that defines it.',
                               'messages': {'default': '{detail}'},
                               'parameters': {'detail': 'Configuration failure detail.'},
                               'summary': 'Citry could not set up the template parser for your application, so it '
                                          'cannot check this template.',
                               'surfaces': ['check', 'lsp'],
                               'title': 'Template parser setup failed',
                               'when': 'The tag rules that your application or its extensions add to the parser cannot '
                                       'be built or applied.'},
 'citry.parse.syntax': {'code': 'citry.parse.syntax',
                        'constant': 'PARSE_SYNTAX',
                        'defaultSeverity': 'error',
                        'documentationPath': '/ide/diagnostics/#citry.parse.syntax',
                        'examples': [{'language': 'citry-html',
                                      'source': '<section>\n  <p>Hello</p>',
                                      'title': 'Unclosed element'}],
                        'fix': 'Correct the template at the reported position. The message says what the parser '
                               'expected there.',
                        'messages': {'default': '{detail}'},
                        'parameters': {'detail': 'Parser-provided explanation.'},
                        'summary': 'The template has a syntax mistake, such as an unclosed element or an unfinished '
                                   'expression. Citry cannot read the template, so it does not render.',
                        'surfaces': ['parser', 'formatter', 'check', 'lsp'],
                        'title': 'Invalid template syntax',
                        'when': 'The parser finds malformed markup, an incomplete expression, or another syntax error. '
                                'Only the first syntax error in a template is reported.'},
 'citry.parse.value': {'code': 'citry.parse.value',
                       'constant': 'PARSE_VALUE',
                       'defaultSeverity': 'error',
                       'documentationPath': '/ide/diagnostics/#citry.parse.value',
                       'fix': 'If an extension adds its own template syntax, update it or report the message to its '
                              'authors. Otherwise, report the message as a Citry bug.',
                       'messages': {'default': '{detail}'},
                       'parameters': {'detail': 'Parser-provided explanation.'},
                       'summary': 'Citry was given a value it cannot parse as a template. This is usually not a '
                                  'mistake in your template text.',
                       'surfaces': ['parser', 'formatter', 'check', 'lsp'],
                       'title': 'Invalid template value',
                       'when': 'A parser API receives a value it cannot turn into template source, for example when an '
                               'extension that adds its own template syntax reports positions that do not fit the '
                               'template.'},
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
                                     'fix': 'Move the state into js_data() or $component, and write the listener in '
                                            'its Vue form, such as @click. If another library on the page reads x-* '
                                            'attributes, set rule_alpine_attribute to "ignore".',
                                     'messages': {'default': "'{name}' is an Alpine attribute. Citry uses Vue, so "
                                                             'nothing reads it. Replace it with its Vue form, or set '
                                                             "rule_alpine_attribute to 'ignore' if a library on the "
                                                             "page reads '{name}'."},
                                     'parameters': {'name': 'Attribute name as written in the template.'},
                                     'summary': 'An HTML element still has an Alpine x-* attribute, such as x-data or '
                                                'x-on:click. Citry uses Vue, so nothing reads it and it does nothing.',
                                     'surfaces': ['check', 'lsp'],
                                     'title': 'Alpine attribute on an HTML element',
                                     'when': 'An Alpine directive name, such as x-data, x-on:click, or x-intersect, '
                                             'sits on an HTML element or <c-element>, including inside nested '
                                             'templates. Other x-* names, such as x-webkit-airplay, are ordinary HTML. '
                                             'Component tags are not checked, because an x-* attribute there is a '
                                             'Python keyword argument. x-cloak is reported as '
                                             'citry.template.alpine-cloak.'},
 'citry.template.alpine-cloak': {'code': 'citry.template.alpine-cloak',
                                 'configurableSeverity': True,
                                 'constant': 'TEMPLATE_ALPINE_CLOAK',
                                 'defaultSeverity': 'error',
                                 'documentationPath': '/ide/diagnostics/#citry.template.alpine-cloak',
                                 'examples': [{'language': 'citry-html',
                                               'source': '<div x-cloak>{{ message }}</div>',
                                               'title': 'Leftover x-cloak'}],
                                 'fix': 'Delete x-cloak and its [x-cloak] CSS rule. The HTML from the server already '
                                        'shows the content.',
                                 'messages': {'default': "Nothing in Citry removes 'x-cloak', so a '[x-cloak]' CSS "
                                                         "rule keeps this element hidden. Delete 'x-cloak' and its "
                                                         "'[x-cloak]' rule; the server-rendered HTML already shows the "
                                                         'content.'},
                                 'parameters': {},
                                 'summary': 'An HTML element still has x-cloak. Nothing removes it, so a [x-cloak] CSS '
                                            'rule hides the element for good.',
                                 'surfaces': ['check', 'lsp'],
                                 'title': 'x-cloak hides an element for good',
                                 'when': 'x-cloak, in any letter case, sits on an HTML element or <c-element>, '
                                         'including inside nested templates. Component tags are not checked.'},
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
                                            'fix': 'Use one of the valid values the message lists. If a script on the '
                                                   'page reads its own values from the attribute, set '
                                                   'rule_invalid_attribute_value to "ignore" for that component.',
                                            'messages': {'default': "'{value}' is not a valid value for '{attribute}' "
                                                                    'on <{element}>. Valid values: {allowed}.',
                                                         'empty': "'{attribute}' on <{element}> needs a value. Valid "
                                                                  'values: {allowed}.',
                                                         'frame-name': "'{value}' is not a valid value for "
                                                                       "'{attribute}' on <{element}>. A frame name "
                                                                       "cannot start with '_'.",
                                                         'pragma': "'{value}' is not a pragma browsers act on in "
                                                                   "'{attribute}' on <{element}>. If it is an HTTP "
                                                                   'header, send it in the HTTP response instead. '
                                                                   'Valid values: {allowed}.',
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
                                            'summary': 'An HTML attribute that accepts only certain keywords, such as '
                                                       'draggable or type, has another value. The browser ignores it '
                                                       'or falls back to a default, with no error.',
                                            'surfaces': ['check', 'lsp'],
                                            'title': 'HTML attribute value the browser does not accept',
                                            'when': 'The value is not one of the keywords the HTML Standard lists for '
                                                    'that attribute on that element. Letter case does not matter, '
                                                    'except for list markers in type on <ol> and <li>. A Vue binding '
                                                    'whose value is one JavaScript string, such as :dir="\'rtl\'", is '
                                                    'checked too. Other bound values, component tags, <c-element>, '
                                                    'custom elements, elements inside <svg> or <math>, and attributes '
                                                    'that take a list of words, such as rel, are not checked.'},
 'citry.template.marker-name-invalid': {'code': 'citry.template.marker-name-invalid',
                                        'constant': 'TEMPLATE_MARKER_NAME_INVALID',
                                        'defaultSeverity': 'error',
                                        'documentationPath': '/ide/diagnostics/#citry.template.marker-name-invalid',
                                        'fix': 'Give the marker one literal name that starts with a letter and '
                                               'contains only letters, digits, _ or -. Remove other attributes and '
                                               'named fills.',
                                        'messages': {'dynamic': 'Marker name must be a static literal.',
                                                     'extra': 'Marker accepts only its name attribute.',
                                                     'invalid': 'Marker name must match [A-Za-z][A-Za-z0-9_-]*.',
                                                     'missing': 'Marker requires a literal name attribute.',
                                                     'named_fill': 'Marker accepts only its default slot.'},
                                        'parameters': {},
                                        'summary': 'A <c-mark> tag, which marks part of a component that an event '
                                                   'handler can replace, has no usable name, an extra attribute, or '
                                                   'content it does not accept.',
                                        'surfaces': ['check', 'lsp'],
                                        'title': 'Invalid <c-mark> tag',
                                        'when': 'A <c-mark> tag has no name attribute, a dynamic or invalid name, any '
                                                'other attribute, or a named fill.'},
 'citry.template.unknown-component': {'code': 'citry.template.unknown-component',
                                      'constant': 'TEMPLATE_UNKNOWN_COMPONENT',
                                      'defaultSeverity': 'error',
                                      'documentationPath': '/ide/diagnostics/#citry.template.unknown-component',
                                      'examples': [{'language': 'citry-html',
                                                    'source': '<c-missing-card />',
                                                    'title': 'Unregistered component tag'}],
                                      'fix': 'Correct the tag name, or register the component with the application '
                                             'that Citry loaded.',
                                      'messages': {'default': 'Component <{tag}> is not registered.'},
                                      'parameters': {'tag': 'Authored component tag, including the c- prefix.'},
                                      'summary': 'A component tag names a component that your application does not '
                                                 'register, often because of a typo. The template fails to render.',
                                      'surfaces': ['check', 'lsp'],
                                      'title': 'Unknown component',
                                      'when': 'A <c-*> tag names no component in the selected application or library, '
                                              'counting built-in names and aliases.'},
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
                                     'fix': 'Correct the name, or add it to the data that template_data() returns. If '
                                            'another integration provides it, declare it in template_variables, or '
                                            'change rule_unknown_template_variable.',
                                     'messages': {'allow-extra': "Template variable '{name}' is not declared. It may "
                                                                 'be supplied dynamically.',
                                                  'closed': "Template variable '{name}' is not available in this "
                                                            'template.',
                                                  'unknown': "Template variable '{name}' is not declared. Citry could "
                                                             'not determine whether it is supplied dynamically.'},
                                     'parameters': {'name': 'Authored variable name.'},
                                     'summary': 'A template reads a variable that nothing provides, often because of a '
                                                'typo. Rendering then fails with a KeyError.',
                                     'surfaces': ['check', 'lsp'],
                                     'title': 'Unknown template variable',
                                     'when': "A name in {{ ... }} or in a c-* attribute is not in the component's "
                                             'template data, a c-for or c-fill binding around it, template_globals, or '
                                             'the declared template_variables. In a template that several components '
                                             'share, every one of them must provide the name.'},
 'citry.vue.python-variable': {'code': 'citry.vue.python-variable',
                               'configurableSeverity': True,
                               'constant': 'VUE_PYTHON_VARIABLE',
                               'defaultSeverity': 'warning',
                               'documentationPath': '/ide/diagnostics/#citry.vue.python-variable',
                               'examples': [{'language': 'citry-html',
                                             'source': '<li c-for="item in items" :title="item"></li>',
                                             'title': 'Python loop variable in a Vue binding'}],
                               'fix': 'Pass the Python value with a c- attribute, such as c-title="item" instead of '
                                      ':title="item", or loop with Vue\'s v-for. If a browser value has the same name, '
                                      'rename one of them.',
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
                               'summary': 'A Vue expression reads a Python c-for or c-fill variable. The browser never '
                                          'sees that variable, so the value is missing, or Vue shows a different '
                                          'browser value with the same name.',
                               'surfaces': ['check', 'lsp'],
                               'title': 'Python variable read by a Vue expression',
                               'when': 'A Vue expression inside a c-for loop or c-fill binding reads the Python '
                                       'variable, and no Vue v-for or slot alias of that name is around it. When Citry '
                                       'knows every name the component sends to the browser and the name is not among '
                                       'them, it reports citry.vue.unknown-variable instead, unless that rule is set '
                                       'to ignore.'},
 'citry.vue.unknown-variable': {'code': 'citry.vue.unknown-variable',
                                'configurableSeverity': True,
                                'constant': 'VUE_UNKNOWN_VARIABLE',
                                'defaultSeverity': 'error',
                                'documentationPath': '/ide/diagnostics/#citry.vue.unknown-variable',
                                'examples': [{'language': 'citry-html',
                                              'source': '<button :disabled="submitting1">Save</button>',
                                              'title': 'Unknown name in a Vue expression'}],
                                'fix': 'Correct the name, or send the value from js_data(). If it is a Python '
                                       'variable, pass it with a c- attribute instead. Declare names that come from '
                                       'outside Citry in vue_variables, or change rule_unknown_vue_variable.',
                                'messages': {'default': "Vue variable '{name}' is not available in this component.",
                                             'python': "Vue variable '{name}' is not available in this component. "
                                                       "'{name}' is a Python variable here, which the browser never "
                                                       "sees; pass its value with a c- attribute or loop with Vue's "
                                                       'v-for.'},
                                'parameters': {'name': 'Authored Vue variable name.'},
                                'summary': 'A Vue expression reads a name the component does not send to the browser, '
                                           'often because of a typo. Vue shows nothing, or the expression fails in the '
                                           'browser.',
                                'surfaces': ['check', 'lsp'],
                                'title': 'Unknown Vue variable',
                                'when': 'A name in a Vue expression is not a JsData or js_data() key, a v-for or slot '
                                        'alias around it, a Vue or Citry helper, a browser global, or a declared '
                                        'vue_variables entry.'}}

EXTERNAL_CODE_PREFIXES: Final = [{'prefix': 'citry.python.',
  'provider': 'ty',
  'summary': 'Python type errors in template expressions and c-* values, such as a value of the wrong type for a '
             'component input. They come from ty, the Python type checker Citry runs. The part after citry.python. is '
             "ty's rule name, and the message is ty's."},
 {'prefix': 'citry.typescript.',
  'provider': 'TypeScript',
  'summary': 'TypeScript errors in component JavaScript and Vue expressions, such as a wrong argument type, an unknown '
             "member, or a wrong number of arguments. The part after citry.typescript. is TypeScript's error number, "
             "such as ts2322, and the message is TypeScript's. When one of Citry's own diagnostics already reports the "
             'same mistake, Citry shows only its own.'}]

# fmt: on
