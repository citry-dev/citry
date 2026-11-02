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
      ], 16 /* FULL_PROPS */),
      _createElementVNode("div", _mergeProps({
        class: "cui-toast",
        role: "group",
        tabindex: "0",
        "data-citry-ui-part": "toast"
      }, _ctx.$citryPrepared.citryAttrs4), [
        _createElementVNode("div", {
          class: "cui-toast__content",
          "data-citry-ui-part": "content"
        }, [
          _createElementVNode("div", _mergeProps({
            class: "cui-toast__title",
            "data-citry-ui-part": "title"
          }, _ctx.$citryPrepared.citryAttrs5), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */)
        ]),
        _createElementVNode("div", {
          class: "cui-toast__actions",
          "data-citry-ui-part": "actions"
        }, [
          _createElementVNode("button", _mergeProps({
            type: "button",
            "data-citry-toast-dismiss": "",
            "data-citry-ui-part": "dismiss"
          }, _ctx.$citryPrepared.citryAttrs6), "×", 16 /* FULL_PROPS */)
        ])
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2a78ffc943652f2280f19d6d89cff0d24e99fe01fa76d8ee40530759f4fd60bd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_toast_region_5c499f86 = _resolveComponent("citry-c-toast-region-5c499f86")
  
  return (_openBlock(), _createElementBlock("section", { class: "toast-example" }, [
    _createElementVNode("p", null, "Dismiss a visible message to promote the queued third item."),
    (_openBlock(), _createBlock(_component_citry_c_toast_region_5c499f86, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2a717cd971f05b83.id,
      key: _ctx.$citryPrepared.calls.citryCall2a717cd971f05b83.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["3b751dce32839938967b4e09156c83c0949e1eb4d02867ecc98639c1e445c2aa"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2a717cd971f05b83","typeKey":"CToastRegion_eec238","componentTag":"citry-c-toast-region-5c499f86","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_toast_visible_limit_319613bd = _resolveComponent("citry-toast-visible-limit-319613bd")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_toast_visible_limit_319613bd, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9df484271b1757c2.id,
      key: _ctx.$citryPrepared.calls.citryCall9df484271b1757c2.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6bc5de813fbec23b58b681aa0517cb3abcc9f1cc513d1eaafdcf1f524fae3158"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9df484271b1757c2","typeKey":"ToastVisibleLimit_416dc2","componentTag":"citry-toast-visible-limit-319613bd","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
