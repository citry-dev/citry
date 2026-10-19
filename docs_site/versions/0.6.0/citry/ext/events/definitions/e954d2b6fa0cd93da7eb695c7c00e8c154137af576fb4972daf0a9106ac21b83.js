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
        onOpenChange:(next,detail)=>{
          if (next) {
            _ctx.lastPoint=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
            _ctx.lastInvocation=detail.reason === 'contextmenu' ? 'pointer' : detail.reason;
          }
        },
      }, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall7f45b8434d719c28.id,
        key: _ctx.$citryPrepared.calls.citryCall7f45b8434d719c28.key
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
            "citry-id": _ctx.$citryPrepared.calls.citryCall81771cb4b13d8124.id,
            key: _ctx.$citryPrepared.calls.citryCall81771cb4b13d8124.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect corner")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallc204171303ca3bc4.id,
            key: _ctx.$citryPrepared.calls.citryCallc204171303ca3bc4.key
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
        "citry-id": _ctx.$citryPrepared.calls.citryCallaff47f2c021462b2.id,
        key: _ctx.$citryPrepared.calls.citryCallaff47f2c021462b2.key
      }, {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-positioning__target is-top-end",
            tabindex: "0"
          }, _ctx.$citryPrepared.citryAttrs1), "Top end", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallea4bf61ed6f05d64.id,
            key: _ctx.$citryPrepared.calls.citryCallea4bf61ed6f05d64.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect corner")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall1ac2b3d75dec3164.id,
            key: _ctx.$citryPrepared.calls.citryCall1ac2b3d75dec3164.key
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
        "citry-id": _ctx.$citryPrepared.calls.citryCall628321b0a956a5b4.id,
        key: _ctx.$citryPrepared.calls.citryCall628321b0a956a5b4.key
      }, {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-positioning__target is-bottom-start",
            tabindex: "0"
          }, _ctx.$citryPrepared.citryAttrs2), "Bottom start", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall8e88144172e04f7f.id,
            key: _ctx.$citryPrepared.calls.citryCall8e88144172e04f7f.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect corner")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall7fc71696d8865158.id,
            key: _ctx.$citryPrepared.calls.citryCall7fc71696d8865158.key
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
        onOpenChange:(next,detail)=>{
          _ctx.externalOpen=next;
          if (next) {
            _ctx.lastPoint=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
            _ctx.lastInvocation=detail.reason === 'contextmenu' ? 'pointer' : detail.reason;
            return true;
          }
        },
      }, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall533f105939cc1146.id,
        key: _ctx.$citryPrepared.calls.citryCall533f105939cc1146.key
      }), {
        ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
          _createElementVNode("div", _mergeProps({
            class: "context-menu-positioning__target is-bottom-end",
            tabindex: "0"
          }, _ctx.$citryPrepared.citryAttrs3), "Bottom end", 16 /* FULL_PROPS */)
        ]),
        ['citrySlot0021c864d3777155']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall1d4f6ed96e2fdbbf.id,
            key: _ctx.$citryPrepared.calls.citryCall1d4f6ed96e2fdbbf.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Inspect corner")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall1d7d21c49751a92a.id,
            key: _ctx.$citryPrepared.calls.citryCall1d7d21c49751a92a.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Duplicate record")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCalla960be0513328fd3.id,
            key: _ctx.$citryPrepared.calls.citryCalla960be0513328fd3.key
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
        "citry-id": _ctx.$citryPrepared.calls.citryCalle1fcb00fcae22977.id,
        key: _ctx.$citryPrepared.calls.citryCalle1fcb00fcae22977.key
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
            "citry-id": _ctx.$citryPrepared.calls.citryCall4ff2fa00126aa90c.id,
            key: _ctx.$citryPrepared.calls.citryCall4ff2fa00126aa90c.key
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
          "citry-id": _ctx.$citryPrepared.calls.citryCallc5a7eb9c11a739af.id,
          key: _ctx.$citryPrepared.calls.citryCallc5a7eb9c11a739af.key
        }, {
          ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
            _createElementVNode("div", _mergeProps({
              class: "context-menu-positioning__target",
              tabindex: "0"
            }, _ctx.$citryPrepared.citryAttrs5), "Target inside transform, filter, and containment", 16 /* FULL_PROPS */)
          ]),
          ['citrySlot0021c864d3777155']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallf064e585843c1b64.id,
              key: _ctx.$citryPrepared.calls.citryCallf064e585843c1b64.key
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a48632ec65c5cfcf4aeb6bf3ff2c33da936b618e216f4d4b5d06124f0ab9273f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall81771cb4b13d8124","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc204171303ca3bc4","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7f45b8434d719c28","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n        onOpenChange:(next,detail)=>{\n          if (next) {\n            lastPoint=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;\n            lastInvocation=detail.reason === 'contextmenu' ? 'pointer' : detail.reason;\n          }\n        },\n      }","sourceStart":1099,"sourceEnd":1374}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall81771cb4b13d8124","citryCallc204171303ca3bc4"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallea4bf61ed6f05d64","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1ac2b3d75dec3164","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallaff47f2c021462b2","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall1ac2b3d75dec3164","citryCallea4bf61ed6f05d64"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall8e88144172e04f7f","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7fc71696d8865158","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall628321b0a956a5b4","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall7fc71696d8865158","citryCall8e88144172e04f7f"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1d4f6ed96e2fdbbf","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall1d7d21c49751a92a","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla960be0513328fd3","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall533f105939cc1146","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n        open:externalOpen,\n        onOpenChange:(next,detail)=>{\n          externalOpen=next;\n          if (next) {\n            lastPoint=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;\n            lastInvocation=detail.reason === 'contextmenu' ? 'pointer' : detail.reason;\n            return true;\n          }\n        },\n      }","sourceStart":4301,"sourceEnd":4657}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall1d4f6ed96e2fdbbf","citryCall1d7d21c49751a92a","citryCalla960be0513328fd3"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall4ff2fa00126aa90c","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle1fcb00fcae22977","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall4ff2fa00126aa90c"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf064e585843c1b64","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallc5a7eb9c11a739af","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCallf064e585843c1b64"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_context_menu_positioning_and_rtl_70f0699a = _resolveComponent("citry-context-menu-positioning-and-rtl-70f0699a")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_context_menu_positioning_and_rtl_70f0699a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalle8b80f12a5592c4e.id,
      key: _ctx.$citryPrepared.calls.citryCalle8b80f12a5592c4e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a59aa71a93518dcae53b762ecf2df65995486a584fbe527b088c96ec9d65c501"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalle8b80f12a5592c4e","typeKey":"ContextMenuPositioningAndRtl_bf8030","componentTag":"citry-context-menu-positioning-and-rtl-70f0699a","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
