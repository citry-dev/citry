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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-popover-host",
    "data-citry-popover-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot371618f8b14ff656'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot371618f8b14ff656", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("div", _mergeProps({
      class: "cui-popover",
      popover: "manual",
      role: "dialog",
      tabindex: "-1",
      "data-citry-ui-part": "popover"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("header", {
        class: "cui-popover__header",
        "data-citry-ui-part": "header"
      }, [
        _createElementVNode("h2", _mergeProps({
          class: "cui-popover__title",
          "data-citry-ui-part": "title"
        }, _ctx.$citryPrepared.citryAttrs1), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot6797d7221c481487'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot6797d7221c481487", { key: 1 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */)
      ]),
      _createElementVNode("div", {
        class: "cui-popover__body",
        "data-citry-ui-part": "body"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot324bf05fa215c365'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot324bf05fa215c365", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2b649a5f47d1d9e8e1b8f057ac12e41dfe825104ddb7610df5fe7acaa7676ffe"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_menu_submenu_c9e45699 = _resolveComponent("citry-c-menu-submenu-c9e45699")
  const _component_citry_c_menu_0bdb31ef = _resolveComponent("citry-c-menu-0bdb31ef")
  const _component_citry_c_popover_e1fe086e = _resolveComponent("citry-c-popover-e1fe086e")
  
  return (_openBlock(), _createElementBlock("section", { class: "archive-lifecycle-demo" }, [
    (_openBlock(), _createBlock(_component_citry_c_popover_e1fe086e, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallbae1912a794448cb.id,
      key: _ctx.$citryPrepared.calls.citryCallbae1912a794448cb.key
    }, {
      ['citrySlot371618f8b14ff656']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld649fba97ed7e42f.id,
          key: _ctx.$citryPrepared.calls.citryCalld649fba97ed7e42f.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Open reading room")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot6797d7221c481487']: _withCtx(() => [
        _createTextVNode("Reading room")
      ]),
      ['citrySlot324bf05fa215c365']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_0bdb31ef, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallc564bb8a1f5c7e80.id,
          key: _ctx.$citryPrepared.calls.citryCallc564bb8a1f5c7e80.key
        }, {
          ['citrySlote9035851c53b236c']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall3f113d01e69b9e02.id,
              key: _ctx.$citryPrepared.calls.citryCall3f113d01e69b9e02.key
            }, {
              ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                _createTextVNode("Nested folio menu")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          ['citrySlot4a45b3d88f07d9ae']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall1a056786c06f24ce.id,
              key: _ctx.$citryPrepared.calls.citryCall1a056786c06f24ce.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode("Inspect binding")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
            (_openBlock(), _createBlock(_component_citry_c_menu_submenu_c9e45699, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallc410997707110e3e.id,
              key: _ctx.$citryPrepared.calls.citryCallc410997707110e3e.key
            }, {
              ['citrySlot5edbca3669e97392']: _withCtx(() => [
                _createTextVNode("Other editions")
              ]),
              ['citrySlot6bda043c1d90fe5c']: _withCtx(() => [
                (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
                  "citry-id": _ctx.$citryPrepared.calls.citryCalld13d66d741b01591.id,
                  key: _ctx.$citryPrepared.calls.citryCalld13d66d741b01591.key
                }, {
                  ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                    _createTextVNode("First edition")
                  ]),
                  _: 2 /* DYNAMIC */
                }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
      onClick: $event => (_ctx.$refs.vault.showModal()),
      "citry-id": _ctx.$citryPrepared.calls.citryCall6de6d627f783cacc.id,
      key: _ctx.$citryPrepared.calls.citryCall6de6d627f783cacc.key
    }, {
      ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
        _createTextVNode("Open modal vault")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"])),
    _createElementVNode("dialog", {
      ref: "vault",
      "aria-labelledby": "vault-title"
    }, [
      _createElementVNode("h2", { id: "vault-title" }, "Royal vault"),
      _createElementVNode("p", null, "Opening this modal closes unrelated anchored layers."),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$refs.vault.close())
      }, "Close vault", 8 /* PROPS */, ["onClick"])
    ], 512 /* NEED_PATCH */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["7d55516e0b7fc6ac33def0094e490380392538c370a783808a9d6cce39d05fd9"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld649fba97ed7e42f","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall3f113d01e69b9e02","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1a056786c06f24ce","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld13d66d741b01591","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc410997707110e3e","typeKey":"CMenuSubmenu_cba41f","componentTag":"citry-c-menu-submenu-c9e45699","bindings":[],"fills":[{"name":"citrySlot5edbca3669e97392","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6bda043c1d90fe5c","localDescendants":["citryCalld13d66d741b01591"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc564bb8a1f5c7e80","typeKey":"CMenu_4350e4","componentTag":"citry-c-menu-0bdb31ef","bindings":[],"fills":[{"name":"citrySlot4a45b3d88f07d9ae","localDescendants":["citryCall1a056786c06f24ce","citryCallc410997707110e3e","citryCalld13d66d741b01591"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote9035851c53b236c","localDescendants":["citryCall3f113d01e69b9e02"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallbae1912a794448cb","typeKey":"CPopover_d4bf44","componentTag":"citry-c-popover-e1fe086e","bindings":[],"fills":[{"name":"citrySlot324bf05fa215c365","localDescendants":["citryCall1a056786c06f24ce","citryCall3f113d01e69b9e02","citryCallc410997707110e3e","citryCallc564bb8a1f5c7e80","citryCalld13d66d741b01591"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot371618f8b14ff656","localDescendants":["citryCalld649fba97ed7e42f"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6797d7221c481487","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6de6d627f783cacc","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"$refs.vault.showModal()","sourceStart":2120,"sourceEnd":2152}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_menu_lifecycle_0c86243c = _resolveComponent("citry-menu-lifecycle-0c86243c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_menu_lifecycle_0c86243c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall08ae4e59d9018871.id,
      key: _ctx.$citryPrepared.calls.citryCall08ae4e59d9018871.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6fe6c9790a5082ec056e875ba37a07ca8a9747961287c25742a48f8149189cd8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall08ae4e59d9018871","typeKey":"MenuLifecycle_0685f1","componentTag":"citry-menu-lifecycle-0c86243c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
