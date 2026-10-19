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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e09b7efe2b35d220750a2206dc497ddf14f61452fbb4653ca32cf57ec81a2381"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_number_input_bb49fdfe = _resolveComponent("citry-c-number-input-bb49fdfe")
  
  return (_openBlock(), _createElementBlock("section", { class: "number-input-example-stack" }, [
    (_openBlock(), _createBlock(_component_citry_c_number_input_bb49fdfe, {
      value: _ctx.value,
      onValueChange: (next,detail)=>{_ctx.value=next;_ctx.last=`${detail.source}: ${next}`},
      "citry-id": _ctx.$citryPrepared.calls.citryCall6edbfc93aee4dd2a.id,
      key: _ctx.$citryPrepared.calls.citryCall6edbfc93aee4dd2a.key
    }, null, 8 /* PROPS */, ["value", "onValueChange", "citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(`Canonical value: ${_ctx.value}; ${_ctx.last}`)
    }, "Canonical value: 2", 8 /* PROPS */, ["textContent"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f12e6335bc1b8b68d660b8d851f91e77636aa49662ff40ed0e9b304ec6ca4c9b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6edbfc93aee4dd2a","typeKey":"CNumberInput_3f8aee","componentTag":"citry-c-number-input-bb49fdfe","bindings":[{"kind":"prop","name":":value","value":"value","sourceStart":79,"sourceEnd":93},{"kind":"prop","name":":onValueChange","value":"(next,detail)=>{value=next;last=`${detail.source}: ${next}`}","sourceStart":94,"sourceEnd":171}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_number_input_626dc9c3 = _resolveComponent("citry-controlled-number-input-626dc9c3")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_number_input_626dc9c3, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall089d1ff585289103.id,
      key: _ctx.$citryPrepared.calls.citryCall089d1ff585289103.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["01a546027944c3687758ba6fdc96fc240a7eb9c5c9a6578d0288f2ba28527064"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall089d1ff585289103","typeKey":"ControlledNumberInput_d2b24b","componentTag":"citry-controlled-number-input-626dc9c3","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
