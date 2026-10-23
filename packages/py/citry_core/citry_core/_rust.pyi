# This file adds typing for the API exposed from Rust via maturin.
#
# IMPORTANT: The filename `_rust.pyi` matches the `<rust_module_name>` part of
# the `module-name` setting in `pyproject.toml` (`tool.maturin.module-name = "citry_core._rust"`).
# This ensures type checkers can find the type stubs for the Rust extension module.
#
# Since the Rust code exposed to Python is scoped under modules, we need to define
# the API as class attributes, e.g.
#
# ```py
# class template_parser:
#     class Tag:
#         ...
# ```
#
# So that in Python we can access it as:
#
# ```py
# from citry_core import _rust
# _rust.template_parser.Tag(...)
# ```
#
# Notes:
# - Functions without `self` are treated as module-level functions.
#   This matches how typeshed defines modules.

from collections.abc import Callable, Iterable, Mapping
from typing import Any, Literal

# Whether this extension was compiled without optimizations ("debug", the
# plain `maturin develop` build) or with them ("release", `--release` and
# published wheels). Benchmarks refuse to measure a "debug" build.
BUILD_PROFILE: Literal["release", "debug"]

########################################################
# Internationalization
########################################################

class i18n:
    class I18nCompileError(ValueError):
        code: str
        diagnostic_json: str

    class CompiledCatalog:
        @property
        def schema_version(self) -> int: ...
        @property
        def revision(self) -> str: ...
        @property
        def formats_revision(self) -> str: ...
        def artifact_json(self) -> str: ...
        def browser_artifact_json(self, locale: str, request_json: str) -> str: ...
        def browser_parser_artifact_json(self, locale: str) -> str: ...
        def format(
            self,
            locale: str,
            message_id: str,
            args_json: str = "{}",
            attribute: str | None = None,
        ) -> str: ...
        def resolve_json(
            self,
            locale: str,
            message_id: str,
            args_json: str = "{}",
            attribute: str | None = None,
        ) -> str: ...
        def _resolve(
            self,
            locale: str,
            message_id: str,
            args_json: str = "{}",
            attribute: str | None = None,
        ) -> tuple[str, str, bool]: ...
        def resolve_rich_json(
            self,
            locale: str,
            message_id: str,
            args_json: str,
            slot_names_json: str,
            attribute: str | None = None,
        ) -> str: ...
        def format_number(self, locale: str, profile: str, value: str) -> str: ...
        def parse_number_json(self, locale: str, profile: str, input: str) -> str: ...
        def format_percent(self, locale: str, profile: str, value: str) -> str: ...
        def parse_percent_json(self, locale: str, profile: str, input: str) -> str: ...
        def format_currency(
            self,
            locale: str,
            profile: str,
            value: str,
            currency: str,
        ) -> str: ...
        def format_date(
            self,
            locale: str,
            profile: str,
            year: int,
            month: int,
            day: int,
        ) -> str: ...
        def parse_date_json(self, locale: str, profile: str, input: str) -> str: ...
        def parse_date_segments_json(
            self,
            locale: str,
            profile: str,
            year: str,
            month: str,
            day: str,
        ) -> str: ...
        def format_time(
            self,
            locale: str,
            profile: str,
            hour: int,
            minute: int,
            second: int,
            nanosecond: int,
        ) -> str: ...
        def parse_time_json(self, locale: str, profile: str, input: str) -> str: ...
        def parse_time_segments_json(
            self,
            locale: str,
            profile: str,
            hour: str,
            minute: str,
            second: str | None,
            day_period: str | None,
        ) -> str: ...
        def format_datetime(
            self,
            locale: str,
            profile: str,
            year: int,
            month: int,
            day: int,
            hour: int,
            minute: int,
            second: int,
            nanosecond: int,
            time_zone: str,
            offset_seconds: int,
            epoch_seconds: int,
        ) -> str: ...
        def parse_datetime_json(self, locale: str, profile: str, input: str) -> str: ...
        def parse_datetime_segments_json(
            self,
            locale: str,
            profile: str,
            year: str,
            month: str,
            day: str,
            hour: str,
            minute: str,
            second: str | None,
            day_period: str | None,
        ) -> str: ...
        def format_relative_time(
            self,
            locale: str,
            profile: str,
            value: str,
            unit: str,
        ) -> str: ...
        def format_list(self, locale: str, profile: str, values: list[str]) -> str: ...
        def format_unit(
            self,
            locale: str,
            profile: str,
            value: str,
            unit: str,
        ) -> str: ...

    class CatalogCompiler:
        def __init__(self) -> None: ...
        def compile(self, request_json: str) -> i18n.CompiledCatalog: ...
        def compile_link_unit(self, request_json: str) -> str: ...
        def analyze_source(self, path: str, source: str) -> str: ...
        def clear(self) -> None: ...

    class TextCatalog:
        def __init__(self, locale: str, source: str, origin: str) -> None: ...
        @property
        def origin(self) -> str: ...
        def entries(self) -> list[tuple[str, bool, list[str]]]: ...
        def format(self, message_id: str, attribute: str | None = None) -> str: ...

    @staticmethod
    def canonicalize_locale(value: str) -> str: ...
    @staticmethod
    def locale_direction(value: str) -> str | None: ...

########################################################
# HTML transform
########################################################

