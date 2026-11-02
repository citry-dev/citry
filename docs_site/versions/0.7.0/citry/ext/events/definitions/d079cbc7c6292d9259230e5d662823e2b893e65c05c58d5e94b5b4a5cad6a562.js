(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("section", _mergeProps({
    ref: "root",
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
          }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
          _createElementVNode("div", _mergeProps({
            class: "cui-toast__description",
            "data-citry-ui-part": "description"
          }, _ctx.$citryPrepared.citryAttrs3), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */)
        ]),
        _createElementVNode("div", {
          class: "cui-toast__actions",
          "data-citry-ui-part": "actions"
        }, [
          _createElementVNode("button", _mergeProps({
            type: "button",
            "data-citry-toast-dismiss": "",
            "data-citry-ui-part": "dismiss"
          }, _ctx.$citryPrepared.citryAttrs4), "×", 16 /* FULL_PROPS */)
        ])
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["043c2baf0a465bf0d64f63c3773d8a055683e98c267b447cd1645c7a81045f05"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_toast_region_5c499f86 = _resolveComponent("citry-c-toast-region-5c499f86")
  
  return (_openBlock(), _createElementBlock("section", { class: "toast-theme" }, [
    (_openBlock(), _createBlock(_component_citry_c_toast_region_5c499f86, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall340b662f0d6075e6.id,
      key: _ctx.$citryPrepared.calls.citryCall340b662f0d6075e6.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c249db9e85e7941ce0273adbdd53431315047b0ec6de003011fa3d70a15b481b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall340b662f0d6075e6","typeKey":"CToastRegion_eec238","componentTag":"citry-c-toast-region-5c499f86","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_customized_toast_897effba = _resolveComponent("citry-customized-toast-897effba")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_customized_toast_897effba, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall07d6a82b4c4adf94.id,
      key: _ctx.$citryPrepared.calls.citryCall07d6a82b4c4adf94.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["8394502bb0cfae40de31dc615488209ef3bbdc803e6be62fe6f1f5fae3f6c334"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall07d6a82b4c4adf94","typeKey":"CustomizedToast_d2fdaa","componentTag":"citry-customized-toast-897effba","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
