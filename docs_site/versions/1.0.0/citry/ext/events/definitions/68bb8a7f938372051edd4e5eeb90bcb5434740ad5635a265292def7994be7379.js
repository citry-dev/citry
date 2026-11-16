(function(Vue){
const { renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-scroll-area",
    tabindex: "0",
    "data-citry-ui-part": "scroll-area"
  }, _ctx.$citryPrepared.citryAttrs0), [
    (_ctx.$citryPrepared.selectedSlots['citrySlotdbd1d2942e04f334'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlotdbd1d2942e04f334", { key: 0 })
      : _createCommentVNode("v-if", true)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["1515467170c655985883a90412c7d03f74d07fe291843c485cc0e24885499234"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, normalizeClass: _normalizeClass, normalizeStyle: _normalizeStyle, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, renderList: _renderList, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-callback" }, [
    _createElementVNode("div", { class: "scroll-area-callback__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.rows += 2)
      }, "Add content", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.rows = Math.max(1, _ctx.rows - 2))
      }, " Remove content ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.sentinelTop += 80)
      }, " Move absolute marker ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.showImageLater())
      }, " Load a delayed image ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.expanded=!_ctx.expanded)
      }, " Toggle content stylesheet ", 8 /* PROPS */, ["onClick"])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
      onScroll: $event => (_ctx.nativeCount += 1),
      onScrollend: $event => (_ctx.settled += 1),
      onScrollChange: _ctx.handleScrollChange,
      "citry-id": _ctx.$citryPrepared.calls.citryCall6237c290092c68c3.id,
      key: _ctx.$citryPrepared.calls.citryCall6237c290092c68c3.key
    }, {
      ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
        _createElementVNode("div", {
          class: _normalizeClass(["scroll-area-callback__content", {'scroll-area-callback__content--expanded':_ctx.expanded}])
        }, [
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.rows, (row) => {
            return (_openBlock(), _createElementBlock("p", {
              key: row,
              textContent: _toDisplayString(`Audit row ${row}: current native content`)
            }, null, 8 /* PROPS */, ["textContent"]))
          }), 128 /* KEYED_FRAGMENT */)),
          _createElementVNode("span", {
            class: "scroll-area-callback__sentinel",
            style: _normalizeStyle(`inset-block-start:${_ctx.sentinelTop}px`)
          }, "Absolute marker", 4 /* STYLE */),
          (_ctx.imageVisible)
            ? (_openBlock(), _createElementBlock("img", {
              key: 0,
              class: "scroll-area-callback__image",
              alt: "Delayed audit chart",
              src: "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
            }))
            : _createCommentVNode("v-if", true),
          _createElementVNode("div", {
            ref: "shadowHost",
            class: "scroll-area-callback__shadow-host"
          }, [
            _createElementVNode("div", { ref: "shadowFixture" }, [
              _createElementVNode("p", { style: "inline-size:26rem;min-block-size:5rem;padding:0.5rem" }, " Open ShadowRoot content changes native layout without creating a component callback. ")
            ], 512 /* NEED_PATCH */)
          ], 512 /* NEED_PATCH */)
        ], 2 /* CLASS */)
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onScroll", "onScrollend", "onScrollChange", "citry-id"])),
    _createElementVNode("dl", { class: "scroll-area-callback__readout" }, [
      _createElementVNode("dt", null, "Native scroll events"),
      _createElementVNode("dd", {
        textContent: _toDisplayString(_ctx.nativeCount)
      }, "0", 8 /* PROPS */, ["textContent"]),
      _createElementVNode("dt", null, "Native scrollend events"),
      _createElementVNode("dd", {
        textContent: _toDisplayString(_ctx.settled)
      }, "0", 8 /* PROPS */, ["textContent"]),
      _createElementVNode("dt", null, "Component callbacks"),
      _createElementVNode("dd", {
        textContent: _toDisplayString(_ctx.callbackCount)
      }, "0", 8 /* PROPS */, ["textContent"]),
      _createElementVNode("dt", null, "Logical inline offset"),
      _createElementVNode("dd", {
        textContent: _toDisplayString(_ctx.lastInline)
      }, "0", 8 /* PROPS */, ["textContent"]),
      _createElementVNode("dt", null, "Block offset"),
      _createElementVNode("dd", {
        textContent: _toDisplayString(_ctx.lastBlock)
      }, "0", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["6f10239c1fc194e2ddbfdf7340666d850744d277c4e2d2d4f3727c58f94a8d34"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6237c290092c68c3","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"event","name":"@scroll","value":"nativeCount += 1","sourceStart":585,"sourceEnd":611},{"kind":"event","name":"@scrollend","value":"settled += 1","sourceStart":612,"sourceEnd":637},{"kind":"prop","name":":onScrollChange","value":"handleScrollChange","sourceStart":638,"sourceEnd":674}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_native_callback_75e7e9f6 = _resolveComponent("citry-scroll-area-native-callback-75e7e9f6")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_native_callback_75e7e9f6, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7749a7ef2f732dee.id,
      key: _ctx.$citryPrepared.calls.citryCall7749a7ef2f732dee.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["cb948001ee823068047c5ada9ee4367375c2177645f76da6b5b7f43ffb49f78d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7749a7ef2f732dee","typeKey":"ScrollAreaNativeCallback_1ec2b3","componentTag":"citry-scroll-area-native-callback-75e7e9f6","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
