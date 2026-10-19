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
const { resolveDirective: _resolveDirective, resolveComponent: _resolveComponent, vModelSelect: _vModelSelect, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_scroll_area_4c8d5b93 = _resolveComponent("citry-c-scroll-area-4c8d5b93")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "scroll-area-configuration" }, [
    _createElementVNode("div", { class: "scroll-area-configuration__controls" }, [
      _createElementVNode("label", null, [
        _createTextVNode(" Axis "),
        _withDirectives(_createElementVNode("select", {
          key: "citryReplacementc3c8f354528c0e2c33fcdd7a3e039e730b02475068b8f2136f3e387a5a4b63b2",
          "onUpdate:modelValue": $event => ((_ctx.axis) = $event)
        }, [
          _createElementVNode("option", { value: "block" }, "Block"),
          _createElementVNode("option", { value: "inline" }, "Inline"),
          _createElementVNode("option", { value: "both" }, "Both")
        ], 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelSelect, _ctx.axis],
          [_directive_citry_vue_owned, 'selected']
        ])
      ]),
      _createElementVNode("label", null, [
        _createTextVNode(" Scrollbar width "),
        _withDirectives(_createElementVNode("select", {
          key: "citryReplacement80a29038990d5c0b3b2df3b53fc5565c6797713ed13259b8e7878a83ad4b051d",
          "onUpdate:modelValue": $event => ((_ctx.width) = $event)
        }, [
          _createElementVNode("option", { value: "auto" }, "Auto"),
          _createElementVNode("option", { value: "thin" }, "Thin")
        ], 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelSelect, _ctx.width],
          [_directive_citry_vue_owned, 'selected']
        ])
      ]),
      _createElementVNode("label", null, [
        _createTextVNode(" Scrollbar gutter "),
        _withDirectives(_createElementVNode("select", {
          key: "citryReplacementb8b5e2e609381ce80eb170b9c8ccbeb8d4e99f258fce1ade34ccd4473eb81f58",
          "onUpdate:modelValue": $event => ((_ctx.gutter) = $event)
        }, [
          _createElementVNode("option", { value: "auto" }, "Auto"),
          _createElementVNode("option", { value: "stable" }, "Stable"),
          _createElementVNode("option", { value: "stable-both-edges" }, "Both edges")
        ], 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelSelect, _ctx.gutter],
          [_directive_citry_vue_owned, 'selected']
        ])
      ]),
      _createElementVNode("label", null, [
        _createTextVNode(" Overscroll "),
        _withDirectives(_createElementVNode("select", {
          key: "citryReplacement38cefcc3d4f0aa80a5ee6aa5577edca1292102760d8fa73b6e277267c1b1aa5d",
          "onUpdate:modelValue": $event => ((_ctx.overscroll) = $event)
        }, [
          _createElementVNode("option", { value: "auto" }, "Auto"),
          _createElementVNode("option", { value: "contain" }, "Contain"),
          _createElementVNode("option", { value: "none" }, "None")
        ], 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelSelect, _ctx.overscroll],
          [_directive_citry_vue_owned, 'selected']
        ])
      ])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_scroll_area_4c8d5b93, {
      axis: _ctx.axis,
      scrollbarWidth: _ctx.width,
      scrollbarGutter: _ctx.gutter,
      overscroll: _ctx.overscroll,
      "citry-id": _ctx.$citryPrepared.calls.citryCall3dde2c1fe8ea8910.id,
      key: _ctx.$citryPrepared.calls.citryCall3dde2c1fe8ea8910.key
    }, {
      ['citrySlotdbd1d2942e04f334']: _withCtx(() => [
        _createElementVNode("div", { class: "scroll-area-configuration__content" }, [
          _createElementVNode("span", null, "Record 01"),
          _createElementVNode("span", null, "Identity review"),
          _createElementVNode("span", null, "Approved"),
          _createElementVNode("span", null, "Record 02"),
          _createElementVNode("span", null, "Ledger review"),
          _createElementVNode("span", null, "Pending"),
          _createElementVNode("span", null, "Record 03"),
          _createElementVNode("span", null, "Archive review"),
          _createElementVNode("span", null, "Approved"),
          _createElementVNode("span", null, "Record 04"),
          _createElementVNode("span", null, "Search review"),
          _createElementVNode("span", null, "Pending"),
          _createElementVNode("span", null, "Record 05"),
          _createElementVNode("span", null, "Report review"),
          _createElementVNode("span", null, "Approved"),
          _createElementVNode("span", null, "Record 06"),
          _createElementVNode("span", null, "Export review"),
          _createElementVNode("span", null, "Pending")
        ])
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["axis", "scrollbarWidth", "scrollbarGutter", "overscroll", "citry-id"])),
    _createElementVNode("div", { class: "scroll-area-configuration__actions" }, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {_ctx.axis=null;_ctx.width=null;_ctx.gutter=null;_ctx.overscroll=null}
      }, "Release every override", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.axis='diagonal')
      }, " Try an invalid axis ", 8 /* PROPS */, ["onClick"])
    ]),
    _createElementVNode("output", {
      textContent: _toDisplayString(`Requested: ${_ctx.show(_ctx.axis)}, ${_ctx.show(_ctx.width)}, ${_ctx.show(_ctx.gutter)}, ${_ctx.show(_ctx.overscroll)}`)
    }, "Requested: block, auto, auto, auto", 8 /* PROPS */, ["textContent"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["552056bda53ea554cb7988389ed5a4bf12eb210a89f2847e7b1c1658c5a5beff"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectivec4924a21383308aab6a395ea9c0405d653430587326ff2b522385b653b4eacd0D0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirective09a0a78e8716364dfdcb5d23ca6f45b1ce8113ae1b7c9c5b22fc70e2e6dac8ebD0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirectivece46ab410ab7d075e61b8b86cf3bc9df33b320b20bc12da6562a3cf67e60a82dD0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirective43e0e2972f24050993f403dd3f7c6864ccc544f80cefd06817a0fee8160872fbD0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective09a0a78e8716364dfdcb5d23ca6f45b1ce8113ae1b7c9c5b22fc70e2e6dac8eb","replacementKey":"citryReplacement80a29038990d5c0b3b2df3b53fc5565c6797713ed13259b8e7878a83ad4b051d","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirective43e0e2972f24050993f403dd3f7c6864ccc544f80cefd06817a0fee8160872fb","replacementKey":"citryReplacement38cefcc3d4f0aa80a5ee6aa5577edca1292102760d8fa73b6e277267c1b1aa5d","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirectivec4924a21383308aab6a395ea9c0405d653430587326ff2b522385b653b4eacd0","replacementKey":"citryReplacementc3c8f354528c0e2c33fcdd7a3e039e730b02475068b8f2136f3e387a5a4b63b2","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirectivece46ab410ab7d075e61b8b86cf3bc9df33b320b20bc12da6562a3cf67e60a82d","replacementKey":"citryReplacementb8b5e2e609381ce80eb170b9c8ccbeb8d4e99f258fce1ade34ccd4473eb81f58","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall3dde2c1fe8ea8910","typeKey":"CScrollArea_a799e7","componentTag":"citry-c-scroll-area-4c8d5b93","bindings":[{"kind":"prop","name":":axis","value":"axis","sourceStart":1137,"sourceEnd":1149},{"kind":"prop","name":":scrollbarWidth","value":"width","sourceStart":1150,"sourceEnd":1173},{"kind":"prop","name":":scrollbarGutter","value":"gutter","sourceStart":1174,"sourceEnd":1199},{"kind":"prop","name":":overscroll","value":"overscroll","sourceStart":1200,"sourceEnd":1224}],"fills":[{"name":"citrySlotdbd1d2942e04f334","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_scroll_area_configuration_65568c08 = _resolveComponent("citry-scroll-area-configuration-65568c08")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_scroll_area_configuration_65568c08, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall98bfd7884535fa8a.id,
      key: _ctx.$citryPrepared.calls.citryCall98bfd7884535fa8a.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f70f4d21ef0d078722228051504d1a80fce80a24ec43d8c2040cf3c44f5baecc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall98bfd7884535fa8a","typeKey":"ScrollAreaConfiguration_5d36b6","componentTag":"citry-scroll-area-configuration-65568c08","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
