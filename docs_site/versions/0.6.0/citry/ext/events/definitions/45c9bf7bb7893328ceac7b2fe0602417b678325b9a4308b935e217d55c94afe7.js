(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, renderList: _renderList } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", {
      "aria-hidden": "true",
      "data-citry-ui-part": "visual"
    }, [
      _createElementVNode("span", { "data-citry-ui-part": "empty" }, [
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop0, ($citryPrepared) => {
          return (_openBlock(), _createElementBlock("span", { "data-citry-ui-part": "symbol" }, "★"))
        }), 256 /* UNKEYED_FRAGMENT */))
      ]),
      _createElementVNode("span", { "data-citry-ui-part": "fill" }, [
        _createElementVNode("span", { "data-citry-ui-part": "fill-symbols" }, [
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop1, ($citryPrepared) => {
            return (_openBlock(), _createElementBlock("span", { "data-citry-ui-part": "symbol" }, "★"))
          }), 256 /* UNKEYED_FRAGMENT */))
        ])
      ])
    ]),
    _createElementVNode("span", _mergeProps({ "data-citry-ui-part": "choices" }, _ctx.$citryPrepared.citryAttrs1), [
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.$citryPrepared.citryLoop2, ($citryPrepared) => {
        return (_openBlock(), _createElementBlock("label", _mergeProps({ "data-citry-ui-part": "choice" }, $citryPrepared.citryAttrs0), [
          _withDirectives(_createElementVNode("input", _normalizeProps(_guardReactiveProps($citryPrepared.citryAttrs1)), null, 16 /* FULL_PROPS */), [
            [_directive_citry_vue_owned, ['checked','value']]
          ]),
          _createElementVNode("span", {
            class: "cui-rating__visually-hidden",
            "data-citry-ui-part": "choice-label"
          }, _toDisplayString($citryPrepared.citryText0), 1 /* TEXT */)
        ], 16 /* FULL_PROPS */))
      }), 256 /* UNKEYED_FRAGMENT */))
    ], 16 /* FULL_PROPS */),
    (_ctx.$citryPrepared.citryIf0 === 0)
      ? (_openBlock(), _createElementBlock("span", _mergeProps({
        key: 0,
        class: "cui-rating__visually-hidden",
        "data-citry-ui-part": "readonly-value"
      }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */))
      : _createCommentVNode("v-if", true),
    _withDirectives(_createElementVNode("input", _mergeProps({
      type: "hidden",
      "data-citry-ui-part": "readonly-transport"
    }, _ctx.$citryPrepared.citryAttrs3), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, 'value']
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["b6566a32d04d6df8b55734c4e7f17b0967beddd3ea2a29235ece3cd0bc850af5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_rating_0b4f386c = _resolveComponent("citry-c-rating-0b4f386c")
  
  return (_openBlock(), _createElementBlock("section", { class: "rating-demo-stack" }, [
    (_openBlock(), _createBlock(_component_citry_c_rating_0b4f386c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallfbd6ae3138ec112e.id,
      key: _ctx.$citryPrepared.calls.citryCallfbd6ae3138ec112e.key
    }, null, 8 /* PROPS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_rating_0b4f386c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla2ad0d368af53035.id,
      key: _ctx.$citryPrepared.calls.citryCalla2ad0d368af53035.key
    }, null, 8 /* PROPS */, ["citry-id"])),
    _createElementVNode("p", null, "The first Rating follows its nearest client-enabled i18n provider; the explicit pattern stays fixed.")
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["70476a0a8cbe18aa94e2a5b40820ca85eab102b4ec7586e75d57a6540b94d6ae"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfbd6ae3138ec112e","typeKey":"CRating_b89f9c","componentTag":"citry-c-rating-0b4f386c","bindings":[]},{"localId":"citryCalla2ad0d368af53035","typeKey":"CRating_b89f9c","componentTag":"citry-c-rating-0b4f386c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_rating_locales_4744724c = _resolveComponent("citry-rating-locales-4744724c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_rating_locales_4744724c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb29f2547b10b0eca.id,
      key: _ctx.$citryPrepared.calls.citryCallb29f2547b10b0eca.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fe43b3eabca53eec727edcbf23a315f8de44362dc483b415ccc51dcdf2189afc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb29f2547b10b0eca","typeKey":"RatingLocales_426c8c","componentTag":"citry-rating-locales-4744724c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