class html_transform:
    @staticmethod
    def browser_fragment_matches_elements(
        html: str,
        context: str,
        expected: list[tuple[bool, str, list[tuple[str, str | None]]]],
    ) -> bool: ...
    @staticmethod
    def browser_fragment_matches_nodes(
        html: str,
        context: str,
        expected: list[tuple[str, str, list[tuple[str, str | None]]]],
    ) -> bool:
        """
        Check that the browser builds the expected nodes from an HTML fragment.

        Each expected event is a `(kind, value, attributes)` tuple, in
        document order: `("open", tag, attributes)` for an element whose
        children follow, `("close", tag, [])` for its end, `("shell", tag,
        attributes)` for an element whose contents Vue builds in the browser,
        checked with any contents the server wrote there cut out of `html`
        (its attributes must include `("data-allow-mismatch",
        "children")`, it must have no child nodes, and no `close` follows it),
        `("comment", data, [])` for a Vue anchor comment (`[`, `]`, `v-if`,
        or empty), and `("text", value, [])` for whitespace-only text directly
        in the fragment root.

        Returns `False` when the browser's tree differs, including any comment
        or root text that is not expected.

        Raises `ValueError` if a kind is unknown, or a `close`, `comment`, or
        `text` event carries attributes.
        """
    @staticmethod
    def validate_html_fragment_boundary(html: str) -> None: ...
    @staticmethod
    def static_html_node_count(html: str) -> int:
        """
        Count the top-level nodes the browser creates when Vue inserts `html`
        as one fixed block while it builds a page.

        The browser parses the block inside a `<template>` element, so table
        parts stay where they are written. Vue needs this count to adopt the
        block's nodes when the server already wrote them into the page.
        """
    @staticmethod
    def scan_output_html(html: str) -> list[dict[str, object]]: ...
    @staticmethod
    def _check_output_html(
        html: str,
        *,
        pre_extension: bool,
        csp: bool,
        javascript: Literal["warn", "omit", "forbid"] | None,
        marker_prefix: str | None,
        trusted_tag_starts: frozenset[int],
        omit_handler_marker: str | None,
    ) -> tuple[list[tuple[Any, ...]], str | None]:
        """
        Run the strict-CSP and JavaScript-policy rules over finished HTML.

        Private to `citry`. Returns `(events, cleaned_html)`. Each event is a
        tuple in start-tag order: `("element", tag, token_start, name_start,
        name_end, element_end, trusted, executable, has_manager_attribute,
        cids)` for a `script` or `style` element a selected rule looks at, or
        `(rule, tag, attribute, start, end, token_start, cids)` for one
        attribute or element a rule reports. `cleaned_html` is the page with
        every omit marker removed, or `None` when there was none. Offsets are
        UTF-8 byte offsets.

        Raises `ValueError` for an unknown `javascript` mode.
        """
    @staticmethod
    def _script_type_is_executable(value: str) -> bool:
        """Whether a `<script>` with this `type` value runs in the browser. Private to `citry`."""
    @staticmethod
    def _classify_dependency_attribute(tag: str, name: str, value: str | None) -> int:
        """
        Classify one attribute of a structured `Script` or `Style`. Private to `citry`.

        Returns bit flags: 1 for a Vue activation attribute, 2 for a native
        inline event attribute, 4 for a `javascript:` URL in a URL attribute.
        """
    @staticmethod
    def _is_javascript_url(value: str) -> bool:
        """Whether a URL starts with `javascript:`, read without entity decoding. Private to `citry`."""
    _JAVASCRIPT_MIME_TYPES: frozenset[str]
    @staticmethod
    def mark_html(
        html: str,
        root_attributes: list[str],
        placeholder_attr: str,
    ) -> tuple[list[str], list[tuple[str, str, list[str]]]]:
        """
        Splice attributes onto root-level tags and split the HTML around child
        placeholder elements, in a single scan.

        This is the serializer's fast path. Each attribute in `root_attributes`
        is added (as `attr=""`) to every root-level (depth 0) tag. A placeholder
        is a `<template>` element carrying `placeholder_attr` with a
        whitespace-only body; the output is split around placeholders so the
        caller can join in each child's finished HTML without scanning again.

        Unlike `transform_html`, bytes outside root-level tags are copied
        through verbatim (no re-serialization or normalization), and malformed
        markup is treated as text rather than raising.

        **Arguments**

        - `html` (str): The HTML string to mark. Can be a fragment or full document.
        - `root_attributes` (List[str]): Attribute names to add to root-level tags.
        - `placeholder_attr` (str): The attribute that identifies placeholder elements.

        **Returns**

        A tuple `(segments, placeholders)`:
            - `segments` (List[str]): the marked HTML split around placeholders;
                always exactly `len(placeholders) + 1` entries.
            - `placeholders` (List[Tuple[str, str, List[str]]]): one entry per
                placeholder, in document order: `(id, placeholder_html, added_attributes)`
                where `id` is the placeholder attribute's value, `placeholder_html`
                is the placeholder element's text (with any spliced attributes,
                for callers that leave unknown ids in place), and
                `added_attributes` lists the attributes spliced into it
                (non-empty only for root-level placeholders).

        The marked HTML is `segments[0] + placeholders[0][1] + segments[1] + ...`.

        **Example**

        ```python
        >>> segments, placeholders = mark_html(
        ...     '<div><template c-render-id="c2"></template></div>',
        ...     ['data-cid-c1'],
        ...     'c-render-id',
        ... )
        >>> segments
        ['<div data-cid-c1="">', '</div>']
        >>> placeholders
        [('c2', '<template c-render-id="c2"></template>', [])]
        ```
        """

    @staticmethod
    def transform_html(
        html: str,
        root_attributes: list[str],
        all_attributes: list[str],
        check_end_names: bool | None = None,
        track_added_attributes_for_tags_with_this_attribute: str | None = None,
    ) -> tuple[str, dict[str, list[str]]]:
        """
        Transform given HTML string.

        This function performs the following transformations:

        1. **Add root attributes**: Attributes specified in `root_attributes` are added
        only to root-level elements (elements at depth 0).

        2. **Add attributes to all elements**: Attributes specified in `all_attributes`
        are added to every element in the HTML.

        In addition, this transformer also:

        1. **Tracks added attributes**: If `track_added_attributes_for_tags_with_this_attribute`
        is set, captures which attributes were added to elements that have the specified
        attribute, returning a dictionary mapping attribute values to lists of attributes added to tag.

        2. **Validates end tags**: If `check_end_names` is enabled, validates that
        closing tags match their corresponding opening tags.

        **Arguments**

        - `html` (str): The HTML string to transform. Can be a fragment or full document.
        - `root_attributes` (List[str]): List of attribute names to add to root elements only.
        - `all_attributes` (List[str]): List of attribute names to add to all elements.
        - `check_end_names` (Optional[bool]): Whether to validate matching of end tags. Defaults to False.
        - `track_added_attributes_for_tags_with_this_attribute` (Optional[str]): If set, captures which attributes were added to elements with this attribute.

        **Returns**

        A tuple containing:
            - The transformed HTML string
            - A dictionary mapping captured attribute values to lists of attributes that were added
                to those elements. Only populated if `track_added_attributes_for_tags_with_this_attribute` is set, otherwise empty dict.

        **Example**

        ```python
        >>> html = '<div data-id="123"><p>Hello</p></div>'
        >>> html, captured = transform_html(html, ['data-root-id'], ['data-v-123'], track_added_attributes_for_tags_with_this_attribute='data-id')
        >>> print(captured)
        {'123': ['data-root-id', 'data-v-123']}
        ```

        **Raises**

        ValueError: If the HTML is malformed or cannot be parsed.
        """

