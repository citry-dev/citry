(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("citry-dynamic-f8cf9dbc03e1c4e7", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs0)), [
    _createElementVNode("span", _mergeProps({
      class: "cui-button__loading",
      "aria-hidden": "true",
      "data-citry-ui-part": "loading-indicator"
    }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotb7a5d3c5d10a90ea", { key: 0 })
        : (_ctx.$citryPrepared.selectedSlots['citrySlotb7a5d3c5d10a90ea'] === 'fallback')
          ? (_openBlock(), _createElementBlock("span", {
            key: 1,
            class: "cui-button__spinner"
          }))
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("span", {
      class: "cui-button__content",
      "data-citry-ui-part": "content"
    }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f0d8fda3d3bfb1f'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f0d8fda3d3bfb1f", { key: 2 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1db84ab0869cd4eff3aa136033c0ded1b33d1f09a37939b8a7465799de6baca"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([{"alias":"citry-dynamic-f8cf9dbc03e1c4e7","tag":"button","sourceStart":1,"sourceEnd":69}]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("form", _mergeProps({
    ref: "root",
    class: "cui-form",
    "data-citry-ui-part": "form"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("fieldset", {
      class: "cui-form__fieldset",
      "data-citry-ui-part": "fieldset"
    }, [
      _createElementVNode("legend", {
        hidden: "",
        "aria-hidden": "true"
      }),
      (_ctx.$citryPrepared.selectedSlots['citrySlotf39a0a3e8a179bdf'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlotf39a0a3e8a179bdf", { key: 0 })
        : _createCommentVNode("v-if", true)
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["81a1fc957f2a8755f8ce082405e4e351c8f4f04f20700087e02025fa7a4b1a92"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, vModelText: _vModelText, withDirectives: _withDirectives, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createTextVNode: _createTextVNode, renderList: _renderList, withCtx: _withCtx, vShow: _vShow } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_button_ff3c7a5d = _resolveComponent("citry-c-button-ff3c7a5d")
  const _component_citry_c_form_54ae8704 = _resolveComponent("citry-c-form-54ae8704")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "filter-sequence" }, [
    _createElementVNode("header", null, [
      _createElementVNode("p", null, "Filter wheel"),
      _createElementVNode("h2", null, "Build an exposure sequence")
    ]),
    (_openBlock(), _createBlock(_component_citry_c_form_54ae8704, {
      onSubmit: _withModifiers($event => (_ctx.result = JSON.stringify(new window.FormData($event.target).getAll('filter'))), ["prevent"]),
      "citry-id": _ctx.$citryPrepared.calls.citryCallb8e94a87a0c59e52.id,
      key: _ctx.$citryPrepared.calls.citryCallb8e94a87a0c59e52.key
    }, {
      ['citrySlotf39a0a3e8a179bdf']: _withCtx(() => [
        _createElementVNode("div", { class: "filter-sequence__rows" }, [
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_ctx.rows, (row, index) => {
            return (_openBlock(), _createElementBlock("div", {
              key: row.id,
              class: "filter-sequence__row"
            }, [
              _createElementVNode("label", {
                for: `filter-${row.id}`,
                textContent: _toDisplayString(`Exposure ${index + 1}`)
              }, null, 8 /* PROPS */, ["for", "textContent"]),
              _withDirectives(_createElementVNode("input", {
                key: "citryReplacement6fd9b5c236988d42c3cd3e6358549ec995072000eaaec540f95e0a5e1fb3d31b",
                id: `filter-${row.id}`,
                name: "filter",
                "onUpdate:modelValue": $event => ((row.value) = $event)
              }, null, 8 /* PROPS */, ["id", "onUpdate:modelValue"]), [
                [_vModelText, row.value],
                [_directive_citry_vue_owned, ['checked','value']]
              ]),
              _createElementVNode("button", {
                type: "button",
                onClick: $event => (_ctx.rows.splice(index, 1))
              }, "Remove", 8 /* PROPS */, ["onClick"])
            ]))
          }), 128 /* KEYED_FRAGMENT */))
        ]),
        _createElementVNode("div", { class: "filter-sequence__actions" }, [
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            onClick: $event => (_ctx.rows.push({ id: _ctx.nextId++, value: 'New filter' })),
            "citry-id": _ctx.$citryPrepared.calls.citryCalla97d42711dd50bd6.id,
            key: _ctx.$citryPrepared.calls.citryCalla97d42711dd50bd6.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Add exposure ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            onClick: $event => (_ctx.rows.length > 1 && _ctx.rows.unshift(_ctx.rows.pop())),
            "citry-id": _ctx.$citryPrepared.calls.citryCall38b3c06201606a23.id,
            key: _ctx.$citryPrepared.calls.citryCall38b3c06201606a23.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Rotate order ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onClick", "citry-id"])),
          (_openBlock(), _createBlock(_component_citry_c_button_ff3c7a5d, {
            "citry-id": _ctx.$citryPrepared.calls.citryCall19e583cf13667fe9.id,
            key: _ctx.$citryPrepared.calls.citryCall19e583cf13667fe9.key
          }, {
            ['citrySlot6f0d8fda3d3bfb1f']: _withCtx(() => [
              _createTextVNode(" Read FormData ")
            ]),
            _: 2 /* DYNAMIC */
          }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["onSubmit", "citry-id"])),
    _withDirectives(_createElementVNode("output", {
      key: "citryReplacement07a221808124d3108a33b8c05f549f279b10d2dbbdeee0cdea619d03960a4f55",
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.result)
    }, null, 8 /* PROPS */, ["textContent"]), [
      [_vShow, _ctx.result]
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9324878847930779aee12a08e3a9f55c281c7ef05623b197c0dcb1adeb6d5981"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective44b982d8485d6bf34136ff09ebee5255d18aa508cb2e8211ca88ca6f87c2adc8D1","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirective32b0174664de45efad0b963cd28d5815e10b44b301eb95514243172afde1c3a2D0","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective32b0174664de45efad0b963cd28d5815e10b44b301eb95514243172afde1c3a2","replacementKey":"citryReplacement07a221808124d3108a33b8c05f549f279b10d2dbbdeee0cdea619d03960a4f55","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirective44b982d8485d6bf34136ff09ebee5255d18aa508cb2e8211ca88ca6f87c2adc8","replacementKey":"citryReplacement6fd9b5c236988d42c3cd3e6358549ec995072000eaaec540f95e0a5e1fb3d31b","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCalla97d42711dd50bd6","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"rows.push({ id: nextId++, value: 'New filter' })","sourceStart":953,"sourceEnd":1010}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall38b3c06201606a23","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[{"kind":"event","name":"@click","value":"rows.length > 1 && rows.unshift(rows.pop())","sourceStart":1275,"sourceEnd":1327}],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall19e583cf13667fe9","typeKey":"CButton_353146","componentTag":"citry-c-button-ff3c7a5d","bindings":[],"fills":[{"name":"citrySlot6f0d8fda3d3bfb1f","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallb8e94a87a0c59e52","typeKey":"CForm_4a6900","componentTag":"citry-c-form-54ae8704","bindings":[{"kind":"event","name":"@submit.prevent","value":"result = JSON.stringify(new window.FormData($event.target).getAll('filter'))","sourceStart":148,"sourceEnd":242}],"fills":[{"name":"citrySlotf39a0a3e8a179bdf","localDescendants":["citryCall19e583cf13667fe9","citryCall38b3c06201606a23","citryCalla97d42711dd50bd6"],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_filter_sequence_42dd62a4 = _resolveComponent("citry-filter-sequence-42dd62a4")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_filter_sequence_42dd62a4, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld7aa931fd9d9b241.id,
      key: _ctx.$citryPrepared.calls.citryCalld7aa931fd9d9b241.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f314fba602b1f18e9476b5bdecebfd08b2fe4338a9a3cb850bec272228207994"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld7aa931fd9d9b241","typeKey":"FilterSequence_4395b6","componentTag":"citry-filter-sequence-42dd62a4","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
