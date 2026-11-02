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
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("svg", _mergeProps({
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    focusable: "false",
    "data-citry-ui-part": "icon"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("g", { class: "cui-icon__glyph" }, [
      _createElementVNode("path", { d: "m21 21-4.34-4.34" }),
      _createElementVNode("circle", {
        cx: "11",
        cy: "11",
        r: "8"
      })
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["5dfbb0567308f43d9ddca8015548271d40ea293ae577a92091781058d192fe5d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-361caf6ce22af4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", {
      class: "cui-menu__item-start",
      "aria-hidden": "true",
      "data-citry-ui-part": "menu-item-start"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot445c6c6a0da32c02'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot445c6c6a0da32c02", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("span", { class: "cui-menu__item-copy" }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-label",
        "data-citry-ui-part": "menu-item-label"
      }, _ctx.$citryPrepared.citryAttrs1), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot1914d19b2433c73f'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot1914d19b2433c73f", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-description",
        "data-citry-ui-part": "menu-item-description"
      }, _ctx.$citryPrepared.citryAttrs2), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot78539127ef118382'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot78539127ef118382", { key: 2 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("span", {
      class: "cui-menu__item-end",
      "aria-hidden": "true",
      "data-citry-ui-part": "menu-item-end"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlotc69fa79170a59085'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotc69fa79170a59085", { key: 3 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["21cfaa195e2989b0325cf004f23c4ee7ca16696c7d6617fcce421f60e23b2b21"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("svg", _mergeProps({
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    focusable: "false",
    "data-citry-ui-part": "icon"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("g", { class: "cui-icon__glyph" }, [
      _createElementVNode("path", { d: "M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z" })
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["8ce3bed2916f5f31eae1c9370ce8ec4346d910f387bbc0c83986ee96b3549f65"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-361caf6ce22af4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", {
      class: "cui-menu__item-start",
      "aria-hidden": "true",
      "data-citry-ui-part": "menu-item-start"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot445c6c6a0da32c02'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot445c6c6a0da32c02", { key: 0 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("span", { class: "cui-menu__item-copy" }, [
      _createElementVNode("span", _mergeProps({
        class: "cui-menu__item-label",
        "data-citry-ui-part": "menu-item-label"
      }, _ctx.$citryPrepared.citryAttrs1), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot1914d19b2433c73f'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot1914d19b2433c73f", { key: 1 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("span", {
      class: "cui-menu__item-end",
      "aria-hidden": "true",
      "data-citry-ui-part": "menu-item-end"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlotc69fa79170a59085'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotc69fa79170a59085", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["bec459613665150c46e902e5ad2e10693950229a22b12c90d6ee326c43ac53eb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_icon_f8b347d7 = _resolveComponent("citry-c-icon-f8b347d7")
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_menu_0bdb31ef = _resolveComponent("citry-c-menu-0bdb31ef")
  
  return (_openBlock(), _createElementBlock("section", { class: "archive-content-demo" }, [
    (_openBlock(), _createBlock(_component_citry_c_menu_0bdb31ef, _mergeProps({
      onAction: (value) => _ctx.lastAction = value,
    }, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5317925bd7b10d6f.id,
      key: _ctx.$citryPrepared.calls.citryCall5317925bd7b10d6f.key
    }), {
      ['citrySlote9035851c53b236c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall1d115d5c9f148ed6.id,
          key: _ctx.$citryPrepared.calls.citryCall1d115d5c9f148ed6.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Catalog tools")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot4a45b3d88f07d9ae']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall76ebcc0727e1f074.id,
          key: _ctx.$citryPrepared.calls.citryCall76ebcc0727e1f074.key
        }, {
          ['citrySlot445c6c6a0da32c02']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_icon_f8b347d7, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallc785c0072ac0d159.id,
              key: _ctx.$citryPrepared.calls.citryCallc785c0072ac0d159.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ]),
          ['citrySlot1914d19b2433c73f']: _withCtx(() => [
            _createTextVNode("Search illuminated texts")
          ]),
          ['citrySlot78539127ef118382']: _withCtx(() => [
            _createTextVNode("Find titles, scribes, and sigils.")
          ]),
          ['citrySlotc69fa79170a59085']: _withCtx(() => [
            _createElementVNode("kbd", null, "Alt Shift F")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall4305af9479d5af16.id,
          key: _ctx.$citryPrepared.calls.citryCall4305af9479d5af16.key
        }, {
          ['citrySlot445c6c6a0da32c02']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_icon_f8b347d7, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall49bf0ff1bc741fc5.id,
              key: _ctx.$citryPrepared.calls.citryCall49bf0ff1bc741fc5.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ]),
          ['citrySlot1914d19b2433c73f']: _withCtx(() => [
            _createTextVNode("Mark this passage")
          ]),
          ['citrySlotc69fa79170a59085']: _withCtx(() => [
            _createElementVNode("kbd", null, "Alt Shift P")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("output", {
      textContent: _toDisplayString(`Last command: ${_ctx.lastAction}`)
    }, "Last command: none", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["39f91d1c8c7cd6ee966b789395e3875288cd12bb78bd4e6e8976bec4fde32982"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1d115d5c9f148ed6","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc785c0072ac0d159","typeKey":"CIcon_8e5345","componentTag":"citry-c-icon-f8b347d7","bindings":[]},{"localId":"citryCall76ebcc0727e1f074","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlot1914d19b2433c73f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot445c6c6a0da32c02","localDescendants":["citryCallc785c0072ac0d159"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot78539127ef118382","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc69fa79170a59085","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall49bf0ff1bc741fc5","typeKey":"CIcon_8e5345","componentTag":"citry-c-icon-f8b347d7","bindings":[]},{"localId":"citryCall4305af9479d5af16","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlot1914d19b2433c73f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot445c6c6a0da32c02","localDescendants":["citryCall49bf0ff1bc741fc5"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc69fa79170a59085","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall5317925bd7b10d6f","typeKey":"CMenu_4350e4","componentTag":"citry-c-menu-0bdb31ef","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n      onAction: (value) => lastAction = value,\n    }","sourceStart":65,"sourceEnd":128}],"fills":[{"name":"citrySlot4a45b3d88f07d9ae","localDescendants":["citryCall4305af9479d5af16","citryCall49bf0ff1bc741fc5","citryCall76ebcc0727e1f074","citryCallc785c0072ac0d159"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote9035851c53b236c","localDescendants":["citryCall1d115d5c9f148ed6"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_menu_item_content_f374001a = _resolveComponent("citry-menu-item-content-f374001a")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_menu_item_content_f374001a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb13db51e0f694599.id,
      key: _ctx.$citryPrepared.calls.citryCallb13db51e0f694599.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["87f2a10a239304ef503235e79e31b975214d31c617a2bfc5ab2a22f57767da55"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb13db51e0f694599","typeKey":"MenuItemContent_ccd3ff","componentTag":"citry-menu-item-content-f374001a","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
