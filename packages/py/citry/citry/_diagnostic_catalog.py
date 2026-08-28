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
JS_DATA_UNSUPPORTED_TYPE = 'citry.js-data.unsupported-type'
ALPINE_UNKNOWN_VARIABLE = 'citry.alpine.unknown-variable'
CSP_INCOMPATIBLE_BROWSER_CODE = 'citry.csp.incompatible-browser-code'
COMPONENT_JS_UNKNOWN_VARIABLE = 'citry.component-js.unknown-variable'
BROWSER_UNKNOWN_SERVER_EVENT = 'citry.browser.unknown-server-event'
BROWSER_UNKNOWN_COMPONENT_PROP = 'citry.browser.unknown-component-prop'
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

DIAGNOSTICS: Final = {'citry.alpine.unknown-variable': {'code': 'citry.alpine.unknown-variable',
                                   'configurableSeverity': True,
                                   'constant': 'ALPINE_UNKNOWN_VARIABLE',
                                   'defaultSeverity': 'error',
                                   'documentationPath': '/ide/diagnostics/#citry.alpine.unknown-variable',
                                   'examples': [{'language': 'citry-html',
                                                 'source': '<button :disabled="submitting1">Save</button>',
                                                 'title': 'Unknown name in an Alpine expression'}],
                                   'messages': {'default': "Alpine variable '{name}' is not available in this "
                                                           'component.'},
                                   'parameters': {'name': 'Authored Alpine variable name.'},
                                   'summary': 'A free identifier in an Alpine expression is absent from the '
                                              "component's proven browser scope.",
                                   'surfaces': ['check', 'lsp'],
                                   'title': 'Unknown Alpine variable',
                                   'when': 'An Alpine expression references a root that is not supplied by JsData, '
                                           'x-data, an enclosing x-for, a proven $component scope write, an Alpine or '
                                           'Citry magic, a browser global, or configured lint-only Alpine variables.'},
 'citry.browser.incompatible-component-prop': {'code': 'citry.browser.incompatible-component-prop',
                                               'constant': 'BROWSER_INCOMPATIBLE_COMPONENT_PROP',
                                               'defaultSeverity': 'error',
                                               'documentationPath': '/ide/diagnostics/#citry.browser.incompatible-component-prop',
                                               'examples': [{'language': 'citry-html',
                                                             'source': '<c-card $c-props="{ count: \'many\' }" />',
                                                             'title': 'Wrong literal type'}],
                                               'messages': {'default': "Client prop '{name}' expects {expected}, but "
                                                                       'this value is {actual}.'},
                                               'parameters': {'actual': 'Proven authored value type.',
                                                              'expected': "Child component's declared JavaScript type.",
                                                              'name': 'Authored client-prop key.'},
                                               'summary': 'A static $c-props value has a proven type outside the child '
                                                          "component's prop declaration.",
                                               'surfaces': ['check', 'lsp'],
                                               'title': 'Incompatible client prop',
                                               'when': 'Citry can prove both the authored value type and the static '
                                                       '$component({props}) type, and the value cannot satisfy that '
                                                       'prop.'},
 'citry.browser.missing-component-prop': {'code': 'citry.browser.missing-component-prop',
                                          'constant': 'BROWSER_MISSING_COMPONENT_PROP',
                                          'defaultSeverity': 'error',
                                          'documentationPath': '/ide/diagnostics/#citry.browser.missing-component-prop',
                                          'examples': [{'language': 'citry-html',
                                                        'source': '<c-card $c-props="{}" />',
                                                        'title': 'Missing required prop'}],
                                          'messages': {'default': "Required client prop '{name}' is missing for "
                                                                  '<{tag}>.'},
                                          'parameters': {'name': 'Required client-prop name.',
                                                         'tag': 'Authored child component tag.'},
                                          'summary': 'A static $c-props object omits a required prop declared by the '
                                                     'child component.',
                                          'surfaces': ['check', 'lsp'],
                                          'title': 'Missing required client prop',
                                          'when': 'A statically resolved component receives a direct $c-props object '
                                                  'without a required static $component({props}) key and no dynamic '
                                                  'spread can supply it.'},
 'citry.browser.unknown-component-prop': {'code': 'citry.browser.unknown-component-prop',
                                          'constant': 'BROWSER_UNKNOWN_COMPONENT_PROP',
                                          'defaultSeverity': 'error',
                                          'documentationPath': '/ide/diagnostics/#citry.browser.unknown-component-prop',
                                          'examples': [{'language': 'citry-html',
                                                        'source': '<c-card $c-props="{ missing: value }" />',
                                                        'title': 'Unknown client prop'}],
                                          'messages': {'default': "Client prop '{name}' is not declared by <{tag}>."},
                                          'parameters': {'name': 'Authored client-prop key.',
                                                         'tag': 'Authored child component tag.'},
                                          'summary': 'A static $c-props object contains a key that the child component '
                                                     'does not declare.',
                                          'surfaces': ['check', 'lsp'],
                                          'title': 'Unknown client prop',
                                          'when': 'A statically resolved component receives a direct $c-props object '
                                                  'key absent from its static $component({props}) declaration.'},
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
                                        'when': 'An Alpine expression or component JavaScript calls sendEvent, '
                                                '$sendEvent, $loading, or $error with an unknown non-empty string '
                                                'literal, or a declarative @c-* binding names an unknown handler.'},
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
 'citry.component-js.unknown-variable': {'code': 'citry.component-js.unknown-variable',
                                         'configurableSeverity': True,
                                         'constant': 'COMPONENT_JS_UNKNOWN_VARIABLE',
                                         'defaultSeverity': 'error',
                                         'documentationPath': '/ide/diagnostics/#citry.component-js.unknown-variable',
                                         'examples': [{'language': 'javascript',
                                                       'source': '$component(({ data }) => {\n'
                                                                 '  scope.ready = data.ready;\n'
                                                                 '});',
                                                       'title': 'Missing callback destructuring'}],
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
                                         'messages': {'default': 'Alpine CSP 3.16.2 cannot evaluate {detail} here. '
                                                                 'Move complex logic to Component.js and call a scope '
                                                                 'method from the template.'},
                                         'parameters': {'detail': 'The unsupported directive, host, token, or '
                                                                  'operation.'},
                                         'summary': 'An Alpine or Citry browser expression uses a host or source form '
                                                    'unsupported by the pinned Alpine CSP evaluator.',
                                         'surfaces': ['check', 'lsp'],
                                         'title': 'Browser code is incompatible with strict CSP',
                                         'when': 'The selected Citry application configures CSP warning or strict mode '
                                                 'and a source-classifiable browser expression is incompatible with '
                                                 'Alpine CSP 3.16.2.'},
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
                                             'variables.'}}

EXTERNAL_CODE_PREFIXES: Final = [{'prefix': 'citry.python.',
  'provider': 'ty',
  'summary': 'Python semantic diagnostics retained from the pinned ty analyzer. The suffix and message remain '
             'provider-owned.'}]

# fmt: on