########################################################
# Client graph
########################################################

class safe_eval:
    @staticmethod
    def safe_eval(source: str) -> str:
        """
        Transform a Python expression string to make it safe for evaluation.

        This function takes a Python expression string and transforms it into safe code
        by wrapping potentially unsafe operations (like variable access, function calls,
        attribute access, etc.) with sandboxed function calls.

        **Args:**

        - source (str): The Python expression string to transform.

        **Returns:**

        - str: The transformed Python expression as a string.

        **Raises:**

        - SyntaxError: If the input is not valid Python syntax or contains forbidden constructs.

        **Examples:**

        ```python
        >>> safe_eval("my_var + 1")
        'variable("my_var") + 1'

        >>> safe_eval("lambda x: x + my_var")
        'lambda x: x + variable("my_var")'
        ```

        **Transformations:**

        The following transformations are applied to make expressions safe for evaluation:

        1. **Variable access** - `my_var` → `variable("my_var")`
        2. **Function calls** - `foo(1, 2, a=3, *args, **kwargs)` → `call(foo, 1, 2, a=x, *args, **kwargs)`
        3. **Attribute access** - `obj.attr` → `attribute(obj, "attr")`
        4. **Subscript access** - `obj[key]` → `subscript(obj, key)`
        5. **Walrus operator** - `(x := value)` → `assign("x", value)`

        Because of the changes above, we also need to transform:

        6. **Slice notation** - `obj[1:10:2]` → `subscript(obj, slice(1, 10, 2))`
           - Because slice syntax is valid only inside square brackets.
        7. **F-strings** - `f"Hello {price!r:.2f}"` → `format("Hello {}", (variable("price"), "r", ".2f"))`
           - To avoid issues with quote escaping and enable error reporting
        8. **T-strings** - `t"Hello {name!r:>10}"` → `template("Hello ", interpolation(variable("name"), "expr", "r", ">10"))`
           - To avoid issues with quote escaping
        """

########################################################
# Template formatter
########################################################

class template_formatter:
    class TemplateFormatError(ValueError):
        """A structured refusal to format authored Citry template text."""

        code: str
        message: str
        range: tuple[int, int] | None
        diagnostic: template_parser.ParseDiagnostic | None

    class _EmbeddedFormatPlan:
        """Opaque source-bound handle for an embedded-formatting pass."""

        @property
        def id(self) -> str: ...
        @property
        def formatted_source(self) -> str: ...
        @property
        def requests(
            self,
        ) -> list[
            tuple[
                str,
                str,
                str,
                str,
                str,
                tuple[int, int],
                int,
                str,
            ]
        ]: ...
        @property
        def notices(
            self,
        ) -> list[tuple[str, str, str | None, str | None]]: ...

    @staticmethod
    def format_template(
        source: str,
        *,
        options: template_parser.ParseOptions | None = None,
    ) -> str: ...
    @staticmethod
    def python_expression_provider() -> str: ...
    @staticmethod
    def prepare_embedded_format(source: str) -> template_formatter._EmbeddedFormatPlan: ...
    @staticmethod
    def finish_embedded_format(
        plan: template_formatter._EmbeddedFormatPlan,
        results: list[
            tuple[
                str,
                str,
                str,
                str | None,
                str | None,
                str | None,
            ]
        ],
    ) -> tuple[
        str,
        list[tuple[str, str, str | None, str | None]],
        list[str],
    ]: ...

