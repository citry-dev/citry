(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-number-input",
    "data-citry-ui-part": "number-input"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      _createElementVNode("button", _mergeProps({
        type: "button",
        tabindex: "-1",
        "data-citry-ui-part": "decrement"
      }, _ctx.$citryPrepared.citryAttrs1), [
        _createElementVNode("span", { "aria-hidden": "true" }, "−")
      ], 16 /* FULL_PROPS */),
      _withDirectives(_createElementVNode("input", _mergeProps({
        type: "text",
        role: "spinbutton",
        inputmode: "decimal",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, ['checked','value']]
      ]),
      _createElementVNode("button", _mergeProps({
        type: "button",
        tabindex: "-1",
        "data-citry-ui-part": "increment"
      }, _ctx.$citryPrepared.citryAttrs3), [
        _createElementVNode("span", { "aria-hidden": "true" }, "+")
      ], 16 /* FULL_PROPS */)
    ]),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "hidden",
      disabled: ""
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, []]
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["aebd83fc1095a940f641070270f466daca470d7f64b9c5c7ed5c6417153ab454"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-field",
    "data-citry-field-root": "",
    "data-citry-ui-part": "field"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote2526e6f745e4169'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote2526e6f745e4169", { key: 0 })
        : _createCommentVNode("v-if", true),
      _createElementVNode("span", {
        class: "cui-field__required",
        "aria-hidden": "true",
        "data-citry-ui-part": "required-indicator"
      }, " * ")
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f90e269deb4619c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f90e269deb4619c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs2), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote7646b39489ca911'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7646b39489ca911", { key: 2 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs3), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["f30ef56c8a46836137f3aa085cbf64b130dbb8e330ec07abe463865cd9280bbf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-field",
    "data-citry-field-root": "",
    "data-citry-ui-part": "field"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote2526e6f745e4169'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote2526e6f745e4169", { key: 0 })
        : _createCommentVNode("v-if", true),
      _createElementVNode("span", _mergeProps({
        class: "cui-field__required",
        "aria-hidden": "true",
        "data-citry-ui-part": "required-indicator"
      }, _ctx.$citryPrepared.citryAttrs2), " * ", 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f90e269deb4619c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f90e269deb4619c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs3), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote7646b39489ca911'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7646b39489ca911", { key: 2 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a5c3b89119e24e0edb50b0c4d8146aa09a3101e367fac6a368ec0e1841947dcf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_number_input_bb49fdfe = _resolveComponent("citry-c-number-input-bb49fdfe")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  
  return (_openBlock(), _createElementBlock("section", { class: "number-input-example-grid" }, [
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall86abbe44fa6ded08.id,
      key: _ctx.$citryPrepared.calls.citryCall86abbe44fa6ded08.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode("Validate the draft")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_number_input_bb49fdfe, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalle4966e3a653b478b.id,
          key: _ctx.$citryPrepared.calls.citryCalle4966e3a653b478b.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      ['citrySlote7646b39489ca911']: _withCtx(() => [
        _createTextVNode("Enter a quarter step from 0 through 3.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallcf65ae2312ed7122.id,
      key: _ctx.$citryPrepared.calls.citryCallcf65ae2312ed7122.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode("Clamp on commit")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_number_input_bb49fdfe, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallf47bdd536b821e66.id,
          key: _ctx.$citryPrepared.calls.citryCallf47bdd536b821e66.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      ['citrySlote7646b39489ca911']: _withCtx(() => [
        _createTextVNode("A parse-valid outside value moves to the nearest bound.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["572859dab1b3ccf6ca65cc44c2994c962567f2bfd06587ab8656e14f7293f4e6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle4966e3a653b478b","typeKey":"CNumberInput_3f8aee","componentTag":"citry-c-number-input-bb49fdfe","bindings":[]},{"localId":"citryCall86abbe44fa6ded08","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCalle4966e3a653b478b"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf47bdd536b821e66","typeKey":"CNumberInput_3f8aee","componentTag":"citry-c-number-input-bb49fdfe","bindings":[]},{"localId":"citryCallcf65ae2312ed7122","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCallf47bdd536b821e66"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_number_input_constraints_bb89e1ab = _resolveComponent("citry-number-input-constraints-bb89e1ab")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_number_input_constraints_bb89e1ab, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle2cb38bcd633f931.id,
      key: _ctx.$citryPrepared.calls.citryCalle2cb38bcd633f931.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b934db49e8e59f6e1308c7fddafe2e3ea54a03a4861252230211c975514a3bbb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle2cb38bcd633f931","typeKey":"NumberInputConstraints_ab94c8","componentTag":"citry-number-input-constraints-bb89e1ab","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
