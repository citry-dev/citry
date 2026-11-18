(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

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
    }, [
      _createElementVNode("div", _mergeProps({
        class: "cui-toast",
        role: "group",
        tabindex: "0",
        "data-citry-ui-part": "toast"
      }, _ctx.$citryPrepared.citryAttrs1), [
        _createElementVNode("div", {
          class: "cui-toast__content",
          "data-citry-ui-part": "content"
        }, [
          _createElementVNode("div", _mergeProps({
            class: "cui-toast__title",
            "data-citry-ui-part": "title"
          }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */)
        ]),
        _createElementVNode("div", {
          class: "cui-toast__actions",
          "data-citry-ui-part": "actions"
        }, [
          _createElementVNode("button", _mergeProps({
            type: "button",
            "data-citry-toast-dismiss": "",
            "data-citry-ui-part": "dismiss"
          }, _ctx.$citryPrepared.citryAttrs3), "×", 16 /* FULL_PROPS */)
        ])
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6d43f4dcb7e2b11e96876f241bb2d663d891c276f981a3e3b99aeb3643c73845"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_toast_region_5c499f86 = _resolveComponent("citry-c-toast-region-5c499f86")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "toast-example",
    dir: "rtl"
  }, [
    _createElementVNode("p", null, "Logical start follows this RTL context."),
    (_openBlock(), _createBlock(_component_citry_c_toast_region_5c499f86, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2abd54e8b229ef25.id,
      key: _ctx.$citryPrepared.calls.citryCall2abd54e8b229ef25.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2a8779824232ae2bb3007dddb45982aa1ef2b8cf32df7da59254e54868ae0623"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2abd54e8b229ef25","typeKey":"CToastRegion_eec238","componentTag":"citry-c-toast-region-5c499f86","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_toast_placement_rtl_0e3911fe = _resolveComponent("citry-toast-placement-rtl-0e3911fe")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_toast_placement_rtl_0e3911fe, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9db3c789327de25d.id,
      key: _ctx.$citryPrepared.calls.citryCall9db3c789327de25d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["9cdb4cc4425e44c09a6d927efff6a20a75bfc96f0aee06dd8658eea6e9fb5a19"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9db3c789327de25d","typeKey":"ToastPlacementRtl_6452a4","componentTag":"citry-toast-placement-rtl-0e3911fe","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
