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
TEMPLATE_MISSPELLED_DIRECTIVE = 'citry.template.misspelled-directive'
TEMPLATE_MISSPELLED_ATTRIBUTE = 'citry.template.misspelled-attribute'
TEMPLATE_MISSPELLED_ELEMENT = 'citry.template.misspelled-element'
TEMPLATE_UNKNOWN_ARIA_ATTRIBUTE = 'citry.template.unknown-aria-attribute'
TEMPLATE_INVALID_NESTING = 'citry.template.invalid-nesting'
TEMPLATE_DUPLICATE_ID = 'citry.template.duplicate-id'
TEMPLATE_MISSING_IMAGE_ALT = 'citry.template.missing-image-alt'
TEMPLATE_UNKNOWN_URL = 'citry.template.unknown-url'
TEMPLATE_UNKNOWN_INJECT_KEY = 'citry.template.unknown-inject-key'
JS_DATA_UNSUPPORTED_TYPE = 'citry.js-data.unsupported-type'
JS_DATA_PUBLIC_NAME_COLLISION = 'citry.js-data.public-name-collision'
CSS_MISSPELLED_VARIABLE = 'citry.css.misspelled-variable'
CSS_MISSPELLED_CLASS = 'citry.css.misspelled-class'
CSS_UNDECLARED_CLASS = 'citry.css.undeclared-class'
CSS_UNDECLARED_VARIABLE = 'citry.css.undeclared-variable'
VUE_UNKNOWN_VARIABLE = 'citry.vue.unknown-variable'
VUE_PYTHON_VARIABLE = 'citry.vue.python-variable'
VUE_INVALID_EXPRESSION = 'citry.vue.invalid-expression'
VUE_COMPILE_ERROR = 'citry.vue.compile-error'
VUE_MISSPELLED_EVENT = 'citry.vue.misspelled-event'
COMPONENT_JS_UNKNOWN_VARIABLE = 'citry.component-js.unknown-variable'
COMPONENT_JS_UNKNOWN_MEMBER = 'citry.component-js.unknown-member'
BROWSER_INVALID_STATE_BINDING_TARGET = 'citry.browser.invalid-state-binding-target'
BROWSER_INVALID_MODEL_TARGET = 'citry.browser.invalid-model-target'
BROWSER_UNKNOWN_STATE_FIELD = 'citry.browser.unknown-state-field'
BROWSER_UNKNOWN_SERVER_EVENT = 'citry.browser.unknown-server-event'
BROWSER_UNDECLARED_EMIT = 'citry.browser.undeclared-emit'
BROWSER_UNDECLARED_COMPONENT_EVENT = 'citry.browser.undeclared-component-event'
BROWSER_MISSING_COMPONENT_PROP = 'citry.browser.missing-component-prop'
BROWSER_INCOMPATIBLE_COMPONENT_PROP = 'citry.browser.incompatible-component-prop'
BROWSER_MISSING_COMPONENT_KEY = 'citry.browser.missing-component-key'
BROWSER_PROP_ASSIGNMENT = 'citry.browser.prop-assignment'
BROWSER_UNKNOWN_SERVER_EVENT_FIELD = 'citry.browser.unknown-server-event-field'
BROWSER_UNKNOWN_FORM_FIELD = 'citry.browser.unknown-form-field'
BROWSER_MISSING_FORM_FIELD = 'citry.browser.missing-form-field'
BROWSER_MISSING_SERVER_EVENT_FIELD = 'citry.browser.missing-server-event-field'
BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD = 'citry.browser.incompatible-server-event-field'
CHECK_TEMPLATE_DECLARATION = 'citry.check.template-declaration'
CHECK_TEMPLATE_LANGUAGE_UNSUPPORTED = 'citry.check.template-language-unsupported'
CHECK_TEMPLATE_VALUE_INVALID = 'citry.check.template-value-invalid'
CHECK_TEMPLATE_FILE_NOT_FOUND = 'citry.check.template-file-not-found'
CHECK_TEMPLATE_FILE_UNREADABLE = 'citry.check.template-file-unreadable'
CHECK_TEMPLATE_NAMESPACE_UNAVAILABLE = 'citry.check.template-namespace-unavailable'
CHECK_TEMPLATE_NOT_CHECKED = 'citry.check.template-not-checked'
CHECK_URL_CHECKER_MISSING = 'citry.check.url-checker-missing'
CHECK_URL_CHECKER_FAILED = 'citry.check.url-checker-failed'
CHECK_PYTHON_SOURCE_UNREADABLE = 'citry.check.python-source-unreadable'
I18N_CATALOG_INVALID = 'citry.i18n.catalog-invalid'
I18N_UNKNOWN_MESSAGE = 'citry.i18n.unknown-message'
I18N_ARGUMENT_INVALID = 'citry.i18n.argument-invalid'
I18N_MISSING_PARAM_TYPE = 'citry.i18n.missing-param-type'
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
                                                             'title': 'Wrong literal type'},
                                                            {'language': 'citry-html',
                                                             'source': '<c-status :open="open ? \'open\' : \'closed\'" '
                                                                       '/>',
                                                             'title': 'A string for a Boolean prop'}],
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
                                                       'Citry knows, from a literal, a condition whose two results are '
                                                       "literals, JsData, or a loop binding, and the child's declared "
                                                       'Vue prop type does not accept it. For a Boolean prop, Vue '
                                                       "turns the string '' and the prop's own name, hyphenated, into "
                                                       'true, so any other string literal is reported.'},
 'citry.browser.incompatible-server-event-field': {'code': 'citry.browser.incompatible-server-event-field',
                                                   'configurableSeverity': True,
                                                   'constant': 'BROWSER_INCOMPATIBLE_SERVER_EVENT_FIELD',
                                                   'defaultSeverity': 'error',
                                                   'documentationPath': '/ide/diagnostics/#citry.browser.incompatible-server-event-field',
                                                   'examples': [{'language': 'citry-html',
                                                                 'source': '<button @c-click="save({amount: '
                                                                           '\'1\'})">Add</button>',
                                                                 'title': 'A string for an int field'}],
                                                   'fix': 'Send a value of the type the field declares, such as 1 '
                                                          "instead of '1'.",
                                                   'messages': {'default': "Server event '{event}' rejects this value "
                                                                           "for field '{name}': {detail}"},
                                                   'parameters': {'detail': "The server's message for this value.",
                                                                  'event': "The server event's name.",
                                                                  'name': "The field's name."},
                                                   'summary': 'An @c-* binding sends a literal value that the '
                                                              "handler's data class does not accept for that field. "
                                                              'The server rejects the call, and the handler does not '
                                                              'run.',
                                                   'surfaces': ['check', 'lsp'],
                                                   'title': 'Wrong type for a server event field',
                                                   'when': 'A key in the object literal of an @c-* binding has a '
                                                           "literal value, such as '1', true, 2.5, or null, or a "
                                                           "condition whose two results are literals, and the server's "
                                                           'check for that field rejects it. The browser sends the '
                                                           'arguments as JSON, which the server checks strictly: a '
                                                           'string is not turned into a number. For a handler that '
                                                           'accepts GET, the browser may send them as a query string '
                                                           'instead, which the server reads as text, so a value is '
                                                           'reported only when both ways fail. Values that are not '
                                                           'literals are not checked. A Pydantic data class is not '
                                                           'checked, because Pydantic converts values. When several '
                                                           'components share the template, it is checked only when '
                                                           'they use the same data class for the handler. citry check '
                                                           'needs your application for this rule, and the editor '
                                                           'reports it once it has loaded your application.'},
 'citry.browser.invalid-model-target': {'code': 'citry.browser.invalid-model-target',
                                        'configurableSeverity': True,
                                        'constant': 'BROWSER_INVALID_MODEL_TARGET',
                                        'defaultSeverity': 'error',
                                        'documentationPath': '/ide/diagnostics/#citry.browser.invalid-model-target',
                                        'examples': [{'language': 'citry-html',
                                                      'source': '<form v-model="query" @c-submit.prevent="search">\n'
                                                                '  <input type="search" name="q">\n'
                                                                '</form>',
                                                      'title': 'v-model on a form'}],
                                        'fix': 'Move v-model to the <input>, <textarea>, or <select> that holds the '
                                               'value. For a custom element, bind its value property and listen for '
                                               'its change event instead.',
                                        'messages': {'default': 'v-model does not work on <{tag}>, which holds no '
                                                                'value. Put it on an <input>, <textarea>, or <select>, '
                                                                'or on a component.'},
                                        'parameters': {'tag': 'Tag name as written in the template.'},
                                        'summary': 'v-model is on an element that has no value to bind, such as a '
                                                   '<form> or a <div>. The component fails to render when Citry '
                                                   'compiles it for Vue.',
                                        'surfaces': ['check', 'lsp'],
                                        'title': 'v-model on an element that holds no value',
                                        'when': 'v-model, with or without modifiers such as .lazy, is on an HTML '
                                                'element other than <input>, <textarea>, or <select>, or on a custom '
                                                'element such as <my-picker>. Component tags, PascalCase Vue '
                                                'components, and <c-element> are not reported, because they decide '
                                                'what v-model binds; neither is v-pre content, which Vue does not '
                                                'compile. citry check --static and an editor that has not loaded your '
                                                "application report it too, with the severity the component's own Lint "
                                                'class sets as a plain string.'},
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
 'citry.browser.missing-component-key': {'code': 'citry.browser.missing-component-key',
                                         'configurableSeverity': True,
                                         'constant': 'BROWSER_MISSING_COMPONENT_KEY',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.browser.missing-component-key',
                                         'examples': [{'language': 'citry-html',
                                                       'source': '<c-for each="project in projects">\n'
                                                                 '  <c-Card c-title="project.title" />\n'
                                                                 '</c-for>',
                                                       'title': 'A card per project'}],
                                         'fix': 'Add #c-key with a value that identifies each item and stays the same, '
                                                'such as #c-key="task.id".',
                                         'messages': {'default': '<{tag}> repeats inside <c-for> but has no #c-key. '
                                                                 'This page uses Vue, and the render fails when the '
                                                                 'loop has two items.'},
                                         'parameters': {'tag': 'Component tag as written in the template.'},
                                         'summary': 'A component that a <c-for> loop repeats has no #c-key, on a page '
                                                    'that uses Vue. The page fails to render as soon as the loop has '
                                                    'two items.',
                                         'surfaces': ['check'],
                                         'title': 'Repeated component without #c-key',
                                         'when': 'A registered component tag sits inside a <c-for> body, or carries '
                                                 "c-for itself, and has no #c-key. It is reported when the template's "
                                                 'component or the repeated component makes the page use Vue: it has '
                                                 'component JavaScript, js_data() or JsData, an Events class, or a Vue '
                                                 'attribute (v-*, @, or :) in its template. A transparent component '
                                                 'and a simple=True component are not reported, because they render '
                                                 "into their caller's HTML. Another component on the same page can "
                                                 'also make it use Vue, which this check cannot see. citry check needs '
                                                 'your application for this rule.'},
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
 'citry.browser.missing-form-field': {'code': 'citry.browser.missing-form-field',
                                      'configurableSeverity': True,
                                      'constant': 'BROWSER_MISSING_FORM_FIELD',
                                      'defaultSeverity': 'error',
                                      'documentationPath': '/ide/diagnostics/#citry.browser.missing-form-field',
                                      'examples': [{'language': 'citry-html',
                                                    'source': '<form @c-submit.prevent="search">\n'
                                                              '  <button>Search</button>\n'
                                                              '</form>',
                                                    'title': 'A form without the required control'}],
                                      'fix': 'Add a control with that name, or give the field a default in the '
                                             "handler's data class.",
                                      'messages': {'default': "Server event '{event}' requires field '{name}', but no "
                                                              'control in this form has that name, so the server '
                                                              'rejects every submit.'},
                                      'parameters': {'event': "The server event's name.",
                                                     'name': "The required field's name."},
                                      'summary': 'A form sends its fields to a server event, but none of its controls '
                                                 "is named after a field that the handler's data class requires. The "
                                                 'server rejects every submit, and the handler does not run.',
                                      'surfaces': ['check', 'lsp'],
                                      'title': 'Missing form field',
                                      'when': 'A <form> has an @c-submit binding that writes no arguments, such as '
                                              '@c-submit.prevent="search" or search(), so the browser sends the '
                                              "form's named controls, as a post without JavaScript does. No <input>, "
                                              '<select>, <textarea>, or <button> in the form has the name of a field '
                                              'without a default. The rule runs only when the template shows every '
                                              'name the form can send: the form has no id, which a control elsewhere '
                                              'could name in its form attribute, and it holds no component, custom '
                                              'element, slot, <template>, loop, v-html, #c-ignore content, attribute '
                                              'spread, or name written as an expression. A Pydantic data class is not '
                                              'checked, because Pydantic converts values and may read a field under '
                                              'another name. When several components share the template, it is checked '
                                              'only when they use the same data class for the handler. citry check '
                                              'needs your application for this rule, and the editor reports it once it '
                                              'has loaded your application.'},
 'citry.browser.missing-server-event-field': {'code': 'citry.browser.missing-server-event-field',
                                              'configurableSeverity': True,
                                              'constant': 'BROWSER_MISSING_SERVER_EVENT_FIELD',
                                              'defaultSeverity': 'error',
                                              'documentationPath': '/ide/diagnostics/#citry.browser.missing-server-event-field',
                                              'examples': [{'language': 'citry-html',
                                                            'source': '<button @c-click="save()">Add</button>',
                                                            'title': 'No arguments for a required field'}],
                                              'fix': "Send the field, or give it a default in the handler's data "
                                                     'class.',
                                              'messages': {'default': "Server event '{event}' requires field '{name}', "
                                                                      'which this call does not send, so the server '
                                                                      'rejects it.'},
                                              'parameters': {'event': "The server event's name.",
                                                             'name': "The required field's name."},
                                              'summary': 'An @c-* binding calls a server event without a field that '
                                                         "the handler's data class requires. The server rejects the "
                                                         'call, and the handler does not run.',
                                              'surfaces': ['check', 'lsp'],
                                              'title': 'Missing server event field',
                                              'when': 'The arguments of an @c-* binding are an object literal with no '
                                                      '... spread and no computed key, and they leave out a field that '
                                                      'has no default; or the binding sends no arguments, as in save '
                                                      'or save(), from an element that cannot contain a form, such as '
                                                      'a button. A binding with no arguments on a <form>, or for the '
                                                      'submit event, is not reported here, because the browser then '
                                                      "sends the form's fields; citry.browser.missing-form-field "
                                                      'checks those. A Pydantic data class is not checked. When '
                                                      'several components share the template, it is checked only when '
                                                      'they use the same data class for the handler. citry check needs '
                                                      'your application for this rule, and the editor reports it once '
                                                      'it has loaded your application.'},
 'citry.browser.prop-assignment': {'code': 'citry.browser.prop-assignment',
                                   'configurableSeverity': True,
                                   'constant': 'BROWSER_PROP_ASSIGNMENT',
                                   'defaultSeverity': 'error',
                                   'documentationPath': '/ide/diagnostics/#citry.browser.prop-assignment',
                                   'examples': [{'language': 'citry-html',
                                                 'source': '<button @click="open = false">Close</button>',
                                                 'title': 'Closing from the child'}],
                                   'fix': "Emit an event and let the parent change the value, as in $emit('close'), or "
                                          "copy the prop into the component's own data and change the copy.",
                                   'messages': {'default': "Prop '{name}' is read-only, so this assignment does not "
                                                           'change it. Emit an event to let the parent change it.',
                                                'v-model': "v-model writes to prop '{name}', which is read-only, so "
                                                           'the input cannot change it. Emit an event to let the '
                                                           'parent change it.'},
                                   'parameters': {'name': "The prop's name."},
                                   'summary': 'A component changes a prop it receives from its parent. Vue props are '
                                              'read-only, so the assignment does not change the value and Vue logs a '
                                              'warning instead.',
                                   'surfaces': ['check', 'lsp'],
                                   'title': 'Assignment to a Vue prop',
                                   'when': "In the component's own template, a Vue expression assigns to one of the "
                                           "component's declared props with =, +=, or another assignment operator, or "
                                           "with ++ or --, or binds it with v-model. In the component's JavaScript, it "
                                           'is reported for an assignment through this or the $component context, such '
                                           'as this.open = false. Citry finds the assignment by reading the text after '
                                           'the name, so the JavaScript check reports at most a warning. A write to a '
                                           'field of an object prop, such as open.count = 1, is not reported, and '
                                           'neither is a name that a v-for or slot binds. citry check needs your '
                                           'application for this rule, and the editor reports it once it has loaded '
                                           'your application.'},
 'citry.browser.undeclared-component-event': {'code': 'citry.browser.undeclared-component-event',
                                              'configurableSeverity': True,
                                              'constant': 'BROWSER_UNDECLARED_COMPONENT_EVENT',
                                              'defaultSeverity': 'warning',
                                              'documentationPath': '/ide/diagnostics/#citry.browser.undeclared-component-event',
                                              'examples': [{'language': 'citry-html',
                                                            'source': '<c-Lane @drop-tsak="moveTask($event)"></c-Lane>',
                                                            'title': 'Misspelled child event'},
                                                           {'language': 'citry-html',
                                                            'source': '<c-Card @hdie="hideCard"></c-Card>',
                                                            'title': 'A lowercase typo'}],
                                              'fix': "Correct the event name, or add it to the child's emits. It is a "
                                                     'warning by default; to make an undeclared listener fail citry '
                                                     'check, set rule_undeclared_component_event to "error".',
                                              'messages': {'default': "Component '{component}' does not declare event "
                                                                      "'{name}' in its emits option.",
                                                           'suggestion': "Component '{component}' does not declare "
                                                                         "event '{name}' in its emits option. Did you "
                                                                         "mean '{suggestion}'?"},
                                              'parameters': {'component': 'Component tag, lowercased, including the c- '
                                                                          'prefix.',
                                                             'name': 'Authored event name.',
                                                             'suggestion': 'The declared event closest to the written '
                                                                           'name.'},
                                              'summary': 'A template listens on a child component for an event the '
                                                         'child does not declare, often because of a typo. The '
                                                         'listener usually never runs.',
                                              'surfaces': ['check', 'lsp'],
                                              'title': 'Listener for an event the child component does not declare',
                                              'when': 'An @name or v-on:name listener on a component tag names an '
                                                      "event that the child's emits does not list and no on<Event> "
                                                      "prop accepts. Vue then passes the listener to the child's root "
                                                      'element, where it runs only for a DOM event of that name. A '
                                                      'plain lowercase name, such as hdie, is reported only when it is '
                                                      "not a DOM event that the HTML Standard or Vue's types list, "
                                                      "such as click. Citry checks only when the child's emits is an "
                                                      'array of strings or an object with plain keys. citry check '
                                                      'needs your application for this rule, and the editor reports it '
                                                      'once it has loaded your application.'},
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
 'citry.browser.unknown-form-field': {'code': 'citry.browser.unknown-form-field',
                                      'configurableSeverity': True,
                                      'constant': 'BROWSER_UNKNOWN_FORM_FIELD',
                                      'defaultSeverity': 'error',
                                      'documentationPath': '/ide/diagnostics/#citry.browser.unknown-form-field',
                                      'examples': [{'language': 'citry-html',
                                                    'source': '<form @c-submit.prevent="search">\n'
                                                              '  <input name="qeury" />\n'
                                                              '</form>',
                                                    'title': "A typo in a control's name"}],
                                      'fix': "Correct the control's name, or add the field to the handler's data "
                                             'class.',
                                      'messages': {'default': "The form sends field '{name}', which server event "
                                                              "'{event}' does not declare, so the server rejects the "
                                                              'submit.',
                                                   'no-data': "The form sends field '{name}', but server event "
                                                              "'{event}' takes no data, so the server rejects the "
                                                              'submit.',
                                                   'suggestion': "The form sends field '{name}', which server event "
                                                                 "'{event}' does not declare, so the server rejects "
                                                                 "the submit. Did you mean '{suggestion}'?"},
                                      'parameters': {'event': "The server event's name.",
                                                     'name': "The control's name as written.",
                                                     'suggestion': 'The declared field one typing slip from the name.'},
                                      'summary': 'A form sends its fields to a server event, and one of its controls '
                                                 "has a name that the handler's data class does not declare. The "
                                                 'server rejects each submit that sends that control, and the handler '
                                                 'does not run.',
                                      'surfaces': ['check', 'lsp'],
                                      'title': 'Unknown form field',
                                      'when': 'A <form> has an @c-submit binding that writes no arguments, such as '
                                              '@c-submit.prevent="search" or search(), so the browser sends the '
                                              "form's named controls, as a post without JavaScript does. An <input>, "
                                              '<select>, <textarea>, or submit <button> in the form has a static name '
                                              "the handler's data class does not declare, or the handler takes no data "
                                              'parameter. A submit button sends its name only when it is the one that '
                                              'submits the form, and a checkbox only when it is checked. A control is '
                                              'not checked when the browser may not send it with this form or may send '
                                              'it under another name: it is disabled, by its own disabled attribute, a '
                                              'bound :disabled, or a disabled <fieldset>; it is tied to another form '
                                              'by its form attribute; it is a file input, a button that cannot submit, '
                                              'or a button whose click is prevented, as in @click.prevent; its type or '
                                              'name is written as an expression; or it has an attribute spread such as '
                                              'v-bind="attrs". An image input sends where it was clicked, as x and y, '
                                              'or name.x and name.y, so those names are checked instead of its name. '
                                              "Neither are the host's CSRF field names that the server removes before "
                                              'it checks the data class, by default csrfmiddlewaretoken. A Pydantic '
                                              'data class is not checked, because Pydantic converts values and may '
                                              'read a field under another name. When several components share the '
                                              'template, it is checked only when they use the same data class for the '
                                              'handler. citry check needs your application for this rule, and the '
                                              'editor reports it once it has loaded your application.'},
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
 'citry.browser.unknown-server-event-field': {'code': 'citry.browser.unknown-server-event-field',
                                              'configurableSeverity': True,
                                              'constant': 'BROWSER_UNKNOWN_SERVER_EVENT_FIELD',
                                              'defaultSeverity': 'error',
                                              'documentationPath': '/ide/diagnostics/#citry.browser.unknown-server-event-field',
                                              'examples': [{'language': 'citry-html',
                                                            'source': '<button @c-click="save({amont: '
                                                                      '1})">Add</button>',
                                                            'title': 'A typo in a field name'}],
                                              'fix': "Correct the key, or add the field to the handler's data class.",
                                              'messages': {'default': "Server event '{event}' has no field '{name}', "
                                                                      'so the server rejects this call.',
                                                           'no-data': "Server event '{event}' takes no data, so the "
                                                                      'server rejects this call because of field '
                                                                      "'{name}'.",
                                                           'suggestion': "Server event '{event}' has no field "
                                                                         "'{name}', so the server rejects this call. "
                                                                         "Did you mean '{suggestion}'?"},
                                              'parameters': {'event': "The server event's name.",
                                                             'name': 'The key as written.',
                                                             'suggestion': 'The declared field one typing slip from '
                                                                           'the key.'},
                                              'summary': 'An @c-* binding sends an object with a key that the '
                                                         "handler's data class does not declare. The server rejects "
                                                         'the call, and the handler does not run.',
                                              'surfaces': ['check', 'lsp'],
                                              'title': 'Unknown server event field',
                                              'when': 'The arguments of an @c-* binding, such as '
                                                      '@c-click="save({amont: 1})", are an object literal with a key '
                                                      "the handler's data class does not declare, or the handler takes "
                                                      'no data parameter. A key written next to a ... spread is still '
                                                      'checked. A Pydantic data class is not checked, because Pydantic '
                                                      'may ignore extra keys or read a field under another name. When '
                                                      'several components share the template, it is checked only when '
                                                      'they use the same data class for the handler. citry check needs '
                                                      'your application for this rule, and the editor reports it once '
                                                      'it has loaded your application.'},
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
 'citry.check.template-not-checked': {'code': 'citry.check.template-not-checked',
                                      'constant': 'CHECK_TEMPLATE_NOT_CHECKED',
                                      'defaultSeverity': 'information',
                                      'documentationPath': '/ide/diagnostics/#citry.check.template-not-checked',
                                      'examples': [{'language': 'citry',
                                                    'source': 'from app.base import BaseCard\n'
                                                              '\n'
                                                              '\n'
                                                              'class Card(BaseCard):\n'
                                                              '    template = """\n'
                                                              '      <article>{{ title }}</article>\n'
                                                              '    """',
                                                    'title': 'A base class from another module'}],
                                      'fix': 'Nothing is wrong with the code. To check the template, load your '
                                             'application: run citry check with it, as in citry --app module:engine '
                                             'check, and give the editor the same module:engine path, in the citry.app '
                                             'setting in VS Code. For a class you added or renamed, the message stays '
                                             'until the editor loads the application again, which VS Code does when '
                                             'you save a Python file.',
                                      'messages': {'default': 'Citry cannot tell from this file that {component} is a '
                                                              'component, because it extends {base}, which comes from '
                                                              'another module, so this template is checked only when '
                                                              'Citry loads your application and finds {component} '
                                                              'there.'},
                                      'parameters': {'base': 'The imported class it extends, as written.',
                                                     'component': 'The class name.'},
                                      'summary': 'A class sets a template, but it extends a class from another module '
                                                 'of your project, so Citry cannot tell from the file alone that it is '
                                                 'a component. Its template is checked only when Citry loads your '
                                                 'application and finds the class there.',
                                      'surfaces': ['check', 'lsp'],
                                      'title': 'Template checked only with the application',
                                      'when': 'A class in a Python file sets template to a string literal that '
                                              'contains a tag, Citry cannot prove from that file that the class is a '
                                              'component, and it extends a class imported from a module of your '
                                              'project, directly or through a class defined in the same file. A class '
                                              'from an installed package does not count. citry check --static lists it '
                                              'as a note. The editor shows it as information on the class name while '
                                              'it has not loaded your application, and for a class added or renamed '
                                              'since it loaded the application. citry check with your application '
                                              'loaded, citry check --types, and an editor that has loaded the '
                                              'application find the class in the component registry and check its '
                                              'template, so they do not report it.'},
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
 'citry.check.url-checker-failed': {'code': 'citry.check.url-checker-failed',
                                    'constant': 'CHECK_URL_CHECKER_FAILED',
                                    'defaultSeverity': 'information',
                                    'documentationPath': '/ide/diagnostics/#citry.check.url-checker-failed',
                                    'fix': "Fix the error the message shows. It comes from your framework's routing "
                                           'code, such as a URL pattern module that fails to import. Until it is '
                                           'fixed, citry check skips those links.',
                                    'messages': {'default': "Citry skipped the link path '{path}', because asking your "
                                                            'web framework whether your app serves it raised an error: '
                                                            '{detail}',
                                                 'several': "Citry skipped {count} link paths, such as '{path}', "
                                                            'because asking your web framework whether your app serves '
                                                            'them raised an error: {detail}'},
                                    'parameters': {'count': 'How many paths were skipped.',
                                                   'detail': 'The error the framework raised.',
                                                   'path': 'The skipped path that sorts first.'},
                                    'summary': 'Your web framework raised an error while citry check asked whether '
                                               'your app serves a link path, so citry check skipped that link.',
                                    'surfaces': ['check'],
                                    'title': 'Link check failed',
                                    'when': 'The path checker that citry.contrib.flask.mount(), '
                                            'citry.contrib.fastapi.mount(), or citry.contrib.django.urlpatterns() '
                                            'registered raises an error for one or more link paths. Each of those '
                                            'paths is skipped, and citry check lists one note with the error for the '
                                            'skipped path that sorts first. The note never fails the check.'},
 'citry.check.url-checker-missing': {'code': 'citry.check.url-checker-missing',
                                     'constant': 'CHECK_URL_CHECKER_MISSING',
                                     'defaultSeverity': 'information',
                                     'documentationPath': '/ide/diagnostics/#citry.check.url-checker-missing',
                                     'fix': 'Point --app at a module that mounts Citry when it is imported, such as '
                                            'app.main:citry_app when app/main.py calls mount(app, citry_app), or '
                                            'config.urls:citry_app, with DJANGO_SETTINGS_MODULE set, for a Django '
                                            'project whose urls.py calls urlpatterns(). To stop checking links, set '
                                            'rule_unknown_url to "ignore".',
                                     'messages': {'default': "Links such as '{path}' were not checked, because no web "
                                                             'framework integration told Citry which paths your app '
                                                             'serves. Point --app at the module that calls '
                                                             'citry.contrib.flask.mount(), '
                                                             'citry.contrib.fastapi.mount(), or '
                                                             'citry.contrib.django.urlpatterns(), or set '
                                                             'rule_unknown_url to "ignore".'},
                                     'parameters': {'path': 'One of the paths that were not checked.'},
                                     'summary': 'citry check did not check the link paths in your templates, because '
                                                'no web framework integration told Citry which paths your app serves.',
                                     'surfaces': ['check'],
                                     'title': 'Links not checked',
                                     'when': 'A template has an href, src, or action path that starts with a single /, '
                                             'rule_unknown_url is not "ignore" for it, and no '
                                             'citry.contrib.flask.mount(), citry.contrib.fastapi.mount(), or '
                                             'citry.contrib.django.urlpatterns() call ran while citry check loaded '
                                             'your application. This happens when the module the --app option names '
                                             'only creates the Citry instance and nothing imports the module that '
                                             'mounts it, or when you serve Citry with citry.contrib.asgi or '
                                             "citry.contrib.wsgi, which do not know your app's routes. citry check "
                                             'lists it once, as a note, and it never fails the check.'},
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
 'citry.css.misspelled-class': {'code': 'citry.css.misspelled-class',
                                'configurableSeverity': True,
                                'constant': 'CSS_MISSPELLED_CLASS',
                                'defaultSeverity': 'warning',
                                'documentationPath': '/ide/diagnostics/#citry.css.misspelled-class',
                                'examples': [{'language': 'citry',
                                              'source': 'class Board(Component):\n'
                                                        '    template = """\n'
                                                        '      <div class="bord"></div>\n'
                                                        '    """\n'
                                                        '\n'
                                                        '    css = """\n'
                                                        '      .board {\n'
                                                        '        display: grid;\n'
                                                        '      }\n'
                                                        '    """',
                                              'title': 'A dropped letter'}],
                                'fix': 'Use the class name the CSS styles. If a stylesheet that Citry does not read '
                                       'styles this class on purpose, set rule_misspelled_css_class to "ignore" for '
                                       'this component.',
                                'messages': {'default': "No CSS that Citry reads styles the class '{name}'. Did you "
                                                        "mean '{suggestion}', from this component's CSS?"},
                                'parameters': {'name': 'The class as written.',
                                               'suggestion': "The class from the component's CSS one typing slip "
                                                             'away.'},
                                'summary': "A class in a template is one typing slip from a class the component's own "
                                           'CSS styles, such as bord for board. No CSS that Citry reads styles the '
                                           'class as written, so the element renders without those styles.',
                                'surfaces': ['check'],
                                'title': 'Misspelled CSS class',
                                'when': "A static class attribute in a component's template, on an HTML element or a "
                                        'component tag, holds a class of three or more characters that is one typing '
                                        "slip from a class selector in the component's own css or css_file: two "
                                        'neighboring letters swapped, one letter typed twice, or one letter left out. '
                                        'These slips usually name another class of the same family, so they do not '
                                        'count: one that moves, doubles, or drops a digit, such as col-1 for col-12; a '
                                        'missing final s after a letter other than s, such as tab for tabs; one of '
                                        'these short words, as the whole class or as its last word after a hyphen or '
                                        'underscore, next to its longer form: close (closed), collapse (collapsed), '
                                        'disable (disabled), enable (enabled), fade (faded), mute (muted), show '
                                        '(shown), slide (slider), and toggle (toggled or toggler), such as '
                                        'navbar-toggle for navbar-toggler; and one letter typed twice or left out in a '
                                        'first hyphen-separated part of one or two characters, such as p-4 for px-4 or '
                                        'm-auto for ml-auto. Two letters swapped in that part, such as iu-button for '
                                        'ui-button, are reported. The class is reported only when no CSS that Citry '
                                        "reads declares it: no selector in a registered component's css, css_file, "
                                        'inline or local-file Dependencies stylesheet, or template <style> element '
                                        'that holds CSS names it, and no attribute selector such as [class^="btn-"] '
                                        'matches it. Bound classes, such as :class, v-bind:class, and c-class, words '
                                        'inside {{ }} in a class attribute, and classes on tags that render no '
                                        'element, such as c-if or template, are not checked. citry check needs your '
                                        'application for this rule; the editor does not run it.'},
 'citry.css.misspelled-variable': {'code': 'citry.css.misspelled-variable',
                                   'configurableSeverity': True,
                                   'constant': 'CSS_MISSPELLED_VARIABLE',
                                   'defaultSeverity': 'warning',
                                   'documentationPath': '/ide/diagnostics/#citry.css.misspelled-variable',
                                   'examples': [{'language': 'css',
                                                 'source': 'h1 {\n  color: var(--acent);\n}',
                                                 'title': 'A dropped letter'}],
                                   'fix': "Use the key's exact name. If another stylesheet sets this property on "
                                          'purpose, add a fallback, as in var(--name, inherit), or set '
                                          'rule_misspelled_css_variable to "ignore" for this component.',
                                   'messages': {'default': 'Nothing sets --{name}, so this property gets its initial '
                                                           'or inherited value. Did you mean --{suggestion}, from '
                                                           'css_data()?'},
                                   'parameters': {'name': 'The custom property as written, without the leading --.',
                                                  'suggestion': 'The css_data() key one typing slip away.'},
                                   'summary': "A component's CSS reads a custom property that is one typing slip from "
                                              'a key its css_data() returns, such as var(--acent) for accent. Nothing '
                                              'sets that property, so the CSS property that reads it gets its '
                                              'inherited or initial value.',
                                   'surfaces': ['check'],
                                   'title': 'Misspelled css_data() variable',
                                   'when': "A var(--name) in the component's own css or css_file has no fallback "
                                           'value, the same CSS does not set --name itself, every key that css_data() '
                                           'or CssData returns is known, name is not one of them, and name is one '
                                           'typing slip from one of them: two neighboring letters swapped, one letter '
                                           'typed twice, or one letter left out. Properties that a parent component or '
                                           'a site stylesheet sets are not reported unless they are that close to a '
                                           'key. citry check needs your application for this rule.'},
 'citry.css.undeclared-class': {'code': 'citry.css.undeclared-class',
                                'configurableSeverity': True,
                                'constant': 'CSS_UNDECLARED_CLASS',
                                'defaultSeverity': 'ignore',
                                'documentationPath': '/ide/diagnostics/#citry.css.undeclared-class',
                                'examples': [{'language': 'citry-html',
                                              'source': '<div class="card-header">Title</div>',
                                              'title': 'A class without CSS'}],
                                'fix': 'Add CSS for the class to a component, or remove the class. For a component '
                                       'that uses classes from a stylesheet Citry does not read, set '
                                       'rule_undeclared_css_class to "ignore" in its Lint class.',
                                'messages': {'default': "No CSS that Citry reads styles the class '{name}'."},
                                'parameters': {'name': 'The class as written.'},
                                'summary': 'A class in a template is not named by any CSS that Citry reads, so either '
                                           'nothing styles it or a stylesheet outside Citry does.',
                                'surfaces': ['check'],
                                'title': 'Class that no CSS declares',
                                'when': 'The rule is off by default, because it also reports classes from a site '
                                        'stylesheet or a CSS framework such as Tailwind, and classes used only by '
                                        'JavaScript or tests. With rule_undeclared_css_class set to "warning" or '
                                        '"error", it reports each class in a static class attribute, on an HTML '
                                        'element or a component tag, that no CSS Citry reads declares. A class counts '
                                        "as declared when a selector in a registered component's css, css_file, inline "
                                        'or local-file Dependencies stylesheet, or template <style> element that holds '
                                        'CSS names it anywhere, as in .name, .card .name, .name:hover, or :is(.name), '
                                        'including inside @media and nested rules, or when an attribute selector such '
                                        'as [class~="name"] or [class^="btn-"] matches it. Citry does not read '
                                        'stylesheets linked by URL, local files that cannot be read as UTF-8, sources '
                                        'written in another language through css_lang, or <link> tags in templates, so '
                                        'their classes are reported. Bound classes, words inside {{ }} in a class '
                                        'attribute, and classes on tags that render no element are not checked, and a '
                                        'class that citry.css.misspelled-class reports is not reported again. citry '
                                        'check needs your application for this rule; the editor does not run it.'},
 'citry.css.undeclared-variable': {'code': 'citry.css.undeclared-variable',
                                   'configurableSeverity': True,
                                   'constant': 'CSS_UNDECLARED_VARIABLE',
                                   'defaultSeverity': 'ignore',
                                   'documentationPath': '/ide/diagnostics/#citry.css.undeclared-variable',
                                   'examples': [{'language': 'css',
                                                 'source': '.card {\n  padding: var(--card-gap);\n}',
                                                 'title': 'A property set nowhere'}],
                                   'fix': "Set the property in a component's CSS or css_data(), add a fallback, as in "
                                          'var(--name, 1rem), or, for a component that reads properties a stylesheet '
                                          'outside Citry sets, set rule_undeclared_css_variable to "ignore" in its '
                                          'Lint class.',
                                   'messages': {'default': 'Nothing that Citry reads sets --{name}, so this property '
                                                           'gets its initial or inherited value unless a stylesheet or '
                                                           'script outside Citry sets it.'},
                                   'parameters': {'name': 'The custom property as written, without the leading --.'},
                                   'summary': "A component's CSS reads a custom property with var(--name) and no "
                                              'fallback, and nothing that Citry reads sets it. Unless a stylesheet or '
                                              'script outside Citry sets it, the CSS property that reads it gets its '
                                              'inherited or initial value.',
                                   'surfaces': ['check'],
                                   'title': 'Custom property that nothing sets',
                                   'when': 'The rule is off by default, because it also reports properties that a site '
                                           'stylesheet, a design system, or a script outside Citry sets. With '
                                           'rule_undeclared_css_variable set to "warning" or "error", it reports each '
                                           "var(--name) without a fallback value in a component's own css or css_file "
                                           'when nothing that Citry reads sets --name. Citry counts as setting it: a '
                                           '--name: declaration or an @property --name rule in a registered '
                                           "component's css, css_file, inline or local-file Dependencies stylesheet, "
                                           'or template <style> element that holds CSS; a css_data() or CssData key '
                                           'called name on any registered component; a style attribute in a template '
                                           'that sets --name; and the text --name in quotes, or followed by a colon, '
                                           "in a :style or c-style binding, in a component's JavaScript, or in the "
                                           'Python module that defines a component. A component whose own css_data() '
                                           'keys Citry cannot all read is not checked, but a property that only such a '
                                           'component sets is still reported where another component reads it. A var() '
                                           "in a template's style attribute is not checked, and a var() that "
                                           'citry.css.misspelled-variable reports is not reported again. citry check '
                                           'needs your application for this rule; the editor does not run it.'},
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
 'citry.i18n.missing-param-type': {'code': 'citry.i18n.missing-param-type',
                                   'configurableSeverity': True,
                                   'constant': 'I18N_MISSING_PARAM_TYPE',
                                   'defaultSeverity': 'warning',
                                   'documentationPath': '/ide/diagnostics/#citry.i18n.missing-param-type',
                                   'fix': 'Add a comment such as # @param {str} $name above the message, naming the '
                                          'type the variable really takes. Set rule_i18n_missing_param_type to "error" '
                                          'to make a missing type fail catalog compilation, or to "ignore" to hide '
                                          'this warning.',
                                   'messages': {'default': '{detail}'},
                                   'parameters': {'detail': 'Message and variable that lack a type.'},
                                   'summary': 'A message uses a variable that has no # @param comment, so Citry cannot '
                                              'check the type of the value that callers pass in.',
                                   'surfaces': ['check'],
                                   'title': 'Message variable without a type',
                                   'when': 'A source-language message uses a variable such as { $name } in its value '
                                           'or an attribute, has no # @param comment declaring its type, and '
                                           'rule_i18n_missing_param_type is "warning". A variable used in a selector '
                                           'or a formatting function without a type fails catalog compilation and is '
                                           'reported as citry.i18n.catalog-invalid.'},
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
                                           'match. For a Secret, read its value on the server with get_secret_value() '
                                           'where you need it, and leave it out of js_data().',
                                    'messages': {'default': "JsData field '{name}' is not a clean JSON value: "
                                                            '{detail}. Browser tooling will treat its type as unknown.',
                                                 'secret': "JsData field '{name}' can hold a citry.Secret, and "
                                                           'rendering this component raises TypeError when it does: '
                                                           '{detail}.'},
                                    'parameters': {'detail': 'Why the value is not a clean JSON type.',
                                                   'name': 'JsData field name.'},
                                    'summary': 'A JsData field has a type that cannot be sent to the browser as JSON, '
                                               'such as a set or a date. Editor help treats the value as any. A '
                                               'citry.Secret is reported too, because rendering refuses to send one.',
                                    'surfaces': ['check', 'lsp'],
                                    'title': 'JsData field is not a JSON type',
                                    'when': 'A declared or inferred JsData field has a type that strict JSON cannot '
                                            'carry, such as bytes, a set, a callable, a date or time, or a whole class '
                                            'instance. A citry.Secret counts too: Citry never sends one to the '
                                            'browser, and rendering the component raises TypeError. With your '
                                            'application loaded, citry check also reads a module-level value that '
                                            'js_data() puts in its result, such as {"token": API_TOKEN} for API_TOKEN '
                                            '= Secret(...), and reports it when its value is not JSON. It reads such a '
                                            'value when it is the whole result, a value or item of a dict, list, or '
                                            'tuple literal in it, a name unpacked into a list such as [*TOKENS], '
                                            'either branch of a conditional expression, or the argument of Const(...); '
                                            'the value may be an attribute of a module-level name, such as '
                                            'config.API_TOKEN where config is a module or a plain class, when reading '
                                            'it runs no code: a property, or an object with a __getattr__ hook such as '
                                            "Django's lazy settings, is not read. A value read through an attribute is "
                                            'judged only when it is built from plain dicts, lists, tuples, strings, '
                                            'numbers, booleans, None, and Secrets. A module-level value holding '
                                            "another kind of object is reported only when that object's class could "
                                            'never pass the JSON check, so a lazy object or a dict subclass is '
                                            'skipped. A value nested too deeply to read is skipped. Without --types, a '
                                            'value that a call computes, such as get_token(), is not read. The editor '
                                            'and citry check --types also report a value that ty, the Python type '
                                            'checker Citry runs, types as a standard library type JSON cannot carry, '
                                            'such as PurePosixPath, datetime, Decimal, UUID, a set, or complex, or as '
                                            'a Secret.'},
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
 'citry.template.duplicate-id': {'code': 'citry.template.duplicate-id',
                                 'configurableSeverity': True,
                                 'constant': 'TEMPLATE_DUPLICATE_ID',
                                 'defaultSeverity': 'error',
                                 'documentationPath': '/ide/diagnostics/#citry.template.duplicate-id',
                                 'examples': [{'language': 'citry-html',
                                               'source': '<div id="board">\n  <h1 id="board">Board</h1>\n</div>',
                                               'title': 'The same id twice'}],
                                 'fix': 'Give one of the elements another id.',
                                 'messages': {'default': "Another element in this template already has id '{id}'. An "
                                                         'id must be unique in the page.'},
                                 'parameters': {'id': 'The repeated id value.'},
                                 'summary': 'Two elements in one template always render with the same literal id. An '
                                            "id must be unique in the page, so a label's for attribute, "
                                            'aria-labelledby, URL fragments, and getElementById find only the first '
                                            'element.',
                                 'surfaces': ['check', 'lsp'],
                                 'title': 'Duplicate element id',
                                 'when': 'Two elements have the same static id value, and neither is inside a '
                                         'condition or a loop: c-if, c-elif, c-else, c-for, or c-empty, as a tag or as '
                                         'an attribute on the element or around it; v-if, v-else-if, v-else, or v-for; '
                                         'a c-fill, a <c-slot> fallback, the body of a component tag, or a <template>. '
                                         'Those may render an element zero or several times, so the check cannot know '
                                         'whether both appear. v-show does not count, because a hidden element is '
                                         'still in the page. The same id coming from two templates is not reported. '
                                         'citry check --static and an editor that has not loaded your application '
                                         "report it too, with the severity the component's own Lint class sets as a "
                                         'plain string.'},
 'citry.template.invalid-attribute-value': {'code': 'citry.template.invalid-attribute-value',
                                            'configurableSeverity': True,
                                            'constant': 'TEMPLATE_INVALID_ATTRIBUTE_VALUE',
                                            'defaultSeverity': 'error',
                                            'documentationPath': '/ide/diagnostics/#citry.template.invalid-attribute-value',
                                            'examples': [{'language': 'citry-html',
                                                          'source': '<div draggable="treu">Drag me</div>',
                                                          'title': 'A misspelled keyword'},
                                                         {'language': 'citry-html',
                                                          'source': '<input type="datetime" name="start">',
                                                          'title': 'An input type the browser does not know'},
                                                         {'language': 'citry-html',
                                                          'source': '<button disabled="false">Search</button>',
                                                          'title': 'A boolean attribute set to false'}],
                                            'fix': 'Use one of the valid values the message lists. For a boolean '
                                                   'attribute, write it with no value, leave it out, or bind a '
                                                   'JavaScript boolean such as :disabled="saving". If a script on the '
                                                   'page reads its own values from the attribute, set '
                                                   'rule_invalid_attribute_value to "ignore" for that component.',
                                            'messages': {'boolean': "'{attribute}' on <{element}> is on whenever it is "
                                                                    "present, so '{value}' still turns it on. Write it "
                                                                    'with no value to turn it on, and leave it out to '
                                                                    'turn it off.',
                                                         'boolean-binding': "'{attribute}' on <{element}> is on "
                                                                            'whenever it is present, so the string '
                                                                            "'{value}' still turns it on. Bind a "
                                                                            'JavaScript boolean instead, such as '
                                                                            ':{attribute}="false".',
                                                         'default': "'{value}' is not a valid value for '{attribute}' "
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
                                                       'draggable or type, has another value, or a boolean attribute '
                                                       'such as disabled has a value other than empty or its own name, '
                                                       'which still turns it on. The browser raises no error either '
                                                       'way.',
                                            'surfaces': ['check', 'lsp'],
                                            'title': 'HTML attribute value the browser does not accept',
                                            'when': 'The value is not one of the keywords the HTML Standard lists for '
                                                    'that attribute on that element. A boolean attribute, such as '
                                                    'disabled or required, is on whenever it is present, so any value '
                                                    "other than the empty string or the attribute's own name is "
                                                    'reported, including "false" and "true". Letter case does not '
                                                    'matter, except for list markers in type on <ol> and <li>. A Vue '
                                                    'binding whose value is one JavaScript string, such as '
                                                    ':dir="\'rtl\'", is checked too. Other bound values, component '
                                                    'tags, <c-element>, custom elements, elements inside <svg> or '
                                                    '<math>, and attributes that take a list of words, such as rel, '
                                                    'are not checked. citry check --static and an editor that has not '
                                                    'loaded your application report it as a warning unless the '
                                                    "component's own Lint class sets the rule as a plain string, "
                                                    'because they cannot read your LintSettings.'},
 'citry.template.invalid-nesting': {'code': 'citry.template.invalid-nesting',
                                    'configurableSeverity': True,
                                    'constant': 'TEMPLATE_INVALID_NESTING',
                                    'defaultSeverity': 'error',
                                    'documentationPath': '/ide/diagnostics/#citry.template.invalid-nesting',
                                    'examples': [{'language': 'citry-html',
                                                  'source': '<p>Owner: <div>{{ owner.name }}</div></p>',
                                                  'title': 'A div inside a paragraph'}],
                                    'fix': 'Change the <p> to a <div>, or change the inner element to an inline one '
                                           'such as <span>.',
                                    'messages': {'default': '<{tag}> cannot be inside <p>. The browser closes the <p> '
                                                            'before it, so the page structure differs from the '
                                                            'template.'},
                                    'parameters': {'tag': 'Tag name of the inner element as written in the template.'},
                                    'summary': 'An element that starts a new block, such as <div> or <ul>, is inside a '
                                               '<p>. The browser closes the paragraph before that element, so the page '
                                               'has a different structure from the template, and a page that Vue '
                                               'renders fails to compile.',
                                    'surfaces': ['check', 'lsp'],
                                    'title': 'Element the browser moves out of a paragraph',
                                    'when': 'A <p> is open around the element, directly or through inline elements, '
                                            'custom elements, c-if, c-elif, c-else, c-for, c-empty, or a <c-slot> '
                                            'fallback, and the element is one that the HTML Standard says closes an '
                                            'open <p>: address, article, aside, blockquote, details, dialog, div, dl, '
                                            'dd, dt, fieldset, figcaption, figure, footer, form, h1 to h6, header, '
                                            'hgroup, hr, li, main, menu, nav, ol, p, pre, search, section, summary, '
                                            'table, ul, and obsolete ones such as center and xmp. Content inside '
                                            '<button>, <table>, <template>, <noscript>, <svg>, <math>, a component '
                                            'tag, or <c-element> is not checked, because the browser keeps it inside '
                                            'or the check cannot see what renders there. citry check --static and an '
                                            'editor that has not loaded your application report it too, with the '
                                            "severity the component's own Lint class sets as a plain string."},
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
 'citry.template.missing-image-alt': {'code': 'citry.template.missing-image-alt',
                                      'configurableSeverity': True,
                                      'constant': 'TEMPLATE_MISSING_IMAGE_ALT',
                                      'defaultSeverity': 'warning',
                                      'documentationPath': '/ide/diagnostics/#citry.template.missing-image-alt',
                                      'examples': [{'language': 'citry-html',
                                                    'source': '<img src="/static/avatar.svg" width="32" height="32">',
                                                    'title': 'An avatar without alt text'}],
                                      'fix': 'Describe the image in alt. For an image that only decorates the page, '
                                             'write alt="" so screen readers skip it.',
                                      'messages': {'default': '<img> has no alt text. Describe the image in alt, or '
                                                              'write alt="" for an image that only decorates the '
                                                              'page.'},
                                      'parameters': {},
                                      'summary': 'An <img> has no alt text. A screen reader then reads out the file '
                                                 'name or nothing useful, and the image has no text when it fails to '
                                                 'load.',
                                      'surfaces': ['check', 'lsp'],
                                      'title': 'Image without alt text',
                                      'when': 'An <img> has no alt in any form (alt, c-alt, :alt, or v-bind:alt), no '
                                              'aria-label or aria-labelledby, and no role="none" or '
                                              'role="presentation". An image with a c-bind or v-bind spread is not '
                                              'reported, because the spread may add alt. Neither is an <img> that is a '
                                              "component's only top-level element, or the only element in each block "
                                              'of a top-level c-if, c-elif, and c-else chain, when the component may '
                                              'have browser code (JavaScript, js_data(), State, or event handlers), '
                                              "because Vue passes the alt that a parent writes on the component's tag "
                                              'to that element. citry check without --static, and an editor that has '
                                              'loaded your application, report that image when the component has no '
                                              'browser code. citry check --static and an editor that has not loaded '
                                              "your application report the other images too, but never a component's "
                                              "only top-level <img>, with the severity the component's own Lint class "
                                              'sets as a plain string.'},
 'citry.template.misspelled-attribute': {'code': 'citry.template.misspelled-attribute',
                                         'configurableSeverity': True,
                                         'constant': 'TEMPLATE_MISSPELLED_ATTRIBUTE',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.template.misspelled-attribute',
                                         'examples': [{'language': 'citry-html',
                                                       'source': '<div titel="Board">...</div>',
                                                       'title': 'A typo in title'},
                                                      {'language': 'citry-html',
                                                       'source': '<img :scr="avatarUrl">',
                                                       'title': 'A typo in a Vue binding'}],
                                         'fix': 'Use the attribute the message names. If a script on the page really '
                                                'reads an attribute with this name, write it as data-<name>, or set '
                                                'rule_misspelled_attribute to "ignore" for that component.',
                                         'messages': {'default': "'{name}' is not an attribute of <{element}>, so the "
                                                                 "browser ignores it. Did you mean '{suggestion}'?"},
                                         'parameters': {'element': 'Element name as written in the template.',
                                                        'name': 'Attribute name as written in the template.',
                                                        'suggestion': 'The attribute the author probably meant, '
                                                                      'written with the same binding prefix.'},
                                         'summary': 'An attribute on an HTML element looks like a typo of an attribute '
                                                    'that element accepts, such as titel for title. The browser keeps '
                                                    'it as an unknown attribute and ignores it, with no error.',
                                         'surfaces': ['check', 'lsp'],
                                         'title': 'Misspelled HTML attribute',
                                         'when': 'The attribute is not one the HTML Standard lists for that element or '
                                                 'for every element, and it is one typing slip from one that is: two '
                                                 'neighboring letters swapped, one letter typed twice, or one letter '
                                                 'left out, such as titel, clas, or herf. A binding such as :titel, '
                                                 'v-bind:titel, or c-titel is checked by the attribute it sets. Letter '
                                                 'case does not matter. Names with a hyphen or a colon, such as '
                                                 'data-*, aria-*, or hx-*, bindings with a modifier such as .prop, '
                                                 "component tags, custom elements, <c-element>, bindings on Vue's "
                                                 '<slot>, and elements inside <svg> or <math> are not checked. A c-* '
                                                 'name that looks like a misspelled directive, such as c-fro, is '
                                                 'reported as citry.template.misspelled-directive instead. citry check '
                                                 '--static and an editor that has not loaded your application report '
                                                 "it too, with the severity the component's own Lint class sets as a "
                                                 'plain string.'},
 'citry.template.misspelled-directive': {'code': 'citry.template.misspelled-directive',
                                         'configurableSeverity': True,
                                         'constant': 'TEMPLATE_MISSPELLED_DIRECTIVE',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.template.misspelled-directive',
                                         'examples': [{'language': 'citry-html',
                                                       'source': '<div c-iff="show">Details</div>',
                                                       'title': 'A typo in c-if'},
                                                      {'language': 'citry-html',
                                                       'source': '<input c-model="query">',
                                                       'title': 'A directive name from Vue'},
                                                      {'language': 'citry-html',
                                                       'source': '<p v-iff="open">Details</p>',
                                                       'title': 'A typo in v-if'}],
                                         'fix': 'Use the directive the message names. If the attribute really is meant '
                                                'for the browser, pass it through c-bind, such as c-bind="{\'show\': '
                                                'value}", or set rule_misspelled_directive to "ignore" for that '
                                                'component.',
                                         'messages': {'default': "'{name}' is not a Citry directive, so it renders an "
                                                                 "HTML attribute named '{attribute}'. Did you mean "
                                                                 "'{suggestion}'?",
                                                      'vue': "'{name}' is not a Citry directive, so it renders an HTML "
                                                             "attribute named '{attribute}'. For Vue's directive, "
                                                             "write '{suggestion}'.",
                                                      'vue-directive': "'{name}' is not a Vue directive, so Vue looks "
                                                                       'for a custom directive of that name and the '
                                                                       'page fails in the browser. Did you mean '
                                                                       "'{suggestion}'?"},
                                         'parameters': {'attribute': 'The attribute name the element renders, without '
                                                                     'c-.',
                                                        'name': 'Attribute name as written in the template.',
                                                        'suggestion': 'The directive the author probably meant.'},
                                         'summary': 'A c-* attribute on an HTML element looks like a Citry directive, '
                                                    'such as c-iff for c-if, but is not one, so Citry renders it as an '
                                                    'ordinary attribute and the directive never runs. Or a v-* '
                                                    'attribute looks like a Vue directive, such as v-iff for v-if, so '
                                                    'Vue looks for a custom directive of that name and the page fails.',
                                         'surfaces': ['check', 'lsp'],
                                         'title': 'Misspelled Citry directive',
                                         'when': 'The part after c- is not an HTML attribute that the element accepts, '
                                                 'and it looks like a directive: if, elif, else, for, empty, or bind '
                                                 'with two neighboring letters swapped, one letter typed twice, or one '
                                                 'letter left out, such as c-fro, c-iff, or c-ele; one of those in '
                                                 'other letter case, such as c-If; a spelled-out c-elif, such as '
                                                 'c-else-if; c-show for c-if or c-model for v-model; or c-key or '
                                                 'c-ignore without the #. A different letter, or an extra letter that '
                                                 'is not a double, is not a typo, because it usually makes an ordinary '
                                                 'word such as c-kind or c-form; neither are c-or, c-bid, c-bin, or a '
                                                 'one-letter name. On a custom element, which can define its own '
                                                 'attributes, the c-show, c-model, c-key, and c-ignore names are not '
                                                 'reported. Only HTML elements, custom elements, and <c-element> are '
                                                 'checked, not component tags or elements inside <svg> or <math>. A '
                                                 'v-* name is reported on any element outside <svg>, <math>, and v-pre '
                                                 'content, component tags included, when it is not a Vue directive and '
                                                 'it is a typing slip (two neighboring letters swapped, one letter '
                                                 'typed twice, or one letter left out) away from one, such as v-iff, '
                                                 'v-shwo, or v-IFF, or is a spelled-out v-else-if, such as v-elif or '
                                                 'v-elseif. A custom directive whose name is one slip from a Vue '
                                                 'directive is reported too; set the rule to "ignore" for that '
                                                 'component. citry check --static and an editor that has not loaded '
                                                 "your application report it too, with the severity the component's "
                                                 'own Lint class sets as a plain string.'},
 'citry.template.misspelled-element': {'code': 'citry.template.misspelled-element',
                                       'configurableSeverity': True,
                                       'constant': 'TEMPLATE_MISSPELLED_ELEMENT',
                                       'defaultSeverity': 'error',
                                       'documentationPath': '/ide/diagnostics/#citry.template.misspelled-element',
                                       'examples': [{'language': 'citry-html',
                                                     'source': '<dvi class="board">...</dvi>',
                                                     'title': 'A typo in div'}],
                                       'fix': 'Use the element the message names. If a Vue plugin registers a '
                                              'component with this name, set rule_misspelled_element to "ignore" for '
                                              'that component.',
                                       'messages': {'default': '<{tag}> is not an HTML element. Did you mean '
                                                               '<{suggestion}>?'},
                                       'parameters': {'suggestion': 'The HTML element the author probably meant.',
                                                      'tag': 'Tag name as written in the template.'},
                                       'summary': 'A tag looks like a typo of an HTML element, such as <dvi> for '
                                                  '<div>. The browser renders it as an unknown element with no styles '
                                                  'or behavior, with no error.',
                                       'surfaces': ['check', 'lsp'],
                                       'title': 'Misspelled HTML element',
                                       'when': 'The tag is lowercase, has no hyphen and no c- prefix, is not an HTML, '
                                               "SVG, or obsolete HTML element or one of Vue's built-in tags such as "
                                               '<component>, and is one typing slip from an HTML element: two '
                                               'neighboring letters swapped, one letter typed twice, or one letter '
                                               'left out. Any other unknown lowercase tag is not reported, because a '
                                               'Vue plugin may register a component under that name. Elements inside '
                                               '<svg> or <math> are not checked. Outside <math>, a MathML name one '
                                               'slip from an HTML element, such as <min>, is reported, because there '
                                               'it is more likely a typo of <main>. citry check --static and an editor '
                                               'that has not loaded your application report it too, with the severity '
                                               "the component's own Lint class sets as a plain string."},
 'citry.template.unknown-aria-attribute': {'code': 'citry.template.unknown-aria-attribute',
                                           'configurableSeverity': True,
                                           'constant': 'TEMPLATE_UNKNOWN_ARIA_ATTRIBUTE',
                                           'defaultSeverity': 'error',
                                           'documentationPath': '/ide/diagnostics/#citry.template.unknown-aria-attribute',
                                           'examples': [{'language': 'citry-html',
                                                         'source': '<button :aria-expandd="open">Menu</button>',
                                                         'title': 'A typo in aria-expanded'}],
                                           'fix': 'Use the ARIA attribute the message names, or the one you meant from '
                                                  'the WAI-ARIA list. To keep a custom value on the element, store it '
                                                  'in a data-* attribute.',
                                           'messages': {'default': "'{name}' is not an ARIA attribute, so browsers and "
                                                                   'screen readers ignore it.',
                                                        'suggestion': "'{name}' is not an ARIA attribute, so browsers "
                                                                      'and screen readers ignore it. Did you mean '
                                                                      "'{suggestion}'?"},
                                           'parameters': {'name': 'Attribute name as written in the template.',
                                                          'suggestion': 'The ARIA attribute closest to the written '
                                                                        'name.'},
                                           'summary': 'An aria-* attribute is not one that WAI-ARIA defines, often '
                                                      'because of a typo such as aria-expandd. Browsers and screen '
                                                      'readers ignore it, so the element loses the state or label it '
                                                      'was meant to have.',
                                           'surfaces': ['check', 'lsp'],
                                           'title': 'Unknown ARIA attribute',
                                           'when': 'The attribute name, after any :, v-bind:, or c- prefix, starts '
                                                   'with aria- and is not a WAI-ARIA 1.2 or 1.3 state or property. '
                                                   'Letter case does not matter. ARIA lets no page invent its own '
                                                   'aria-* names, so every unknown name is reported, not only typos. '
                                                   'Component tags are not checked, because there the name is an '
                                                   'input. citry check --static and an editor that has not loaded your '
                                                   "application report it too, with the severity the component's own "
                                                   'Lint class sets as a plain string.'},
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
 'citry.template.unknown-inject-key': {'code': 'citry.template.unknown-inject-key',
                                       'configurableSeverity': True,
                                       'constant': 'TEMPLATE_UNKNOWN_INJECT_KEY',
                                       'defaultSeverity': 'warning',
                                       'documentationPath': '/ide/diagnostics/#citry.template.unknown-inject-key',
                                       'examples': [{'language': 'python',
                                                     'source': 'board = self.inject("bord")  # the page provides '
                                                               '"board"',
                                                     'title': 'A misspelled key'}],
                                       'fix': 'Correct the key to the one the page provides, or provide the key above '
                                              'the component. Pass a default, such as self.inject("key", None), when '
                                              'the value is optional. If the key comes from somewhere Citry cannot '
                                              'see, set rule_unknown_inject_key to "ignore" in the component\'s Lint '
                                              'class, or for the whole app in LintSettings.',
                                       'messages': {'default': "No component above {component} provides '{key}', so "
                                                               "self.inject('{key}') raises KeyError when the page "
                                                               "renders. Provide '{key}' above {component}, or pass a "
                                                               'default to inject().',
                                                    'nowhere': "Nothing in your app provides '{key}', so "
                                                               "self.inject('{key}') in {component} raises KeyError "
                                                               "when the page renders. Provide '{key}' above "
                                                               '{component}, or pass a default to inject().',
                                                    'nowhereSuggestion': "Nothing in your app provides '{key}', so "
                                                                         "self.inject('{key}') in {component} raises "
                                                                         'KeyError when the page renders. Did you mean '
                                                                         "'{suggestion}'?",
                                                    'suggestion': "No component above {component} provides '{key}', so "
                                                                  "self.inject('{key}') raises KeyError when the page "
                                                                  "renders. Did you mean '{suggestion}'?"},
                                       'parameters': {'component': 'The name of the component class that calls '
                                                                   'inject().',
                                                      'key': 'The key the component reads.',
                                                      'suggestion': 'A provided key that is one typing slip from it.'},
                                       'summary': 'A component reads a shared value with self.inject("key"), but no '
                                                  'component above it provides that key, so rendering it raises '
                                                  'KeyError.',
                                       'surfaces': ['check', 'lsp'],
                                       'title': 'Shared value read under a key nothing provides',
                                       'when': 'A method of a component class, or of a base class or mixin it extends, '
                                               'calls self.inject() with one string literal and no default, and no '
                                               'provider Citry can see gives that key to the component. Citry starts '
                                               "at each template that uses the component's tag, such as <c-card />, "
                                               'and walks up through the templates that use those components. A key '
                                               'counts when a <c-provide key="..."> wraps the tag; when a component on '
                                               'the way calls self.provide() with it; when the tag is slot content and '
                                               'the component whose <c-slot> shows it wraps that <c-slot> in '
                                               '<c-provide> or calls self.provide(); when a <c-provide> or '
                                               'self.provide() wraps a <c-component c-is="...">, which may render any '
                                               "component; or when a render(provides={...}) call in your project's "
                                               'Python files passes it as a literal key, which counts for every '
                                               'component. A key written as a module-level string constant counts as '
                                               'that string. If the component appears in several places and one of '
                                               'them provides the key, nothing is reported. When no template uses the '
                                               "component's tag, because Python renders it, a <c-component "
                                               'c-is="..."> picks it, or it appears only inside its own template, the '
                                               'key is compared with every key the app provides anywhere. Citry '
                                               'reports nothing for a call with a default, such as self.inject("key", '
                                               'None), or a key written as a name or expression; below a <c-provide '
                                               'c-key="...">, a self.provide() key written as an expression, a tag '
                                               'inside a <c-component c-is="...">, markup in a component\'s attribute, '
                                               "or a component Python builds inside a component's methods or passes to "
                                               'another component, such as Layout(slots={"default": Widget()}); below '
                                               'a component whose Python source it cannot read; and nothing at all '
                                               'while a registered template cannot be parsed. A key the page does '
                                               'provide is reported when Citry cannot see the provider: a provides '
                                               'dictionary built elsewhere, a self.provide() call in a helper '
                                               'function, or a render(provides=...) call outside the folder you run '
                                               'citry check from. That is why the rule is a warning. The rule runs in '
                                               'citry check with your application loaded, and in an editor that has '
                                               'loaded your application; the editor checks the calls in the file you '
                                               'edit against the keys your app provided when it last loaded.'},
 'citry.template.unknown-url': {'code': 'citry.template.unknown-url',
                                'configurableSeverity': True,
                                'constant': 'TEMPLATE_UNKNOWN_URL',
                                'defaultSeverity': 'warning',
                                'documentationPath': '/ide/diagnostics/#citry.template.unknown-url',
                                'examples': [{'language': 'citry-html',
                                              'source': '<a href="/abuot">About</a>',
                                              'title': 'A misspelled page path'}],
                                'fix': 'Correct the path, or add the route or file. If another server answers the '
                                       'path, set rule_unknown_url to "ignore" in the component\'s Lint class, or for '
                                       'the whole app in LintSettings.',
                                'messages': {'default': "Your app has no route or static file for '{path}', so the "
                                                        'browser gets a 404 Not Found.',
                                             'suggestion': "Your app has no route or static file for '{path}', so the "
                                                           'browser gets a 404 Not Found. Did you mean '
                                                           "'{suggestion}'?"},
                                'parameters': {'path': 'The path the browser requests, without its query string and '
                                                       'fragment.',
                                               'suggestion': 'A path your app serves that is one typing slip from it.'},
                                'summary': 'A link, image, script, or form points at a path on your site that none of '
                                           "your app's routes or static files serves, so the browser gets a 404 Not "
                                           'Found.',
                                'surfaces': ['check', 'lsp'],
                                'title': 'Link to a missing page or file',
                                'when': "An HTML element's href, src, or action is a path that starts with a single /, "
                                        'such as /about or /static/logo.svg, and your web framework answers that it '
                                        "serves no such path. Citry asks the framework that mounts it: Flask's URL "
                                        'rules and static folders when you call citry.contrib.flask.mount(), the '
                                        'routes and StaticFiles mounts of a FastAPI or Starlette app when you call '
                                        "citry.contrib.fastapi.mount(), and Django's URL patterns and static file "
                                        'finders when you call citry.contrib.django.urlpatterns(). The query string '
                                        'and fragment are ignored. These are not checked: a URL with a scheme, such as '
                                        'https: or mailto:; a //host/... URL; a relative path; a value written as an '
                                        'expression, such as :href or c-href; a <base href> or a <link '
                                        'rel="preconnect"> or rel="dns-prefetch"; a path under the prefix Citry\'s own '
                                        'routes are mounted at; a parameter type that only the view checks, such as a '
                                        'FastAPI project_id: int argument; and, with Django, a path under MEDIA_URL. '
                                        'The rule runs in citry check with your application loaded, and in an editor '
                                        'that has loaded your application, and only when one of those calls runs while '
                                        "Citry imports the module that --app, or the editor's citry.app setting, "
                                        'names. The editor checks the paths your templates hold when it loads your '
                                        'application, so a path you add later is checked after the next load. A path '
                                        'that another server answers for your site, such as a reverse proxy, is '
                                        'reported too, which is why the rule is a warning.'},
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
 'citry.vue.compile-error': {'code': 'citry.vue.compile-error',
                             'configurableSeverity': True,
                             'constant': 'VUE_COMPILE_ERROR',
                             'defaultSeverity': 'error',
                             'documentationPath': '/ide/diagnostics/#citry.vue.compile-error',
                             'examples': [{'language': 'citry-html',
                                           'source': '<table>\n  <div>Row</div>\n</table>',
                                           'title': 'A div directly inside a table'}],
                             'fix': "Follow the compiler's message. For a table, put rows in <tr> and cells in <td> or "
                                    '<th>; for nested buttons, forms or links, close the outer one first or use '
                                    'another element; for v-else, put it on the element right after the one with v-if '
                                    'or v-else-if.',
                             'messages': {'default': 'Vue cannot compile this template: {detail}'},
                             'parameters': {'detail': 'What the compiler found, as one sentence.'},
                             'summary': "Vue's compiler rejects the template, so a component that uses Vue fails to "
                                        'render. Most often the browser would build a different element tree from the '
                                        'one the template describes: a <div> directly inside a <table>, a <button> '
                                        'inside a <button>, a <form> inside a <form>, or an <a> inside an <a>. A '
                                        'v-else with no v-if right before it, and a component inside a Vue v-for, are '
                                        'reported too.',
                             'surfaces': ['check', 'lsp'],
                             'title': "Template that Vue's compiler rejects",
                             'when': 'Citry writes the Vue template that a render compiles, runs the same compiler on '
                                     'it, and reports each error at the text you wrote. Every c-if, c-elif and c-else '
                                     'branch, and the body of every c-for, is checked, but usually on its own, so a '
                                     'mistake that spans the c-if or c-for tag, such as a <div> in a c-for directly '
                                     'inside a <table>, may not be reported. A Vue expression with a syntax error is '
                                     'reported as citry.vue.invalid-expression, and a block element inside a <p> as '
                                     'citry.template.invalid-nesting, so this rule does not report them again, even '
                                     'when those rules are turned off. A component inside a Vue v-for is reported only '
                                     'by citry check with the application loaded, which can tell whether the component '
                                     "is transparent or simple; such a component renders into its caller's HTML and "
                                     'may sit inside a v-for. Content inside #c-ignore or <c-raw>, whether a '
                                     "<c-element>'s content fits the tag Python chooses, where a component tag sits, "
                                     'and attributes an extension handles, such as @c-click, are not checked, and a '
                                     "template that uses an extension's own template syntax is skipped. citry check "
                                     '--static and an editor that has not loaded your application report it too, with '
                                     "the severity the component's own Lint class sets as a plain string."},
 'citry.vue.invalid-expression': {'code': 'citry.vue.invalid-expression',
                                  'configurableSeverity': True,
                                  'constant': 'VUE_INVALID_EXPRESSION',
                                  'defaultSeverity': 'error',
                                  'documentationPath': '/ide/diagnostics/#citry.vue.invalid-expression',
                                  'examples': [{'language': 'citry-html',
                                                'source': '<p v-if="open &&">Details</p>',
                                                'title': 'An unfinished condition'}],
                                  'fix': 'Complete or correct the expression, such as v-if="open && ready".',
                                  'messages': {'default': "The Vue expression in '{attribute}' is not valid "
                                                          'JavaScript, so Vue cannot compile this template.'},
                                  'parameters': {'attribute': 'Attribute that holds the expression, as written in the '
                                                              'template.'},
                                  'summary': 'A Vue expression, such as the value of v-if, :title, or @click, is not '
                                             'valid JavaScript. Vue cannot compile the template, so the page fails '
                                             'when it renders.',
                                  'surfaces': ['check', 'lsp'],
                                  'title': 'Vue expression with a syntax error',
                                  'when': 'The expression does not parse as JavaScript, after character references '
                                          'such as &amp;&amp; are decoded the way Vue decodes them. A listener may '
                                          'also hold statements or a function expression. The arguments of a server '
                                          'call such as @c-click="save({...})" are checked too. A valueless :title, '
                                          'which Vue reads as :title="title", everything on or inside an element with '
                                          'v-pre, which Vue does not compile, and custom directive values are not '
                                          'checked, although Vue still fails on a custom directive value that is not '
                                          'valid JavaScript. citry check --static and an editor that has not loaded '
                                          "your application report it too, with the severity the component's own Lint "
                                          'class sets as a plain string.'},
 'citry.vue.misspelled-event': {'code': 'citry.vue.misspelled-event',
                                'configurableSeverity': True,
                                'constant': 'VUE_MISSPELLED_EVENT',
                                'defaultSeverity': 'warning',
                                'documentationPath': '/ide/diagnostics/#citry.vue.misspelled-event',
                                'examples': [{'language': 'citry-html',
                                              'source': '<button @clik="toggle()">Show details</button>',
                                              'title': 'A typo in click'}],
                                'fix': 'Use the event the message names. If the page dispatches a custom event with '
                                       'this name, set rule_misspelled_event to "ignore" for that component.',
                                'messages': {'default': "'{event}' is not a DOM event, so this listener never runs. "
                                                        "Did you mean '{suggestion}'?"},
                                'parameters': {'event': 'Event name as written in the template.',
                                               'suggestion': 'The DOM event the author probably meant.'},
                                'summary': 'A listener on an HTML element names an event that looks like a typo of a '
                                           'DOM event, such as @clik for @click. No element fires that event, so the '
                                           'listener never runs.',
                                'surfaces': ['check', 'lsp'],
                                'title': 'Misspelled DOM event',
                                'when': 'The event name in @name or v-on:name, before any modifier, is all lowercase '
                                        "letters, is not a DOM event that the HTML Standard or Vue's types list, and "
                                        'is one typing slip from one that is: two neighboring letters swapped, one '
                                        'letter typed twice, or one letter left out. Names with a hyphen, a colon, or '
                                        'an uppercase letter, and a few ordinary words such as scrolled and touched, '
                                        'are not reported, because they are usually custom events. Component tags, '
                                        'custom elements, and v-pre content are not checked. citry check --static and '
                                        'an editor that has not loaded your application report it too, with the '
                                        "severity the component's own Lint class sets as a plain string."},
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
