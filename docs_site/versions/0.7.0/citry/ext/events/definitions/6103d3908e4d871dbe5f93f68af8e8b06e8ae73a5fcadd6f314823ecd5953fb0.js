(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-tags-input",
    "data-citry-ui-part": "tags-input"
  }, _ctx.$citryPrepared.citryAttrs0), [
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
window.__citryRuntimeDefinitions["aa09c9ba611afad659ff6f3a14227773a2b2848e62b27bda158973f24af0e891"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, createTextVNode: _createTextVNode, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_tags_input_9b0c5a93 = _resolveComponent("citry-c-tags-input-9b0c5a93")
  
  return (_openBlock(), _createElementBlock("section", { class: "tags-input-morph" }, [
    _createElementVNode("div", { class: "tags-input-morph__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEvent6c', $event))
      }, " Morph with the same baseline ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEventcb', $event))
      }, " Morph to a new baseline ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.controlled=!_ctx.controlled)
      }, " Toggle controlled handoff ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.mounted=!_ctx.mounted)
      }, " Remove or restore the fixture ", 8 /* PROPS */, ["onClick"])
    ]),
    _createElementVNode("p", null, [
      _createTextVNode("Server step: "),
      _createElementVNode("output", null, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
    ]),
    (_ctx.mounted)
      ? (_openBlock(), _createElementBlock("div", { key: 0 }, [
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          value: _ctx.controlled ? _ctx.tags : null,
          onValueChange: _ctx.applyControlledTags,
          "citry-id": _ctx.$citryPrepared.calls.citryCall2a3a239f5f7253ad.id,
          key: _ctx.$citryPrepared.calls.citryCall2a3a239f5f7253ad.key
        }, null, 8 /* PROPS */, ["value", "onValueChange", "citry-id"]))
      ]))
      : _createCommentVNode("v-if", true),
    _createElementVNode("p", null, " Unchanged server baselines preserve uncontrolled tags, draft, selection, and focus. Step two supplies a new baseline. An active composition keeps the exact editor node through either morph. ")
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["8d1469a7bd8bb63de9542b83d26697f1713ca1d907bd609806103055f91b0d77"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2a3a239f5f7253ad","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":value","value":"controlled ? tags : null","sourceStart":727,"sourceEnd":760},{"kind":"prop","name":":onValueChange","value":"applyControlledTags","sourceStart":761,"sourceEnd":797}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tags_input_morph_and_cleanup_51a3bcde = _resolveComponent("citry-tags-input-morph-and-cleanup-51a3bcde")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tags_input_morph_and_cleanup_51a3bcde, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalldfdf5fb8494c8d89.id,
      key: _ctx.$citryPrepared.calls.citryCalldfdf5fb8494c8d89.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c1afcd418c66436a4184f22f708614f88f65a6f14198200ae8f1db4ba2966aec"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldfdf5fb8494c8d89","typeKey":"TagsInputMorphAndCleanup_bdfc29","componentTag":"citry-tags-input-morph-and-cleanup-51a3bcde","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
