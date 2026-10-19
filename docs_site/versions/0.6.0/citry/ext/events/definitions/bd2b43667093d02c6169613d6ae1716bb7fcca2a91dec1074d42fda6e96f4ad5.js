(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createTextVNode: _createTextVNode } = Vue

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
  ], 16 /* FULL_PROPS */)), [
    [_directive_citry_vue_owned, 'selected']
  ])
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["83474cb5567d41c6d93479f4238bf21b74bd11c09e5b5758a7dcdc3388cc2ce5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["173fb2f2aa6f6e87b26c18beae5ae339facef3620fae4bb8bef55081cbf8e0e5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f8cf9dbc03e1c4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", _mergeProps({
      class: "cui-button__loading",
      "aria-hidden": "true",
      "data-citry-ui-part": "loading-indicator"
    }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb7a5d3c5d10a90ea", { key: 0 })
        : (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'fallback')
          ? (_openBlock(), _createElementBlock("span", {
            key: 1,
            class: "cui-button__spinner"
          }))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-button__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f0d8fda3d3bfb1f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f0d8fda3d3bfb1f", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1db84ab0869cd4eff3aa136033c0ded1b33d1f09a37939b8a7465799de6baca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_native_select_1e9583b3 = _resolveComponent("citry-c-native-select-1e9583b3")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  
  return (_openBlock(), _createElementBlock("section", { class: "ocean-controlled" }, [
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall1857d64e56be8751.id,
      key: _ctx.$citryPrepared.calls.citryCall1857d64e56be8751.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode("Survey vessel")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_native_select_1e9583b3, {
          value: _ctx.controlled
            ? _ctx.vessel
            : undefined,
          onInput: $event => (_ctx.vessel = $event.target.value),
          "citry-id": _ctx.$citryPrepared.calls.citryCall40d7da5f4c721cf9.id,
          key: _ctx.$citryPrepared.calls.citryCall40d7da5f4c721cf9.key
        }, null, 8 /* PROPS */, ["value", "onInput", "citry-id"]))
      ]),
      ['citrySlote7646b39489ca911']: _withCtx(() => [
        _createElementVNode("span", {
          textContent: _toDisplayString(_ctx.controlled
          ? 'Application controlled'
          : 'Browser controlled')
        }, null, 8 /* PROPS */, ["textContent"])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("div", { class: "ocean-controlled__actions" }, [
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        onClick: $event => (_ctx.controlled = false),
        "citry-id": _ctx.$citryPrepared.calls.citryCall73e41de3904f4dbf.id,
        key: _ctx.$citryPrepared.calls.citryCall73e41de3904f4dbf.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode(" Release ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        onClick: $event => {
        _ctx.vessel = 'calypso';
        _ctx.controlled = true;
      },
        "citry-id": _ctx.$citryPrepared.calls.citryCallb80e0419adc99fd8.id,
        key: _ctx.$citryPrepared.calls.citryCallb80e0419adc99fd8.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode(" Assign Calypso ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
        onClick: $event => {
        _ctx.vessel = null;
        _ctx.controlled = true;
      },
        "citry-id": _ctx.$citryPrepared.calls.citryCall08f50190fb1d4639.id,
        key: _ctx.$citryPrepared.calls.citryCall08f50190fb1d4639.key
      }, {
        ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
          _createTextVNode(" Clear ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["922dd11f3891e20772e37977d007c96b19620bde2f68c31e061d41ee0b33954e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall40d7da5f4c721cf9","typeKey":"CNativeSelect_bd67d3","componentTag":"citry-c-native-select-1e9583b3","bindings":[{"kind":"prop","name":":value","value":"controlled\n            ? vessel\n            : undefined","sourceStart":339,"sourceEnd":403},{"kind":"event","name":"@input","value":"vessel = $event.target.value","sourceStart":404,"sourceEnd":441}]},{"localId":"citryCall1857d64e56be8751","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCall40d7da5f4c721cf9"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall73e41de3904f4dbf","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"controlled = false","sourceStart":882,"sourceEnd":909}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb80e0419adc99fd8","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"\n        vessel = 'calypso';\n        controlled = true;\n      ","sourceStart":1163,"sourceEnd":1234}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall08f50190fb1d4639","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"\n        vessel = null;\n        controlled = true;\n      ","sourceStart":1495,"sourceEnd":1561}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_native_select_3e8f03ba = _resolveComponent("citry-controlled-native-select-3e8f03ba")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_native_select_3e8f03ba, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall3550b2d24a2e9fd0.id,
      key: _ctx.$citryPrepared.calls.citryCall3550b2d24a2e9fd0.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["de27f014c13e1bc766c51f1ff2c3b696cc989f1b88edcb16a902cb2211f4baa7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3550b2d24a2e9fd0","typeKey":"ControlledNativeSelect_46c9b9","componentTag":"citry-controlled-native-select-3e8f03ba","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
