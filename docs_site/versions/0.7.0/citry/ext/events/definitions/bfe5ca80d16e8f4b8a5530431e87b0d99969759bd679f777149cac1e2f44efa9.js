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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, createTextVNode: _createTextVNode, createCommentVNode: _createCommentVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-lifecycle" }, [
    _createElementVNode("div", { class: "scroll-area-lifecycle__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEvent76', $event))
      }, " Retained-root server update ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$citryEvents.dispatch('citryEventd4', $event))
      }, " Replace the root ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.mounted=!_ctx.mounted)
      }, " Remove or restore locally ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.direction=_ctx.direction === 'ltr' ? 'rtl' : 'ltr')
      }, "Flip direction", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {
        const area=_ctx.$root.querySelector('#scroll-area-lifecycle-target');
        if (area) {
          area.setAttribute('tabindex','-1');
          area.setAttribute('role','button');
          area.dataset.axis='invalid';
        }
      }
      }, "Damage then repair owned attributes", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {
        const area=_ctx.$root.querySelector('#scroll-area-lifecycle-target');
        if (area) area.style.writingMode =
          area.style.writingMode === 'vertical-rl'
            ? 'horizontal-tb'
            : 'vertical-rl';
      }
      }, "Toggle unsupported writing mode", 8 /* PROPS */, ["onClick"])
    ]),
    _createElementVNode("p", null, [
      _createTextVNode("Server step: "),
      _createElementVNode("output", null, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
    ]),
    (_ctx.mounted)
      ? (_openBlock(), _createElementBlock("div", {
        key: 0,
        dir: _ctx.direction
      }, [
        (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
          onScrollChange: (detail)=>
            _ctx.lastOffset=Math.round(detail.blockOffset),
          "citry-id": _ctx.$citryPrepared.calls.citryCalldaf305a0211d9da0.id,
          key: _ctx.$citryPrepared.calls.citryCalldaf305a0211d9da0.key
        }, {
          ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
            _createElementVNode("div", { class: "scroll-area-lifecycle__content" }, [
              _createElementVNode("p", null, "Server generation " + _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */),
              _createElementVNode("p", null, "Scroll before using a server action."),
              _createElementVNode("p", null, "A retained root preserves its logical position and focus."),
              _createElementVNode("p", null, "A replacement root starts with native browser position."),
              _createElementVNode("p", null, "Removal cancels pending callback and observer work."),
              _createElementVNode("p", null, "Restoration creates a fresh local instance."),
              _createElementVNode("p", null, "Nested content focus is never redirected."),
              _createElementVNode("p", null, "The viewport remains useful without JavaScript.")
            ])
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onScrollChange", "citry-id"]))
      ], 8 /* PROPS */, ["dir"]))
      : _createCommentVNode("v-if", true),
    _createElementVNode("output", {
      textContent: _toDisplayString(`Last user scroll offset ${_ctx.lastOffset}`)
    }, " Last user scroll offset 0 ", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["610124e10817a106a2ad9a6da29e7563803f8a5efc0d6b81749918345fa9e7cb"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldaf305a0211d9da0","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n            lastOffset=Math.round(detail.blockOffset)","sourceStart":1375,"sourceEnd":1457}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_lifecycle_b605d5ce = _resolveComponent("citry-scroll-area-lifecycle-b605d5ce")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_lifecycle_b605d5ce, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall920413275e5b1d8d.id,
      key: _ctx.$citryPrepared.calls.citryCall920413275e5b1d8d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["7d8f73cd7c957d9d4947125c957aedd34d40f65f59f6cd45d10c0accac8f434a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall920413275e5b1d8d","typeKey":"ScrollAreaLifecycle_87b285","componentTag":"citry-scroll-area-lifecycle-b605d5ce","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
