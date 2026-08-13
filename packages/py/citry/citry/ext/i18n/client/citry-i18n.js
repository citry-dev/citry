/* Citry i18n client runtime. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-i18n.ts (pnpm run build there). Bundles @fluent/bundle 0.19.1 (Apache-2.0). */
(() => {
  // ../../../node_modules/.pnpm/@fluent+bundle@0.19.1/node_modules/@fluent/bundle/esm/types.js
  var FluentType = class {
    /**
     * Create a `FluentType` instance.
     *
     * @param value The JavaScript value to wrap.
     */
    constructor(value) {
      this.value = value;
    }
    /**
     * Unwrap the raw value stored by this `FluentType`.
     */
    valueOf() {
      return this.value;
    }
  };
  var FluentNone = class extends FluentType {
    /**
     * Create an instance of `FluentNone` with an optional fallback value.
     * @param value The fallback value of this `FluentNone`.
     */
    constructor(value = "???") {
      super(value);
    }
    /**
     * Format this `FluentNone` to the fallback string.
     */
    toString(scope) {
      return `{${this.value}}`;
    }
  };
  var FluentNumber = class extends FluentType {
    /**
     * Create an instance of `FluentNumber` with options to the
     * `Intl.NumberFormat` constructor.
     *
     * @param value The number value of this `FluentNumber`.
     * @param opts Options which will be passed to `Intl.NumberFormat`.
     */
    constructor(value, opts = {}) {
      super(value);
      this.opts = opts;
    }
    /**
     * Format this `FluentNumber` to a string.
     */
    toString(scope) {
      if (scope) {
        try {
          const nf = scope.memoizeIntlObject(Intl.NumberFormat, this.opts);
          return nf.format(this.value);
        } catch (err) {
          scope.reportError(err);
        }
      }
      return this.value.toString(10);
    }
  };
  var FluentDateTime = class _FluentDateTime extends FluentType {
    static supportsValue(value) {
      if (typeof value === "number")
        return true;
      if (value instanceof Date)
        return true;
      if (value instanceof FluentType)
        return _FluentDateTime.supportsValue(value.valueOf());
      if ("Temporal" in globalThis) {
        const _Temporal = globalThis.Temporal;
        if (value instanceof _Temporal.Instant || value instanceof _Temporal.PlainDateTime || value instanceof _Temporal.PlainDate || value instanceof _Temporal.PlainMonthDay || value instanceof _Temporal.PlainTime || value instanceof _Temporal.PlainYearMonth) {
          return true;
        }
      }
      return false;
    }
    /**
     * Create an instance of `FluentDateTime` with options to the
     * `Intl.DateTimeFormat` constructor.
     *
     * @param value The number value of this `FluentDateTime`, in milliseconds.
     * @param opts Options which will be passed to `Intl.DateTimeFormat`.
     */
    constructor(value, opts = {}) {
      if (value instanceof _FluentDateTime) {
        opts = { ...value.opts, ...opts };
        value = value.value;
      } else if (value instanceof FluentType) {
        value = value.valueOf();
      }
      if (typeof value === "object" && "calendarId" in value && opts.calendar === void 0) {
        opts = { ...opts, calendar: value.calendarId };
      }
      super(value);
      this.opts = opts;
    }
    [Symbol.toPrimitive](hint) {
      return hint === "string" ? this.toString() : this.toNumber();
    }
    /**
     * Convert this `FluentDateTime` to a number.
     * Note that this isn't always possible due to the nature of Temporal objects.
     * In such cases, a TypeError will be thrown.
     */
    toNumber() {
      const value = this.value;
      if (typeof value === "number")
        return value;
      if (value instanceof Date)
        return value.getTime();
      if ("epochMilliseconds" in value) {
        return value.epochMilliseconds;
      }
      if ("toZonedDateTime" in value) {
        return value.toZonedDateTime("UTC").epochMilliseconds;
      }
      throw new TypeError("Unwrapping a non-number value as a number");
    }
    /**
     * Format this `FluentDateTime` to a string.
     */
    toString(scope) {
      if (scope) {
        try {
          const dtf = scope.memoizeIntlObject(Intl.DateTimeFormat, this.opts);
          return dtf.format(this.value);
        } catch (err) {
          scope.reportError(err);
        }
      }
      if (typeof this.value === "number" || this.value instanceof Date) {
        return new Date(this.value).toISOString();
      }
      return this.value.toString();
    }
  };

  // ../../../node_modules/.pnpm/@fluent+bundle@0.19.1/node_modules/@fluent/bundle/esm/resolver.js
  var MAX_PLACEABLES = 100;
  var FSI = "\u2068";
  var PDI = "\u2069";
  function match(scope, selector, key) {
    if (key === selector) {
      return true;
    }
    if (key instanceof FluentNumber && selector instanceof FluentNumber && key.value === selector.value) {
      return true;
    }
    if (selector instanceof FluentNumber && typeof key === "string") {
      let category = scope.memoizeIntlObject(Intl.PluralRules, selector.opts).select(selector.value);
      if (key === category) {
        return true;
      }
    }
    return false;
  }
  function getDefault(scope, variants, star) {
    if (variants[star]) {
      return resolvePattern(scope, variants[star].value);
    }
    scope.reportError(new RangeError("No default"));
    return new FluentNone();
  }
  function getArguments(scope, args) {
    const positional = [];
    const named = /* @__PURE__ */ Object.create(null);
    for (const arg of args) {
      if (arg.type === "narg") {
        named[arg.name] = resolveExpression(scope, arg.value);
      } else {
        positional.push(resolveExpression(scope, arg));
      }
    }
    return { positional, named };
  }
  function resolveExpression(scope, expr) {
    switch (expr.type) {
      case "str":
        return expr.value;
      case "num":
        return new FluentNumber(expr.value, {
          minimumFractionDigits: expr.precision
        });
      case "var":
        return resolveVariableReference(scope, expr);
      case "mesg":
        return resolveMessageReference(scope, expr);
      case "term":
        return resolveTermReference(scope, expr);
      case "func":
        return resolveFunctionReference(scope, expr);
      case "select":
        return resolveSelectExpression(scope, expr);
      default:
        return new FluentNone();
    }
  }
  function resolveVariableReference(scope, { name }) {
    let arg;
    if (scope.params) {
      if (Object.prototype.hasOwnProperty.call(scope.params, name)) {
        arg = scope.params[name];
      } else {
        return new FluentNone(`$${name}`);
      }
    } else if (scope.args && Object.prototype.hasOwnProperty.call(scope.args, name)) {
      arg = scope.args[name];
    } else {
      scope.reportError(new ReferenceError(`Unknown variable: $${name}`));
      return new FluentNone(`$${name}`);
    }
    if (arg instanceof FluentType) {
      return arg;
    }
    switch (typeof arg) {
      case "string":
        return arg;
      case "number":
        return new FluentNumber(arg);
      case "object":
        if (FluentDateTime.supportsValue(arg)) {
          return new FluentDateTime(arg);
        }
      // eslint-disable-next-line no-fallthrough
      default:
        scope.reportError(new TypeError(`Variable type not supported: $${name}, ${typeof arg}`));
        return new FluentNone(`$${name}`);
    }
  }
  function resolveMessageReference(scope, { name, attr }) {
    const message = scope.bundle._messages.get(name);
    if (!message) {
      scope.reportError(new ReferenceError(`Unknown message: ${name}`));
      return new FluentNone(name);
    }
    if (attr) {
      const attribute = message.attributes[attr];
      if (attribute) {
        return resolvePattern(scope, attribute);
      }
      scope.reportError(new ReferenceError(`Unknown attribute: ${attr}`));
      return new FluentNone(`${name}.${attr}`);
    }
    if (message.value) {
      return resolvePattern(scope, message.value);
    }
    scope.reportError(new ReferenceError(`No value: ${name}`));
    return new FluentNone(name);
  }
  function resolveTermReference(scope, { name, attr, args }) {
    const id = `-${name}`;
    const term = scope.bundle._terms.get(id);
    if (!term) {
      scope.reportError(new ReferenceError(`Unknown term: ${id}`));
      return new FluentNone(id);
    }
    if (attr) {
      const attribute = term.attributes[attr];
      if (attribute) {
        scope.params = getArguments(scope, args).named;
        const resolved2 = resolvePattern(scope, attribute);
        scope.params = null;
        return resolved2;
      }
      scope.reportError(new ReferenceError(`Unknown attribute: ${attr}`));
      return new FluentNone(`${id}.${attr}`);
    }
    scope.params = getArguments(scope, args).named;
    const resolved = resolvePattern(scope, term.value);
    scope.params = null;
    return resolved;
  }
  function resolveFunctionReference(scope, { name, args }) {
    let func = scope.bundle._functions[name];
    if (!func) {
      scope.reportError(new ReferenceError(`Unknown function: ${name}()`));
      return new FluentNone(`${name}()`);
    }
    if (typeof func !== "function") {
      scope.reportError(new TypeError(`Function ${name}() is not callable`));
      return new FluentNone(`${name}()`);
    }
    try {
      let resolved = getArguments(scope, args);
      return func(resolved.positional, resolved.named);
    } catch (err) {
      scope.reportError(err);
      return new FluentNone(`${name}()`);
    }
  }
  function resolveSelectExpression(scope, { selector, variants, star }) {
    let sel = resolveExpression(scope, selector);
    if (sel instanceof FluentNone) {
      return getDefault(scope, variants, star);
    }
    for (const variant of variants) {
      const key = resolveExpression(scope, variant.key);
      if (match(scope, sel, key)) {
        return resolvePattern(scope, variant.value);
      }
    }
    return getDefault(scope, variants, star);
  }
  function resolveComplexPattern(scope, ptn) {
    if (scope.dirty.has(ptn)) {
      scope.reportError(new RangeError("Cyclic reference"));
      return new FluentNone();
    }
    scope.dirty.add(ptn);
    const result = [];
    const useIsolating = scope.bundle._useIsolating && ptn.length > 1;
    for (const elem of ptn) {
      if (typeof elem === "string") {
        result.push(scope.bundle._transform(elem));
        continue;
      }
      scope.placeables++;
      if (scope.placeables > MAX_PLACEABLES) {
        scope.dirty.delete(ptn);
        throw new RangeError(`Too many placeables expanded: ${scope.placeables}, max allowed is ${MAX_PLACEABLES}`);
      }
      if (useIsolating) {
        result.push(FSI);
      }
      result.push(resolveExpression(scope, elem).toString(scope));
      if (useIsolating) {
        result.push(PDI);
      }
    }
    scope.dirty.delete(ptn);
    return result.join("");
  }
  function resolvePattern(scope, value) {
    if (typeof value === "string") {
      return scope.bundle._transform(value);
    }
    return resolveComplexPattern(scope, value);
  }

  // ../../../node_modules/.pnpm/@fluent+bundle@0.19.1/node_modules/@fluent/bundle/esm/scope.js
  var Scope = class {
    constructor(bundle, errors, args) {
      this.dirty = /* @__PURE__ */ new WeakSet();
      this.params = null;
      this.placeables = 0;
      this.bundle = bundle;
      this.errors = errors;
      this.args = args;
    }
    reportError(error) {
      if (!this.errors || !(error instanceof Error)) {
        throw error;
      }
      this.errors.push(error);
    }
    memoizeIntlObject(ctor, opts) {
      let cache2 = this.bundle._intls.get(ctor);
      if (!cache2) {
        cache2 = {};
        this.bundle._intls.set(ctor, cache2);
      }
      let id = JSON.stringify(opts);
      if (!cache2[id]) {
        cache2[id] = new ctor(this.bundle.locales, opts);
      }
      return cache2[id];
    }
  };

  // ../../../node_modules/.pnpm/@fluent+bundle@0.19.1/node_modules/@fluent/bundle/esm/builtins.js
  function values(opts, allowed) {
    const unwrapped = /* @__PURE__ */ Object.create(null);
    for (const [name, opt] of Object.entries(opts)) {
      if (allowed.includes(name)) {
        unwrapped[name] = opt.valueOf();
      }
    }
    return unwrapped;
  }
  var NUMBER_ALLOWED = [
    "unitDisplay",
    "currencyDisplay",
    "useGrouping",
    "minimumIntegerDigits",
    "minimumFractionDigits",
    "maximumFractionDigits",
    "minimumSignificantDigits",
    "maximumSignificantDigits"
  ];
  function NUMBER(args, opts) {
    let arg = args[0];
    if (arg instanceof FluentNone) {
      return new FluentNone(`NUMBER(${arg.valueOf()})`);
    }
    if (arg instanceof FluentNumber) {
      return new FluentNumber(arg.valueOf(), {
        ...arg.opts,
        ...values(opts, NUMBER_ALLOWED)
      });
    }
    if (arg instanceof FluentDateTime) {
      return new FluentNumber(arg.toNumber(), {
        ...values(opts, NUMBER_ALLOWED)
      });
    }
    throw new TypeError("Invalid argument to NUMBER");
  }
  var DATETIME_ALLOWED = [
    "dateStyle",
    "timeStyle",
    "fractionalSecondDigits",
    "dayPeriod",
    "hour12",
    "weekday",
    "era",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "timeZoneName"
  ];
  function DATETIME(args, opts) {
    let arg = args[0];
    if (arg instanceof FluentNone) {
      return new FluentNone(`DATETIME(${arg.valueOf()})`);
    }
    if (arg instanceof FluentDateTime || arg instanceof FluentNumber) {
      return new FluentDateTime(arg, values(opts, DATETIME_ALLOWED));
    }
    throw new TypeError("Invalid argument to DATETIME");
  }

  // ../../../node_modules/.pnpm/@fluent+bundle@0.19.1/node_modules/@fluent/bundle/esm/memoizer.js
  var cache = /* @__PURE__ */ new Map();
  function getMemoizerForLocale(locales) {
    const stringLocale = Array.isArray(locales) ? locales.join(" ") : locales;
    let memoizer = cache.get(stringLocale);
    if (memoizer === void 0) {
      memoizer = /* @__PURE__ */ new Map();
      cache.set(stringLocale, memoizer);
    }
    return memoizer;
  }

  // ../../../node_modules/.pnpm/@fluent+bundle@0.19.1/node_modules/@fluent/bundle/esm/bundle.js
  var FluentBundle = class {
    /**
     * Create an instance of `FluentBundle`.
     *
     * @example
     * ```js
     * let bundle = new FluentBundle(["en-US", "en"]);
     *
     * let bundle = new FluentBundle(locales, {useIsolating: false});
     *
     * let bundle = new FluentBundle(locales, {
     *   useIsolating: true,
     *   functions: {
     *     NODE_ENV: () => process.env.NODE_ENV
     *   }
     * });
     * ```
     *
     * @param locales - Used to instantiate `Intl` formatters used by translations.
     * @param options - Optional configuration for the bundle.
     */
    constructor(locales, { functions, useIsolating = true, transform = (v) => v } = {}) {
      this._terms = /* @__PURE__ */ new Map();
      this._messages = /* @__PURE__ */ new Map();
      this.locales = Array.isArray(locales) ? locales : [locales];
      this._functions = {
        NUMBER,
        DATETIME,
        ...functions
      };
      this._useIsolating = useIsolating;
      this._transform = transform;
      this._intls = getMemoizerForLocale(locales);
    }
    /**
     * Check if a message is present in the bundle.
     *
     * @param id - The identifier of the message to check.
     */
    hasMessage(id) {
      return this._messages.has(id);
    }
    /**
     * Return a raw unformatted message object from the bundle.
     *
     * Raw messages are `{value, attributes}` shapes containing translation units
     * called `Patterns`. `Patterns` are implementation-specific; they should be
     * treated as black boxes and formatted with `FluentBundle.formatPattern`.
     *
     * @param id - The identifier of the message to check.
     */
    getMessage(id) {
      return this._messages.get(id);
    }
    /**
     * Add a translation resource to the bundle.
     *
     * @example
     * ```js
     * let res = new FluentResource("foo = Foo");
     * bundle.addResource(res);
     * bundle.getMessage("foo");
     * // → {value: .., attributes: {..}}
     * ```
     *
     * @param res
     * @param options
     */
    addResource(res, { allowOverrides = false } = {}) {
      const errors = [];
      for (let i = 0; i < res.body.length; i++) {
        let entry = res.body[i];
        if (entry.id.startsWith("-")) {
          if (allowOverrides === false && this._terms.has(entry.id)) {
            errors.push(new Error(`Attempt to override an existing term: "${entry.id}"`));
            continue;
          }
          this._terms.set(entry.id, entry);
        } else {
          if (allowOverrides === false && this._messages.has(entry.id)) {
            errors.push(new Error(`Attempt to override an existing message: "${entry.id}"`));
            continue;
          }
          this._messages.set(entry.id, entry);
        }
      }
      return errors;
    }
    /**
     * Format a `Pattern` to a string.
     *
     * Format a raw `Pattern` into a string. `args` will be used to resolve
     * references to variables passed as arguments to the translation.
     *
     * In case of errors `formatPattern` will try to salvage as much of the
     * translation as possible and will still return a string. For performance
     * reasons, the encountered errors are not returned but instead are appended
     * to the `errors` array passed as the third argument.
     *
     * If `errors` is omitted, the first encountered error will be thrown.
     *
     * @example
     * ```js
     * let errors = [];
     * bundle.addResource(
     *     new FluentResource("hello = Hello, {$name}!"));
     *
     * let hello = bundle.getMessage("hello");
     * if (hello.value) {
     *     bundle.formatPattern(hello.value, {name: "Jane"}, errors);
     *     // Returns "Hello, Jane!" and `errors` is empty.
     *
     *     bundle.formatPattern(hello.value, undefined, errors);
     *     // Returns "Hello, {$name}!" and `errors` is now:
     *     // [<ReferenceError: Unknown variable: name>]
     * }
     * ```
     */
    formatPattern(pattern, args = null, errors = null) {
      if (typeof pattern === "string") {
        return this._transform(pattern);
      }
      let scope = new Scope(this, errors, args);
      try {
        let value = resolveComplexPattern(scope, pattern);
        return value.toString(scope);
      } catch (err) {
        if (scope.errors && err instanceof Error) {
          scope.errors.push(err);
          return new FluentNone().toString(scope);
        }
        throw err;
      }
    }
  };

  // ../../../node_modules/.pnpm/@fluent+bundle@0.19.1/node_modules/@fluent/bundle/esm/resource.js
  var RE_MESSAGE_START = /^(-?[a-zA-Z][\w-]*) *= */gm;
  var RE_ATTRIBUTE_START = /\.([a-zA-Z][\w-]*) *= */y;
  var RE_VARIANT_START = /\*?\[/y;
  var RE_NUMBER_LITERAL = /(-?[0-9]+(?:\.([0-9]+))?)/y;
  var RE_IDENTIFIER = /([a-zA-Z][\w-]*)/y;
  var RE_REFERENCE = /([$-])?([a-zA-Z][\w-]*)(?:\.([a-zA-Z][\w-]*))?/y;
  var RE_FUNCTION_NAME = /^[A-Z][A-Z0-9_-]*$/;
  var RE_TEXT_RUN = /([^{}\n\r]+)/y;
  var RE_STRING_RUN = /([^\\"\n\r]*)/y;
  var RE_STRING_ESCAPE = /\\([\\"])/y;
  var RE_UNICODE_ESCAPE = /\\u([a-fA-F0-9]{4})|\\U([a-fA-F0-9]{6})/y;
  var RE_LEADING_NEWLINES = /^\n+/;
  var RE_TRAILING_SPACES = / +$/;
  var RE_BLANK_LINES = / *\r?\n/g;
  var RE_INDENT = /( *)$/;
  var TOKEN_BRACE_OPEN = /{\s*/y;
  var TOKEN_BRACE_CLOSE = /\s*}/y;
  var TOKEN_BRACKET_OPEN = /\[\s*/y;
  var TOKEN_BRACKET_CLOSE = /\s*] */y;
  var TOKEN_PAREN_OPEN = /\s*\(\s*/y;
  var TOKEN_ARROW = /\s*->\s*/y;
  var TOKEN_COLON = /\s*:\s*/y;
  var TOKEN_COMMA = /\s*,?\s*/y;
  var TOKEN_BLANK = /\s+/y;
  var FluentResource = class {
    constructor(source) {
      this.body = [];
      RE_MESSAGE_START.lastIndex = 0;
      let cursor = 0;
      while (true) {
        let next = RE_MESSAGE_START.exec(source);
        if (next === null) {
          break;
        }
        cursor = RE_MESSAGE_START.lastIndex;
        try {
          this.body.push(parseMessage(next[1]));
        } catch (err) {
          if (err instanceof SyntaxError) {
            continue;
          }
          throw err;
        }
      }
      function test(re) {
        re.lastIndex = cursor;
        return re.test(source);
      }
      function consumeChar(char, errorClass) {
        if (source[cursor] === char) {
          cursor++;
          return true;
        }
        if (errorClass) {
          throw new errorClass(`Expected ${char}`);
        }
        return false;
      }
      function consumeToken(re, errorClass) {
        if (test(re)) {
          cursor = re.lastIndex;
          return true;
        }
        if (errorClass) {
          throw new errorClass(`Expected ${re.toString()}`);
        }
        return false;
      }
      function match2(re) {
        re.lastIndex = cursor;
        let result = re.exec(source);
        if (result === null) {
          throw new SyntaxError(`Expected ${re.toString()}`);
        }
        cursor = re.lastIndex;
        return result;
      }
      function match1(re) {
        return match2(re)[1];
      }
      function parseMessage(id) {
        let value = parsePattern();
        let attributes = parseAttributes();
        if (value === null && Object.keys(attributes).length === 0) {
          throw new SyntaxError("Expected message value or attributes");
        }
        return { id, value, attributes };
      }
      function parseAttributes() {
        let attrs = /* @__PURE__ */ Object.create(null);
        while (test(RE_ATTRIBUTE_START)) {
          let name = match1(RE_ATTRIBUTE_START);
          let value = parsePattern();
          if (value === null) {
            throw new SyntaxError("Expected attribute value");
          }
          attrs[name] = value;
        }
        return attrs;
      }
      function parsePattern() {
        let first;
        if (test(RE_TEXT_RUN)) {
          first = match1(RE_TEXT_RUN);
        }
        if (source[cursor] === "{" || source[cursor] === "}") {
          return parsePatternElements(first ? [first] : [], Infinity);
        }
        let indent = parseIndent();
        if (indent) {
          if (first) {
            return parsePatternElements([first, indent], indent.length);
          }
          indent.value = trim(indent.value, RE_LEADING_NEWLINES);
          return parsePatternElements([indent], indent.length);
        }
        if (first) {
          return trim(first, RE_TRAILING_SPACES);
        }
        return null;
      }
      function parsePatternElements(elements = [], commonIndent) {
        while (true) {
          if (test(RE_TEXT_RUN)) {
            elements.push(match1(RE_TEXT_RUN));
            continue;
          }
          if (source[cursor] === "{") {
            elements.push(parsePlaceable());
            continue;
          }
          if (source[cursor] === "}") {
            throw new SyntaxError("Unbalanced closing brace");
          }
          let indent = parseIndent();
          if (indent) {
            elements.push(indent);
            commonIndent = Math.min(commonIndent, indent.length);
            continue;
          }
          break;
        }
        let lastIndex = elements.length - 1;
        let lastElement = elements[lastIndex];
        if (typeof lastElement === "string") {
          elements[lastIndex] = trim(lastElement, RE_TRAILING_SPACES);
        }
        let baked = [];
        for (let element of elements) {
          if (element instanceof Indent) {
            element = element.value.slice(0, element.value.length - commonIndent);
          }
          if (element) {
            baked.push(element);
          }
        }
        return baked;
      }
      function parsePlaceable() {
        consumeToken(TOKEN_BRACE_OPEN, SyntaxError);
        let selector = parseInlineExpression();
        if (consumeToken(TOKEN_BRACE_CLOSE)) {
          return selector;
        }
        if (consumeToken(TOKEN_ARROW)) {
          let variants = parseVariants();
          consumeToken(TOKEN_BRACE_CLOSE, SyntaxError);
          return {
            type: "select",
            selector,
            ...variants
          };
        }
        throw new SyntaxError("Unclosed placeable");
      }
      function parseInlineExpression() {
        if (source[cursor] === "{") {
          return parsePlaceable();
        }
        if (test(RE_REFERENCE)) {
          let [, sigil, name, attr = null] = match2(RE_REFERENCE);
          if (sigil === "$") {
            return { type: "var", name };
          }
          if (consumeToken(TOKEN_PAREN_OPEN)) {
            let args = parseArguments();
            if (sigil === "-") {
              return { type: "term", name, attr, args };
            }
            if (RE_FUNCTION_NAME.test(name)) {
              return { type: "func", name, args };
            }
            throw new SyntaxError("Function names must be all upper-case");
          }
          if (sigil === "-") {
            return {
              type: "term",
              name,
              attr,
              args: []
            };
          }
          return { type: "mesg", name, attr };
        }
        return parseLiteral();
      }
      function parseArguments() {
        let args = [];
        while (true) {
          switch (source[cursor]) {
            case ")":
              cursor++;
              return args;
            case void 0:
              throw new SyntaxError("Unclosed argument list");
          }
          args.push(parseArgument());
          consumeToken(TOKEN_COMMA);
        }
      }
      function parseArgument() {
        let expr = parseInlineExpression();
        if (expr.type !== "mesg") {
          return expr;
        }
        if (consumeToken(TOKEN_COLON)) {
          return {
            type: "narg",
            name: expr.name,
            value: parseLiteral()
          };
        }
        return expr;
      }
      function parseVariants() {
        let variants = [];
        let count = 0;
        let star;
        while (test(RE_VARIANT_START)) {
          if (consumeChar("*")) {
            star = count;
          }
          let key = parseVariantKey();
          let value = parsePattern();
          if (value === null) {
            throw new SyntaxError("Expected variant value");
          }
          variants[count++] = { key, value };
        }
        if (count === 0) {
          return null;
        }
        if (star === void 0) {
          throw new SyntaxError("Expected default variant");
        }
        return { variants, star };
      }
      function parseVariantKey() {
        consumeToken(TOKEN_BRACKET_OPEN, SyntaxError);
        let key;
        if (test(RE_NUMBER_LITERAL)) {
          key = parseNumberLiteral();
        } else {
          key = {
            type: "str",
            value: match1(RE_IDENTIFIER)
          };
        }
        consumeToken(TOKEN_BRACKET_CLOSE, SyntaxError);
        return key;
      }
      function parseLiteral() {
        if (test(RE_NUMBER_LITERAL)) {
          return parseNumberLiteral();
        }
        if (source[cursor] === '"') {
          return parseStringLiteral();
        }
        throw new SyntaxError("Invalid expression");
      }
      function parseNumberLiteral() {
        let [, value, fraction = ""] = match2(RE_NUMBER_LITERAL);
        let precision = fraction.length;
        return {
          type: "num",
          value: parseFloat(value),
          precision
        };
      }
      function parseStringLiteral() {
        consumeChar('"', SyntaxError);
        let value = "";
        while (true) {
          value += match1(RE_STRING_RUN);
          if (source[cursor] === "\\") {
            value += parseEscapeSequence();
            continue;
          }
          if (consumeChar('"')) {
            return { type: "str", value };
          }
          throw new SyntaxError("Unclosed string literal");
        }
      }
      function parseEscapeSequence() {
        if (test(RE_STRING_ESCAPE)) {
          return match1(RE_STRING_ESCAPE);
        }
        if (test(RE_UNICODE_ESCAPE)) {
          let [, codepoint4, codepoint6] = match2(RE_UNICODE_ESCAPE);
          let codepoint = parseInt(codepoint4 || codepoint6, 16);
          return codepoint <= 55295 || 57344 <= codepoint ? (
            // It's a Unicode scalar value.
            String.fromCodePoint(codepoint)
          ) : (
            // Lonely surrogates can cause trouble when the parsing result is
            // saved using UTF-8. Use U+FFFD REPLACEMENT CHARACTER instead.
            "\uFFFD"
          );
        }
        throw new SyntaxError("Unknown escape sequence");
      }
      function parseIndent() {
        let start = cursor;
        consumeToken(TOKEN_BLANK);
        switch (source[cursor]) {
          case ".":
          case "[":
          case "*":
          case "}":
          case void 0:
            return false;
          case "{":
            return makeIndent(source.slice(start, cursor));
        }
        if (source[cursor - 1] === " ") {
          return makeIndent(source.slice(start, cursor));
        }
        return false;
      }
      function trim(text, re) {
        return text.replace(re, "");
      }
      function makeIndent(blank) {
        let value = blank.replace(RE_BLANK_LINES, "\n");
        let length = RE_INDENT.exec(blank)[1].length;
        return new Indent(value, length);
      }
    }
  };
  var Indent = class {
    constructor(value, length) {
      this.value = value;
      this.length = length;
    }
  };

  // src/citry-i18n.ts
  var SERVICE_KEY = "citry_i18n";
  var MANIFEST_SELECTOR = 'script[type="application/json"][data-citry-i18n]';
  var FSI2 = "\u2068";
  var PDI2 = "\u2069";
  var BIDI_CONTROLS = new Set(Array.from("\u061C\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u2066\u2067\u2068\u2069"));
  var PARAGRAPH_BOUNDARIES = new Set(Array.from("\r\n\x85\u2029"));
  var DECIMAL_PATTERN = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
  var INTEGER_PATTERN = /^-?(?:0|[1-9][0-9]*)$/;
  var PARAMETER_TYPES = /* @__PURE__ */ new Set(["Decimal", "Slot", "datetime", "int", "scalar", "str"]);
  var BINDING_ATTRIBUTE_TARGETS = /* @__PURE__ */ new Set([
    "alt",
    "aria-description",
    "aria-label",
    "aria-placeholder",
    "aria-roledescription",
    "aria-valuetext",
    "placeholder",
    "title"
  ]);
  var globalValue = globalThis;
  var citry = globalValue.Citry;
  if (!citry?.alpine || !citry.manager) {
    throw new Error("[Citry] i18n runtime needs the Citry dependency manager before it loads.");
  }
  var alpine = null;
  var configuration = null;
  var activeFluentFailures = null;
  var definitions = /* @__PURE__ */ new Map();
  var requirementsByProvider = /* @__PURE__ */ new Map();
  var bindingDefinitions = /* @__PURE__ */ new Map();
  var bindingReferenceCounts = /* @__PURE__ */ new Map();
  var manifestRequirements = /* @__PURE__ */ new WeakMap();
  var manifestDefinitions = /* @__PURE__ */ new WeakMap();
  var processedManifests = /* @__PURE__ */ new WeakSet();
  var activeManifests = /* @__PURE__ */ new WeakSet();
  var mountedProviders = /* @__PURE__ */ new Map();
  var internals = /* @__PURE__ */ new WeakMap();
  function fail(code, message) {
    const error = new TypeError(`[Citry] i18n: ${message}`);
    error.code = code;
    activeFluentFailures?.push(error);
    throw error;
  }
  function exactObject(value, name) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      fail("I18N_WIRE_INVALID", `${name} must be an object.`);
    }
    return value;
  }
  function exactKeys(value, expected, name) {
    const actual = Object.keys(value).sort();
    const sortedExpected = [...expected].sort();
    if (actual.length !== sortedExpected.length || actual.some((key, index) => key !== sortedExpected[index])) {
      fail("I18N_WIRE_INVALID", `${name} has unknown or missing fields.`);
    }
  }
  function exactString(value, name) {
    if (typeof value !== "string" || value.length === 0) {
      fail("I18N_WIRE_INVALID", `${name} must be a non-empty string.`);
    }
    return value;
  }
  function stringList(value, name) {
    if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || item.length === 0)) {
      fail("I18N_WIRE_INVALID", `${name} must be a list of non-empty strings.`);
    }
    if (new Set(value).size !== value.length) fail("I18N_WIRE_INVALID", `${name} contains duplicates.`);
    return value;
  }
  function immutableContext(value, name) {
    const item = exactObject(value, name);
    exactKeys(
      item,
      ["catalog_revision", "direction", "fallback_locales", "formats_revision", "locale", "time_zone", "tzdb_revision"],
      name
    );
    const direction = item.direction;
    if (direction !== "ltr" && direction !== "rtl") fail("I18N_WIRE_INVALID", `${name}.direction is invalid.`);
    const timeZone = item.time_zone;
    if (timeZone !== null && (typeof timeZone !== "string" || timeZone.length === 0)) {
      fail("I18N_WIRE_INVALID", `${name}.time_zone must be null or a non-empty string.`);
    }
    return Object.freeze({
      catalog_revision: exactString(item.catalog_revision, `${name}.catalog_revision`),
      direction,
      fallback_locales: Object.freeze(stringList(item.fallback_locales, `${name}.fallback_locales`)),
      formats_revision: exactString(item.formats_revision, `${name}.formats_revision`),
      locale: exactString(item.locale, `${name}.locale`),
      time_zone: timeZone,
      tzdb_revision: exactString(item.tzdb_revision, `${name}.tzdb_revision`)
    });
  }
  function fieldPolicy(value, name, allowClear) {
    const item = exactObject(value, name);
    const mode = item.mode;
    if (mode !== "inherit" && mode !== "explicit" && (!allowClear || mode !== "clear")) {
      fail("I18N_WIRE_INVALID", `${name}.mode is invalid.`);
    }
    exactKeys(item, mode === "explicit" ? ["mode", "value"] : ["mode"], name);
    return Object.freeze(
      mode === "explicit" ? { mode, value: exactString(item.value, `${name}.value`) } : { mode }
    );
  }
  function providerDefinition(value) {
    const item = exactObject(value, "an i18n provider");
    exactKeys(item, ["context", "id", "parent", "policy"], "an i18n provider");
    const parent = item.parent;
    if (parent !== null && (typeof parent !== "string" || parent.length === 0)) {
      fail("I18N_WIRE_INVALID", "an i18n provider parent must be null or a render ID.");
    }
    const policy = exactObject(item.policy, "an i18n provider policy");
    exactKeys(policy, ["direction", "locale", "time_zone"], "an i18n provider policy");
    return Object.freeze({
      context: immutableContext(item.context, "an i18n provider context"),
      id: exactString(item.id, "an i18n provider id"),
      parent,
      policy: Object.freeze({
        direction: fieldPolicy(policy.direction, "an i18n direction policy", false),
        locale: fieldPolicy(policy.locale, "an i18n locale policy", false),
        time_zone: fieldPolicy(policy.time_zone, "an i18n time-zone policy", true)
      })
    });
  }
  function native(value) {
    if (value !== null && typeof value === "object" && "valueOf" in value) {
      const method = value.valueOf;
      if (typeof method === "function") return method.call(value);
    }
    return value;
  }
  function prohibitedText(value) {
    return Array.from(value).some((character) => BIDI_CONTROLS.has(character) || PARAGRAPH_BOUNDARIES.has(character));
  }
  function decimalInput(value, typeName) {
    if (typeof value === "bigint") return value.toString();
    if (typeof value === "number") {
      if (Number.isInteger(value) && !Number.isSafeInteger(value)) {
        fail("I18N_ARGUMENT_INVALID", `a ${typeName} integer must be safe, a bigint, or a canonical decimal string.`);
      }
      if (!Number.isFinite(value)) fail("I18N_ARGUMENT_INVALID", "numeric message arguments must be finite.");
      const text = Object.is(value, -0) ? "-0" : String(value);
      if (typeName === "int" && !INTEGER_PATTERN.test(text)) {
        fail("I18N_ARGUMENT_INVALID", "an int argument must not contain a fraction.");
      }
      return text;
    }
    if (typeof value !== "string") fail("I18N_ARGUMENT_INVALID", `a ${typeName} argument needs a numeric value.`);
    const pattern = typeName === "int" ? INTEGER_PATTERN : DECIMAL_PATTERN;
    if (!pattern.test(value)) fail("I18N_ARGUMENT_INVALID", `a ${typeName} argument is not canonical.`);
    return value;
  }
  function argumentValue(name, typeName, value) {
    let result;
    if (typeName === "str") {
      if (typeof value !== "string") fail("I18N_ARGUMENT_INVALID", `$${name} must be a string.`);
      result = value;
    } else if (typeName === "int" || typeName === "Decimal") {
      result = decimalInput(value, typeName);
    } else if (typeName === "scalar") {
      result = typeof value === "string" ? value : decimalInput(value, "Decimal");
    } else if (typeName === "datetime") {
      if (!(value instanceof Date) || !Number.isFinite(value.valueOf())) {
        fail("I18N_ARGUMENT_INVALID", `$${name} must be a valid Date.`);
      }
      result = value.toISOString();
    } else if (typeName === "Slot") {
      fail("I18N_ARGUMENT_INVALID", `$${name} is a Slot and must be rendered through <c-trans>.`);
    } else {
      fail("I18N_ARGUMENT_INVALID", `$${name} has unsupported type ${typeName}.`);
    }
    if (prohibitedText(result)) fail("I18N_ARGUMENT_INVALID", `$${name} contains a prohibited bidi boundary.`);
    return result;
  }
  function exactArguments(contract, rawValues) {
    const expected = Object.keys(contract).sort();
    const actual = Object.keys(rawValues).sort();
    if (expected.length !== actual.length || expected.some((name, index) => name !== actual[index])) {
      fail("I18N_ARGUMENT_INVALID", `message arguments must be exactly: ${expected.join(", ") || "(none)"}.`);
    }
    return Object.fromEntries(expected.map((name) => [name, argumentValue(name, contract[name], rawValues[name])]));
  }
  function formatExactNumber(locale, value) {
    const fractionDigits = value.includes(".") ? value.length - value.indexOf(".") - 1 : 0;
    if (fractionDigits > 20) {
      fail("I18N_NUMBER_UNSUPPORTED", "browser NUMBER() supports at most 20 exact fraction digits.");
    }
    const formatter = new Intl.NumberFormat(locale, {
      maximumFractionDigits: fractionDigits,
      minimumFractionDigits: fractionDigits,
      useGrouping: true
    });
    return formatter.format(value);
  }
  function formatOptions(value, name) {
    const item = exactObject(value, `${name} options`);
    exactKeys(item, ["format"], `${name} options`);
    return Object.freeze({ format: exactString(item.format, `${name} format`) });
  }
  function profile(kind, name) {
    const category = configuration?.formats[kind];
    const value = category?.[name];
    if (value === void 0) fail("I18N_FORMAT_INVALID", `unknown ${kind} format ${name}.`);
    return exactObject(value, `${kind} format ${name}`);
  }
  function exactNumberFormatter(locale, options) {
    return new Intl.NumberFormat(locale, options);
  }
  function formatIntlNumber(locale, value, options, kind) {
    const decimal = decimalInput(value, "Decimal");
    const fractionDigits = decimal.includes(".") ? decimal.length - decimal.indexOf(".") - 1 : 0;
    if (fractionDigits > 20) {
      fail("I18N_FORMAT_UNSUPPORTED", `browser ${kind} formatting supports at most 20 exact fraction digits.`);
    }
    const displayedFractionDigits = kind === "number" || kind === "unit" ? fractionDigits : kind === "percent" ? Math.max(0, fractionDigits - 2) : null;
    const formatter = exactNumberFormatter(locale, {
      ...options,
      ...displayedFractionDigits === null ? {} : {
        maximumFractionDigits: displayedFractionDigits,
        minimumFractionDigits: displayedFractionDigits
      }
    });
    return formatter.format(decimal);
  }
  function integerField(value, name, minimum, maximum) {
    if (typeof value !== "number" || !Number.isInteger(value) || value < minimum || value > maximum) {
      fail("I18N_FORMAT_INVALID", `${name} must be an integer from ${minimum} through ${maximum}.`);
    }
    return value;
  }
  function dateValue(value) {
    const item = exactObject(value, "date fields");
    exactKeys(item, ["day", "month", "year"], "date fields");
    const year = integerField(item.year, "date year", 1, 9999);
    const month = integerField(item.month, "date month", 1, 12);
    const day = integerField(item.day, "date day", 1, 31);
    const result = /* @__PURE__ */ new Date(0);
    result.setUTCHours(12, 0, 0, 0);
    result.setUTCFullYear(year, month - 1, day);
    if (result.getUTCFullYear() !== year || result.getUTCMonth() !== month - 1 || result.getUTCDate() !== day) {
      fail("I18N_FORMAT_INVALID", "date fields do not form a real ISO calendar date.");
    }
    return result;
  }
  function timeValue(value) {
    const item = exactObject(value, "time fields");
    const keys = Object.keys(item).sort();
    if (keys.some((key) => !["hour", "millisecond", "minute", "second"].includes(key)) || !keys.includes("hour") || !keys.includes("minute")) {
      fail("I18N_FORMAT_INVALID", "time fields need hour and minute and may add second and millisecond.");
    }
    const hour = integerField(item.hour, "time hour", 0, 23);
    const minute = integerField(item.minute, "time minute", 0, 59);
    const second = integerField(item.second ?? 0, "time second", 0, 59);
    const millisecond = integerField(item.millisecond ?? 0, "time millisecond", 0, 999);
    return new Date(Date.UTC(1970, 0, 1, hour, minute, second, millisecond));
  }
  function dateTimeOptions(length) {
    if (length !== "short" && length !== "medium" && length !== "long") {
      fail("I18N_FORMAT_INVALID", "a temporal profile has an invalid length.");
    }
    if (length === "short") return { day: "numeric", month: "numeric", year: "2-digit" };
    if (length === "medium") return { day: "numeric", month: "short", year: "numeric" };
    return { day: "numeric", month: "long", year: "numeric" };
  }
  function wallTimeOptions(length) {
    if (length !== "short" && length !== "medium" && length !== "long") {
      fail("I18N_FORMAT_INVALID", "a temporal profile has an invalid length.");
    }
    return { hour: "numeric", minute: "2-digit", second: "2-digit" };
  }
  function createFormatter(internal) {
    function locale() {
      return internal.state.context.locale;
    }
    return Object.freeze({
      currency(value, currency, rawOptions) {
        const options = formatOptions(rawOptions, "currency");
        const spec = profile("currency", options.format);
        exactKeys(spec, [], `currency format ${options.format}`);
        if (!/^[A-Z]{3}$/.test(currency)) {
          fail("I18N_FORMAT_INVALID", "currency must be exactly three uppercase ASCII letters.");
        }
        return formatIntlNumber(locale(), value, { currency, style: "currency" }, "currency");
      },
      date(value, rawOptions) {
        const options = formatOptions(rawOptions, "date");
        const spec = profile("date", options.format);
        return new Intl.DateTimeFormat(locale(), { ...dateTimeOptions(spec.length), timeZone: "UTC" }).format(
          dateValue(value)
        );
      },
      datetime(value, rawOptions) {
        const options = formatOptions(rawOptions, "datetime");
        const spec = profile("datetime", options.format);
        if (!(value instanceof Date) || !Number.isFinite(value.valueOf())) {
          fail("I18N_FORMAT_INVALID", "datetime needs a valid JavaScript Date instant.");
        }
        const timeZone = internal.state.context.time_zone;
        if (timeZone === null) fail("I18N_FORMAT_INVALID", "datetime needs time_zone in the active i18n context.");
        const timeZoneName = spec.time_zone_name;
        if (timeZoneName !== "none" && timeZoneName !== "short" && timeZoneName !== "long") {
          fail("I18N_FORMAT_INVALID", "a datetime profile has an invalid time_zone_name.");
        }
        return new Intl.DateTimeFormat(locale(), {
          ...dateTimeOptions(spec.length),
          ...wallTimeOptions(spec.length),
          timeZone,
          ...timeZoneName === "none" ? {} : { timeZoneName }
        }).format(value);
      },
      list(values2, rawOptions) {
        const options = formatOptions(rawOptions, "list");
        const spec = profile("list", options.format);
        if (!Array.isArray(values2) || values2.some((value) => typeof value !== "string")) {
          fail("I18N_FORMAT_INVALID", "list formatting needs an array of strings.");
        }
        if (values2.some((value) => value.length === 0 || prohibitedText(value))) {
          fail("I18N_FORMAT_INVALID", "list items must be non-empty and contain no bidi or paragraph controls.");
        }
        const type = spec.kind === "and" ? "conjunction" : spec.kind === "or" ? "disjunction" : null;
        const style = spec.length === "wide" ? "long" : spec.length;
        if (type === null || style !== "long" && style !== "short" && style !== "narrow") {
          fail("I18N_FORMAT_INVALID", "a list profile is invalid.");
        }
        return new Intl.ListFormat(locale(), { style, type }).format(values2.map((value) => `${FSI2}${value}${PDI2}`));
      },
      number(value, rawOptions) {
        const options = formatOptions(rawOptions, "number");
        profile("number", options.format);
        return formatIntlNumber(locale(), value, {}, "number");
      },
      percent(value, rawOptions) {
        const options = formatOptions(rawOptions, "percent");
        profile("percent", options.format);
        return formatIntlNumber(locale(), value, { style: "percent" }, "percent");
      },
      relativeTime(value, rawOptions) {
        const item = exactObject(rawOptions, "relative time options");
        exactKeys(item, ["format", "unit"], "relative time options");
        const format = exactString(item.format, "relative time format");
        const unit = exactString(item.unit, "relative time unit");
        const spec = profile("relative_time", format);
        if (unit !== "day" || spec.unit !== "day") {
          fail("I18N_FORMAT_INVALID", "relative time currently supports only unit day.");
        }
        const decimal = decimalInput(value, "Decimal");
        const numeric = pluralInput(decimal);
        return new Intl.RelativeTimeFormat(locale(), { numeric: "always", style: "long" }).format(numeric, "day");
      },
      time(value, rawOptions) {
        const options = formatOptions(rawOptions, "time");
        const spec = profile("time", options.format);
        return new Intl.DateTimeFormat(locale(), { ...wallTimeOptions(spec.length), timeZone: "UTC" }).format(
          timeValue(value)
        );
      },
      unit(value, unit, rawOptions) {
        const options = formatOptions(rawOptions, "unit");
        const spec = profile("unit", options.format);
        if (typeof unit !== "string" || unit.length === 0) fail("I18N_FORMAT_INVALID", "unit must be a string.");
        const unitDisplay = spec.width;
        if (unitDisplay !== "long" && unitDisplay !== "short" && unitDisplay !== "narrow") {
          fail("I18N_FORMAT_INVALID", "a unit profile has an invalid width.");
        }
        const decimal = decimalInput(value, "Decimal");
        const numeric = Number(decimal);
        if (!Number.isFinite(numeric) || normalizedDecimal(String(numeric)) !== normalizedDecimal(decimal)) {
          fail(
            "I18N_FORMAT_UNSUPPORTED",
            "browser unit formatting cannot preserve this exact value for plural selection."
          );
        }
        return formatIntlNumber(locale(), decimal, { style: "unit", unit, unitDisplay }, "unit");
      }
    });
  }
  function numberParserRecord(value, name) {
    const item = exactObject(value, name);
    exactKeys(
      item,
      [
        "decimal",
        "digits",
        "grouping",
        "minus_prefix",
        "minus_suffix",
        "notation",
        "plus_prefix",
        "plus_suffix",
        "primary_group",
        "secondary_group"
      ],
      name
    );
    const digits = item.digits;
    if (!Array.isArray(digits) || digits.length !== 10 || digits.some((digit) => typeof digit !== "string" || Array.from(digit).length !== 1) || new Set(digits).size !== 10) {
      fail("I18N_WIRE_INVALID", `${name}.digits must contain ten distinct Unicode characters.`);
    }
    const notation = item.notation;
    if (notation !== "decimal" && notation !== "decimal_or_scientific") {
      fail("I18N_WIRE_INVALID", `${name}.notation is invalid.`);
    }
    const primaryGroup = item.primary_group;
    const secondaryGroup = item.secondary_group;
    if (typeof primaryGroup !== "number" || !Number.isInteger(primaryGroup) || primaryGroup < 0 || primaryGroup > 32 || typeof secondaryGroup !== "number" || !Number.isInteger(secondaryGroup) || secondaryGroup < 0 || secondaryGroup > 32) {
      fail("I18N_WIRE_INVALID", `${name} has invalid grouping sizes.`);
    }
    const decimal = exactString(item.decimal, `${name}.decimal`);
    const grouping = exactString(item.grouping, `${name}.grouping`);
    if (decimal === grouping) fail("I18N_WIRE_INVALID", `${name} reuses one decimal and grouping separator.`);
    for (const field of ["minus_prefix", "minus_suffix", "plus_prefix", "plus_suffix"]) {
      if (typeof item[field] !== "string") fail("I18N_WIRE_INVALID", `${name}.${field} must be a string.`);
    }
    return Object.freeze({
      decimal,
      digits: Object.freeze([...digits]),
      grouping,
      minus_prefix: item.minus_prefix,
      minus_suffix: item.minus_suffix,
      notation,
      plus_prefix: item.plus_prefix,
      plus_suffix: item.plus_suffix,
      primary_group: primaryGroup,
      secondary_group: secondaryGroup
    });
  }
  function parserArtifact(value, locale, formatsRevision) {
    const item = exactObject(value, `browser parser artifact ${locale}`);
    exactKeys(item, ["formats_revision", "locale", "number", "percent", "revision", "schema_version"], "parser artifact");
    if (item.schema_version !== 1 || item.locale !== locale || item.formats_revision !== formatsRevision || typeof item.revision !== "string" || item.revision.length === 0) {
      fail("I18N_WIRE_INVALID", `browser parser artifact ${locale} has incompatible identity.`);
    }
    const number = Object.fromEntries(
      Object.entries(exactObject(item.number, `browser parser artifact ${locale}.number`)).map(([profile2, record]) => [
        profile2,
        numberParserRecord(record, `number parser ${profile2}`)
      ])
    );
    const percent = Object.fromEntries(
      Object.entries(exactObject(item.percent, `browser parser artifact ${locale}.percent`)).map(([profile2, value2]) => {
        const record = exactObject(value2, `percent parser ${profile2}`);
        exactKeys(record, ["affix", "numbers", "patterns"], `percent parser ${profile2}`);
        if (record.affix !== "required" && record.affix !== "omit") {
          fail("I18N_WIRE_INVALID", `percent parser ${profile2}.affix is invalid.`);
        }
        if (!Array.isArray(record.patterns) || record.patterns.length !== 3) {
          fail("I18N_WIRE_INVALID", `percent parser ${profile2}.patterns must contain three records.`);
        }
        const patterns = record.patterns.map((rawPattern, index) => {
          const pattern = exactObject(rawPattern, `percent parser ${profile2}.patterns[${index}]`);
          exactKeys(pattern, ["negative", "prefix", "suffix"], `percent parser ${profile2}.patterns[${index}]`);
          if (typeof pattern.negative !== "boolean" || typeof pattern.prefix !== "string" || typeof pattern.suffix !== "string") {
            fail("I18N_WIRE_INVALID", `percent parser ${profile2}.patterns[${index}] is invalid.`);
          }
          return Object.freeze({
            negative: pattern.negative,
            prefix: pattern.prefix,
            suffix: pattern.suffix
          });
        });
        return [
          profile2,
          Object.freeze({
            affix: record.affix,
            numbers: numberParserRecord(record.numbers, `percent parser ${profile2}.numbers`),
            patterns: Object.freeze(patterns)
          })
        ];
      })
    );
    return Object.freeze({
      formats_revision: formatsRevision,
      locale,
      number: Object.freeze(number),
      percent: Object.freeze(percent),
      revision: item.revision,
      schema_version: 1
    });
  }
  function numericParseResult(input, state, error, value = null) {
    return Object.freeze({ error, input, state, valid: state === "valid", value });
  }
  function codePointLength(value) {
    return Array.from(value).length;
  }
  function stripSign(input, prefix, suffix) {
    if (prefix.length === 0 && suffix.length === 0) return null;
    if (!input.startsWith(prefix) || !input.endsWith(suffix)) return null;
    return input.slice(prefix.length, input.length - suffix.length);
  }
  function parsePlainNumber(input, record) {
    if (input.length === 0) return numericParseResult(input, "incomplete", "empty");
    if (input.trim() !== input) return numericParseResult(input, "invalid", "whitespace");
    let negative = false;
    let unsigned = stripSign(input, record.minus_prefix, record.minus_suffix);
    if (unsigned !== null) {
      negative = true;
    } else {
      unsigned = stripSign(input, record.plus_prefix, record.plus_suffix);
      if (unsigned === null && input.startsWith("-")) {
        negative = true;
        unsigned = input.slice(1);
      } else if (unsigned === null && input.startsWith("+")) {
        unsigned = input.slice(1);
      } else if (unsigned === null) {
        unsigned = input;
      }
    }
    if (unsigned.length === 0) return numericParseResult(input, "incomplete", "sign_without_digits");
    const firstDecimal = unsigned.indexOf(record.decimal);
    if (firstDecimal >= 0 && unsigned.indexOf(record.decimal, firstDecimal + record.decimal.length) >= 0) {
      return numericParseResult(input, "invalid", "multiple_decimal_separators");
    }
    const integer = firstDecimal < 0 ? unsigned : unsigned.slice(0, firstDecimal);
    const fraction = firstDecimal < 0 ? null : unsigned.slice(firstDecimal + record.decimal.length);
    if (integer.length === 0) return numericParseResult(input, "incomplete", "missing_integer_digits");
    if (fraction === "") return numericParseResult(input, "incomplete", "missing_fraction_digits");
    const groups = integer.split(record.grouping);
    if (groups.some((group) => group.length === 0)) {
      return groups[groups.length - 1] === "" ? numericParseResult(input, "incomplete", "unfinished_group") : numericParseResult(input, "invalid", "empty_group");
    }
    if (groups.length > 1) {
      if (record.primary_group === 0 || record.secondary_group === 0) {
        return numericParseResult(input, "invalid", "grouping_not_allowed");
      }
      const finalCount = codePointLength(groups[groups.length - 1]);
      if (finalCount < record.primary_group) return numericParseResult(input, "incomplete", "unfinished_group");
      if (finalCount > record.primary_group) return numericParseResult(input, "invalid", "wrong_primary_group");
      if (groups.slice(1, -1).some((group) => codePointLength(group) !== record.secondary_group)) {
        return numericParseResult(input, "invalid", "wrong_secondary_group");
      }
      const leading = codePointLength(groups[0]);
      if (leading === 0 || leading > record.secondary_group) {
        return numericParseResult(input, "invalid", "wrong_leading_group");
      }
    }
    const digitMap = new Map(record.digits.map((digit, index) => [digit, String(index)]));
    let canonical = negative ? "-" : "";
    for (const character of Array.from(groups.join(""))) {
      const digit = digitMap.get(character);
      if (digit === void 0) return numericParseResult(input, "invalid", "foreign_or_invalid_digit");
      canonical += digit;
    }
    if (fraction !== null) {
      if (fraction.includes(record.grouping)) return numericParseResult(input, "invalid", "grouping_in_fraction");
      canonical += ".";
      for (const character of Array.from(fraction)) {
        const digit = digitMap.get(character);
        if (digit === void 0) return numericParseResult(input, "invalid", "foreign_or_invalid_digit");
        canonical += digit;
      }
    }
    if (canonical.length > 32768) return numericParseResult(input, "invalid", "number_out_of_range");
    return numericParseResult(input, "valid", null, canonical);
  }
  function shiftExactDecimal(value, power) {
    const negative = value.startsWith("-");
    const unsigned = negative ? value.slice(1) : value;
    const [integer, fraction = ""] = unsigned.split(".");
    let digits = `${integer}${fraction}`;
    let point = integer.length + power;
    if (point <= 0) {
      digits = `${"0".repeat(-point)}${digits}`;
      point = 0;
    } else if (point >= digits.length) {
      digits = `${digits}${"0".repeat(point - digits.length)}`;
      point = digits.length;
    }
    if (digits.length > 32768) return null;
    const rendered = point === 0 ? `0.${digits}` : point === digits.length ? digits : `${digits.slice(0, point)}.${digits.slice(point)}`;
    const [rawInteger, rawFraction] = rendered.split(".");
    const normalizedInteger = rawInteger.replace(/^0+(?=\d)/, "");
    const normalized = rawFraction === void 0 ? normalizedInteger : `${normalizedInteger}.${rawFraction}`;
    return negative && /[1-9]/.test(digits) ? `-${normalized}` : normalized;
  }
  function parseNumber(input, record) {
    if (record.notation === "decimal") return parsePlainNumber(input, record);
    const separators = Array.from(input.matchAll(/[eE]/g));
    if (separators.length === 0) return parsePlainNumber(input, record);
    if (separators.length > 1) return numericParseResult(input, "invalid", "multiple_exponents");
    const separator = separators[0].index;
    const significand = parsePlainNumber(input.slice(0, separator), record);
    if (!significand.valid) return Object.freeze({ ...significand, input });
    let exponentInput = input.slice(separator + 1);
    if (exponentInput.length === 0) return numericParseResult(input, "incomplete", "missing_exponent_digits");
    let negative = false;
    if (exponentInput.startsWith("-")) {
      negative = true;
      exponentInput = exponentInput.slice(1);
    } else if (exponentInput.startsWith("+")) {
      exponentInput = exponentInput.slice(1);
    }
    if (exponentInput.length === 0) return numericParseResult(input, "incomplete", "missing_exponent_digits");
    const digitMap = new Map(record.digits.map((digit, index) => [digit, String(index)]));
    let ascii = "";
    for (const character of Array.from(exponentInput)) {
      const digit = digitMap.get(character);
      if (digit === void 0) {
        return numericParseResult(input, "invalid", "foreign_or_invalid_exponent_digit");
      }
      ascii += digit;
    }
    if (ascii.length > 5) return numericParseResult(input, "invalid", "exponent_out_of_range");
    const absolute = Number(ascii);
    const exponent = negative ? -absolute : absolute;
    if (!Number.isInteger(exponent) || exponent < -32768 || exponent > 32767) {
      return numericParseResult(input, "invalid", "exponent_out_of_range");
    }
    const shifted = shiftExactDecimal(significand.value, exponent);
    return shifted === null ? numericParseResult(input, "invalid", "number_out_of_range") : numericParseResult(input, "valid", null, shifted);
  }
  function createParser(internal) {
    function artifact() {
      const result = configuration?.parsers.get(internal.state.context.locale);
      if (result === void 0) fail("I18N_PARSE_UNAVAILABLE", "the current locale has no browser parser artifact.");
      return result;
    }
    return Object.freeze({
      number(input, rawOptions) {
        if (typeof input !== "string") fail("I18N_PARSE_INVALID", "number input must be a string.");
        const options = formatOptions(rawOptions, "number parser");
        const record = artifact().number[options.format];
        if (record === void 0) fail("I18N_PARSE_INVALID", `unknown number parser ${options.format}.`);
        return parseNumber(input, record);
      },
      percent(input, rawOptions) {
        if (typeof input !== "string") fail("I18N_PARSE_INVALID", "percent input must be a string.");
        const options = formatOptions(rawOptions, "percent parser");
        const record = artifact().percent[options.format];
        if (record === void 0) fail("I18N_PARSE_INVALID", `unknown percent parser ${options.format}.`);
        if (record.affix === "omit") {
          const parsed = parsePlainNumber(input, record.numbers);
          if (!parsed.valid) return parsed;
          const value = shiftExactDecimal(parsed.value, -2);
          return value === null ? numericParseResult(input, "invalid", "number_out_of_range") : numericParseResult(input, "valid", null, value);
        }
        if (Array.from(input).some(
          (character) => BIDI_CONTROLS.has(character) && !["\u061C", "\u200E", "\u200F"].includes(character)
        )) {
          return numericParseResult(input, "invalid", "bidi_control");
        }
        const normalized = input.replace(/[\u061c\u200e\u200f]/g, "");
        for (const pattern of record.patterns) {
          if (!normalized.startsWith(pattern.prefix) || !normalized.endsWith(pattern.suffix)) continue;
          const inner = normalized.slice(pattern.prefix.length, normalized.length - pattern.suffix.length);
          const parsed = parsePlainNumber(inner, record.numbers);
          if (!parsed.valid) return Object.freeze({ ...parsed, input });
          const signed = pattern.negative && !parsed.value.startsWith("-") ? `-${parsed.value}` : parsed.value;
          const value = shiftExactDecimal(signed, -2);
          return value === null ? numericParseResult(input, "invalid", "number_out_of_range") : numericParseResult(input, "valid", null, value);
        }
        return normalized.includes("%") || normalized.includes("\u066A") ? numericParseResult(input, "invalid", "wrong_percent_affix") : numericParseResult(input, "incomplete", "missing_percent_affix");
      }
    });
  }
  function normalizedDecimal(value) {
    const negative = value.startsWith("-");
    const unsigned = negative ? value.slice(1) : value;
    const [integer, fraction = ""] = unsigned.split(".");
    const normalizedFraction = fraction.replace(/0+$/, "");
    const magnitude = normalizedFraction.length === 0 ? integer : `${integer}.${normalizedFraction}`;
    return /^0(?:\.0*)?$/.test(magnitude) ? "0" : `${negative ? "-" : ""}${magnitude}`;
  }
  function sameExactDecimal(left, right) {
    return DECIMAL_PATTERN.test(right) && normalizedDecimal(left) === normalizedDecimal(right);
  }
  function pluralInput(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      fail("I18N_PLURAL_UNSUPPORTED", "browser plural selection cannot preserve this exact decimal.");
    }
    if (INTEGER_PATTERN.test(value)) {
      if (!Number.isSafeInteger(numeric)) {
        fail("I18N_PLURAL_UNSUPPORTED", "browser plural selection requires a safe integer.");
      }
      return numeric;
    }
    if (value.endsWith("0") || String(numeric) !== value) {
      fail("I18N_PLURAL_UNSUPPORTED", "browser Intl.PluralRules cannot preserve this decimal's exact visible digits.");
    }
    return numeric;
  }
  function fluentFunctions(locale, formats) {
    return {
      CITRY_PLURAL(positional, named) {
        const value = String(native(positional[0]));
        if (!DECIMAL_PATTERN.test(value)) fail("I18N_PLURAL_INVALID", "CITRY_PLURAL received a non-decimal value.");
        const mode = named.mode === void 0 ? "cardinal" : String(native(named.mode));
        if (mode !== "cardinal" && mode !== "ordinal") fail("I18N_PLURAL_INVALID", "plural mode is invalid.");
        if (Object.keys(named).some((name) => name !== "exact" && name !== "mode")) {
          fail("I18N_PLURAL_INVALID", "CITRY_PLURAL received an unknown option.");
        }
        if (named.exact !== void 0) {
          const exact = String(native(named.exact)).split(",").find((candidate) => sameExactDecimal(value, candidate));
          if (exact !== void 0) return `exact-${exact}`;
        }
        return new Intl.PluralRules(locale, { type: mode }).select(pluralInput(value));
      },
      CITRY_TEXT(positional, named) {
        if (Object.keys(named).length !== 0) fail("I18N_TEXT_INVALID", "CITRY_TEXT does not accept options.");
        const value = String(native(positional[0]));
        if (prohibitedText(value)) fail("I18N_TEXT_INVALID", "CITRY_TEXT received a prohibited bidi boundary.");
        return `${FSI2}${value}${PDI2}`;
      },
      NUMBER(positional, named) {
        const profile2 = String(native(named.profile));
        if (Object.keys(named).length !== 1 || formats.number?.[profile2] === void 0) {
          fail("I18N_NUMBER_INVALID", `NUMBER received unknown profile ${profile2}.`);
        }
        const value = String(native(positional[0]));
        if (!DECIMAL_PATTERN.test(value)) fail("I18N_NUMBER_INVALID", "NUMBER received a non-decimal value.");
        return `${FSI2}${formatExactNumber(locale, value)}${PDI2}`;
      },
      SLOT() {
        return fail("I18N_SLOT_INVALID", "plain browser translation cannot format a Slot.");
      }
    };
  }
  function browserArtifact(value, locale) {
    const item = exactObject(value, "a browser catalog artifact");
    exactKeys(
      item,
      [
        "bundles",
        "catalog_revision",
        "formats_revision",
        "messages",
        "requested_locale",
        "revision",
        "runtime",
        "schema_version"
      ],
      "a browser catalog artifact"
    );
    if (item.schema_version !== 1 || item.runtime !== "@fluent/bundle@0.19.1" || item.requested_locale !== locale) {
      fail("I18N_ARTIFACT_INVALID", "the browser artifact version or requested locale does not match.");
    }
    if (configuration === null || item.catalog_revision !== configuration.catalogRevision || item.formats_revision !== configuration.formatsRevision) {
      fail("I18N_ARTIFACT_INVALID", "the browser artifact catalog or formatter revision is stale.");
    }
    exactString(item.revision, "a browser artifact revision");
    return item;
  }
  function createMessageRuntime(value, locale) {
    const artifact = browserArtifact(value, locale);
    const messages = exactObject(artifact.messages, "browser artifact messages");
    const bundles = exactObject(artifact.bundles, "browser artifact bundles");
    const compiled = /* @__PURE__ */ new Map();
    for (const [bundleLocale, source] of Object.entries(bundles)) {
      if (typeof source !== "string") fail("I18N_ARTIFACT_INVALID", "a browser bundle must contain FTL text.");
      const bundle = new FluentBundle(bundleLocale, {
        functions: fluentFunctions(bundleLocale, configuration.formats),
        useIsolating: false
      });
      const errors = bundle.addResource(new FluentResource(source), { allowOverrides: false });
      if (errors.length !== 0) fail("I18N_ARTIFACT_INVALID", "a browser bundle failed to parse.");
      compiled.set(bundleLocale, bundle);
    }
    for (const [token, rawEntry] of Object.entries(messages)) {
      const item = exactObject(rawEntry, `browser message ${token}`);
      exactKeys(item, ["bundle_locale", "contract", "internal_id"], `browser message ${token}`);
      const contract = exactObject(item.contract, `browser message ${token} contract`);
      for (const [name, typeName] of Object.entries(contract)) {
        if (!name || typeof typeName !== "string" || !PARAMETER_TYPES.has(typeName)) {
          fail("I18N_ARTIFACT_INVALID", `browser message ${token} has an invalid parameter contract.`);
        }
      }
      const entry = item;
      exactString(entry.bundle_locale, `browser message ${token} bundle_locale`);
      exactString(entry.internal_id, `browser message ${token} internal_id`);
      const bundle = compiled.get(entry.bundle_locale);
      if (bundle?.getMessage(entry.internal_id)?.value == null) {
        fail("I18N_ARTIFACT_INVALID", `browser message ${token} has no compiled pattern.`);
      }
    }
    return Object.freeze({
      artifact,
      format(token, values2) {
        const entry = artifact.messages[token];
        if (entry === void 0) fail("I18N_MESSAGE_MISSING", `browser message ${token} is not loaded.`);
        const bundle = compiled.get(entry.bundle_locale);
        const message = bundle?.getMessage(entry.internal_id);
        if (bundle === void 0 || message?.value == null) {
          fail("I18N_ARTIFACT_INVALID", `browser message ${token} is unavailable.`);
        }
        const errors = [];
        const callbackFailures = [];
        const previousFailures = activeFluentFailures;
        activeFluentFailures = callbackFailures;
        let output;
        try {
          output = bundle.formatPattern(message.value, exactArguments(entry.contract, values2), errors);
        } finally {
          activeFluentFailures = previousFailures;
        }
        if (callbackFailures.length !== 0) throw callbackFailures[0];
        if (errors.length !== 0) fail("I18N_MESSAGE_INVALID", `browser message ${token} failed to format.`);
        return output;
      }
    });
  }
  function taggedBindingValue(value, name) {
    const item = exactObject(value, name);
    exactKeys(item, ["type", "value"], name);
    const typeName = exactString(item.type, `${name}.type`);
    const text = typeof item.value === "string" ? item.value : fail("I18N_WIRE_INVALID", `${name}.value must be a string.`);
    if (typeName === "str") return text;
    if (typeName === "int") {
      if (!INTEGER_PATTERN.test(text)) fail("I18N_WIRE_INVALID", `${name} is not a canonical integer.`);
      const number = Number(text);
      return Number.isSafeInteger(number) ? number : text;
    }
    if (typeName === "decimal") {
      if (!DECIMAL_PATTERN.test(text)) fail("I18N_WIRE_INVALID", `${name} is not a canonical decimal.`);
      return text;
    }
    if (typeName === "datetime") {
      const date = new Date(text);
      if (!Number.isFinite(date.valueOf())) {
        fail("I18N_WIRE_INVALID", `${name} is not a canonical datetime instant.`);
      }
      return date;
    }
    fail("I18N_WIRE_INVALID", `${name}.type is unsupported.`);
  }
  function bindingDefinition(value, provider2, renderedLocale) {
    const item = exactObject(value, "an i18n binding");
    const expected = ["id", "message", "target", "values"];
    if (Object.prototype.hasOwnProperty.call(item, "output")) expected.push("output");
    if (Object.prototype.hasOwnProperty.call(item, "values_expression")) expected.push("values_expression");
    exactKeys(item, expected, "an i18n binding");
    const targetItem = exactObject(item.target, "an i18n binding target");
    const kind = targetItem.kind;
    let target;
    if (kind === "text") {
      exactKeys(targetItem, ["kind"], "an i18n text target");
      target = Object.freeze({ kind });
    } else if (kind === "attribute") {
      exactKeys(targetItem, ["kind", "name"], "an i18n attribute target");
      const name = exactString(targetItem.name, "an i18n attribute target name");
      if (!BINDING_ATTRIBUTE_TARGETS.has(name)) fail("I18N_WIRE_INVALID", `binding target ${name} is not allowed.`);
      target = Object.freeze({ kind, name });
    } else {
      fail("I18N_WIRE_INVALID", "an i18n binding target kind is invalid.");
    }
    const rawValues = exactObject(item.values, "i18n binding values");
    const values2 = Object.freeze(
      Object.fromEntries(
        Object.entries(rawValues).map(([name, tagged]) => [
          name,
          taggedBindingValue(tagged, `i18n binding value ${name}`)
        ])
      )
    );
    const output = item.output;
    if (output !== void 0 && (typeof output !== "string" || output.length === 0)) {
      fail("I18N_WIRE_INVALID", "an i18n binding output must be a non-empty string.");
    }
    const valuesExpression = item.values_expression;
    if (valuesExpression !== void 0 && (typeof valuesExpression !== "string" || valuesExpression.length === 0)) {
      fail("I18N_WIRE_INVALID", "an i18n binding values_expression must be a non-empty string.");
    }
    return Object.freeze({
      id: exactString(item.id, "an i18n binding id"),
      message: exactString(item.message, "an i18n binding message"),
      ...output === void 0 ? {} : { output },
      provider: provider2,
      renderedLocale,
      target,
      values: values2,
      ...valuesExpression === void 0 ? {} : { valuesExpression }
    });
  }
  function requirementRecord(value) {
    const item = exactObject(value, "an i18n requirement");
    exactKeys(
      item,
      ["artifacts", "bindings", "messages", "outputs", "owner", "provider", "rendered_locale"],
      "an i18n requirement"
    );
    const provider2 = exactString(item.provider, "an i18n requirement provider");
    const owner = exactString(item.owner, "an i18n requirement owner");
    const renderedLocale = exactString(item.rendered_locale, "an i18n requirement rendered_locale");
    const outputs = new Set(stringList(item.outputs, "i18n requirement outputs"));
    const messages = new Set(stringList(item.messages, "i18n requirement messages"));
    const artifacts = /* @__PURE__ */ new Map();
    for (const [locale, artifact] of Object.entries(exactObject(item.artifacts, "i18n requirement artifacts"))) {
      artifacts.set(locale, createMessageRuntime(artifact, locale));
    }
    if (!Array.isArray(item.bindings)) fail("I18N_WIRE_INVALID", "i18n requirement bindings must be a list.");
    const bindings = Object.freeze(item.bindings.map((binding) => bindingDefinition(binding, provider2, renderedLocale)));
    return { artifacts, bindings, messages, outputs, owner, provider: provider2, renderedLocale };
  }
  function configureManifest(value) {
    const item = exactObject(value, "an i18n manifest");
    exactKeys(
      item,
      [
        "catalog_revision",
        "contexts",
        "formats",
        "formats_revision",
        "locales",
        "messages_url",
        "parsers",
        "providers",
        "requirements",
        "runtime",
        "schema_version"
      ],
      "an i18n manifest"
    );
    if (item.schema_version !== 1 || item.runtime !== "@fluent/bundle@0.19.1") {
      fail("I18N_WIRE_INVALID", "the i18n manifest version is unsupported.");
    }
    const locales = stringList(item.locales, "i18n manifest locales");
    const contexts = /* @__PURE__ */ new Map();
    for (const [locale, context] of Object.entries(exactObject(item.contexts, "i18n manifest contexts"))) {
      if (!locales.includes(locale)) fail("I18N_WIRE_INVALID", `context locale ${locale} is not selectable.`);
      const checked = immutableContext(context, `context ${locale}`);
      if (checked.locale !== locale) fail("I18N_WIRE_INVALID", `context ${locale} names another locale.`);
      contexts.set(locale, checked);
    }
    if (contexts.size !== locales.length) fail("I18N_WIRE_INVALID", "the i18n context table is incomplete.");
    const messagesUrl = item.messages_url;
    if (messagesUrl !== null && (typeof messagesUrl !== "string" || messagesUrl.length === 0)) {
      fail("I18N_WIRE_INVALID", "the i18n messages URL must be null or a non-empty string.");
    }
    const parsers = /* @__PURE__ */ new Map();
    for (const [locale, artifact] of Object.entries(exactObject(item.parsers, "i18n parser artifacts"))) {
      if (!locales.includes(locale)) fail("I18N_WIRE_INVALID", `parser locale ${locale} is not selectable.`);
      parsers.set(locale, parserArtifact(artifact, locale, exactString(item.formats_revision, "formats_revision")));
    }
    if (parsers.size !== locales.length) fail("I18N_WIRE_INVALID", "the i18n parser artifact table is incomplete.");
    const next = {
      catalogRevision: exactString(item.catalog_revision, "i18n catalog_revision"),
      contexts,
      formats: exactObject(item.formats, "i18n formats"),
      formatsRevision: exactString(item.formats_revision, "i18n formats_revision"),
      locales: new Set(locales),
      messagesUrl,
      parsers
    };
    if (configuration !== null && (configuration.catalogRevision !== next.catalogRevision || configuration.formatsRevision !== next.formatsRevision || JSON.stringify(Array.from(configuration.locales)) !== JSON.stringify(locales) || configuration.messagesUrl !== next.messagesUrl || JSON.stringify(configuration.formats) !== JSON.stringify(next.formats) || JSON.stringify(Array.from(configuration.parsers)) !== JSON.stringify(Array.from(next.parsers)))) {
      fail("I18N_WIRE_INVALID", "an i18n fragment uses a different project configuration.");
    }
    return [item, next];
  }
  function addRequirement(requirement) {
    const target = requirementsByProvider.get(requirement.provider) ?? /* @__PURE__ */ new Set();
    target.add(requirement);
    requirementsByProvider.set(requirement.provider, target);
    for (const binding of requirement.bindings) {
      const existing = bindingDefinitions.get(binding.id);
      if (existing !== void 0 && JSON.stringify(existing) !== JSON.stringify(binding)) {
        fail("I18N_WIRE_INVALID", `binding ${binding.id} has conflicting definitions.`);
      }
      bindingDefinitions.set(binding.id, binding);
      bindingReferenceCounts.set(binding.id, (bindingReferenceCounts.get(binding.id) ?? 0) + 1);
    }
    invalidateProviderTree(requirement.provider);
  }
  function removeRequirement(requirement) {
    const target = requirementsByProvider.get(requirement.provider);
    if (target === void 0) return;
    target.delete(requirement);
    if (target.size === 0) requirementsByProvider.delete(requirement.provider);
    for (const binding of requirement.bindings) {
      const remaining = (bindingReferenceCounts.get(binding.id) ?? 0) - 1;
      if (remaining <= 0) {
        bindingReferenceCounts.delete(binding.id);
        bindingDefinitions.delete(binding.id);
      } else {
        bindingReferenceCounts.set(binding.id, remaining);
      }
    }
    invalidateProviderTree(requirement.provider);
  }
  function processManifest(element, acceptedOwners = null) {
    if (processedManifests.has(element)) {
      if (!activeManifests.has(element)) {
        (manifestRequirements.get(element) ?? []).forEach(addRequirement);
        activeManifests.add(element);
      }
      return;
    }
    let manifest;
    let nextConfiguration;
    [manifest, nextConfiguration] = configureManifest(JSON.parse(element.textContent ?? ""));
    if (!Array.isArray(manifest.providers) || !Array.isArray(manifest.requirements)) {
      fail("I18N_WIRE_INVALID", "an i18n manifest needs provider and requirement lists.");
    }
    const previousConfiguration = configuration;
    if (configuration === null) configuration = nextConfiguration;
    let nextDefinitions;
    let requirements;
    try {
      nextDefinitions = manifest.providers.map(providerDefinition).filter((definition) => acceptedOwners === null || acceptedOwners.has(definition.id));
      requirements = manifest.requirements.map(requirementRecord).filter((requirement) => acceptedOwners === null || acceptedOwners.has(requirement.owner));
    } catch (error) {
      configuration = previousConfiguration;
      throw error;
    }
    try {
      const definitionIds = /* @__PURE__ */ new Set();
      for (const definition of nextDefinitions) {
        if (definitions.has(definition.id) || definitionIds.has(definition.id)) {
          fail("I18N_WIRE_INVALID", `provider ${definition.id} is duplicated.`);
        }
        if (definition.context.catalog_revision !== nextConfiguration.catalogRevision) {
          fail("I18N_WIRE_INVALID", `provider ${definition.id} has a stale catalog revision.`);
        }
        definitionIds.add(definition.id);
      }
      const stagedBindings = /* @__PURE__ */ new Map();
      for (const requirement of requirements) {
        const localIds = /* @__PURE__ */ new Set();
        for (const binding of requirement.bindings) {
          if (localIds.has(binding.id)) fail("I18N_WIRE_INVALID", `binding ${binding.id} is duplicated.`);
          localIds.add(binding.id);
          const existing = bindingDefinitions.get(binding.id) ?? stagedBindings.get(binding.id);
          if (existing !== void 0 && JSON.stringify(existing) !== JSON.stringify(binding)) {
            fail("I18N_WIRE_INVALID", `binding ${binding.id} has conflicting definitions.`);
          }
          stagedBindings.set(binding.id, binding);
        }
      }
    } catch (error) {
      configuration = previousConfiguration;
      throw error;
    }
    nextDefinitions.forEach((definition) => {
      definitions.set(definition.id, definition);
    });
    requirements.forEach(addRequirement);
    manifestRequirements.set(element, requirements);
    manifestDefinitions.set(element, nextDefinitions);
    processedManifests.add(element);
    activeManifests.add(element);
  }
  function bindingMarkersWithin(root) {
    const markers = Array.from(root.querySelectorAll("[data-citry-i18n-binding]"));
    for (const template of root.querySelectorAll("template")) {
      markers.push(...bindingMarkersWithin(template.content));
    }
    return markers;
  }
  function markerOwnsBinding(marker, bindingId) {
    return (marker.getAttribute("data-citry-i18n-binding") ?? "").trim().split(/\s+/).includes(bindingId);
  }
  function applyPreparedBindingWrite(destination, write) {
    if (write.binding.target.kind === "text") destination.textContent = write.text;
    else destination.setAttribute(write.binding.target.name, write.text);
  }
  function providerContextForPreparation(providerId) {
    return mountedProviders.get(providerId)?.state.context ?? definitions.get(providerId)?.context ?? null;
  }
  function adjustPreparedProviders(definitionList) {
    const pending = new Map(definitionList.map((definition) => [definition.id, definition]));
    const adjusted = [];
    let progress = true;
    while (pending.size !== 0 && progress) {
      progress = false;
      for (const [id, definition] of pending) {
        if (definition.parent === null) {
          adjusted.push(definition);
          pending.delete(id);
          progress = true;
          continue;
        }
        if (pending.has(definition.parent)) continue;
        const parentContext = providerContextForPreparation(definition.parent);
        if (parentContext === null) continue;
        const context = childContext(parentContext, definition);
        const replacement = sameContext(context, definition.context) ? definition : Object.freeze({ ...definition, context });
        definitions.set(id, replacement);
        adjusted.push(replacement);
        pending.delete(id);
        progress = true;
      }
    }
    for (const definition of pending.values()) adjusted.push(definition);
    return adjusted;
  }
  async function prepareRequirementForCurrentLocale(requirement) {
    for (let attempt = 0; attempt < 16; attempt += 1) {
      const context = providerContextForPreparation(requirement.provider);
      if (context === null) return;
      await fetchArtifact(requirement, context.locale);
      if (providerContextForPreparation(requirement.provider)?.locale === context.locale) return;
    }
    fail("I18N_BINDING_INVALID", `provider ${requirement.provider} kept changing while its fragment prepared.`);
  }
  function rollbackPreparedFrameworkManifest(prepared) {
    if (activeManifests.has(prepared.element)) {
      prepared.requirements.forEach(removeRequirement);
      activeManifests.delete(prepared.element);
    }
    for (const definition of prepared.definitions) {
      if (!mountedProviders.has(definition.id)) definitions.delete(definition.id);
    }
  }
  async function prepareFrameworkManifest(element, acceptedOwners, candidateRoot) {
    processManifest(element, acceptedOwners);
    const requirements = manifestRequirements.get(element) ?? [];
    const definitionList = manifestDefinitions.get(element) ?? [];
    const partial = {
      adjustedProviders: adjustPreparedProviders(definitionList),
      definitions: definitionList,
      element,
      requirements
    };
    try {
      await Promise.all(requirements.map(prepareRequirementForCurrentLocale));
      const writes = [];
      const markers = candidateRoot === null ? [] : bindingMarkersWithin(candidateRoot);
      for (const requirement of requirements) {
        const context = providerContextForPreparation(requirement.provider);
        if (context === null) continue;
        const runtime = requirement.artifacts.get(context.locale);
        for (const binding of requirement.bindings) {
          if (candidateRoot !== null && !markers.some((marker) => markerOwnsBinding(marker, binding.id))) {
            fail("I18N_BINDING_INVALID", `binding ${binding.id} has no destination in its fragment candidate.`);
          }
          if (context.locale === requirement.renderedLocale) continue;
          if (runtime === void 0) {
            fail("I18N_BINDING_INVALID", `provider ${requirement.provider} did not prepare locale ${context.locale}.`);
          }
          const token = binding.output === void 0 ? binding.message : `${binding.message}.${binding.output}`;
          writes.push(Object.freeze({ binding, text: runtime.format(token, binding.values) }));
        }
      }
      for (const write of writes) {
        for (const destination of markers.filter((marker) => markerOwnsBinding(marker, write.binding.id))) {
          applyPreparedBindingWrite(destination, write);
        }
      }
      return Object.freeze({ ...partial, writes });
    } catch (error) {
      rollbackPreparedFrameworkManifest({ ...partial, writes: [] });
      throw error;
    }
  }
  function commitPreparedFrameworkManifest(prepared) {
    const elements = Array.from(document.querySelectorAll("[data-cid]"));
    for (const definition of prepared.adjustedProviders) {
      const wrapper = elements.find(
        (element) => (element.getAttribute("data-cid") ?? "").trim().split(/\s+/).includes(definition.id)
      );
      if (wrapper === void 0) continue;
      wrapper.lang = definition.context.locale;
      wrapper.dir = definition.context.direction;
    }
    const markers = bindingMarkersWithin(document);
    for (const write of prepared.writes) {
      const destinations = markers.filter((element) => markerOwnsBinding(element, write.binding.id));
      if (destinations.length === 0) {
        fail("I18N_BINDING_INVALID", `binding ${write.binding.id} has no inserted destination.`);
      }
      for (const destination of destinations) {
        applyPreparedBindingWrite(destination, write);
      }
    }
  }
  function manifestsWithin(node) {
    if (!(node instanceof Element)) return [];
    const result = node.matches(MANIFEST_SELECTOR) ? [node] : [];
    return [...result, ...Array.from(node.querySelectorAll(MANIFEST_SELECTOR))];
  }
  function processExistingManifests() {
    document.querySelectorAll(MANIFEST_SELECTOR).forEach((element) => {
      processManifest(element);
    });
  }
  function retireDisconnectedProviders() {
    for (const [id, internal] of mountedProviders) {
      if (internal.wrapper.isConnected) continue;
      treeRoot(internal).generation += 1;
      if (internal.parent !== null) internal.parent.children.delete(internal);
      mountedProviders.delete(id);
    }
  }
  function treeRoot(internal) {
    let current = internal;
    while (current.parent !== null) current = current.parent;
    return current;
  }
  function invalidateProviderTree(providerId) {
    const internal = mountedProviders.get(providerId);
    if (internal !== void 0) treeRoot(internal).generation += 1;
  }
  function sameContext(left, right) {
    return left.catalog_revision === right.catalog_revision && left.direction === right.direction && left.formats_revision === right.formats_revision && left.locale === right.locale && left.time_zone === right.time_zone && left.tzdb_revision === right.tzdb_revision && JSON.stringify(left.fallback_locales) === JSON.stringify(right.fallback_locales);
  }
  function handleMutations(mutations) {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        manifestsWithin(node).forEach((element) => {
          processManifest(element);
        });
      });
      mutation.removedNodes.forEach((node) => {
        for (const element of manifestsWithin(node)) {
          if (element.isConnected || !activeManifests.has(element)) continue;
          const requirements = manifestRequirements.get(element) ?? [];
          requirements.forEach(removeRequirement);
          activeManifests.delete(element);
        }
      });
    }
    retireDisconnectedProviders();
  }
  function contextForLocale(locale) {
    const context = configuration?.contexts.get(locale);
    if (context === void 0) fail("I18N_LOCALE_INVALID", `locale ${locale} is not selectable.`);
    return context;
  }
  function childContext(parent, definition) {
    const locale = definition.policy.locale.mode === "explicit" ? definition.policy.locale.value : parent.locale;
    const localeContext = contextForLocale(locale);
    const direction = definition.policy.direction.mode === "explicit" ? definition.policy.direction.value : definition.policy.locale.mode === "explicit" ? localeContext.direction : parent.direction;
    const timeZone = definition.policy.time_zone.mode === "explicit" ? definition.policy.time_zone.value : definition.policy.time_zone.mode === "clear" ? null : parent.time_zone;
    return Object.freeze({
      ...localeContext,
      direction,
      time_zone: timeZone,
      tzdb_revision: timeZone === null ? "none" : definition.context.tzdb_revision
    });
  }
  function rootSwitchContext(internal, locale) {
    const localeContext = contextForLocale(locale);
    return Object.freeze({
      ...localeContext,
      direction: internal.definition.policy.direction.mode === "explicit" ? internal.definition.policy.direction.value : localeContext.direction,
      time_zone: internal.state.context.time_zone,
      tzdb_revision: internal.state.context.tzdb_revision
    });
  }
  function providerRequirements(internal) {
    return Array.from(requirementsByProvider.get(internal.definition.id) ?? []);
  }
  async function fetchArtifact(requirement, locale) {
    const loaded = requirement.artifacts.get(locale);
    if (loaded !== void 0) return loaded;
    const url = configuration?.messagesUrl;
    if (url === null || url === void 0) {
      fail("I18N_MESSAGES_UNAVAILABLE", `static output has no ${locale} artifact for this message set.`);
    }
    const response = await fetch(url, {
      body: JSON.stringify({
        catalog_revision: configuration.catalogRevision,
        locale,
        messages: Array.from(requirement.messages),
        outputs: Array.from(requirement.outputs),
        schema_version: 1
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST"
    });
    if (!response.ok) fail("I18N_MESSAGES_UNAVAILABLE", `the ${locale} message request failed with ${response.status}.`);
    const runtime = createMessageRuntime(await response.json(), locale);
    requirement.artifacts.set(locale, runtime);
    return runtime;
  }
  function plannedTree(root) {
    const planned = [];
    function visit(internal, inherited) {
      const context = root.plannedContexts.get(internal) ?? (inherited === null ? internal.state.context : childContext(inherited, internal.definition));
      planned.push([internal, context]);
      Array.from(internal.children).forEach((child) => {
        visit(child, context);
      });
    }
    visit(root, null);
    return planned;
  }
  async function stageTree(planned) {
    await Promise.all(
      planned.flatMap(
        ([internal, context]) => providerRequirements(internal).map((requirement) => fetchArtifact(requirement, context.locale))
      )
    );
    return planned.map(([internal, context]) => [internal, context]);
  }
  function planProviderSubtree(internal, context, owner) {
    const coordinator = treeRoot(internal);
    function visit(target, next) {
      coordinator.plannedContexts.set(target, next);
      coordinator.plannedOwners.set(target, owner);
      Array.from(target.children).forEach((child) => {
        visit(child, childContext(next, child.definition));
      });
    }
    visit(internal, context);
  }
  function restoreFailedPlan(coordinator, owner, initiator, error) {
    for (const [target, targetOwner] of coordinator.plannedOwners) {
      if (targetOwner !== owner) continue;
      coordinator.plannedOwners.delete(target);
      coordinator.plannedContexts.delete(target);
      target.state.status = Object.freeze({ phase: "ready" });
    }
    const code = error instanceof Error ? error.code ?? error.message : String(error);
    if (initiator.wrapper.isConnected) initiator.state.status = Object.freeze({ error: code, phase: "error" });
  }
  function formatLoaded(internal, message, values2, attr) {
    if (typeof message !== "string" || message.length === 0) fail("I18N_MESSAGE_INVALID", "message must be a string.");
    if (attr !== void 0 && (typeof attr !== "string" || attr.length === 0)) {
      fail("I18N_MESSAGE_INVALID", "attr must be a non-empty string when provided.");
    }
    const token = attr === void 0 ? message : `${message}.${attr}`;
    for (const requirement of providerRequirements(internal)) {
      const runtime = requirement.artifacts.get(internal.state.context.locale);
      const entry = runtime?.artifact.messages[token];
      if (runtime !== void 0 && entry !== void 0) return { entry, text: runtime.format(token, values2) };
    }
    fail(
      "I18N_MESSAGE_MISSING",
      `message ${token} is not loaded; declare a literal client use or await i18n.ensureMessages(${JSON.stringify(message)}).`
    );
  }
  function bindingValues(value, name) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      fail("I18N_BINDING_INVALID", `${name} must return an object of named values.`);
    }
    return value;
  }
  function bindingFingerprint(values2) {
    const normalized = [];
    for (const [name, value] of Object.entries(values2).sort(([left], [right]) => left.localeCompare(right))) {
      if (value instanceof Date) {
        normalized.push([name, "datetime", value.toISOString()]);
        continue;
      }
      const nativeValue = native(value);
      if (typeof nativeValue === "bigint") normalized.push([name, "int", nativeValue.toString()]);
      else if (typeof nativeValue === "number") {
        normalized.push([name, "number", decimalInput(nativeValue, "Decimal")]);
      } else if (typeof nativeValue === "string") normalized.push([name, "string", nativeValue]);
      else fail("I18N_BINDING_INVALID", `binding value ${name} has unsupported type ${typeof nativeValue}.`);
    }
    return JSON.stringify(normalized);
  }
  function reportBindingError(id, error) {
    console.error(`[Citry] i18n binding ${id} failed:`, error);
  }
  function resolvedLoaded(internal, message, values2, output) {
    const resolved = formatLoaded(internal, message, values2, output);
    const locale = resolved.entry.bundle_locale;
    const selected = configuration?.contexts.get(locale);
    return Object.freeze({
      direction: selected?.direction ?? internal.state.context.direction,
      locale,
      text: resolved.text,
      usedFallback: locale !== internal.state.context.locale
    });
  }
  function activateDeclarativeBinding(element, definition) {
    if (alpine === null) fail("I18N_BINDING_INVALID", `binding ${definition.id} initialized before Alpine.`);
    const service = alpine.evaluate(element, `$inject('${SERVICE_KEY}', null)`);
    const internal = service !== null && typeof service === "object" ? internals.get(service) : void 0;
    if (internal === void 0 || internal.definition.id !== definition.provider) {
      fail("I18N_BINDING_INVALID", `binding ${definition.id} is outside its logical i18n provider.`);
    }
    let values2 = definition.values;
    let effectReference = null;
    const active = {
      disposed: false,
      refresh() {
        if (active.disposed) return;
        const resolved = resolvedLoaded(internal, definition.message, values2, definition.output);
        if (definition.target.kind === "text") element.textContent = resolved.text;
        else element.setAttribute(definition.target.name, resolved.text);
      }
    };
    internal.bindings.add(active);
    if (definition.valuesExpression !== void 0) {
      let initial = true;
      effectReference = alpine.effect(() => {
        if (active.disposed) return;
        try {
          const evaluated = bindingValues(
            alpine.evaluate(element, definition.valuesExpression),
            `binding ${definition.id} values expression`
          );
          const preserve = initial && internal.state.context.locale === definition.renderedLocale && bindingFingerprint(evaluated) === bindingFingerprint(definition.values);
          values2 = evaluated;
          initial = false;
          if (!preserve) active.refresh();
        } catch (error) {
          initial = false;
          reportBindingError(definition.id, error);
        }
      });
    } else if (internal.state.context.locale !== definition.renderedLocale) {
      active.refresh();
    }
    alpine.onElRemoved(element, () => {
      if (active.disposed) return;
      active.disposed = true;
      internal.bindings.delete(active);
      if (effectReference !== null) alpine.release(effectReference);
    });
    return active;
  }
  function activateMarker(element) {
    element.removeAttribute("x-citry-tr");
    const ids = (element.getAttribute("data-citry-i18n-binding") ?? "").trim().split(/\s+/).filter(Boolean);
    if (ids.length === 0 || new Set(ids).size !== ids.length) {
      fail("I18N_BINDING_INVALID", "an i18n binding marker is empty or contains duplicate IDs.");
    }
    const destinations = /* @__PURE__ */ new Set();
    for (const id of ids) {
      const definition = bindingDefinitions.get(id);
      if (definition === void 0) fail("I18N_BINDING_INVALID", `binding marker ${id} has no checked record.`);
      const destination = definition.target.kind === "text" ? "text" : `attribute:${definition.target.name}`;
      if (destinations.has(destination)) fail("I18N_BINDING_INVALID", `binding marker ${id} duplicates ${destination}.`);
      destinations.add(destination);
      activateDeclarativeBinding(element, definition);
    }
  }
  function createService(internal) {
    const formatter = createFormatter(internal);
    const parser = createParser(internal);
    const service = {
      get context() {
        return internal.state.context;
      },
      get format() {
        return formatter;
      },
      get parse() {
        return parser;
      },
      get status() {
        return internal.state.status;
      },
      bind(options) {
        if (options === null || typeof options !== "object") {
          fail("I18N_BINDING_INVALID", "bind() needs an options object.");
        }
        const message = exactString(options.message, "bind() message");
        const output = options.output;
        if (output !== void 0 && (typeof output !== "string" || output.length === 0)) {
          fail("I18N_BINDING_INVALID", "bind() output must be a non-empty string.");
        }
        if (typeof options.onChange !== "function") fail("I18N_BINDING_INVALID", "bind() needs onChange.");
        if (options.values !== void 0 && typeof options.values !== "function") {
          fail("I18N_BINDING_INVALID", "bind() values must be a function.");
        }
        let values2 = {};
        let effectReference = null;
        const id = `imperative:${internal.definition.id}`;
        const active = {
          disposed: false,
          refresh() {
            if (active.disposed) return;
            try {
              if (options.values !== void 0) values2 = bindingValues(options.values(), "bind() values");
              const resolved = resolvedLoaded(internal, message, values2, output);
              options.onChange(resolved.text, resolved);
            } catch (error) {
              reportBindingError(id, error);
            }
          }
        };
        internal.bindings.add(active);
        if (options.values !== void 0) effectReference = alpine.effect(active.refresh);
        else active.refresh();
        return Object.freeze({
          dispose() {
            if (active.disposed) return;
            active.disposed = true;
            internal.bindings.delete(active);
            if (effectReference !== null) alpine.release(effectReference);
          },
          refresh: active.refresh
        });
      },
      async ensureMessages(input) {
        const messages = typeof input === "string" ? [input] : [...input];
        stringList(messages, "ensureMessages messages");
        const requirement = {
          artifacts: /* @__PURE__ */ new Map(),
          bindings: [],
          messages: new Set(messages),
          owner: internal.definition.id,
          outputs: /* @__PURE__ */ new Set(),
          provider: internal.definition.id,
          renderedLocale: internal.state.context.locale
        };
        await fetchArtifact(requirement, internal.state.context.locale);
        addRequirement(requirement);
      },
      resolve(message, values2 = {}, options = {}) {
        return resolvedLoaded(internal, message, values2, options.attr);
      },
      subscribe(callback) {
        if (typeof callback !== "function") fail("I18N_SUBSCRIBER_INVALID", "subscribe needs a callback.");
        internal.subscribers.add(callback);
        try {
          callback(internal.state.context);
        } catch (error) {
          reportBindingError("subscriber", error);
        }
        return () => internal.subscribers.delete(callback);
      },
      async switchLocale(locale) {
        if (typeof locale !== "string" || !configuration?.locales.has(locale)) {
          fail("I18N_LOCALE_INVALID", `locale ${String(locale)} is not selectable.`);
        }
        const initiator = internal;
        const coordinator = treeRoot(initiator);
        coordinator.switchGeneration += 1;
        const request = coordinator.switchGeneration;
        planProviderSubtree(initiator, rootSwitchContext(initiator, locale), request);
        for (const target of coordinator.plannedOwners.keys()) coordinator.plannedOwners.set(target, request);
        coordinator.generation += 1;
        for (const [target, targetOwner] of coordinator.plannedOwners) {
          if (targetOwner === request) {
            target.state.status = Object.freeze({
              phase: "loading",
              target: coordinator.plannedContexts.get(target).locale
            });
          }
        }
        for (let attempt = 0; attempt < 32; attempt += 1) {
          const generation = coordinator.generation;
          const snapshot = plannedTree(coordinator);
          let staged;
          try {
            staged = await stageTree(snapshot);
          } catch (error2) {
            if (request !== coordinator.switchGeneration) {
              return Object.freeze({ status: "stale" });
            }
            if (!initiator.wrapper.isConnected) {
              restoreFailedPlan(coordinator, request, initiator, error2);
              return Object.freeze({ status: "stale" });
            }
            if (generation !== coordinator.generation) continue;
            restoreFailedPlan(coordinator, request, initiator, error2);
            throw error2;
          }
          if (request !== coordinator.switchGeneration) {
            return Object.freeze({ status: "stale" });
          }
          if (!initiator.wrapper.isConnected) {
            restoreFailedPlan(coordinator, request, initiator, new Error("the switching provider was removed"));
            return Object.freeze({ status: "stale" });
          }
          if (generation !== coordinator.generation) continue;
          const changed = [];
          for (const [target, context] of staged) {
            target.wrapper.lang = context.locale;
            target.wrapper.dir = context.direction;
            if (!sameContext(target.state.context, context)) changed.push([target, context]);
            target.state.context = context;
            target.state.status = Object.freeze({ phase: "ready" });
          }
          coordinator.plannedContexts.clear();
          coordinator.plannedOwners.clear();
          for (const [target, context] of changed) {
            target.bindings.forEach((binding) => {
              try {
                binding.refresh();
              } catch (error2) {
                reportBindingError("provider-commit", error2);
              }
            });
            target.subscribers.forEach((callback) => {
              try {
                callback(context);
              } catch (error2) {
                reportBindingError("subscriber", error2);
              }
            });
          }
          return Object.freeze({ context: initiator.state.context, status: "committed" });
        }
        const error = new Error("the provider tree kept changing while its locale switch staged");
        restoreFailedPlan(coordinator, request, initiator, error);
        throw error;
      },
      tr(message, values2 = {}, options = {}) {
        return formatLoaded(internal, message, values2, options.attr).text;
      }
    };
    return Object.freeze(service);
  }
  function provider(element, parentService) {
    if (!(element instanceof HTMLElement) || !element.isConnected) {
      fail("I18N_PROVIDER_INVALID", "a client provider needs one live wrapper element.");
    }
    const ids = (element.getAttribute("data-cid") ?? "").trim().split(/\s+/).filter(Boolean);
    const candidates = ids.filter((id) => definitions.has(id) && !mountedProviders.has(id));
    if (candidates.length !== 1) fail("I18N_PROVIDER_INVALID", "the wrapper does not identify one unused provider.");
    const definition = definitions.get(candidates[0]);
    const parent = parentService === null ? null : internals.get(parentService) ?? fail("I18N_PROVIDER_INVALID", "the inherited service is not owned by this i18n runtime.");
    if ((parent?.definition.id ?? null) !== definition.parent) {
      fail("I18N_PROVIDER_INVALID", "the provider's server and browser parents differ.");
    }
    if (alpine === null) fail("I18N_PROVIDER_INVALID", "the provider initialized before Alpine was ready.");
    const resolved = parent === null ? definition.context : childContext(parent.state.context, definition);
    if (resolved.locale !== definition.context.locale || resolved.direction !== definition.context.direction || resolved.time_zone !== definition.context.time_zone) {
      fail("I18N_PROVIDER_INVALID", "the provider's server and browser contexts differ.");
    }
    const internal = {
      bindings: /* @__PURE__ */ new Set(),
      children: /* @__PURE__ */ new Set(),
      definition,
      generation: 0,
      parent: parent ?? null,
      plannedContexts: /* @__PURE__ */ new Map(),
      plannedOwners: /* @__PURE__ */ new Map(),
      state: alpine.reactive({
        context: resolved,
        status: Object.freeze({ phase: "ready" })
      }),
      subscribers: /* @__PURE__ */ new Set(),
      switchGeneration: 0,
      wrapper: element
    };
    const service = createService(internal);
    const complete = Object.assign(internal, { service });
    internals.set(service, complete);
    mountedProviders.set(definition.id, complete);
    parent?.children.add(complete);
    treeRoot(complete).generation += 1;
    return service;
  }
  citry.i18n = Object.freeze({ provider });
  citry.manager.registerFrameworkManifest("i18n", {
    commit(token) {
      commitPreparedFrameworkManifest(token);
    },
    match(element) {
      return element.matches(MANIFEST_SELECTOR);
    },
    prepare(element, options) {
      return prepareFrameworkManifest(element, options?.acceptedOwners ?? null, options?.candidateRoot ?? null);
    },
    rollback(token) {
      rollbackPreparedFrameworkManifest(token);
    }
  });
  citry.manager.decorateContext((context) => {
    context.i18n = context.inject(SERVICE_KEY, null);
  });
  citry.alpine.beforeStart((runtime) => {
    alpine = runtime;
    processExistingManifests();
    runtime.directive("citry-tr", activateMarker);
    citry.alpine._magic("i18n", (element) => runtime.evaluate(element, `$inject('${SERVICE_KEY}')`));
  });
  citry.alpine._register({
    init(element) {
      if (element.hasAttribute("data-citry-i18n-binding")) element.setAttribute("x-citry-tr", "");
    },
    mutations: handleMutations
  });
})();
