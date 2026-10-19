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
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-alert",
    "data-citry-ui-part": "alert"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_openBlock(), _createElementBlock("div", {
      class: "cui-alert__indicator",
      "aria-hidden": "true",
      "data-citry-ui-part": "indicator"
    }, [
      (_openBlock(), _createElementBlock("svg", {
        class: "cui-alert__icon",
        xmlns: "http://www.w3.org/2000/svg",
        viewBox: "0 0 24 24",
        fill: "none",
        stroke: "currentColor",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        focusable: "false",
        "aria-hidden": "true"
      }, [
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs1)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "M12 16v-4" }),
          _createElementVNode("path", { d: "M12 8h.01" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs2)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "m9 12 2 2 4-4" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs3)), [
          _createElementVNode("path", { d: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" }),
          _createElementVNode("path", { d: "M12 9v4" }),
          _createElementVNode("path", { d: "M12 17h.01" })
        ], 16 /* FULL_PROPS */),
        _createElementVNode("g", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs4)), [
          _createElementVNode("circle", {
            cx: "12",
            cy: "12",
            r: "10"
          }),
          _createElementVNode("path", { d: "m15 9-6 6" }),
          _createElementVNode("path", { d: "m9 9 6 6" })
        ], 16 /* FULL_PROPS */)
      ]))
    ])),
    _createElementVNode("div", {
      class: "cui-alert__content",
      "data-citry-ui-part": "content"
    }, [
      _createElementVNode("div", {
        class: "cui-alert__message",
        "data-citry-ui-part": "message"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlotc35871f9572748e0'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlotc35871f9572748e0", { key: 0 })
          : _createCommentVNode("v-if", true)
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["cfd1cee44a47ed0d1489a52019304f00209819201262aef64a76d01588e18535"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-dialog-host",
    "data-citry-dialog-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot39e9540beec747a3'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot39e9540beec747a3", { key: 0 })
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
            (_ctx.$citryPrepared.selectedSlots['citrySlot52f4d122daf10cdd'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot52f4d122daf10cdd", { key: 1 })
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
          (_ctx.$citryPrepared.selectedSlots['citrySlot4c119cf029159074'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot4c119cf029159074", { key: 2 })
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8c0878bf9747556de54b1f24281346a3e9c755093ba4ac00b0b293e786f7f1d2"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("section", _mergeProps({
    ref: "root",
    class: "cui-toast-region",
    role: "region",
    tabindex: "-1",
    "data-citry-ui-part": "region"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-toast-region__announcer",
      "aria-live": "polite",
      "aria-atomic": "true",
      "data-citry-ui-part": "announcer-polite"
    }),
    _createElementVNode("div", {
      class: "cui-toast-region__announcer",
      "aria-live": "assertive",
      "aria-atomic": "true",
      "data-citry-ui-part": "announcer-assertive"
    }),
    _createElementVNode("div", {
      class: "cui-toast-region__list",
      "data-citry-toast-list": ""
    })
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["eb20e67cdd6be68963f5ca2b31469fede0919246d1738547ee7ef5db1abff427"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_alert_b3af2726 = _resolveComponent("citry-c-alert-b3af2726")
  const _component_citry_c_dialog_eece56dc = _resolveComponent("citry-c-dialog-eece56dc")
  const _component_citry_c_toast_region_5c499f86 = _resolveComponent("citry-c-toast-region-5c499f86")
  
  return (_openBlock(), _createElementBlock("section", { class: "toast-example" }, [
    (_openBlock(), _createBlock(_component_citry_c_dialog_eece56dc, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6c0ca9feec81a96e.id,
      key: _ctx.$citryPrepared.calls.citryCall6c0ca9feec81a96e.key
    }, {
      ['citrySlot39e9540beec747a3']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall6fdd186015bd0429.id,
          key: _ctx.$citryPrepared.calls.citryCall6fdd186015bd0429.key
        }, {
          ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
            _createTextVNode("Open modal task")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      ['citrySlot52f4d122daf10cdd']: _withCtx(() => [
        _createTextVNode("Modal-local feedback")
      ]),
      ['citrySlot4c119cf029159074']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_alert_b3af2726, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallbb9ea579da10b535.id,
          key: _ctx.$citryPrepared.calls.citryCallbb9ea579da10b535.key
        }, {
          ['citrySlotc35871f9572748e0']: _withCtx(() => [
            _createTextVNode("Use Alert for immediate feedback inside this task.")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    (_openBlock(), _createBlock(_component_citry_c_toast_region_5c499f86, {
      items: _ctx.items,
      "citry-id": _ctx.$citryPrepared.calls.citryCall8439b79a75b703a9.id,
      key: _ctx.$citryPrepared.calls.citryCall8439b79a75b703a9.key
    }, null, 8 /* PROPS */, ["items", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["b0781547dcc29ec427c46845f248a0ff0c0f83233dc246f9629b9ac3fdefd4f5"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6fdd186015bd0429","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallbb9ea579da10b535","typeKey":"CAlert_0cc501","componentTag":"citry-c-alert-b3af2726","bindings":[],"fills":[{"name":"citrySlotc35871f9572748e0","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6c0ca9feec81a96e","typeKey":"CDialog_e133eb","componentTag":"citry-c-dialog-eece56dc","bindings":[],"fills":[{"name":"citrySlot39e9540beec747a3","localDescendants":["citryCall6fdd186015bd0429"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot4c119cf029159074","localDescendants":["citryCallbb9ea579da10b535"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot52f4d122daf10cdd","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8439b79a75b703a9","typeKey":"CToastRegion_eec238","componentTag":"citry-c-toast-region-5c499f86","bindings":[{"kind":"prop","name":":items","value":"items","sourceStart":979,"sourceEnd":993}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_toast_modal_pause_2fde4840 = _resolveComponent("citry-toast-modal-pause-2fde4840")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_toast_modal_pause_2fde4840, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall4ed050f81db56147.id,
      key: _ctx.$citryPrepared.calls.citryCall4ed050f81db56147.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8dfda301e8a9e278ddb6ac463c8e5afafa6cf4ccce75641b6aeb2c8fa0d4ab22"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4ed050f81db56147","typeKey":"ToastModalPause_347bd0","componentTag":"citry-toast-modal-pause-2fde4840","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
