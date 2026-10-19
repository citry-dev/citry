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
window.__citryRuntimeDefinitions["3aef99d20b7a82a3a9edc8433e1c0b61c8dbd194abe015b9cdd3db0961a3c5f1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall0944cd97843df107","typeKey":"CInternalMenuSurface_597468","componentTag":"citry-c-internal-menu-surface-37f82339","bindings":[],"fills":[{"name":"citrySlot5176cbf97df342fc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":["citrySlot0021c864d3777155"]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_context_menu_c149a668 = _resolveComponent("citry-c-context-menu-c149a668")
  
  return (_openBlock(), _createElementBlock("section", { class: "context-menu-customization" }, [
    _createElementVNode("div", { class: "context-menu-customization__controls" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.orchardEnhanced=!_ctx.orchardEnhanced)
      }, " Toggle server-disabled Orchard enhancement ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.harborEnhanced=!_ctx.harborEnhanced)
      }, " Disable or restore ready Harbor enhancement ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("output", {
        "aria-live": "polite",
        textContent: _toDisplayString(`Orchard ${_ctx.orchardEnhanced ? 'enhanced' : 'native'};
        Harbor ${_ctx.harborEnhanced ? 'enhanced' : 'native'}`)
      }, "Orchard native; Harbor enhanced", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("div", { class: "context-menu-customization__brands" }, [
      _createElementVNode("article", { class: "context-menu-customization__orchard" }, [
        _createElementVNode("h3", null, "Orchard"),
        (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({disabled:!_ctx.orchardEnhanced}, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall462d07e599714a8d.id,
          key: _ctx.$citryPrepared.calls.citryCall462d07e599714a8d.key
        }), {
          ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
            _createElementVNode("div", _mergeProps({
              class: "context-menu-customization__file",
              tabindex: "0"
            }, _ctx.$citryPrepared.citryAttrs0), [
              _createElementVNode("strong", null, "Harvest plan.pdf"),
              _createElementVNode("span", null, "Server-open fallback")
            ], 16 /* FULL_PROPS */)
          ]),
          ['citrySlot0021c864d3777155']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCallb3b8cbd462c393d2.id,
              key: _ctx.$citryPrepared.calls.citryCallb3b8cbd462c393d2.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode("Open file")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall06d34d8969e63c7c.id,
              key: _ctx.$citryPrepared.calls.citryCall06d34d8969e63c7c.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode("Archive file")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _createElementVNode("article", {
        class: "context-menu-customization__harbor",
        style: "color-scheme:dark"
      }, [
        _createElementVNode("h3", null, "Harbor"),
        (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({disabled:!_ctx.harborEnhanced}, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall91df5f9ae47f96f0.id,
          key: _ctx.$citryPrepared.calls.citryCall91df5f9ae47f96f0.key
        }), {
          ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
            _createElementVNode("div", _mergeProps({
              class: "context-menu-customization__file",
              tabindex: "0"
            }, _ctx.$citryPrepared.citryAttrs1), [
              _createElementVNode("strong", null, "Dock schedule.csv"),
              _createElementVNode("span", null, "Server-closed fallback")
            ], 16 /* FULL_PROPS */)
          ]),
          ['citrySlot0021c864d3777155']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCalld84b05c041d1fe7a.id,
              key: _ctx.$citryPrepared.calls.citryCalld84b05c041d1fe7a.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode("Open file")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall9b46acc294dbf2e3.id,
              key: _ctx.$citryPrepared.calls.citryCall9b46acc294dbf2e3.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode("Remove file")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ])
    ]),
    _createElementVNode("p", null, " Without JavaScript, targets remain ordinary native content. A server-closed Menu stays hidden and a server-open Menu remains readable in document flow. The browser context menu remains available until a valid enhanced request is accepted. ")
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["98bd6d893dd0f189d113721d92d95b3b2407c696be49d381b1a0c3f4684847a8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb3b8cbd462c393d2","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall06d34d8969e63c7c","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall462d07e599714a8d","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{disabled:!orchardEnhanced}","sourceStart":733,"sourceEnd":769}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall06d34d8969e63c7c","citryCallb3b8cbd462c393d2"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld84b05c041d1fe7a","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9b46acc294dbf2e3","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall91df5f9ae47f96f0","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{disabled:!harborEnhanced}","sourceStart":1943,"sourceEnd":1978}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall9b46acc294dbf2e3","citryCalld84b05c041d1fe7a"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_context_menu_customization_and_fallback_b5e2a67b = _resolveComponent("citry-context-menu-customization-and-fallback-b5e2a67b")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_context_menu_customization_and_fallback_b5e2a67b, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9a4a671e377852d9.id,
      key: _ctx.$citryPrepared.calls.citryCall9a4a671e377852d9.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ea5d6dbb0c3ef7a69bf13e32dc05a735b753508929b51d4ba4fee186d861f0d3"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9a4a671e377852d9","typeKey":"ContextMenuCustomizationAndFallback_b32c68","componentTag":"citry-context-menu-customization-and-fallback-b5e2a67b","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