########################################################
# Vue compiler
########################################################

class vue:
    @staticmethod
    def _compile_vue(
        template: str,
        local_calls_json: str = "[]",
        element_bindings_json: str = "[]",
        local_call_runs_json: str = "[]",
        dynamic_elements_json: str = "[]",
    ) -> str: ...

    class ServerRenderProgram:
        """
        One compiled render function, read once so the server can run it to
        write HTML that Vue adopts in the browser.
        """

        @property
        def fully_supported(self) -> bool:
            """Whether every part was read; unread parts are left for the browser to build."""

    @staticmethod
    def _read_server_render_program(code: str, dynamic_elements_json: str = "[]") -> vue.ServerRenderProgram:
        """
        Read a compiled render function (`code` from the compiler artifact).

        Raises `ValueError` if the code is not a render function the compiler
        emits, or the dynamic element metadata is invalid.
        """
    @staticmethod
    def _render_for_hydration(
        programs: dict[str, vue.ServerRenderProgram],
        manifest_json: str,
        tags: dict[str, str],
        threshold: int,
        *,
        full_parse_check: bool = False,
    ) -> tuple[str | None, int, int, list[tuple[str, str, str | None, str | None, bool]], str | None]:
        """
        Write a page's Vue host content for hydration from its prepared manifest.

        `programs` maps compiled definition ids to their read render
        functions, `manifest_json` is the prepared manifest, `tags` maps each
        type key to its registered component tag, and the page is only
        returned when it writes more than `threshold` elements.
        `full_parse_check` parses the whole written HTML instead of first
        checking its tokens against stored parser answers; the two checks
        must agree, and the render parity check reports any page where they
        do not. Returns `(html, element_count, shell_count, declines,
        reason)`, where each decline is `(code, detail, component type key,
        shell tag, shell content)`; `shell content` is `True` when the shell
        carries Citry's HTML for its contents, which the browser runtime
        removes before Vue hydrates. `html` is `None` and `reason` names why
        when the page should mount in the browser instead.
        """

########################################################
# Native render path
########################################################

