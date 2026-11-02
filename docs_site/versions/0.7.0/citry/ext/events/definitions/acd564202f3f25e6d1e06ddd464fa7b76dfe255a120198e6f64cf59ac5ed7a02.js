(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({ "data-citry-ui-part": "tags-input" }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("select", _mergeProps({
      class: "cui-tags-input__native",
      multiple: "",
      "data-citry-tags-input-native": ""
    }, _ctx.$citryPrepared.citryAttrs1), [
      _withDirectives(_createElementVNode("option", _mergeProps({ selected: "" }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */), [
        [_directive_citry_vue_owned, 'value']
      ]),
      _withDirectives(_createElementVNode("option", _mergeProps({ selected: "" }, _ctx.$citryPrepared.citryAttrs3), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */), [
        [_directive_citry_vue_owned, 'value']
      ])
    ], 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, []]
    ]),
    _createElementVNode("div", {
      class: "cui-tags-input__control",
      hidden: "",
      "data-citry-ui-part": "control"
    }, [
      _createElementVNode("span", {
        class: "cui-tags-input__tag-list",
        "data-citry-ui-part": "tag-list"
      }, [
        _createElementVNode("span", _mergeProps({
          class: "cui-tags-input__tag",
          "data-citry-ui-part": "tag"
        }, _ctx.$citryPrepared.citryAttrs4), [
          _createElementVNode("span", { "data-citry-ui-part": "tag-label" }, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            tabindex: "-1",
            "data-citry-ui-part": "remove"
          }, _ctx.$citryPrepared.citryAttrs5), "×", 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("span", _mergeProps({
          class: "cui-tags-input__tag",
          "data-citry-ui-part": "tag"
        }, _ctx.$citryPrepared.citryAttrs6), [
          _createElementVNode("span", { "data-citry-ui-part": "tag-label" }, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            tabindex: "-1",
            "data-citry-ui-part": "remove"
          }, _ctx.$citryPrepared.citryAttrs7), "×", 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)
      ]),
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-tags-input__input",
        type: "text",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs8), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, ['checked','value']]
      ])
    ]),
    _createElementVNode("span", {
      hidden: "",
      "data-citry-tags-input-readonly-values": ""
    }),
    _createElementVNode("span", {
      class: "cui-tags-input__status cui-form-control__status",
      role: "status",
      "aria-live": "polite",
      "aria-atomic": "true",
      "data-citry-ui-part": "status"
    })
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["44dbb25ba6440775e3b5a2e06f5232dd9cc98b2921a7b58bc914e1e5bf83d352"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_tags_input_9b0c5a93 = _resolveComponent("citry-c-tags-input-9b0c5a93")
  
  return (_openBlock(), _createElementBlock("section", { class: "tags-input-customization" }, [
    _createElementVNode("article", { class: "tags-input-brand tags-input-brand--orchard" }, [
      _createElementVNode("h3", null, "Orchard field notes"),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall9984d34f58403d97.id,
        key: _ctx.$citryPrepared.calls.citryCall9984d34f58403d97.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    _createElementVNode("article", {
      class: "tags-input-brand tags-input-brand--harbor",
      style: "color-scheme:dark"
    }, [
      _createElementVNode("h3", null, "Harbor field notes"),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall202047ac6c9eda48.id,
        key: _ctx.$citryPrepared.calls.citryCall202047ac6c9eda48.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["80db6ac0832ff5260ff3d6f081e8f053d9420c34925c4f6ee2fbfed10535a533"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9984d34f58403d97","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall202047ac6c9eda48","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tags_input_customization_e36f07e6 = _resolveComponent("citry-tags-input-customization-e36f07e6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tags_input_customization_e36f07e6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall4871771945fe771e.id,
      key: _ctx.$citryPrepared.calls.citryCall4871771945fe771e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a7cc88048671899e8029a6cf791a70060fefe7ccce2aaf33da3a2a914d604183"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4871771945fe771e","typeKey":"TagsInputCustomization_8f0a53","componentTag":"citry-tags-input-customization-e36f07e6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
