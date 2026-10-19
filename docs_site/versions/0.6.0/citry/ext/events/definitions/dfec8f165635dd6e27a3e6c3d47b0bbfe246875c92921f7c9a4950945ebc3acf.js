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
  
  return (_openBlock(), _createElementBlock("section", { class: "split-button-keyboard-demo" }, [
    _createElementVNode("h2", null, "Keyboard specimen workflow"),
    _createElementVNode("p", null, " Tab reaches the primary and Menu Button in DOM order. Enter or Space activates the focused Button. In the Menu, use arrows, Home, End, typeahead, and Escape. "),
    _createElementVNode("div", { class: "split-button-keyboard-demo__controls" }, [
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement2fc5f34b038a069c69eb0ad92bc6883b72d812a75daaadd92a8ca0933755cf27",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.loading) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.loading],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Primary loading")
      ]),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacementcbfd8391ae10a7f9864dd72b442a0c851cac312b8fe6ea835f50fd086d92ca72",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.primaryDisabled) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.primaryDisabled],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Primary disabled")
      ]),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacementf0bacb641c371798200a787ac9e1fbf04b41825f74c3153abbe559bcc3f3a017",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.menuDisabled) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.menuDisabled],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Menu disabled")
      ])
    ]),
    _createElementVNode("div", {
      class: "split-button-keyboard-demo__row",
      dir: "ltr"
    }, [
      _createElementVNode("span", null, "LTR"),
      (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, _mergeProps({ ref: "ltrSplit" }, {loading: _ctx.loading, primaryDisabled: _ctx.primaryDisabled, menuDisabled: _ctx.menuDisabled}, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall50a11d8ca83347b6.id,
        key: _ctx.$citryPrepared.calls.citryCall50a11d8ca83347b6.key
      }), {
        ['citrySlot7be091cc12a38e21']: _withCtx(() => [
          _createTextVNode("Save field note")
        ]),
        ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall3aaa210e43ec679c.id,
            key: _ctx.$citryPrepared.calls.citryCall3aaa210e43ec679c.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Duplicate note")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallb55605a55a7f5473.id,
            key: _ctx.$citryPrepared.calls.citryCallb55605a55a7f5473.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Export note")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall6755a48bcc628c3d.id,
            key: _ctx.$citryPrepared.calls.citryCall6755a48bcc628c3d.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("Archive note")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1040 /* FULL_PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("div", {
      class: "split-button-keyboard-demo__row",
      dir: "rtl"
    }, [
      _createElementVNode("span", null, "RTL"),
      (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, {
        ref: "rtlSplit",
        "citry-id": _ctx.$citryPrepared.calls.citryCalle50ffa8c70de257e.id,
        key: _ctx.$citryPrepared.calls.citryCalle50ffa8c70de257e.key
      }, {
        ['citrySlot7be091cc12a38e21']: _withCtx(() => [
          _createTextVNode("حفظ ملاحظة العينة")
        ]),
        ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCallb249c66e445ba048.id,
            key: _ctx.$citryPrepared.calls.citryCallb249c66e445ba048.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("نسخ الملاحظة")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall7cf7c4db1ade9262.id,
            key: _ctx.$citryPrepared.calls.citryCall7cf7c4db1ade9262.key
          }, {
            ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
              _createTextVNode("تصدير الملاحظة")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.trace.length ? _ctx.trace.join(' → ') : 'Focus trace is empty')
    }, " Focus trace is empty ", 8 /* PROPS */, ["textContent"]),
    _createElementVNode("button", {
      type: "button",
      onClick: $event => (_ctx.trace=[])
    }, "Clear focus trace", 8 /* PROPS */, ["onClick"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["449261afc030abfd71680cc599399830cae8f33f68b83d8838e9436356fd1972"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective62e8d7656fb12f01e036f80a4355e9d5fcf93c6ddce192dd81fafbdd726afd07D0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirectiveb0d55ab6335942984f9c3a6ddd167622e17cc0e98550e7de2c87454edfba0bacD0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirective27d9636ee97d7e46a2278c0f8bd6b3bc770921b83ecf2cc5e6d8f8b1e76a3428D0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective27d9636ee97d7e46a2278c0f8bd6b3bc770921b83ecf2cc5e6d8f8b1e76a3428","replacementKey":"citryReplacementf0bacb641c371798200a787ac9e1fbf04b41825f74c3153abbe559bcc3f3a017","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirective62e8d7656fb12f01e036f80a4355e9d5fcf93c6ddce192dd81fafbdd726afd07","replacementKey":"citryReplacement2fc5f34b038a069c69eb0ad92bc6883b72d812a75daaadd92a8ca0933755cf27","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirectiveb0d55ab6335942984f9c3a6ddd167622e17cc0e98550e7de2c87454edfba0bac","replacementKey":"citryReplacementcbfd8391ae10a7f9864dd72b442a0c851cac312b8fe6ea835f50fd086d92ca72","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall3aaa210e43ec679c","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb55605a55a7f5473","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6755a48bcc628c3d","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall50a11d8ca83347b6","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[{"kind":"ref-static","name":"ref","value":"ltrSplit","sourceStart":773,"sourceEnd":787},{"kind":"props-object","name":"v-bind","value":"{loading, primaryDisabled, menuDisabled}","sourceStart":788,"sourceEnd":837}],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCall3aaa210e43ec679c","citryCall6755a48bcc628c3d","citryCallb55605a55a7f5473"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb249c66e445ba048","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7cf7c4db1ade9262","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalle50ffa8c70de257e","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[{"kind":"ref-static","name":"ref","value":"rtlSplit","sourceStart":2022,"sourceEnd":2036}],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCall7cf7c4db1ade9262","citryCallb249c66e445ba048"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_split_button_focus_and_keyboard_9b704c37 = _resolveComponent("citry-split-button-focus-and-keyboard-9b704c37")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_split_button_focus_and_keyboard_9b704c37, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall6e54cb58b9dc2a3f.id,
      key: _ctx.$citryPrepared.calls.citryCall6e54cb58b9dc2a3f.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["cb9ac6db8cd61013608fd57417a72f82fddce2d9940e598bc0bced287771b742"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall6e54cb58b9dc2a3f","typeKey":"SplitButtonFocusAndKeyboard_ac1c68","componentTag":"citry-split-button-focus-and-keyboard-9b704c37","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