class native_render:
    """
    The Rust half of Citry's native render path; every member is private to Citry.

    ``citry._vue.native_render`` decides whether Citry uses this module. Citry
    builds one ``_RowPlan`` per ``simple='vue'`` template its Python
    evaluator can run without a component instance, from
    ``citry._vue.leaf_program.native_row_plan_tuples`` and asks it for each
    row; ``_RunDigests`` computes the ids of each row of a call run (the
    components one ``c-for`` places), for ordinary components too. When
    Rust read every row of a call run, serialize records the run with one
    ``_NativeRun``, and the view holds one ``_NativeOccurrence`` per row.
    ``_CallRunWalkPlan`` reads every row of a call run's loop in one call,
    when the loop's iterable, the call's inputs and its key are plain paths.
    ``_leaf_values_json`` writes the JSON of an ordinary component's leaf
    data (the values its template, compiled into one leaf program, sends to
    the browser) into a ``_LeafJson``.
    """

    class _RowPlan:
        """The template's operations and read set, ready to check and evaluate rows."""

        def __new__(
            cls,
            ops: tuple[tuple[object, ...], ...],
            roots: tuple[tuple[str, tuple[object, ...]], ...],
            loop_targets: tuple[str, ...],
            spread_limit: int,
            js_safe_integer: int,
        ) -> native_render._RowPlan:
            """
            Build a plan from ``native_row_plan_tuples(node)``.

            Raises `ValueError` when the description has a shape Rust cannot
            evaluate exactly; the template then keeps the Python evaluator. A
            Rust panic raises `RuntimeError`.
            """
        def read(self, variables: object, plain_scalar_types: frozenset[type]) -> native_render._NativeRow | None:
            """
            Check, copy and evaluate one row.

            Returns None when the row is not plain data or is outside what Rust
            reproduces exactly; Python's evaluator then runs on the same
            variables and raises its own error when there is one. An error a
            layout callback raises, or one raised while reading inside a
            value, also gives None; an error raised while looking up a
            variable itself (a key's ``__eq__``) propagates. A Rust panic
            raises `RuntimeError`.
            """

    class _NativeRow:
        """One row Rust read: its copied values and its prepared data's JSON."""

        @property
        def prepared_json(self) -> str:
            """The row's prepared data as ``script_json({"calls": {}, **data}, sort_keys=True)`` writes it."""
        def snapshot(self) -> dict[str, object]:
            """Rebuild the values Rust read as a fresh variables dict. A Rust panic raises `RuntimeError`."""

    class _RunDigests:
        """The two ids of each row of one call run, with the run's shared leading text hashed once."""

        def __new__(cls, placement_prefix_json: str, child_prefix_json: str) -> native_render._RunDigests:
            """Take the JSON text Python's ``_DigestPrefix`` hashes before each row's own item."""
        def member_ids(self, key: str) -> tuple[str, str] | None:
            """Return ``(placement_key, child_id)``, or None for a key with no UTF-8 form."""

    class _NativeRun:
        """One call run whose rows Rust read, recorded with one object instead of one record per row."""

        @staticmethod
        def try_new(
            members: list[object],
            record_type: type,
            component_class: object,
            fragment: object,
            source: object,
            source_span: object,
            placement_prefix_json: str,
            child_prefix_json: str,
            parent_id: str,
            type_key: str,
            definition_id: str,
        ) -> native_render._NativeRun | None:
            """
            Read and check a run's members and compute their ids, changing no assembly state.

            Returns None when any member is not an exact ``record_type`` with
            a ``_NativeRow``, has ``js_data`` or root markers, holds a
            different class, fragment, source or span object from the ones
            given, has a class id other than ``type_key``, or has a key or
            render id that is not an exact str with a UTF-8 form; when a key,
            render id or child id repeats; when ``members`` or ``type_key`` is
            empty; or when ``parent_id``, ``type_key`` or ``definition_id`` is
            not an exact str with a UTF-8 form. Returns None too when reading
            a member raises an `Exception`; any other exception, such as
            `KeyboardInterrupt`, propagates. A Rust panic raises
            `RuntimeError`.
            """
        def commit(
            self,
            seen_render_ids: set[str],
            seen_occurrence_ids: set[str],
            local_identity_keys: set[tuple[tuple[object, ...], tuple[str, ...], object]],
            member_base: tuple[object, ...],
            placement_route: tuple[str, ...],
            supplied_fills: dict[str, Any],
            occurrence_to_render: dict[str, str],
            render_to_occurrence: dict[str, str],
            occurrence_types: dict[str, str],
            occurrence_parents: dict[str, str | None],
            occurrence_placement_keys: dict[str, str | None],
        ) -> bool:
            """
            Check every row against assembly's live state, then write the rows' entries in row order.

            Returns False, having written nothing, when a row's render id or
            child id is already seen, its identity is in
            ``local_identity_keys``, or ``supplied_fills`` has an entry for it.
            A Rust panic raises `RuntimeError`.
            """
        def check_invariants(
            self, reference_parents: dict[str, list[str]], placements: set[tuple[str, str]]
        ) -> tuple[int, int] | None:
            """
            Make assembly's final per-occurrence checks for the rows, in row order.

            Returns ``(row index, check)`` for the first row that fails: check
            0 when another call references it, check 1 when its parent and
            placement key are already in ``placements``. Adds each row's pair
            to ``placements`` otherwise. A Rust panic raises `RuntimeError`.
            """
        def member_ids(self) -> list[str]:
            """Return the rows' child occurrence ids, in row order."""
        def occurrences(self) -> list[native_render._NativeOccurrence]:
            """Return one ``_NativeOccurrence`` per row, in row order."""
        def holds_any(self, ids: Iterable[object]) -> bool:
            """Return whether any of ``ids`` is one of the rows' child occurrence ids."""
        @property
        def parent_id(self) -> str: ...
        @property
        def type_key(self) -> str: ...
        @property
        def definition_id(self) -> str: ...
        def __len__(self) -> int: ...

    class _NativeOccurrence:
        """
        One row of a ``_NativeRun``, as the view's occurrence list holds it.

        ``server_data`` and ``prepared_data`` are read-only mappings shared by
        every row: an empty one, and ``{"calls": {}}``.
        """

        @property
        def id(self) -> str: ...
        @property
        def type_key(self) -> str: ...
        @property
        def definition_id(self) -> str: ...
        @property
        def parent_id(self) -> str: ...
        @property
        def placement_key(self) -> str: ...
        @property
        def render_id(self) -> str: ...
        @property
        def _native(self) -> native_render._NativeRow: ...
        @property
        def server_data(self) -> Mapping[str, object]: ...
        @property
        def prepared_data(self) -> Mapping[str, object]: ...
        @property
        def run(self) -> native_render._NativeRun: ...
        @property
        def index(self) -> int: ...

    class _CallRunWalkPlan:
        """
        The Rust loop walk of one ``c-for`` call run.

        A call run is the rows one ``c-for`` places at one component call
        site. ``ForNode`` builds one plan per loop node from the paths that
        ``citry._vue.native_walk`` makes from the loop's iterable, the call's
        inputs and its key. Each path is ``(name, steps)``: a name, then
        constant subscripts (``str`` or non-negative ``int``).
        """

        def __new__(
            cls,
            target: str,
            iterable: tuple[str, tuple[str | int, ...]],
            kwargs: list[tuple[str, tuple[str | int, ...]]],
            key: tuple[str, tuple[str | int, ...]],
            kwarg_names: list[str],
            name: str,
            source: object,
            position: object,
            metadata_class: type,
            scope_type: type,
            marker_type: type,
        ) -> native_render._CallRunWalkPlan:
            """
            Check the paths and build the plan.

            Raises `ValueError` for a ``_`` name, a negative index or another
            malformed argument, and `RuntimeError` for a Rust panic.
            """
        def walk(
            self, variables: object, get: Callable[[str], type], run_class: type, origin: str | None
        ) -> tuple[list[dict[str, object]], list[object]] | str:
            """
            Read every row of the loop, then look each row's class up with ``get``.

            Returns each row's kwargs dict and ``_PreparedCallMetadata``, in
            loop order, or a ``str`` naming why it declined: ``scope`` (the
            variables are neither an exact ``dict`` nor ``scope_type``),
            ``iterable``, ``missing``, ``not_plain``, ``marker``,
            ``key_type``, ``read_raised``, ``get_raised``, ``class_changed``,
            ``build_raised`` or ``panic``. Anything the walk calls that raises
            an ``Exception`` makes it decline; any other ``BaseException``
            propagates, except PyO3's ``PanicException``, which declines as
            ``panic``. The reads run no template or user code, except that a
            dict lookup runs ``__eq__`` on a stored key whose hash equals the
            key looked up.
            """

    class _LeafJson:
        """
        The JSON Rust wrote for each value of one occurrence's leaf data.

        The cyclic garbage collector does not track it: it holds Rust
        strings and the placeholder, which never refers to a ``_LeafJson``.
        """

        def __len__(self) -> int:
            """The number of leaf values Rust wrote."""

    @staticmethod
    def _leaf_values_json(values: object, placeholder: object) -> native_render._LeafJson | str:
        """
        Write the JSON of each value of one leaf's data, as ``_script_json(_json_plain(value))`` writes it.

        Returns a ``_LeafJson``; Python then stores ``placeholder`` under
        each key of ``values``. Otherwise it returns why Rust declines:
        ``not_plain`` (a value whose type is not exactly ``None``, ``bool``,
        ``int``, ``float``, ``str``, ``list``, ``tuple`` or ``dict``, a key
        that is not exactly ``str``, or ``values`` not exactly a dict),
        ``non_finite``, ``big_int`` (outside 64 bits), ``not_utf8`` (a lone
        surrogate in a str or key), ``cycle`` or ``too_deep`` (nesting
        deeper than 200). Python then converts the leaf itself.
        ``placeholder`` must never refer to a ``_LeafJson``: the collector
        does not track a ``_LeafJson``, so such a cycle would never be
        freed. Citry passes ``native_leaf_json.PLACEHOLDER``. A Rust panic
        raises `RuntimeError`.
        """

    @staticmethod
    def _encode_occurrences(
        occurrences: list[object],
        natives: dict[str, native_render._NativeRow | native_render._LeafJson],
        fallback: Callable[[dict[str, object]], str],
        definition_ids: dict[str, str] | None = None,
    ) -> str:
        """
        Write a manifest's occurrence array, with the prepared data Rust wrote in place.

        An item whose id maps to a ``_NativeRow`` gets that row's prepared
        data. An item whose id maps to a ``_LeafJson`` gets that leaf's JSON
        at each placeholder in its ``preparedData``, and its other values as
        ``fallback`` writes them. A ``_NativeRun`` item stands for all its
        rows, in order. Rust writes each row with the run's compiled
        definition id, which it looks up in ``definition_ids`` (logical id to
        compiled id). Every other item whose id is not in ``natives`` is
        written by ``fallback(item)``. Raises `ValueError` when an item is
        neither a dict nor a ``_NativeRun``, ``natives`` maps an item to
        anything else, a Rust-read row's item does not have the exact shape
        assembly gives it, a leaf occurrence's ``preparedData`` is not an
        exact dict, holds a placeholder whose key has no JSON or lacks a
        placeholder for a value Rust wrote, a leaf occurrence's item has a
        key that is not a str or loses a key while ``fallback`` runs, a run comes
        without ``definition_ids`` or its definition has no compiled id there
        or that id is not a str, or ``fallback`` returns something other than
        a str. A Rust panic raises `RuntimeError`.
        """

