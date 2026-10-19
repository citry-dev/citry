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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-drawer-host",
    "data-citry-drawer-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot0fd16c759f36fbe0'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot0fd16c759f36fbe0", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("dialog", _mergeProps({
      class: "cui-drawer",
      "aria-modal": "true",
      "data-citry-ui-part": "drawer"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("div", {
        class: "cui-drawer__surface",
        "data-citry-ui-part": "surface"
      }, [
        _createElementVNode("header", {
          class: "cui-drawer__header",
          "data-citry-ui-part": "header"
        }, [
          _createElementVNode("h2", _mergeProps({
            class: "cui-drawer__title",
            "data-citry-ui-part": "title"
          }, _ctx.$citryPrepared.citryAttrs1), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot708499261541aa37'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot708499261541aa37", { key: 1 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("button", _mergeProps({
            class: "cui-drawer__close",
            type: "button",
            "data-citry-drawer-close": "",
            "data-citry-drawer-built-in-close": "",
            "data-citry-ui-part": "close"
          }, _ctx.$citryPrepared.citryAttrs2), [
            _createElementVNode("span", { "aria-hidden": "true" }, "×")
          ], 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("div", {
          class: "cui-drawer__body",
          "data-citry-ui-part": "body"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlotcf00dfaff8d30a7d'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotcf00dfaff8d30a7d", { key: 2 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["27a3233616fcadb82523a472b68bb206021a2b741721cdfe996790d029f8d2c6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_drawer_7a79445f = _resolveComponent("citry-c-drawer-7a79445f")
  
  return (_openBlock(), _createElementBlock("section", { class: "drawer-sampler" }, [
    (_openBlock(), _createBlock(_component_citry_c_drawer_7a79445f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall463e50e08d13e303.id,
      key: _ctx.$citryPrepared.calls.citryCall463e50e08d13e303.key
    }, {
      ['citrySlot0fd16c759f36fbe0']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall3cf05af92519e31c.id,
          key: _ctx.$citryPrepared.calls.citryCall3cf05af92519e31c.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Leading Drawer")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot708499261541aa37']: _withCtx(() => [
        _createTextVNode("Atlas index")
      ]),
      ['citrySlotcf00dfaff8d30a7d']: _withCtx(() => [
        _createTextVNode("Browse nearby observations.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_drawer_7a79445f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall51b794880af11c01.id,
      key: _ctx.$citryPrepared.calls.citryCall51b794880af11c01.key
    }, {
      ['citrySlot0fd16c759f36fbe0']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall7cf83fccc579ae1e.id,
          key: _ctx.$citryPrepared.calls.citryCall7cf83fccc579ae1e.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Trailing Drawer")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot708499261541aa37']: _withCtx(() => [
        _createTextVNode("Field note")
      ]),
      ['citrySlotcf00dfaff8d30a7d']: _withCtx(() => [
        _createTextVNode("Edit the selected observation.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_drawer_7a79445f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall40273e2fec3b9f7d.id,
      key: _ctx.$citryPrepared.calls.citryCall40273e2fec3b9f7d.key
    }, {
      ['citrySlot0fd16c759f36fbe0']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallcffe785f0affb8ff.id,
          key: _ctx.$citryPrepared.calls.citryCallcffe785f0affb8ff.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Bottom Sheet")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot708499261541aa37']: _withCtx(() => [
        _createTextVNode("Quick actions")
      ]),
      ['citrySlotcf00dfaff8d30a7d']: _withCtx(() => [
        _createTextVNode("Choose an action for this record.")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["731cc468dcd5eae134dff95d534b37568685e04afa6fc9f592b55b36fd719afe"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall3cf05af92519e31c","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall463e50e08d13e303","typeKey":"CDrawer_01cc33","componentTag":"citry-c-drawer-7a79445f","bindings":[],"fills":[{"name":"citrySlot0fd16c759f36fbe0","localDescendants":["citryCall3cf05af92519e31c"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot708499261541aa37","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotcf00dfaff8d30a7d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7cf83fccc579ae1e","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall51b794880af11c01","typeKey":"CDrawer_01cc33","componentTag":"citry-c-drawer-7a79445f","bindings":[],"fills":[{"name":"citrySlot0fd16c759f36fbe0","localDescendants":["citryCall7cf83fccc579ae1e"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot708499261541aa37","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotcf00dfaff8d30a7d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallcffe785f0affb8ff","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall40273e2fec3b9f7d","typeKey":"CDrawer_01cc33","componentTag":"citry-c-drawer-7a79445f","bindings":[],"fills":[{"name":"citrySlot0fd16c759f36fbe0","localDescendants":["citryCallcffe785f0affb8ff"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot708499261541aa37","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotcf00dfaff8d30a7d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_drawer_at_a_glance_34be24c7 = _resolveComponent("citry-drawer-at-a-glance-34be24c7")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_drawer_at_a_glance_34be24c7, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalldab2a9a0caea4fee.id,
      key: _ctx.$citryPrepared.calls.citryCalldab2a9a0caea4fee.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["cf9c3a164c08bdc0a3629f1a20aa39a88d65ed693be41fe0dff33ce851086bef"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldab2a9a0caea4fee","typeKey":"DrawerAtAGlance_d2586d","componentTag":"citry-drawer-at-a-glance-34be24c7","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
