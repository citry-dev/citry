(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({ class: "cui-slider" }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", _mergeProps({ class: "cui-slider__visually-hidden" }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
    _createElementVNode("span", _mergeProps({ class: "cui-slider__visually-hidden" }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "range",
      "data-citry-ui-part": "native-input"
    }, _ctx.$citryPrepared.citryAttrs3), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, ['checked','value']]
    ]),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "range",
      "data-thumb": "upper",
      "data-citry-ui-part": "native-input"
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, ['checked','value']]
    ]),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "hidden",
      "data-thumb": "single-or-lower",
      "data-citry-ui-part": "readonly-transport"
    }, _ctx.$citryPrepared.citryAttrs5), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, 'value']
    ]),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "hidden",
      "data-thumb": "upper",
      "data-citry-ui-part": "readonly-transport"
    }, _ctx.$citryPrepared.citryAttrs6), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, 'value']
    ]),
    _createElementVNode("div", {
      hidden: "",
      "data-citry-ui-part": "control"
    }, [
      _createElementVNode("div", { "data-citry-ui-part": "track" }, [
        _createElementVNode("span", { "data-citry-ui-part": "fill" }),
        _createElementVNode("button", _mergeProps({
          type: "button",
          role: "slider",
          "data-citry-ui-part": "thumb"
        }, _ctx.$citryPrepared.citryAttrs7), [
          _createElementVNode("span", { "data-citry-ui-part": "value" }, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("button", _mergeProps({
          type: "button",
          role: "slider",
          "data-citry-ui-part": "thumb"
        }, _ctx.$citryPrepared.citryAttrs8), [
          _createElementVNode("span", { "data-citry-ui-part": "value" }, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["19cdc545c3fc5f164db6ec6c2567de95f5461cd4ebfd1a61b35bd17f56a6ee4f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_range_slider_57248115 = _resolveComponent("citry-c-range-slider-57248115")
  
  return (_openBlock(), _createElementBlock("section", { class: "slider-example-stack" }, [
    _createElementVNode("p", null, [
      _createTextVNode("Inside a client-enabled "),
      _createElementVNode("code", null, "<c-i18n>"),
      _createTextVNode(", labels and formatted values switch locale in place.")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_range_slider_57248115, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall954b63df32ab2b63.id,
      key: _ctx.$citryPrepared.calls.citryCall954b63df32ab2b63.key
    }, null, 8 /* PROPS */, ["citry-id"])),
    _createElementVNode("p", null, [
      _createTextVNode("Canonical Form values remain "),
      _createElementVNode("code", null, "1234.5"),
      _createTextVNode(" and "),
      _createElementVNode("code", null, "5678.5"),
      _createTextVNode(".")
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["729eb33720d736c02212a352827a3867799f5c1155c10c8b326e096c01a7fcd6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall954b63df32ab2b63","typeKey":"CRangeSlider_7baa97","componentTag":"citry-c-range-slider-57248115","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_localized_slider_2e26fe5c = _resolveComponent("citry-localized-slider-2e26fe5c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_localized_slider_2e26fe5c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall25fd6becc3442b35.id,
      key: _ctx.$citryPrepared.calls.citryCall25fd6becc3442b35.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["453d9a5321c13e48579f3ea65b7bb04bcfc5cd69e12bd6896e57acfa41599d66"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall25fd6becc3442b35","typeKey":"LocalizedSlider_cb5ebf","componentTag":"citry-localized-slider-2e26fe5c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
