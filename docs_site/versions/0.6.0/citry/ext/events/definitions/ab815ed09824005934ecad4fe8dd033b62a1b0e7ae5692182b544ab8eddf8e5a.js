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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1a3ffb3690111133286c233fe5abe50dfbfcdb378f196c30ad9bb43746532bf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

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
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
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
      }),
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-tags-input__input",
        type: "text",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */), [
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5d1e4c450c44c708d055c50726f840f493d658d181ebefc26e50c2f022dd5b83"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

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
        }, _ctx.$citryPrepared.citryAttrs3), [
          _createElementVNode("span", { "data-citry-ui-part": "tag-label" }, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            tabindex: "-1",
            "data-citry-ui-part": "remove"
          }, _ctx.$citryPrepared.citryAttrs4), "×", 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)
      ]),
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-tags-input__input",
        type: "text",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs5), null, 16 /* FULL_PROPS */), [
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5b90a26d559daa49420a43a53f2857ada1854ae162088658bdea9ea8c59d478c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_tags_input_9b0c5a93 = _resolveComponent("citry-c-tags-input-9b0c5a93")
  
  return (_openBlock(), _createElementBlock("section", { class: "tags-input-variants" }, [
    _createElementVNode("div", { class: "tags-input-variants__grid" }, [
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText0) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalldda225fb7d8176f3.id,
          key: _ctx.$citryPrepared.calls.citryCalldda225fb7d8176f3.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText2) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall9baaca86fff8294f.id,
          key: _ctx.$citryPrepared.calls.citryCall9baaca86fff8294f.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText4) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall11a7a7385193a747.id,
          key: _ctx.$citryPrepared.calls.citryCall11a7a7385193a747.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText6) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalldc27dfa018aa2494.id,
          key: _ctx.$citryPrepared.calls.citryCalldc27dfa018aa2494.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText8) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall3e6a876977a3bce8.id,
          key: _ctx.$citryPrepared.calls.citryCall3e6a876977a3bce8.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText10) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText11), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall5d0cff83f4efe99d.id,
          key: _ctx.$citryPrepared.calls.citryCall5d0cff83f4efe99d.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText12) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText13), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall22ca2e2c086f5904.id,
          key: _ctx.$citryPrepared.calls.citryCall22ca2e2c086f5904.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText14) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText15), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall910263ccafef7a53.id,
          key: _ctx.$citryPrepared.calls.citryCall910263ccafef7a53.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("code", null, _toDisplayString(_ctx.$citryPrepared.citryText16) + " / " + _toDisplayString(_ctx.$citryPrepared.citryText17), 1 /* TEXT */),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall2cee4bac93632bb7.id,
          key: _ctx.$citryPrepared.calls.citryCall2cee4bac93632bb7.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ])
    ]),
    _createElementVNode("div", { class: "tags-input-variants__boundaries" }, [
      _createElementVNode("article", null, [
        _createElementVNode("h3", null, "Empty and required"),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall1a5086c5601dbec8.id,
          key: _ctx.$citryPrepared.calls.citryCall1a5086c5601dbec8.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", null, [
        _createElementVNode("h3", null, "At maximum"),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall150cf016603328b2.id,
          key: _ctx.$citryPrepared.calls.citryCall150cf016603328b2.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      _createElementVNode("article", { style: "color-scheme:dark" }, [
        _createElementVNode("h3", null, "Dark and narrow"),
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall8ee8a612c59c352e.id,
          key: _ctx.$citryPrepared.calls.citryCall8ee8a612c59c352e.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6366dfcb34b64477a782534b5bf86248f5830b7e0480383a6e622081b3612cfe"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldda225fb7d8176f3","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall9baaca86fff8294f","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall11a7a7385193a747","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCalldc27dfa018aa2494","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall3e6a876977a3bce8","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall5d0cff83f4efe99d","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall22ca2e2c086f5904","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall910263ccafef7a53","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall2cee4bac93632bb7","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall1a5086c5601dbec8","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall150cf016603328b2","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]},{"localId":"citryCall8ee8a612c59c352e","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tags_input_variants_and_sizes_a3afc593 = _resolveComponent("citry-tags-input-variants-and-sizes-a3afc593")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tags_input_variants_and_sizes_a3afc593, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallf8c225c3bab25018.id,
      key: _ctx.$citryPrepared.calls.citryCallf8c225c3bab25018.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["87ece756eb358fcbd389640011fb722a9e4cabdd6f855874eddb208741a0aff7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf8c225c3bab25018","typeKey":"TagsInputVariantsAndSizes_85e5b3","componentTag":"citry-tags-input-variants-and-sizes-a3afc593","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
