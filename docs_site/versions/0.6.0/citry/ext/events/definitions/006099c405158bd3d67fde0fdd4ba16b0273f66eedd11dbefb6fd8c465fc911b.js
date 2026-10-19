(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("select", _mergeProps({
    class: "cui-native-select",
    "data-citry-ui-part": "native-select"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives((_openBlock(), _createElementBlock("option", {
      value: "",
      key: _ctx.$citryPrepared.citryKey0
    }, [
      _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
    ], 513 /* TEXT, NEED_PATCH */)), [
      [_directive_citry_vue_owned, []]
    ]),
    _createElementVNode("optgroup", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs2, { key: _ctx.$citryPrepared.citryKey1 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ]),
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs3, { key: _ctx.$citryPrepared.citryKey2 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ]),
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs4, { key: _ctx.$citryPrepared.citryKey3 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ])
    ], 16 /* FULL_PROPS */),
    _createElementVNode("optgroup", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs5)), [
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs6, { key: _ctx.$citryPrepared.citryKey4 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ]),
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs7, { key: _ctx.$citryPrepared.citryKey5 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, 'selected']
  ])
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["68aa99c2b44717c0a47bebf3b090ff5de3ab733e27e3dc9a255e235aeabce84b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["20e43661f277ed6a086a7fa74020f448ecad0a3aed84b6089a89d765db323728"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return _withDirectives((_openBlock(), _createElementBlock("select", _mergeProps({
    class: "cui-native-select",
    "data-citry-ui-part": "native-select"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps({ value: "" }, _ctx.$citryPrepared.citryAttrs1, { key: _ctx.$citryPrepared.citryKey0 }), [
      _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
    ], 17 /* TEXT, FULL_PROPS */)), [
      [_directive_citry_vue_owned, 'selected']
    ]),
    _createElementVNode("optgroup", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs2)), [
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs3, { key: _ctx.$citryPrepared.citryKey1 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ]),
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs4, { key: _ctx.$citryPrepared.citryKey2 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ]),
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs5, { key: _ctx.$citryPrepared.citryKey3 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ])
    ], 16 /* FULL_PROPS */),
    _createElementVNode("optgroup", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs6)), [
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs7, { key: _ctx.$citryPrepared.citryKey4 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ]),
      _withDirectives((_openBlock(), _createElementBlock("option", _mergeProps(_ctx.$citryPrepared.citryAttrs8, { key: _ctx.$citryPrepared.citryKey5 }), [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
      ], 17 /* TEXT, FULL_PROPS */)), [
        [_directive_citry_vue_owned, ['selected','value']]
      ])
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, 'selected']
  ])
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2051cdba06faec33567a5e1292c4d66f6f88b4784c3d5476c1e3498182065cb5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs3), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot853fef0ef19da02c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot853fef0ef19da02c", { key: 2 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["24b48f7ec97f2f76107a0821d94e0433a7cb5e072858f54b604bfd371ef0cbe7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_native_select_1e9583b3 = _resolveComponent("citry-c-native-select-1e9583b3")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "ocean-glance",
    "aria-label": "Ocean habitat survey"
  }, [
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall59668f36731f2f9c.id,
      key: _ctx.$citryPrepared.calls.citryCall59668f36731f2f9c.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode("Primary habitat")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_native_select_1e9583b3, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall51e543220572fa9d.id,
          key: _ctx.$citryPrepared.calls.citryCall51e543220572fa9d.key
        }, null, 8 /* PROPS */, ["citry-id"]))
      ]),
      ['citrySlote7646b39489ca911']: _withCtx(() => [
        _createTextVNode("Choose the habitat represented by this dive.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("div", {
      class: "ocean-glance__deep",
      style: "color-scheme: dark"
    }, [
      (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall348a3943ae5de3b1.id,
        key: _ctx.$citryPrepared.calls.citryCall348a3943ae5de3b1.key
      }, {
        ['citrySlote2526e6f745e4169']: _withCtx(() => [
          _createTextVNode("Unverified station")
        ]),
        ['citrySlot6f90e269deb4619c']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_native_select_1e9583b3, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall6278ecfd26407f61.id,
            key: _ctx.$citryPrepared.calls.citryCall6278ecfd26407f61.key
          }, null, 8 /* PROPS */, ["citry-id"]))
        ]),
        ['citrySlot853fef0ef19da02c']: _withCtx(() => [
          _createTextVNode("Match this station to a surveyed habitat.")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["889ef698b37e178a1a8ef89b329580b8ef8d53957b55b1cf35970ee32de8b137"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall51e543220572fa9d","typeKey":"CNativeSelect_bd67d3","componentTag":"citry-c-native-select-1e9583b3","bindings":[]},{"localId":"citryCall59668f36731f2f9c","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall51e543220572fa9d"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6278ecfd26407f61","typeKey":"CNativeSelect_bd67d3","componentTag":"citry-c-native-select-1e9583b3","bindings":[]},{"localId":"citryCall348a3943ae5de3b1","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall6278ecfd26407f61"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot853fef0ef19da02c","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_native_select_at_a_glance_156b909b = _resolveComponent("citry-native-select-at-a-glance-156b909b")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_native_select_at_a_glance_156b909b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall3b7426d829e7e778.id,
      key: _ctx.$citryPrepared.calls.citryCall3b7426d829e7e778.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["251e88fef47912544d9a24afa86ceb47b7ae3d29e81c020d9a971914b88a9593"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3b7426d829e7e778","typeKey":"NativeSelectAtAGlance_ebbf06","componentTag":"citry-native-select-at-a-glance-156b909b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
