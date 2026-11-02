(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-361caf6ce22af4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", { class: "cui-menu__item-copy" }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-label",
        "data-citry-ui-part": "menu-item-label"
      }, _ctx.$citryPrepared.citryAttrs1), [
        (_ctx.$citryPrepared.selectedSlots['citrySlotf1817a57bc1354a1'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotf1817a57bc1354a1", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["d90350988f10d21b47c3fe72e3948c038edba9d3a6978d531b6920a500081185"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-menu",
    popover: "manual",
    role: "menu",
    "data-citry-menu-root": "",
    "data-citry-ui-part": "menu"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlot5176cbf97df342fc'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot5176cbf97df342fc", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5724fe4436c7b03d9f8295b958e822aaa5b29cb5e0b2c2a376f508224206ef60"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_internal_menu_surface_37f82339 = _resolveComponent("citry-c-internal-menu-surface-37f82339")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-context-menu-host",
    "data-citry-context-menu-host": "",
    "data-citry-ui-part": "context-menu"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotc8e5d267bc58cf8e'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotc8e5d267bc58cf8e", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("span", _mergeProps({
      "aria-hidden": "true",
      popover: "manual",
      "data-citry-context-menu-point": ""
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */),
    (_openBlock(), _createBlock(_component_citry_c_internal_menu_surface_37f82339, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall0944cd97843df107.id,
      key: _ctx.$citryPrepared.calls.citryCall0944cd97843df107.key
    }, {
      ['citrySlot5176cbf97df342fc']: _withCtx(() => [
        _renderSlot(_ctx.$slots, "citrySlot0021c864d3777155")
      ]),
      _: 3 /* FORWARDED */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["057cc3566882b0b0ef3a4cd9d1ce0fcaf9c9aff0d347520d8573c411d3bdf601"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0944cd97843df107","typeKey":"CInternalMenuSurface_597468","componentTag":"citry-c-internal-menu-surface-37f82339","bindings":[],"fills":[{"name":"citrySlot5176cbf97df342fc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":["citrySlot0021c864d3777155"]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, createVNode: _createVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_context_menu_native_card = _resolveComponent("context-menu-native-card")
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_context_menu_c149a668 = _resolveComponent("citry-c-context-menu-c149a668")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "context-menu-native" }, [
    _createElementVNode("p", null, " Select text or use the editing, link, image, media, embedded, and marked regions below. Their browser context menus stay available. "),
    (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({
      onOpenChange:(next,detail)=>
        _ctx.last=`${next ? 'Open' : 'Close'}: ${detail.reason}`,
    }, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall58fb16d63683bfbd.id,
      key: _ctx.$citryPrepared.calls.citryCall58fb16d63683bfbd.key
    }), {
      ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
        _createElementVNode("div", _mergeProps({
          class: "context-menu-native__target",
          tabindex: "0"
        }, _ctx.$citryPrepared.citryAttrs0), [
          _createElementVNode("p", { class: "context-menu-native__selection" }, " Select part of this paragraph before opening its browser menu. "),
          _createElementVNode("label", null, [
            _createTextVNode(" Editable title "),
            _withDirectives(_createElementVNode("input", { value: "Quarterly report" }, null, 512 /* NEED_PATCH */), [
              [_directive_citry_vue_owned, []]
            ])
          ]),
          _createElementVNode("div", { contenteditable: "true" }, "Editable note"),
          _createElementVNode("a", { href: "#native-content-destination" }, "Open linked record"),
          _createElementVNode("img", {
            alt: "Blue document thumbnail",
            width: "72",
            height: "48",
            src: "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
          }),
          _createElementVNode("video", {
            controls: "",
            "aria-label": "Media preview"
          }),
          _createVNode(_component_context_menu_native_card, null, {
            default: _withCtx(() => [
              _createTextVNode("Custom element host")
            ]),
            _: 1 /* STABLE */
          }),
          _createElementVNode("div", {
            "data-citry-context-menu-native": "",
            ref: "closedShadowHost"
          }, " Marked closed-shadow host ", 512 /* NEED_PATCH */),
          _createElementVNode("div", { ref: "openShadowHost" }, " Open-shadow selection fixture ", 512 /* NEED_PATCH */),
          _createElementVNode("iframe", {
            title: "Embedded document boundary",
            srcdoc: "<p>Child document keeps its own browser menu.</p>"
          }),
          _createElementVNode("div", {
            class: "context-menu-native__eligible",
            tabindex: "0"
          }, " Plain file row · Custom commands available here ")
        ], 16 /* FULL_PROPS */)
      ]),
      ['citrySlot0021c864d3777155']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld0f731ac19ba3ca9.id,
          key: _ctx.$citryPrepared.calls.citryCalld0f731ac19ba3ca9.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Rename file row")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallfa5b375afc3a54f3.id,
          key: _ctx.$citryPrepared.calls.citryCallfa5b375afc3a54f3.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Archive file row")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.last)
    }, "No custom request yet", 8 /* PROPS */, ["textContent"]),
    _createElementVNode("span", { id: "native-content-destination" }, "Linked record destination")
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["8e5243a18eabb35bfebb3fde29c2e77b5aa988896b2ef612ba92242c0d8ae8bc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld0f731ac19ba3ca9","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallfa5b375afc3a54f3","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall58fb16d63683bfbd","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n      onOpenChange:(next,detail)=>\n        last=`${next ? 'Open' : 'Close'}: ${detail.reason}`,\n    }","sourceStart":225,"sourceEnd":337}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCalld0f731ac19ba3ca9","citryCallfa5b375afc3a54f3"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_context_menu_native_content_67fd811f = _resolveComponent("citry-context-menu-native-content-67fd811f")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_context_menu_native_content_67fd811f, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall70adf9f5e2261dd9.id,
      key: _ctx.$citryPrepared.calls.citryCall70adf9f5e2261dd9.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["e4c1710431a922acf154f3d608ef207de3ae72a70de810907e9310a0dde0c556"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall70adf9f5e2261dd9","typeKey":"ContextMenuNativeContent_1af840","componentTag":"citry-context-menu-native-content-67fd811f","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
