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
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-tooltip-host",
    "data-citry-tooltip-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot9eed2bc76871905f'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot9eed2bc76871905f", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("div", _mergeProps({
      class: "cui-tooltip",
      popover: "manual",
      role: "tooltip",
      "data-citry-ui-part": "tooltip"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("span", { "data-citry-tooltip-text": "" }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["98b53731948d787aad75d53a8547991901dc00b496aeb5d8835556954527329b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

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
window.__citryRuntimeDefinitions["a48e3f2bfcc515069ea5480852e504394bf691e76942f4e85a33e5c5a7ad2484"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"a","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"a","sourceStart":1,"sourceEnd":69}]));

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
    class: "cui-dialog-host",
    "data-citry-dialog-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot01f533d219338d4d'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot01f533d219338d4d", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("dialog", _mergeProps({
      class: "cui-dialog",
      "data-citry-dialog-surface": "",
      "aria-modal": "true",
      "data-citry-ui-part": "dialog"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("div", {
        class: "cui-dialog__surface",
        "data-citry-ui-part": "surface"
      }, [
        _createElementVNode("header", {
          class: "cui-dialog__header",
          "data-citry-ui-part": "header"
        }, [
          _createElementVNode("h2", _mergeProps({
            class: "cui-dialog__title",
            "data-citry-ui-part": "title"
          }, _ctx.$citryPrepared.citryAttrs1), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot81c7ca490fc15941'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot81c7ca490fc15941", { key: 1 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("button", _mergeProps({
            class: "cui-dialog__close",
            type: "button",
            "data-citry-dialog-close": "",
            "data-citry-dialog-built-in-close": "",
            "data-citry-ui-part": "close"
          }, _ctx.$citryPrepared.citryAttrs2), [
            _createElementVNode("span", { "aria-hidden": "true" }, " × ")
          ], 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("div", {
          class: "cui-dialog__body",
          "data-citry-ui-part": "body"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlotc18de8dd8e2a7fea'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlotc18de8dd8e2a7fea", { key: 2 })
            : _createCommentVNode("v-if", true)
        ]),
        _createElementVNode("footer", {
          class: "cui-dialog__actions",
          "data-citry-ui-part": "actions"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot02ca7b57762cc54c'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot02ca7b57762cc54c", { key: 3 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["4917a1777defc4c41d54d1426b4600df0627e869f4c2c86ce4fc315e4f719ed1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createTextVNode: _createTextVNode, createCommentVNode: _createCommentVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_context_menu_c149a668 = _resolveComponent("citry-c-context-menu-c149a668")
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_popover_e1fe086e = _resolveComponent("citry-c-popover-e1fe086e")
  const _component_citry_c_tooltip_e48e5021 = _resolveComponent("citry-c-tooltip-e48e5021")
  const _component_citry_c_menu_0bdb31ef = _resolveComponent("citry-c-menu-0bdb31ef")
  const _component_citry_c_dialog_eece56dc = _resolveComponent("citry-c-dialog-eece56dc")
  
  return (_openBlock(), _createElementBlock("section", { class: "context-menu-layers" }, [
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Deepest target wins"),
      (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({
        onOpenChange:(next,detail)=>_ctx.last=
          `outer ${next ? 'open' : 'close'} ${detail.reason}`,
      }, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall40d4d42040e79e39.id,
        key: _ctx.$citryPrepared.calls.citryCall40d4d42040e79e39.key
      }), {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-layers__outer",
            tabindex: "0"
          }, _ctx.$citryPrepared.citryAttrs0), [
            _createTextVNode(" Outer card "),
            (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({
              onOpenChange:(next,detail)=>_ctx.last=
                `inner ${next ? 'open' : 'close'} ${detail.reason}`,
            }, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallf1e7b53a6e065ae9.id,
              key: _ctx.$citryPrepared.calls.citryCallf1e7b53a6e065ae9.key
            }), {
              ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
                _createElementVNode("span", _mergeProps({
                  class: "context-menu-layers__inner",
                  tabindex: "0"
                }, _ctx.$citryPrepared.citryAttrs1), "Inner badge", 16 /* FULL_PROPS */)
              ]),
              ['citrySlot0021c864d3777155']: _withCtx(() => [
                (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
                  "citry-id": _ctx.$citryPrepared.calls.citryCalle2765267567116e2.id,
                  key: _ctx.$citryPrepared.calls.citryCalle2765267567116e2.key
                }, {
                  ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                    _createTextVNode("Inspect badge")
                  ]),
                  _: 2 /* DYNAMIC */
                }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
              ]),
              _: 2 /* DYNAMIC */
            }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ], 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall5c5c8e237622750e.id,
            key: _ctx.$citryPrepared.calls.citryCall5c5c8e237622750e.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect card")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Inside another anchored layer"),
      (_openBlock(), _createBlock(_component_citry_c_popover_e1fe086e, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall4df3cec02236dcde.id,
        key: _ctx.$citryPrepared.calls.citryCall4df3cec02236dcde.key
      }, {
        ['citrySlot371618f8b14ff656']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall1d48bc4bb305d296.id,
            key: _ctx.$citryPrepared.calls.citryCall1d48bc4bb305d296.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode("Open inspector")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        ['citrySlot6797d7221c481487']: _withCtx(() => [
          _createTextVNode("Record inspector")
        ]),
        ['citrySlot324bf05fa215c365']: _withCtx(() => [
          (!_ctx.nestedRemoved)
            ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
              (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, {
                "citry-id": _ctx.$citryPrepared.calls.citryCalld6e8e9090f48e161.id,
                key: _ctx.$citryPrepared.calls.citryCalld6e8e9090f48e161.key
              }, {
                ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
                  _createElementVNode("div", _mergeProps({
                    class: "context-menu-layers__popover-target",
                    tabindex: "0"
                  }, _ctx.$citryPrepared.citryAttrs2), "Row inside Popover", 16 /* FULL_PROPS */)
                ]),
                ['citrySlot0021c864d3777155']: _withCtx(() => [
                  (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
                    "citry-id": _ctx.$citryPrepared.calls.citryCall4d05a2d9c05daaa3.id,
                    key: _ctx.$citryPrepared.calls.citryCall4d05a2d9c05daaa3.key
                  }, {
                    ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                      _createTextVNode("Open row")
                    ]),
                    _: 2 /* DYNAMIC */
                  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
                  (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
                    "citry-id": _ctx.$citryPrepared.calls.citryCall61523dceeafe1319.id,
                    key: _ctx.$citryPrepared.calls.citryCall61523dceeafe1319.key
                  }, {
                    ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                      _createTextVNode("Archive row")
                    ]),
                    _: 2 /* DYNAMIC */
                  }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
                ]),
                _: 2 /* DYNAMIC */
              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
            ], 64 /* STABLE_FRAGMENT */))
            : _createCommentVNode("v-if", true)
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {_ctx.nestedRemoved=true; _ctx.last='nested ContextMenu removed'}
      }, "Remove nested ContextMenu", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.nestedRemoved=false)
      }, " Restore the fixture, then repeat the cycle ", 8 /* PROPS */, ["onClick"]),
      (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall1639ab2d831a9a56.id,
        key: _ctx.$citryPrepared.calls.citryCall1639ab2d831a9a56.key
      }, {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({ class: "context-menu-layers__popover-target" }, _ctx.$citryPrepared.citryAttrs3), [
            (_openBlock(), _createBlock(_component_citry_c_tooltip_e48e5021, {
              "citry-id": _ctx.$citryPrepared.calls.citryCalle40200f9c7fc84f6.id,
              key: _ctx.$citryPrepared.calls.citryCalle40200f9c7fc84f6.key
            }, {
              ['citrySlot9eed2bc76871905f']: _withCtx(() => [
                (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
                  "citry-id": _ctx.$citryPrepared.calls.citryCall37e56b0c0cc2d68e.id,
                  key: _ctx.$citryPrepared.calls.citryCall37e56b0c0cc2d68e.key
                }, {
                  ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
                    _createTextVNode("Tooltip-bound target")
                  ]),
                  _: 2 /* DYNAMIC */
                }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ], 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall42013326b15b5a06.id,
            key: _ctx.$citryPrepared.calls.citryCall42013326b15b5a06.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode(" Inspect Tooltip target ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_menu_0bdb31ef, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallc9354f6f0118475e.id,
        key: _ctx.$citryPrepared.calls.citryCallc9354f6f0118475e.key
      }, {
        ['citrySlote9035851c53b236c']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall9561de65d98ad79e.id,
            key: _ctx.$citryPrepared.calls.citryCall9561de65d98ad79e.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Open sibling Menu ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        ['citrySlot4a45b3d88f07d9ae']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalld3365518c54f286f.id,
            key: _ctx.$citryPrepared.calls.citryCalld3365518c54f286f.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode(" Ordinary Menu command ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall736361977e2f8f15.id,
            key: _ctx.$citryPrepared.calls.citryCall736361977e2f8f15.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode(" Native link in Menu ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("p", { id: "context-menu-menu-native-link" }, " Right click inside the open Menu to keep the browser path rather than reinvoking ContextMenu. ")
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Open ShadowRoot scope"),
      _createElementVNode("div", { ref: "shadowFixture" }, [
        (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall7a7e736ed0445a88.id,
          key: _ctx.$citryPrepared.calls.citryCall7a7e736ed0445a88.key
        }, {
          ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
            _createElementVNode("button", _mergeProps({
              class: "context-menu-layers__shadow-target",
              type: "button"
            }, _ctx.$citryPrepared.citryAttrs4), "ShadowRoot target", 16 /* FULL_PROPS */)
          ]),
          ['citrySlot0021c864d3777155']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall768dc98b3ce7e745.id,
              key: _ctx.$citryPrepared.calls.citryCall768dc98b3ce7e745.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode("Inspect shadow record")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ], 512 /* NEED_PATCH */),
      _createElementVNode("div", {
        ref: "shadowHost",
        "data-context-menu-shadow-host": ""
      }, null, 512 /* NEED_PATCH */)
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Later modal owns the top layer"),
      (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall34196efc583a3a2c.id,
        key: _ctx.$citryPrepared.calls.citryCall34196efc583a3a2c.key
      }, {
        ['citrySlot01f533d219338d4d']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallc7908b0c638483ad.id,
            key: _ctx.$citryPrepared.calls.citryCallc7908b0c638483ad.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Open sibling Dialog ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        ['citrySlot81c7ca490fc15941']: _withCtx(() => [
          _createTextVNode("Layer review")
        ]),
        ['citrySlotc18de8dd8e2a7fea']: _withCtx(() => [
          _createTextVNode(" A later modal outside a ContextMenu ancestry force-closes it. ")
        ]),
        ['citrySlot02ca7b57762cc54c']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall4360b4f5d0e5b0cc.id,
            key: _ctx.$citryPrepared.calls.citryCall4360b4f5d0e5b0cc.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode("Close review")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("iframe", {
        title: "Separate document context boundary",
        srcdoc: "<p>A child document needs its own Citry instance.</p>"
      })
    ]),
    _createElementVNode("div", { class: "context-menu-layers__diagnostics" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.counterTick += 1)
      }, " Refresh layer counters ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("output", {
        "aria-live": "polite",
        textContent: _toDisplayString(_ctx.layerSummary(_ctx.counterTick))
      }, "No layer request yet; layers 0; registrations 0", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["890e9c4df50cb774605e911fec77c245613cb9f64a23a58c0edbe11ce635043b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle2765267567116e2","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf1e7b53a6e065ae9","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n              onOpenChange:(next,detail)=>last=\n                `inner ${next ? 'open' : 'close'} ${detail.reason}`,\n            }","sourceStart":571,"sourceEnd":712}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCalle2765267567116e2"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall5c5c8e237622750e","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall40d4d42040e79e39","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n        onOpenChange:(next,detail)=>last=\n          `outer ${next ? 'open' : 'close'} ${detail.reason}`,\n      }","sourceStart":119,"sourceEnd":242}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall5c5c8e237622750e"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":["citryCalle2765267567116e2","citryCallf1e7b53a6e065ae9"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1d48bc4bb305d296","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4d05a2d9c05daaa3","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall61523dceeafe1319","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld6e8e9090f48e161","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall4d05a2d9c05daaa3","citryCall61523dceeafe1319"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4df3cec02236dcde","typeKey":"CPopover_d4bf44","componentTag":"citry-c-popover-e1fe086e","bindings":[],"fills":[{"name":"citrySlot324bf05fa215c365","localDescendants":["citryCall4d05a2d9c05daaa3","citryCall61523dceeafe1319","citryCalld6e8e9090f48e161"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot371618f8b14ff656","localDescendants":["citryCall1d48bc4bb305d296"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6797d7221c481487","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall37e56b0c0cc2d68e","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle40200f9c7fc84f6","typeKey":"CTooltip_ebd738","componentTag":"citry-c-tooltip-e48e5021","bindings":[],"fills":[{"name":"citrySlot9eed2bc76871905f","localDescendants":["citryCall37e56b0c0cc2d68e"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall42013326b15b5a06","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1639ab2d831a9a56","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall42013326b15b5a06"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":["citryCall37e56b0c0cc2d68e","citryCalle40200f9c7fc84f6"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9561de65d98ad79e","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld3365518c54f286f","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall736361977e2f8f15","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc9354f6f0118475e","typeKey":"CMenu_4350e4","componentTag":"citry-c-menu-0bdb31ef","bindings":[],"fills":[{"name":"citrySlot4a45b3d88f07d9ae","localDescendants":["citryCall736361977e2f8f15","citryCalld3365518c54f286f"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote9035851c53b236c","localDescendants":["citryCall9561de65d98ad79e"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall768dc98b3ce7e745","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7a7e736ed0445a88","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall768dc98b3ce7e745"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc7908b0c638483ad","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4360b4f5d0e5b0cc","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall34196efc583a3a2c","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot01f533d219338d4d","localDescendants":["citryCallc7908b0c638483ad"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot02ca7b57762cc54c","localDescendants":["citryCall4360b4f5d0e5b0cc"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot81c7ca490fc15941","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc18de8dd8e2a7fea","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_context_menu_layers_and_roots_947e6d48 = _resolveComponent("citry-context-menu-layers-and-roots-947e6d48")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_context_menu_layers_and_roots_947e6d48, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld8c38b17b77b6f60.id,
      key: _ctx.$citryPrepared.calls.citryCalld8c38b17b77b6f60.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["b87792a4715127d693899b8088bfdcd184be9e6f4dae725a501a37d2f18e34d4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld8c38b17b77b6f60","typeKey":"ContextMenuLayersAndRoots_852f65","componentTag":"citry-context-menu-layers-and-roots-947e6d48","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
