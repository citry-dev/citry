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
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, vModelCheckbox: _vModelCheckbox, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_context_menu_c149a668 = _resolveComponent("citry-c-context-menu-c149a668")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "context-menu-controlled" }, [
    (_openBlock(), _createBlock(_component_citry_c_context_menu_c149a668, _mergeProps({
      open:_ctx.controlled ? _ctx.open : null,
      onOpenChange:(nextOpen,detail)=>{
        _ctx.lastReason=detail.reason;
        _ctx.candidate=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
        if (!_ctx.controlled) return;
        if (!nextOpen) {
          _ctx.open=false;
          return;
        }
        if (!_ctx.accept) return false;
        if (!_ctx.breakClaim) _ctx.open=true;
        return true;
      },
    }, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall14a4b0d846a0e3f8.id,
      key: _ctx.$citryPrepared.calls.citryCall14a4b0d846a0e3f8.key
    }), {
      ['citrySlotc8e5d267bc58cf8e']: _withCtx(() => [
        _createElementVNode("div", _mergeProps({
          class: "context-menu-controlled__target",
          tabindex: "0"
        }, _ctx.$citryPrepared.citryAttrs0), [
          _createElementVNode("strong", null, "Controlled diagram"),
          _createElementVNode("span", null, "Right click or press Shift+F10")
        ], 16 /* FULL_PROPS */)
      ]),
      ['citrySlot0021c864d3777155']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall1f2112e6843a0133.id,
          key: _ctx.$citryPrepared.calls.citryCall1f2112e6843a0133.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Inspect layers")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall6500ac5c98e8dca6.id,
          key: _ctx.$citryPrepared.calls.citryCall6500ac5c98e8dca6.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Duplicate diagram")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("div", {
      role: "group",
      "aria-label": "Controlled visibility settings"
    }, [
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement5eeaeb98e097d6596262e600f4cad3806870e8d84dc4b7e21b67ae8940817b99",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.accept) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.accept],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Claim requests")
      ]),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement3dae2b4181a619308bd48b1a8a070bc34f52b168c63c6f92017372d1da8189fe",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.breakClaim) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.breakClaim],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Break the claim")
      ]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {_ctx.controlled=true;_ctx.open=true}
      }, " Open from owner ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {_ctx.controlled=true;_ctx.open=false}
      }, " Close from owner ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.controlled=false)
      }, " Release control ", 8 /* PROPS */, ["onClick"])
    ]),
    _createElementVNode("output", null, [
      _createTextVNode(" State: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.controlled ? (_ctx.open ? 'controlled open' : 'controlled closed') : 'uncontrolled')
      }, " controlled closed ", 8 /* PROPS */, ["textContent"]),
      _createTextVNode("; request: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.lastReason)
      }, "none", 8 /* PROPS */, ["textContent"]),
      _createTextVNode("; candidate: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.candidate)
      }, "none", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["1cd9649af22ff42ca7b9abfe1c9d111f0015fa6ba6ad3c2ebe8ab0569d848551"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectivee75061b44a79a23c856e0c532cdf60aba26a9eff07970374c9eafb69fbd91a2aD0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirectivee45040b0f678a4ae0637e9bddf7a5ef1eb5b3df5ae49669abbb36f4fd791adb4D0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectivee45040b0f678a4ae0637e9bddf7a5ef1eb5b3df5ae49669abbb36f4fd791adb4","replacementKey":"citryReplacement3dae2b4181a619308bd48b1a8a070bc34f52b168c63c6f92017372d1da8189fe","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirectivee75061b44a79a23c856e0c532cdf60aba26a9eff07970374c9eafb69fbd91a2a","replacementKey":"citryReplacement5eeaeb98e097d6596262e600f4cad3806870e8d84dc4b7e21b67ae8940817b99","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall1f2112e6843a0133","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6500ac5c98e8dca6","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall14a4b0d846a0e3f8","typeKey":"CContextMenu_a62472","componentTag":"citry-c-context-menu-c149a668","bindings":[{"kind":"props-object","name":"v-bind","value":"{\n      open:controlled ? open : null,\n      onOpenChange:(nextOpen,detail)=>{\n        lastReason=detail.reason;\n        candidate=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;\n        if (!controlled) return;\n        if (!nextOpen) {\n          open=false;\n          return;\n        }\n        if (!accept) return false;\n        if (!breakClaim) open=true;\n        return true;\n      },\n    }","sourceStart":76,"sourceEnd":494}],"fills":[{"name":"citrySlot0021c864d3777155","localDescendants":["citryCall1f2112e6843a0133","citryCall6500ac5c98e8dca6"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotc8e5d267bc58cf8e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_context_menu_7c8367a9 = _resolveComponent("citry-controlled-context-menu-7c8367a9")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_context_menu_7c8367a9, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2a2f686de6ad2c92.id,
      key: _ctx.$citryPrepared.calls.citryCall2a2f686de6ad2c92.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["70da6bb1de1a6d6c919521be98b0ac20502fd7ed21d41f8eb995429646fd2e1d"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2a2f686de6ad2c92","typeKey":"ControlledContextMenu_709eba","componentTag":"citry-controlled-context-menu-7c8367a9","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