########################################################
# Template parser (V3)
########################################################

class template_parser:
    @staticmethod
    def analyze_browser_binding_pattern(
        input: str,
    ) -> tuple[bool, list[tuple[str, int, int]], list[tuple[str, int, int]]]: ...
    @staticmethod
    def analyze_browser_source(
        input: str,
        mode: Literal["expression", "statement"],
    ) -> template_parser.BrowserAnalysis: ...
    @staticmethod
    def analyze_component_scope_writes(
        input: str,
    ) -> list[tuple[str, int, int, int, int]]: ...
    @staticmethod
    def analyze_component_source(
        input: str,
    ) -> template_parser.BrowserComponentAnalysis: ...
    # Functions
    @staticmethod
    def parse_template(
        input: str,
        lang: str | None = None,
        user_rules: dict[str, template_parser.TagRules] | None = None,
        *,
        options: template_parser.ParseOptions | None = None,
    ) -> template_parser.Template: ...
    @staticmethod
    def compile_template(
        template: template_parser.Template,
        lang: str | None = None,
    ) -> str: ...
    @staticmethod
    def _compile_prepared_template(
        template: template_parser.Template,
        lang: str | None = None,
    ) -> str: ...
    def format_number(self, locale: str, profile: str, value: str) -> str: ...
    def format_currency(self, locale: str, profile: str, value: str, currency: str) -> str: ...
    def format_date(self, locale: str, profile: str, year: int, month: int, day: int) -> str: ...
    def format_relative_time(self, locale: str, profile: str, value: str, unit: str) -> str: ...
    def format_list(self, locale: str, profile: str, values: list[str]) -> str: ...

    # Browser analysis records. Offsets are UTF-8 byte offsets into the
    # analyzed text. Each record compares equal by value.

    class BrowserSyntaxDiagnostic:
        """The JavaScript parser's first error; `start <= end <=` the text's length in UTF-8 bytes."""

        message: str
        start: int
        end: int

    class BrowserReference:
        """One free name; `written` is true when the code assigns to or updates it there."""

        name: str
        start: int
        end: int
        written: bool

    class BrowserAnalysis:
        """Result of `analyze_browser_source`; `error` is set exactly when `valid` is false."""

        valid: bool
        error: template_parser.BrowserSyntaxDiagnostic | None
        references: list[template_parser.BrowserReference]

    class BrowserComponentBinding:
        """One `$component` context field destructured into a local variable."""

        name: Literal[
            "component",
            "revision",
            "onEvent",
            "id",
            "els",
            "state",
            "sendEvent",
            "loading",
            "error",
            "i18n",
        ]
        local_name: str
        start: int
        end: int
        references: list[tuple[int, int]]

    class BrowserComponentCall:
        """One `$component(...)` call and the range of its first argument."""

        call_start: int
        call_end: int
        callee_start: int
        callee_end: int
        open_paren_end: int
        argument_start: int | None
        argument_end: int | None

    class BrowserPublicName:
        """One statically named instance member declared by a Vue options section."""

        authored_name: str
        exposed_name: str
        origin: str
        name_start: int
        name_end: int
        value_start: int | None
        value_end: int | None
        required: bool | None
        has_default: bool | None
        default_is_null: bool | None
        type_source: str | None

    class BrowserOptionsSection:
        """What one `$component` call proves about one Vue options section."""

        name: str
        state: Literal["absent", "complete", "unknown"]
        start: int | None
        end: int | None
        unknown_reason: str | None

    class BrowserComponentMemberReference:
        """One member the code reads or writes through `this` or the `$component` context, such as `this.open`."""

        receiver: str
        name: str
        start: int
        end: int
        written: bool

    class BrowserEmitName:
        """One event name declared by an `emits` section."""

        name: str
        start: int
        end: int

    class BrowserDirectiveName:
        """One custom directive name declared by a `directives` section."""

        name: str
        start: int
        end: int

    class BrowserComponentAnalysis:
        """Result of `analyze_component_source`; every list is empty when `valid` is false."""

        valid: bool
        references: list[template_parser.BrowserReference]
        bindings: list[template_parser.BrowserComponentBinding]
        component_calls: list[template_parser.BrowserComponentCall]
        public_names: list[template_parser.BrowserPublicName]
        sections: list[template_parser.BrowserOptionsSection]
        member_references: list[template_parser.BrowserComponentMemberReference]
        emits_sections: list[template_parser.BrowserOptionsSection]
        emit_names: list[template_parser.BrowserEmitName]
        directives_sections: list[template_parser.BrowserOptionsSection]
        directive_names: list[template_parser.BrowserDirectiveName]
        inherit_attrs: list[bool | None]

    # AST types

    class ParseDiagnostic:
        """Machine-readable details attached to a template parse exception."""

        code: str
        message: str
        start_index: int | None
        end_index: int | None
        start_line: int | None
        start_column: int | None
        end_line: int | None
        end_column: int | None

    class Token:
        """A span in the template source with position information."""

        def __init__(
            self,
            content: str,
            start_index: int,
            end_index: int,
            line_col: tuple[int, int],
        ) -> None: ...
        content: str
        start_index: int
        end_index: int
        line_col: tuple[int, int]

    class Comment:
        """A template comment `{# ... #}` or HTML comment `<!-- ... -->`."""

        def __init__(self, token: template_parser.Token, value: template_parser.Token) -> None: ...
        token: template_parser.Token
        value: template_parser.Token

    class HtmlAttrKind:
        """Enum: Static, Expression, Template, or Meta."""

        Static: template_parser.HtmlAttrKind
        Expression: template_parser.HtmlAttrKind
        Template: template_parser.HtmlAttrKind
        Meta: template_parser.HtmlAttrKind

    class FillDataField:
        """One source-to-target field in a fill-data destructuring pattern."""

        def __init__(self, source: template_parser.Token, target: template_parser.Token) -> None: ...
        source: template_parser.Token
        target: template_parser.Token

    class FillDataPattern:
        """A parsed whole-record or one-level fill-data binding."""

        def __init__(
            self,
            token: template_parser.Token,
            whole: template_parser.Token | None,
            fields: list[template_parser.FillDataField],
            rest: template_parser.Token | None,
        ) -> None: ...
        token: template_parser.Token
        whole: template_parser.Token | None
        fields: list[template_parser.FillDataField]
        rest: template_parser.Token | None

    class HtmlAttr:
        """An HTML attribute (static, dynamic expression, nested template, or #c-* framework metadata)."""

        def __init__(
            self,
            token: template_parser.Token,
            key: template_parser.Token,
            value: template_parser.Token | None,
            inner_value: template_parser.Token | None,
            quote_char: str | None,
            kind: template_parser.HtmlAttrKind,
            comments: list[template_parser.Comment],
            used_variables: list[template_parser.Token],
            fill_data_pattern: template_parser.FillDataPattern | None = None,
            foreign_parts: list[template_parser.ForeignSourcePart] = ...,
        ) -> None: ...
        token: template_parser.Token
        key: template_parser.Token
        value: template_parser.Token | None
        inner_value: template_parser.Token | None
        quote_char: str | None
        kind: template_parser.HtmlAttrKind
        used_variables: list[template_parser.Token]
        comments: list[template_parser.Comment]
        fill_data_pattern: template_parser.FillDataPattern | None
        foreign_parts: list[template_parser.ForeignSourcePart]

    class HtmlStartTag:
        """An HTML opening tag with its attributes."""

        def __init__(
            self,
            token: template_parser.Token,
            name: template_parser.Token,
            attrs: list[template_parser.HtmlAttr],
            is_self_closing: bool,
            comments: list[template_parser.Comment],
            foreign_parts: list[template_parser.ForeignSourcePart] = ...,
        ) -> None: ...
        token: template_parser.Token
        name: template_parser.Token
        attrs: list[template_parser.HtmlAttr]
        is_self_closing: bool
        comments: list[template_parser.Comment]
        foreign_parts: list[template_parser.ForeignSourcePart]

    class HtmlEndTag:
        """An HTML closing tag."""

        token: template_parser.Token
        name: template_parser.Token
        comments: list[template_parser.Comment]

    class Expr:
        """A template expression `{{ ... }}`."""

        token: template_parser.Token
        value: template_parser.Token
        used_variables: list[template_parser.Token]
        comments: list[template_parser.Comment]

    class Text:
        """Plain text content."""

        token: template_parser.Token

    class ForeignSourcePart:
        """Original source owned by an installed external template provider."""

        def __init__(
            self,
            token: template_parser.Token,
            provider: str,
            ordinal: int = 0,
            may_control_body: bool = False,
        ) -> None: ...
        token: template_parser.Token
        provider: str
        ordinal: int
        may_control_body: bool

    class Node_SelfClosing:
        """A self-closing HTML/component tag."""

        start_tag: template_parser.HtmlStartTag
        used_variables: list[template_parser.Token]
        introduced_variables: list[template_parser.Token]
        comments: list[template_parser.Comment]
        contains_fills: bool
        name: str

    class Node_WithBody:
        """An HTML/component tag with a body."""

        start_tag: template_parser.HtmlStartTag
        end_tag: template_parser.HtmlEndTag
        body: template_parser.Template
        used_variables: list[template_parser.Token]
        introduced_variables: list[template_parser.Token]
        comments: list[template_parser.Comment]
        contains_fills: bool
        name: str

    class Node:
        """Enum: SelfClosing or WithBody. Access the variant via `._0`."""

        SelfClosing: type[template_parser.Node_SelfClosing]
        WithBody: type[template_parser.Node_WithBody]
        name: str

    class TemplateElement_Text:
        """A TemplateElement variant wrapping Text. Access via `._0`."""

        _0: template_parser.Text

    class TemplateElement_Expr:
        """A TemplateElement variant wrapping Expr. Access via `._0`."""

        _0: template_parser.Expr

    class TemplateElement_Node:
        """A TemplateElement variant wrapping Node. Access via `._0`."""

        _0: template_parser.Node_SelfClosing | template_parser.Node_WithBody

    class TemplateElement_Foreign:
        """A TemplateElement variant wrapping ForeignSourcePart. Access via `._0`."""

        _0: template_parser.ForeignSourcePart

    class TemplateElement:
        """
        Enum: Text, Expr, Node, or Foreign. The concrete variant type is one of
        TemplateElement_Text, TemplateElement_Expr, TemplateElement_Node,
        TemplateElement_Foreign.
        """

        Text: type[template_parser.TemplateElement_Text]
        Expr: type[template_parser.TemplateElement_Expr]
        Node: type[template_parser.TemplateElement_Node]
        Foreign: type[template_parser.TemplateElement_Foreign]

    class StaticNamedSlot:
        """A slot with a statically-known name."""

        token: template_parser.Token
        required: bool | None

    class Template:
        """The parsed template AST."""

        elements: list[
            template_parser.TemplateElement_Text
            | template_parser.TemplateElement_Expr
            | template_parser.TemplateElement_Node
            | template_parser.TemplateElement_Foreign
        ]
        comments: list[template_parser.Comment]
        used_variables: list[template_parser.Token]
        slots: list[template_parser.StaticNamedSlot]

    # Config types

    class TagRules:
        """Validation rules for custom component tags."""

        def __init__(
            self,
            allowed_attrs: list[list[str]] | None = None,
            required_attrs: list[list[str]] | None = None,
            allowed_slots: list[str] | None = None,
            required_slots: list[str] | None = None,
            slot_data_fields: dict[str, list[str]] | None = None,
        ) -> None: ...
        allowed_attrs: list[list[str]] | None
        required_attrs: list[list[str]]
        allowed_slots: list[str] | None
        required_slots: list[str]
        slot_data_fields: dict[str, list[str]]

    class ForeignSpan:
        """A half-open UTF-8 byte range owned by an external provider."""

        def __init__(
            self,
            start_byte: int,
            end_byte: int,
            provider: str,
            ordinal: int = 0,
            may_control_body: bool = False,
        ) -> None: ...
        start_byte: int
        end_byte: int
        provider: str
        ordinal: int
        may_control_body: bool

    class ParseOptions:
        """Optional low-level template parser inputs."""

        def __init__(
            self,
            foreign_spans: list[template_parser.ForeignSpan] = ...,
            source_offset: int = 0,
            root_source: str | None = None,
        ) -> None: ...
        foreign_spans: list[template_parser.ForeignSpan]
        source_offset: int
        root_source: str | None

    # Constants

    HTML_VOID_ELEMENTS: frozenset[str]
    """HTML void elements (elements that cannot have children, e.g. ``<br/>``)."""

    RESERVED_TAG_NAMES: frozenset[str]
    """Structural ``<c-*>`` tags the parser handles itself (e.g. ``c-if``, ``c-slot``),
    so they never resolve to a user component."""

    CITRY_DIRECTIVE_NAMES: frozenset[str]
    """Fixed Citry attribute directives whose spelling is owned by the parser."""

    STRUCTURAL_TAG_ATTRIBUTE_NAMES: Mapping[str, frozenset[str]]
    """Fixed parser-owned attribute spellings keyed by structural tag name."""
