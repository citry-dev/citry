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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f3f0267ba71fab158a1093709d337525c369c1aeb471de76c231cb83ca26db90"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-361caf6ce22af4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["2dd141883a0b86e46f4dee372ca395da9eba7d6cbe04575f124612c3a26de1af"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["77b4ad6c5c0fa7847ed86fb9d3316a984e5c2762786191b279b85857b6da2425"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0944cd97843df107","typeKey":"CInternalMenuSurface_597468","componentTag":"citry-c-internal-menu-surface-37f82339","bindings":[],"fills":[{"name":"citrySlot5176cbf97df342fc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":["citrySlot0021c864d3777155"]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createTextVNode: _createTextVNode, renderList: _renderList, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_context_menu_c149a668 = _resolveComponent("citry-c-context-menu-c149a668")
  
  return (_openBlock(), _createElementBlock("section", { class: "context-menu-touch" }, [
    _createElementVNode("div", { class: "context-menu-touch__policy" }, [
      _createElementVNode("strong", null, "Bound fallback"),
      _createElementVNode("span", null, "Hold 700 ms · move at most 10 CSS px"),
      _createElementVNode("span", null, "Matching click guard: pointerup + 1,500 ms"),
      _createElementVNode("span", null, "Absolute guard deadline: 10 seconds")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({
      onOpenChange:(next,detail)=>{
        const state=_ctx.touchState;
        state.phase=next ? 'accepted' : 'idle';
        state.log.unshift(`${next ? 'accepted' : 'closed'} ${detail.reason}`);
      },
    }, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalled278887ef4d4ee2.id,
      key: _ctx.$citryPrepared.calls.citryCalled278887ef4d4ee2.key
    }), {
      ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
        _createElementVNode("button", _mergeProps({
          class: "context-menu-touch__card",
          type: "button",
          "data-context-menu-touch-target": "",
          onClick: $event => (_ctx.touchState.targetClicks += 1)
        }, _ctx.$citryPrepared.citryAttrs0), [
          _createElementVNode("strong", null, "Touch card"),
          _createElementVNode("span", null, "Press and hold for contextual commands")
        ], 16 /* FULL_PROPS */, ["onClick"])
      ]),
      ['citrySlot0021c864d3777155']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall1b6d4747fb13e658.id,
          key: _ctx.$citryPrepared.calls.citryCall1b6d4747fb13e658.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Pin card")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCallf74207d0297d7c34.id,
          key: _ctx.$citryPrepared.calls.citryCallf74207d0297d7c34.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Share card")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("div", {
      class: "context-menu-touch__scroller",
      onScroll: $event => {
      _ctx.touchState.phase='canceled: scroll';
      _ctx.touchState.log.unshift('canceled scroll')
    }
    }, [
      (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({
        open:false,
        onOpenChange:(next,detail)=>{
          _ctx.touchState.phase='controlled refused';
          _ctx.touchState.log.unshift(`refused ${detail.reason}`);
          return false;
        },
      }, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall3c7b1e2d9c840cd6.id,
        key: _ctx.$citryPrepared.calls.citryCall3c7b1e2d9c840cd6.key
      }), {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-touch__card",
            tabindex: "0",
            "data-context-menu-scroll-target": ""
          }, _ctx.$citryPrepared.citryAttrs1), [
            _createElementVNode("strong", null, "Scrollable card"),
            _createElementVNode("span", null, "Scrolling, movement, and another pointer cancel the hold.")
          ], 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall43ea14776936e182.id,
            key: _ctx.$citryPrepared.calls.citryCall43ea14776936e182.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect card")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      _createElementVNode("div", { class: "context-menu-touch__spacer" }, "Scroll boundary")
    ], 40 /* PROPS, NEED_HYDRATION */, ["onScroll"]),
    _createElementVNode("div", { class: "context-menu-touch__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.simulate('hold'))
      }, "Test 700 ms hold", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.simulate('move'))
      }, "Test movement cancel", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.simulate('scroll'))
      }, "Test scroll cancel", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.simulate('lost-up'))
      }, "Test lost pointerup", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.simulate('second'))
      }, "Test second pointer", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {_ctx.touchState.log=[];_ctx.touchState.phase='idle'}
      }, "Clear ledger", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("output", {
        "aria-live": "polite",
        textContent: _toDisplayString(`State: ${_ctx.touchState.phase};
        primary clicks: ${_ctx.touchState.targetClicks}`)
      }, "State: idle; primary clicks: 0", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("ol", { "aria-live": "polite" }, [
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.touchState.log.slice(0,5), (entry) => {
        return (_openBlock(), _createElementBlock("li", {
          key: entry,
          textContent: _toDisplayString(entry)
        }, null, 8 /* PROPS */, ["textContent"]))
      }), 128 /* KEYED_FRAGMENT */))
    ]),
    _createElementVNode("p", null, " Desktop emulation cannot prove an operating system's callout timing. Citry does not disable selection, touch scrolling, or platform callouts. ")
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c9112f6aa921f2b36f50b5533d9373a2650237419b0195718d81a227530190ca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1b6d4747fb13e658","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf74207d0297d7c34","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalled278887ef4d4ee2","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n      onOpenChange:(next,detail)=>{\n        const state=touchState;\n        state.phase=next ? 'accepted' : 'idle';\n        state.log.unshift(`${next ? 'accepted' : 'closed'} ${detail.reason}`);\n      },\n    }","sourceStart":328,"sourceEnd":548}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall1b6d4747fb13e658","citryCallf74207d0297d7c34"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall43ea14776936e182","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall3c7b1e2d9c840cd6","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n        open:false,\n        onOpenChange:(next,detail)=>{\n          touchState.phase='controlled refused';\n          touchState.log.unshift(`refused ${detail.reason}`);\n          return false;\n        },\n      }","sourceStart":1797,"sourceEnd":2019}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall43ea14776936e182"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_context_menu_touch_and_pen_cbda931b = _resolveComponent("citry-context-menu-touch-and-pen-cbda931b")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_context_menu_touch_and_pen_cbda931b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall61e73cd77dbe4c10.id,
      key: _ctx.$citryPrepared.calls.citryCall61e73cd77dbe4c10.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8f7c8c578ddef799b989ec72e117b3c5f1540b62c7cc769aa177484d5b1eb66b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall61e73cd77dbe4c10","typeKey":"ContextMenuTouchAndPen_290450","componentTag":"citry-context-menu-touch-and-pen-cbda931b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
