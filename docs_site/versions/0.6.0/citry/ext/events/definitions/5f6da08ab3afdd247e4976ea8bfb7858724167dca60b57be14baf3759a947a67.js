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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["4e0a4a8620f25db3340e3fa999dcc97fd717899f6026662f313724ebcfe8d750"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ee2e510bee6d9253daa02c36fb4179345231572fc59468f6b0aab4d17364f077"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalldaf305a0211d9da0","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":onScrollChange","value":"(detail)=>\n            lastOffset=Math.round(detail.blockOffset)","sourceStart":1375,"sourceEnd":1457}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_lifecycle_83d507e9 = _resolveComponent("citry-scroll-area-lifecycle-83d507e9")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_lifecycle_83d507e9, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7c591b570974ba3b.id,
      key: _ctx.$citryPrepared.calls.citryCall7c591b570974ba3b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5dc7611747c159e2014d78f578975aa3d30da6519fa0497af4159cf02728df1c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7c591b570974ba3b","typeKey":"ScrollAreaLifecycle_686509","componentTag":"citry-scroll-area-lifecycle-83d507e9","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
