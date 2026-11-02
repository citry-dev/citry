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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["fb5bd7cc218627a4763325998ab83d202f411b1987e331bd9c6df4af22ae946b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-menu__submenu",
    role: "none",
    "data-citry-menu-entry": "",
    "data-citry-menu-submenu": "",
    "data-citry-ui-part": "menu-submenu"
  }, [
    _createElementVNode("button", _mergeProps({
      class: "cui-menu__item cui-menu__submenu-trigger",
      type: "button",
      role: "menuitem",
      tabindex: "-1",
      "aria-haspopup": "menu",
      "aria-expanded": "false",
      "data-citry-ui-part": "menu-submenu-trigger"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("span", { class: "cui-menu__item-copy" }, [
        _createElementVNode("span", _mergeProps({
          class: "cui-menu__item-label",
          "data-citry-ui-part": "menu-item-label"
        }, _ctx.$citryPrepared.citryAttrs1), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot5edbca3669e97392'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot5edbca3669e97392", { key: 0 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */)
      ]),
      (_openBlock(), _createElementBlock("span", {
        class: "cui-menu__item-end cui-menu__submenu-chevron",
        "aria-hidden": "true",
        "data-citry-ui-part": "menu-item-end"
      }, [
        (_openBlock(), _createElementBlock("svg", {
          xmlns: "http://www.w3.org/2000/svg",
          viewBox: "0 0 24 24",
          fill: "none",
          stroke: "currentColor",
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
          focusable: "false",
          "aria-hidden": "true"
        }, [
          _createElementVNode("path", { d: "m9 18 6-6-6-6" })
        ]))
      ]))
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      class: "cui-menu cui-menu--submenu",
      inert: "",
      popover: "manual",
      role: "menu",
      "data-citry-ui-part": "menu"
    }, _ctx.$citryPrepared.citryAttrs2), [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6bda043c1d90fe5c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6bda043c1d90fe5c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-menu__measurement",
      "aria-hidden": "true",
      "data-citry-menu-measure": ""
    })
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a36f0810444fbb96aa072de078b6659c1c86f9ba2dbd1d3e22bd40ecea367f75"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

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
const { resolveComponent: _resolveComponent, renderSlot: _renderSlot, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_internal_menu_surface_37f82339 = _resolveComponent("citry-c-internal-menu-surface-37f82339")
  
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-menu-host",
    "data-citry-menu-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlote9035851c53b236c'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlote9035851c53b236c", { key: 0 })
      : _createCommentVNode("v-if", true),
    (_openBlock(), _createBlock(_component_citry_c_internal_menu_surface_37f82339, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9ee6b0021ed574b1.id,
      key: _ctx.$citryPrepared.calls.citryCall9ee6b0021ed574b1.key
    }, {
      ['citrySlot5176cbf97df342fc']: _withCtx(() => [
        _renderSlot(_ctx.$slots, "citrySlot4a45b3d88f07d9ae")
      ]),
      _: 3 /* FORWARDED */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b24ddf369a561797fe3d836b04319705e11ccc2ed7e18f7d8c0e23bc6d8294a5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9ee6b0021ed574b1","typeKey":"CInternalMenuSurface_597468","componentTag":"citry-c-internal-menu-surface-37f82339","bindings":[],"fills":[{"name":"citrySlot5176cbf97df342fc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":["citrySlot4a45b3d88f07d9ae"]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_menu_submenu_c9e45699 = _resolveComponent("citry-c-menu-submenu-c9e45699")
  const _component_citry_c_menu_0bdb31ef = _resolveComponent("citry-c-menu-0bdb31ef")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "archive-placement-demo",
    dir: _ctx.rtl ? 'rtl' : 'ltr'
  }, [
    (_openBlock(), _createBlock(_component_citry_c_menu_0bdb31ef, _mergeProps({placement: _ctx.placement, matchWidth: _ctx.match}, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2703a80cb9af8f2e.id,
      key: _ctx.$citryPrepared.calls.citryCall2703a80cb9af8f2e.key
    }), {
      ['citrySlote9035851c53b236c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall43a7960b9a5045b7.id,
          key: _ctx.$citryPrepared.calls.citryCall43a7960b9a5045b7.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode(" A deliberately wide enchanted-volume trigger ")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot4a45b3d88f07d9ae']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall6137da9cbd52d284.id,
          key: _ctx.$citryPrepared.calls.citryCall6137da9cbd52d284.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Northern shelf")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall32a0170790d14f6c.id,
          key: _ctx.$citryPrepared.calls.citryCall32a0170790d14f6c.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Southern shelf")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_submenu_c9e45699, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallf7dffccc821280e7.id,
          key: _ctx.$citryPrepared.calls.citryCallf7dffccc821280e7.key
        }, {
          ['citrySlot5edbca3669e97392']: _withCtx(() => [
            _createTextVNode("Hidden wing")
          ]),
          ['citrySlot6bda043c1d90fe5c']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall092e8ad494a1dc49.id,
              key: _ctx.$citryPrepared.calls.citryCall092e8ad494a1dc49.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode("Hall of mirrors")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ], 8 /* PROPS */, ["dir"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["31b7aa845113d7cfdf9559077209ebafa4b8b515c02a1ced0b7ddb1b9f8d264b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall43a7960b9a5045b7","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6137da9cbd52d284","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall32a0170790d14f6c","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall092e8ad494a1dc49","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf7dffccc821280e7","typeKey":"CMenuSubmenu_cba41f","componentTag":"citry-c-menu-submenu-c9e45699","bindings":[],"fills":[{"name":"citrySlot5edbca3669e97392","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6bda043c1d90fe5c","localDescendants":["citryCall092e8ad494a1dc49"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2703a80cb9af8f2e","typeKey":"CMenu_4350e4","componentTag":"citry-c-menu-0bdb31ef","bindings":[{"kind":"props-object","name":"v-bind","value":"{placement, matchWidth: match}","sourceStart":94,"sourceEnd":133}],"fills":[{"name":"citrySlot4a45b3d88f07d9ae","localDescendants":["citryCall092e8ad494a1dc49","citryCall32a0170790d14f6c","citryCall6137da9cbd52d284","citryCallf7dffccc821280e7"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote9035851c53b236c","localDescendants":["citryCall43a7960b9a5045b7"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_menu_placement_e72d3815 = _resolveComponent("citry-menu-placement-e72d3815")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_menu_placement_e72d3815, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb4d47a918aede8a7.id,
      key: _ctx.$citryPrepared.calls.citryCallb4d47a918aede8a7.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["44b63fba5fada0b19f05b1f09fbe63271b963c1a85c27fedd2bc9d714e084fbb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb4d47a918aede8a7","typeKey":"MenuPlacement_ded567","componentTag":"citry-menu-placement-e72d3815","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
