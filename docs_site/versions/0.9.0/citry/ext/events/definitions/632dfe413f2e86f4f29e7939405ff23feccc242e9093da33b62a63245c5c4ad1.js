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
window.__citryRuntimeDefinitions["cf522a59f294773e98e6c0366748ccdea828c64ea58545496ee9ed3af1eb769c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2abd54e8b229ef25","typeKey":"CToastRegion_eec238","componentTag":"citry-c-toast-region-5c499f86","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_toast_placement_rtl_64ba5f34 = _resolveComponent("citry-toast-placement-rtl-64ba5f34")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_toast_placement_rtl_64ba5f34, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle9baf115eddd83ba.id,
      key: _ctx.$citryPrepared.calls.citryCalle9baf115eddd83ba.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["02cfd28f4880aa8e1a6c95963a72956cd6c5ab3a856666e12e15dec7eeb63c4b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle9baf115eddd83ba","typeKey":"ToastPlacementRtl_c7a440","componentTag":"citry-toast-placement-rtl-64ba5f34","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
