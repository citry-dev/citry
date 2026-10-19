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
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, vModelSelect: _vModelSelect, withDirectives: _withDirectives, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_menu_item_a0d45c0d = _resolveComponent("citry-c-menu-item-a0d45c0d")
  const _component_citry_c_split_button_b0dde971 = _resolveComponent("citry-c-split-button-b0dde971")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "split-button-forms" }, [
    _createElementVNode("form", {
      id: "accession-form",
      ref: "accession",
      onSubmit: _withModifiers($event => (
      _ctx.result = `Submitted ${new window.FormData($event.target, $event.submitter).get('action')}`
    ), ["prevent"]),
      onReset: $event => (window.setTimeout(() => _ctx.result = 'Reset accession', 0))
    }, [
      _createElementVNode("label", null, [
        _createTextVNode(" Accession name "),
        _createElementVNode("input", {
          name: "specimen",
          value: "Alpine gentian",
          required: ""
        })
      ]),
      _createElementVNode("div", { class: "split-button-forms__actions" }, [
        (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall713a15e977cb8d7b.id,
          key: _ctx.$citryPrepared.calls.citryCall713a15e977cb8d7b.key
        }, {
          ['citrySlot7be091cc12a38e21']: _withCtx(() => [
            _createTextVNode("Commit accession")
          ]),
          ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall52ca1fe93e458590.id,
              key: _ctx.$citryPrepared.calls.citryCall52ca1fe93e458590.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode(" Export draft ")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
        (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall118efd34a6f9ef70.id,
          key: _ctx.$citryPrepared.calls.citryCall118efd34a6f9ef70.key
        }, {
          ['citrySlot7be091cc12a38e21']: _withCtx(() => [
            _createTextVNode("Reset accession")
          ]),
          ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
            (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
              "citry-id": _ctx.$citryPrepared.calls.citryCalld35efd7c94de3eb6.id,
              key: _ctx.$citryPrepared.calls.citryCalld35efd7c94de3eb6.key
            }, {
              ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
                _createTextVNode(" Restore saved snapshot ")
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ])
    ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit", "onReset"]),
    _createElementVNode("form", {
      id: "secondary-accession-form",
      onSubmit: _withModifiers($event => (
      _ctx.result = `Submitted to secondary Form with ${$event.submitter.value}`
    ), ["prevent"])
    }, [
      _createElementVNode("label", null, [
        _createTextVNode(" Secondary accession "),
        _createElementVNode("input", {
          name: "secondary-specimen",
          value: "Sea thrift",
          required: ""
        })
      ])
    ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit"]),
    _createElementVNode("label", null, [
      _createTextVNode(" External primary Form owner "),
      _withDirectives(_createElementVNode("select", {
        key: "citryReplacementa63e25dc16c908b2ecb078a197cda6b36ebbdc161b13da559df93eccd25a551f",
        "onUpdate:modelValue": $event => ((_ctx.owner) = $event)
      }, [
        _createElementVNode("option", { value: "accession-form" }, "Main accession Form"),
        _createElementVNode("option", { value: "secondary-accession-form" }, "Secondary accession Form")
      ], 8 /* PROPS */, ["onUpdate:modelValue"]), [
        [_vModelSelect, _ctx.owner],
        [_directive_citry_vue_owned, 'selected']
      ])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_split_button_b0dde971, {
      ref: "externalSplit",
      "citry-id": _ctx.$citryPrepared.calls.citryCalla5ce506aeb4d3163.id,
      key: _ctx.$citryPrepared.calls.citryCalla5ce506aeb4d3163.key
    }, {
      ['citrySlot7be091cc12a38e21']: _withCtx(() => [
        _createTextVNode("Commit from outside")
      ]),
      ['citrySlotd19ad2b891ac8270']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_menu_item_a0d45c0d, {
          "citry-id": _ctx.$citryPrepared.calls.citryCall6dd64d7d459dcd5e.id,
          key: _ctx.$citryPrepared.calls.citryCall6dd64d7d459dcd5e.key
        }, {
          ['citrySlotf1817a57bc1354a1']: _withCtx(() => [
            _createTextVNode("Download draft")
          ]),
          _: 2 /* DYNAMIC */
        }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("button", {
      type: "button",
      onClick: $event => (
      window.document.getElementById(_ctx.owner).requestSubmit(
        window.document.getElementById('external-commit-actions-primary')
      )
    )
    }, " Request native submit ", 8 /* PROPS */, ["onClick"]),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.result)
    }, "No Form action yet", 8 /* PROPS */, ["textContent"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["e5fbbae43c18f5600e4765c60cfdaa40fade57fc2bbb98140cb40c2f1317869e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective807d46472fe50d5170dafdbad300926b67094b1b0def8d870ed6d8e7811a6a15D0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective807d46472fe50d5170dafdbad300926b67094b1b0def8d870ed6d8e7811a6a15","replacementKey":"citryReplacementa63e25dc16c908b2ecb078a197cda6b36ebbdc161b13da559df93eccd25a551f","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall52ca1fe93e458590","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall713a15e977cb8d7b","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCall52ca1fe93e458590"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalld35efd7c94de3eb6","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall118efd34a6f9ef70","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCalld35efd7c94de3eb6"],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall6dd64d7d459dcd5e","typeKey":"CMenuItem_202543","componentTag":"citry-c-menu-item-a0d45c0d","bindings":[],"fills":[{"name":"citrySlotf1817a57bc1354a1","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCalla5ce506aeb4d3163","typeKey":"CSplitButton_a10749","componentTag":"citry-c-split-button-b0dde971","bindings":[{"kind":"ref-static","name":"ref","value":"externalSplit","sourceStart":2258,"sourceEnd":2277}],"fills":[{"name":"citrySlot7be091cc12a38e21","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotd19ad2b891ac8270","localDescendants":["citryCall6dd64d7d459dcd5e"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_split_button_forms_82d68e6c = _resolveComponent("citry-split-button-forms-82d68e6c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_split_button_forms_82d68e6c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall9dda978848e94620.id,
      key: _ctx.$citryPrepared.calls.citryCall9dda978848e94620.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["4e993eb365bd4803d9b1a02fdb3b1728a099b87e328b3e8727e69c154ecf1185"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall9dda978848e94620","typeKey":"SplitButtonForms_3a5448","componentTag":"citry-split-button-forms-82d68e6c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
