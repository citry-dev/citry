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
    class: "cui-split-button",
    role: "group",
    "data-citry-menu-host": "",
    "data-citry-ui-part": "split-button"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("button", _mergeProps({
      class: "cui-button cui-split-button__primary",
      "data-citry-ui-part": "split-button-primary"
    }, _ctx.$citryPrepared.citryAttrs1), [
      _createElementVNode("span", _mergeProps({
        class: "cui-button__loading",
        "aria-hidden": "true",
        "data-citry-ui-part": "split-button-primary-loading-indicator"
      }, _ctx.$citryPrepared.citryAttrs2), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot8e6c3d3fdbd8f918'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot8e6c3d3fdbd8f918", { key: 0 })
          : (_ctx.$citryPrepared.selectedSlots['citrySlot8e6c3d3fdbd8f918'] === 'fallback')
            ? (_openBlock(), _createElementBlock("span", {
              key: 1,
              class: "cui-button__spinner"
            }))
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("span", {
        class: "cui-button__content",
        "data-citry-ui-part": "split-button-primary-content"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot7be091cc12a38e21'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot7be091cc12a38e21", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */),
    _createElementVNode("button", _mergeProps({
      class: "cui-button cui-split-button__menu-trigger",
      type: "button",
      "aria-haspopup": "menu",
      "data-citry-menu-trigger": "",
      "data-citry-ui-part": "split-button-menu-trigger"
    }, _ctx.$citryPrepared.citryAttrs3), [
      _createElementVNode("span", {
        class: "cui-split-button__indicator",
        "aria-hidden": "true",
        "data-citry-ui-part": "split-button-menu-indicator"
      })
    ], 16 /* FULL_PROPS */),
    (_openBlock(), _createBlock(_component_citry_c_internal_menu_surface_37f82339, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall13ddc2b7f50a2d82.id,
      key: _ctx.$citryPrepared.calls.citryCall13ddc2b7f50a2d82.key
    }, {
      ['citrySlot5176cbf97df342fc']: _withCtx(() => [
        _renderSlot(_ctx.$slots, "citrySlotd19ad2b891ac8270")
      ]),
      _: 3 /* FORWARDED */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a8f617d5b5514d758fa9c23e398919b6c4da9ed6d43700e776e91adb49036eff"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall13ddc2b7f50a2d82","typeKey":"CInternalMenuSurface_597468","componentTag":"citry-c-internal-menu-surface-37f82339","bindings":[],"fills":[{"name":"citrySlot5176cbf97df342fc","localDescendants":[],"localDescendantRuns":[],"slotOutlets":["citrySlotd19ad2b891ac8270"]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, resolveComponent: _resolveComponent, vModelCheckbox: _vModelCheckbox, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_split_button_b0dde971 = _resolveComponent("citry-c-split-button-b0dde971")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "split-button-disabled-demo" }, [
    _createElementVNode("h2", null, "Large specimen image"),
    _createElementVNode("div", {
      class: "split-button-disabled-demo__controls",
      "aria-label": "Split Button state"
    }, [
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement5eeaeb98e097d6596262e600f4cad3806870e8d84dc4b7e21b67ae8940817b99",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.disabled) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.disabled],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Disable both")
      ]),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement3dae2b4181a619308bd48b1a8a070bc34f52b168c63c6f92017372d1da8189fe",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.primaryDisabled) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.primaryDisabled],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Disable primary")
      ]),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacementda032faacefce503400a76a08cd03518890ba130c13147d565ff38a2d0eb4e0a",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.menuDisabled) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.menuDisabled],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Disable Menu")
      ]),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacementbed22c2d7471792e27dd157e09b70594012e7958fa808b9ad610dd5e0b82a211",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.loading) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.loading],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Save pending")
      ])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, _mergeProps({ ref: "split" }, {
      disabled: _ctx.disabled,
      primaryDisabled: _ctx.primaryDisabled,
      menuDisabled: _ctx.menuDisabled,
      loading: _ctx.loading,
      onAction: (value) => _ctx.last = value,
    }, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall696e1cfff1c6147b.id,
      key: _ctx.$citryPrepared.calls.citryCall696e1cfff1c6147b.key
    }), {
      ['citrySlot7be091cc12a38e21']: _withCtx(() => [
        _createTextVNode(" Save image ")
      ]),
      ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall85b7a149f98fcee1.id,
          key: _ctx.$citryPrepared.calls.citryCall85b7a149f98fcee1.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Export TIFF")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall9d0b081cffa3e7af.id,
          key: _ctx.$citryPrepared.calls.citryCall9d0b081cffa3e7af.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Export JPEG")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.last)
    }, "Ready", 8 /* PROPS */, ["textContent"]),
    _createElementVNode("fieldset", { disabled: "" }, [
      _createElementVNode("legend", null, "Disabled fieldset lifecycle"),
      (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall049326216ed81601.id,
        key: _ctx.$citryPrepared.calls.citryCall049326216ed81601.key
      }, {
        ['citrySlot7be091cc12a38e21']: _withCtx(() => [
          _createTextVNode("Save fieldset image")
        ]),
        ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall62e555d06dc67d61.id,
            key: _ctx.$citryPrepared.calls.citryCall62e555d06dc67d61.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Export fieldset image")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["87826498f7fd2c29f1977b8f54215fb23bb960d7b492a86ce75f0cac59981dd8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectivee75061b44a79a23c856e0c532cdf60aba26a9eff07970374c9eafb69fbd91a2aD0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirectivee45040b0f678a4ae0637e9bddf7a5ef1eb5b3df5ae49669abbb36f4fd791adb4D0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirective66e652a3742b7f95459853b94aea57a89d9db7fcd5eaee4cb4cfac7fabea2502D0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirective51c2e82a2393c2df304974fa6ed4ff1468e55ef7bfdaef87fc7c2c51c734d8aeD0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective51c2e82a2393c2df304974fa6ed4ff1468e55ef7bfdaef87fc7c2c51c734d8ae","replacementKey":"citryReplacementbed22c2d7471792e27dd157e09b70594012e7958fa808b9ad610dd5e0b82a211","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirective66e652a3742b7f95459853b94aea57a89d9db7fcd5eaee4cb4cfac7fabea2502","replacementKey":"citryReplacementda032faacefce503400a76a08cd03518890ba130c13147d565ff38a2d0eb4e0a","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirectivee45040b0f678a4ae0637e9bddf7a5ef1eb5b3df5ae49669abbb36f4fd791adb4","replacementKey":"citryReplacement3dae2b4181a619308bd48b1a8a070bc34f52b168c63c6f92017372d1da8189fe","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirectivee75061b44a79a23c856e0c532cdf60aba26a9eff07970374c9eafb69fbd91a2a","replacementKey":"citryReplacement5eeaeb98e097d6596262e600f4cad3806870e8d84dc4b7e21b67ae8940817b99","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall85b7a149f98fcee1","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall9d0b081cffa3e7af","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall696e1cfff1c6147b","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[{"kind":"ref-static","name":"ref","value":"split","sourceStart":639,"sourceEnd":650},{"kind":"props-object","name":"v-bind","value":"{\n      disabled,\n      primaryDisabled,\n      menuDisabled,\n      loading,\n      onAction: (value) => last = value,\n    }","sourceStart":651,"sourceEnd":782}],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCall85b7a149f98fcee1","citryCall9d0b081cffa3e7af"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall62e555d06dc67d61","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall049326216ed81601","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCall62e555d06dc67d61"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_split_button_disabled_and_loading_b523e491 = _resolveComponent("citry-split-button-disabled-and-loading-b523e491")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_split_button_disabled_and_loading_b523e491, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall4a1b37b8db3b1a35.id,
      key: _ctx.$citryPrepared.calls.citryCall4a1b37b8db3b1a35.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["1721cbf5337e992f9bb8a2620f8bea697147a17ac91b11d5af3d4823b8ec8d63"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4a1b37b8db3b1a35","typeKey":"SplitButtonDisabledAndLoading_f3ee22","componentTag":"citry-split-button-disabled-and-loading-b523e491","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
