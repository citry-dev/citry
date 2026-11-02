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
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_context_menu_c149a668 = _resolveComponent("citry-c-context-menu-c149a668")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "context-menu-positioning",
    style: "--cui-menu-inline-size:18rem",
    dir: _ctx.surfaceDir
  }, [
    _createElementVNode("div", { class: "context-menu-positioning__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.surfaceDir=_ctx.surfaceDir === 'ltr' ? 'rtl' : 'ltr')
      }, "Toggle surface direction", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.targetDir=_ctx.targetDir === 'ltr' ? 'rtl' : 'ltr')
      }, "Toggle target-only direction", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.openFromOwnerState())
      }, "Open from owner state", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.$refs.repairScroller.scrollTop += 32)
      }, " Scroll repair fixture ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.resizeRepairFixture())
      }, " Resize repair fixture ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.testOffscreenRejection())
      }, "Test fully offscreen rejection", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("output", {
        textContent: _toDisplayString(`Accepted point: ${_ctx.lastPoint}; invocation: ${_ctx.lastInvocation}`)
      }, " Accepted point: none; invocation: none ", 8 /* PROPS */, ["textContent"]),
      _createElementVNode("output", {
        textContent: _toDisplayString(_ctx.viewportSummary())
      }, "Visual viewport diagnostic", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("div", { class: "context-menu-positioning__board" }, [
      (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({
        onOpenChange:_ctx.recordAcceptedPoint,
      }, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall7963b23024b56d19.id,
        key: _ctx.$citryPrepared.calls.citryCall7963b23024b56d19.key
      }), {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-positioning__target is-top-start",
            tabindex: "0",
            dir: _ctx.targetDir
          }, _ctx.$citryPrepared.citryAttrs0), "Top start", 16 /* FULL_PROPS */, ["dir"])
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallb5a5822c97df139c.id,
            key: _ctx.$citryPrepared.calls.citryCallb5a5822c97df139c.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect corner")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall8807aee860ada429.id,
            key: _ctx.$citryPrepared.calls.citryCall8807aee860ada429.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Duplicate record")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall506f0d260aad2fee.id,
        key: _ctx.$citryPrepared.calls.citryCall506f0d260aad2fee.key
      }, {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-positioning__target is-top-end",
            tabindex: "0"
          }, _ctx.$citryPrepared.citryAttrs1), "Top end", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall08dfd79cfdde007d.id,
            key: _ctx.$citryPrepared.calls.citryCall08dfd79cfdde007d.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect corner")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalld212a6358201dc83.id,
            key: _ctx.$citryPrepared.calls.citryCalld212a6358201dc83.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Duplicate record")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallc2e0bbcc6d3aaad1.id,
        key: _ctx.$citryPrepared.calls.citryCallc2e0bbcc6d3aaad1.key
      }, {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-positioning__target is-bottom-start",
            tabindex: "0"
          }, _ctx.$citryPrepared.citryAttrs2), "Bottom start", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall2def5889565727c0.id,
            key: _ctx.$citryPrepared.calls.citryCall2def5889565727c0.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect corner")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalle5a12ad9755d0ab8.id,
            key: _ctx.$citryPrepared.calls.citryCalle5a12ad9755d0ab8.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Duplicate record")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({
        open:_ctx.externalOpen,
        onOpenChange:_ctx.claimExternalOpen,
      }, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall31586e5122fc60f1.id,
        key: _ctx.$citryPrepared.calls.citryCall31586e5122fc60f1.key
      }), {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-positioning__target is-bottom-end",
            tabindex: "0"
          }, _ctx.$citryPrepared.citryAttrs3), "Bottom end", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall1f2fa90366ae263b.id,
            key: _ctx.$citryPrepared.calls.citryCall1f2fa90366ae263b.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect corner")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall0b938ec9af0b36aa.id,
            key: _ctx.$citryPrepared.calls.citryCall0b938ec9af0b36aa.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Duplicate record")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall2b39b9e4bdf9b99e.id,
            key: _ctx.$citryPrepared.calls.citryCall2b39b9e4bdf9b99e.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Open a deliberately longer command label")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
      (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall27d1bd9fb967c69a.id,
        key: _ctx.$citryPrepared.calls.citryCall27d1bd9fb967c69a.key
      }, {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("button", _mergeProps({
            class: "context-menu-positioning__target is-offscreen",
            type: "button",
            "data-context-menu-offscreen-target": ""
          }, _ctx.$citryPrepared.citryAttrs4), "Fully offscreen target", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall879bf1d6d7deadaf.id,
            key: _ctx.$citryPrepared.calls.citryCall879bf1d6d7deadaf.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Rejected while fully offscreen")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("div", {
      class: "context-menu-positioning__repair-scroller",
      ref: "repairScroller"
    }, [
      _createElementVNode("div", { class: "context-menu-positioning__repair-spacer" }, "Scrollable repair boundary"),
      _createElementVNode("div", { class: "context-menu-positioning__transformed" }, [
        (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, {
          "citry-id": _ctx.$citryPrepared.calls.citryCalld7b1ec1346986269.id,
          key: _ctx.$citryPrepared.calls.citryCalld7b1ec1346986269.key
        }, {
          ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
            _createElementVNode("div", _mergeProps({
              class: "context-menu-positioning__target",
              tabindex: "0"
            }, _ctx.$citryPrepared.citryAttrs5), "Target inside transform, filter, and containment", 16 /* FULL_PROPS */)
          ]),
          ['citrySlot0021c864d3777155']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallcbd13d7cc798a9ec.id,
              key: _ctx.$citryPrepared.calls.citryCallcbd13d7cc798a9ec.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode("Inspect transformed card")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ])
    ], 512 /* NEED_PATCH */),
    _createElementVNode("p", null, " Pointer requests use the accepted browser event point. Keyboard and owner-open requests derive a visible point from the focused target. The component has no coordinate or placement input. Zoom to 400% to verify the same collision-safe 18 rem surface. ")
  ], 8 /* PROPS */, ["dir"]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["91ab9b50533c92b51ff15e6f9ed5aff002ca73064d7fbaf1d5baa4afaca78378"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb5a5822c97df139c","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8807aee860ada429","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7963b23024b56d19","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n        onOpenChange:recordAcceptedPoint,\n      }","sourceStart":1099,"sourceEnd":1159}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall8807aee860ada429","citryCallb5a5822c97df139c"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall08dfd79cfdde007d","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld212a6358201dc83","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall506f0d260aad2fee","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall08dfd79cfdde007d","citryCalld212a6358201dc83"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2def5889565727c0","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle5a12ad9755d0ab8","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc2e0bbcc6d3aaad1","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall2def5889565727c0","citryCalle5a12ad9755d0ab8"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1f2fa90366ae263b","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall0b938ec9af0b36aa","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall2b39b9e4bdf9b99e","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall31586e5122fc60f1","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n        open:externalOpen,\n        onOpenChange:claimExternalOpen,\n      }","sourceStart":4086,"sourceEnd":4171}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall0b938ec9af0b36aa","citryCall1f2fa90366ae263b","citryCall2b39b9e4bdf9b99e"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall879bf1d6d7deadaf","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall27d1bd9fb967c69a","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall879bf1d6d7deadaf"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallcbd13d7cc798a9ec","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld7b1ec1346986269","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCallcbd13d7cc798a9ec"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_context_menu_positioning_and_rtl_73defe7c = _resolveComponent("citry-context-menu-positioning-and-rtl-73defe7c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_context_menu_positioning_and_rtl_73defe7c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall78c6aacea678f6be.id,
      key: _ctx.$citryPrepared.calls.citryCall78c6aacea678f6be.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c05c07ed6ce15ef3f94a6fb6cfcaf46a83f35be3e22ab450487937ec608234ae"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall78c6aacea678f6be","typeKey":"ContextMenuPositioningAndRtl_639e56","componentTag":"citry-context-menu-positioning-and-rtl-73defe7c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
