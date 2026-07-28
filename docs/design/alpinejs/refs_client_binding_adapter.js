/*
 * Throwaway component-boundary handler scope prototype for
 * refs_client_binding_harness.py.
 *
 * This is research code, not Citry runtime code. It composes the preceding
 * RootGroup spike with an explicit source-location anchor. Whole Alpine
 * handlers and optional Citry argument expressions authored on a child
 * component tag evaluate in the parent's exact lexical scope. `$el`,
 * `$dispatch`, and `$event` come from the physical child; native currentTarget
 * is untouched. This adapter does not model Citry server-handler parsing or
 * dispatch.
 */
(() => {
  function assertElement(value, message) {
    if (!(value instanceof Element)) throw new TypeError(message);
  }

  function makeEvaluationScope(physicalEventScope, sourceFacade) {
    const evaluationScope = { ...physicalEventScope };
    for (const key of Reflect.ownKeys(sourceFacade)) {
      if (Object.hasOwn(evaluationScope, key)) continue;
      Object.defineProperty(evaluationScope, key, {
        configurable: true,
        enumerable: true,
        get: () => Reflect.get(sourceFacade, key),
        set: (value) => Reflect.set(sourceFacade, key, value),
      });
    }
    return evaluationScope;
  }

  class SourceScopeAnchor {
    constructor(carrier, label = "source", isLogicalSourceLive = () => true) {
      this.label = label;
      this.carrier = null;
      this.destroyed = false;
      this.isLogicalSourceLive = isLogicalSourceLive;
      this.setCarrier(carrier);
    }

    setCarrier(carrier) {
      if (this.destroyed) throw new Error(`Cannot update destroyed scope source ${this.label}`);
      assertElement(carrier, `Citry scope source ${this.label} needs an Element evaluation carrier`);
      this.carrier = carrier;
      return this;
    }

    isLive() {
      return !this.destroyed && Boolean(this.carrier?.isConnected) && this.isLogicalSourceLive();
    }

    destroy() {
      this.destroyed = true;
      this.carrier = null;
    }
  }

  class BoundaryScopeClientBinding {
    constructor(group, source, options = {}) {
      if (!(group instanceof window.RootGroupSpike.RootGroup)) {
        throw new TypeError("Citry component-tag client binding needs a RootGroup");
      }
      if (!(source instanceof SourceScopeAnchor)) {
        throw new TypeError("Citry component-tag client binding needs a SourceScopeAnchor");
      }
      this.group = group;
      this.source = source;
      this.onDrop = options.onDrop || (() => {});
      this.cleanups = new Set();
      this.destroyed = false;
    }

    assertDomTarget() {
      if (this.group.els.length === 0) {
        throw new TypeError("Citry component event handler cannot attach because the target has no HTML element root");
      }
    }

    evaluate(expression, event, carrier, extraScope = {}) {
      if (this.destroyed || !this.source.isLive()) {
        this.onDrop("source-not-live");
        return { delivered: false, value: undefined };
      }
      if (!this.group.hasLive(carrier)) {
        this.onDrop("target-not-live");
        return { delivered: false, value: undefined };
      }
      const physicalEventScope = {
        $dispatch: Alpine.dontAutoEvaluateFunctions(() => Alpine.evaluateRaw(carrier, "$dispatch")),
        $el: carrier,
        $event: event,
      };
      const value = Alpine.evaluateRaw(this.source.carrier, expression, {
        // Alpine nests extras.scope inside another merge proxy. Passing an
        // Alpine merge proxy directly would preserve reads but send writes to
        // the wrong fallback object because its exposed keys are not own
        // properties. Own accessors bridge reads and writes to the facade.
        // Physical overrides win; all remaining names and magics come from
        // the source carrier's isolated Alpine stack.
        scope: makeEvaluationScope(physicalEventScope, extraScope),
      });
      return { delivered: true, value };
    }

    _bind(register, expression, receive, extraScope) {
      if (this.destroyed) throw new Error("Cannot attach a destroyed component-tag client binding");
      this.assertDomTarget();
      const stopGroup = register((domEvent, carrier) => {
        const outcome = this.evaluate(expression, domEvent, carrier, extraScope);
        if (outcome.delivered) receive(outcome.value, domEvent, carrier);
      });
      let active = true;
      const cleanup = () => {
        if (!active) return;
        active = false;
        stopGroup();
        this.cleanups.delete(cleanup);
      };
      this.cleanups.add(cleanup);
      return cleanup;
    }

    onAlpine(event, modifiers, expression, receive, extraScope = {}) {
      return this._bind((callback) => this.group.on(event, modifiers, callback), expression, receive, extraScope);
    }

    onCitry(event, spec, argumentExpression, receive, extraScope = {}) {
      return this._bind(
        (callback) => this.group.onCitry(event, spec, callback),
        argumentExpression,
        receive,
        extraScope,
      );
    }

    destroy() {
      if (this.destroyed) return;
      this.destroyed = true;
      for (const cleanup of Array.from(this.cleanups)) cleanup();
      this.cleanups.clear();
    }
  }

  window.BoundaryScopeSpike = { BoundaryScopeClientBinding, SourceScopeAnchor };
})();
