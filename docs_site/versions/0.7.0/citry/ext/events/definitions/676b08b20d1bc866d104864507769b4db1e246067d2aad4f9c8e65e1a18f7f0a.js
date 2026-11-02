(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-tags-input",
    "data-citry-ui-part": "tags-input"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("select", _mergeProps({
      class: "cui-tags-input__native",
      multiple: "",
      "data-citry-tags-input-native": ""
    }, _ctx.$citryPrepared.citryAttrs1), [
      _withDirectives(_createElementVNode("option", _mergeProps({ selected: "" }, _ctx.$citryPrepared.citryAttrs2), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */), [
        [_directive_citry_vue_owned, 'value']
      ])
    ], 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, []]
    ]),
    _createElementVNode("div", {
      class: "cui-tags-input__control",
      hidden: "",
      "data-citry-ui-part": "control"
    }, [
      _createElementVNode("span", {
        class: "cui-tags-input__tag-list",
        "data-citry-ui-part": "tag-list"
      }, [
        _createElementVNode("span", _mergeProps({
          class: "cui-tags-input__tag",
          "data-citry-ui-part": "tag"
        }, _ctx.$citryPrepared.citryAttrs3), [
          _createElementVNode("span", { "data-citry-ui-part": "tag-label" }, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            tabindex: "-1",
            "data-citry-ui-part": "remove"
          }, _ctx.$citryPrepared.citryAttrs4), "×", 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)
      ]),
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-tags-input__input",
        type: "text",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs5), null, 16 /* FULL_PROPS */), [
        [_directive_citry_vue_owned, ['checked','value']]
      ])
    ]),
    _createElementVNode("span", {
      hidden: "",
      "data-citry-tags-input-readonly-values": ""
    }),
    _createElementVNode("span", {
      class: "cui-tags-input__status cui-form-control__status",
      role: "status",
      "aria-live": "polite",
      "aria-atomic": "true",
      "data-citry-ui-part": "status"
    })
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0fb0352dda88fcecb8423f3ed91e911d89b000f500098b4e3ff2977bd9abb0c8"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-field",
    "data-citry-field-root": "",
    "data-citry-ui-part": "field"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("label", _mergeProps({ "data-citry-ui-part": "label" }, _ctx.$citryPrepared.citryAttrs1), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote2526e6f745e4169'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote2526e6f745e4169", { key: 0 })
        : _createCommentVNode("v-if", true),
      _createElementVNode("span", _mergeProps({
        class: "cui-field__required",
        "aria-hidden": "true",
        "data-citry-ui-part": "required-indicator"
      }, _ctx.$citryPrepared.citryAttrs2), " * ", 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", { "data-citry-ui-part": "control" }, [
      (_ctx.$citryPrepared.selectedSlots['citrySlot6f90e269deb4619c'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlot6f90e269deb4619c", { key: 1 })
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "description" }, _ctx.$citryPrepared.citryAttrs3), [
      (_ctx.$citryPrepared.selectedSlots['citrySlote7646b39489ca911'] === 'supplied')
        ? _renderSlot(_ctx.$slots, "citrySlote7646b39489ca911", { key: 2 })
        : _createCommentVNode("v-if", true)
    ], 16 /* FULL_PROPS */),
    _createElementVNode("div", _mergeProps({
      "aria-live": "polite",
      "data-citry-ui-part": "error"
    }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a5c3b89119e24e0edb50b0c4d8146aa09a3101e367fac6a368ec0e1841947dcf"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx, vShow: _vShow } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_tags_input_9b0c5a93 = _resolveComponent("citry-c-tags-input-9b0c5a93")
  const _component_citry_c_field_862570d8 = _resolveComponent("citry-c-field-862570d8")
  
  return (_openBlock(), _createElementBlock("section", { class: "tags-input-paste" }, [
    (_openBlock(), _createBlock(_component_citry_c_field_862570d8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalldb159210e56046c1.id,
      key: _ctx.$citryPrepared.calls.citryCalldb159210e56046c1.key
    }, {
      ['citrySlote2526e6f745e4169']: _withCtx(() => [
        _createTextVNode("Survey regions")
      ]),
      ['citrySlot6f90e269deb4619c']: _withCtx(() => [
        (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
          onCompositionstart: $event => {_ctx.composing=true;_ctx.last='Composition started'},
          onCompositionend: $event => {_ctx.composing=false;_ctx.last='Composition ended'},
          onPaste: $event => (_ctx.last='Paste received'),
          onValueChange: (next,detail)=>
                  _ctx.last=`${detail.source}: ${JSON.stringify(next)}`,
          onValueInvalid: (reason,detail)=>
                  _ctx.last=`Rejected ${reason}: ${detail.candidate || 'batch'}`,
          "citry-id": _ctx.$citryPrepared.calls.citryCalld11924a9d5eb0b7e.id,
          key: _ctx.$citryPrepared.calls.citryCalld11924a9d5eb0b7e.key
        }, null, 8 /* PROPS */, ["onCompositionstart", "onCompositionend", "onPaste", "onValueChange", "onValueInvalid", "citry-id"]))
      ]),
      ['citrySlote7646b39489ca911']: _withCtx(() => [
        _createTextVNode(" Comma, semicolon, and a pasted newline separate regions. At most five tags are accepted. ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"])),
    _createElementVNode("div", { class: "tags-input-paste__sample" }, [
      _createElementVNode("p", null, "Try replacing selected draft text with:"),
      _createElementVNode("pre", null, "coast,forest;wetland\nharbor")
    ]),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.last)
    }, " Paste or compose in the editor ", 8 /* PROPS */, ["textContent"]),
    _withDirectives(_createElementVNode("p", { key: "citryReplacement2b00dbad8710e20ecb9e964057377cb48493d20273de0d964142bef1e101d1a2" }, "The input method editor owns Enter and delimiters.", 512 /* NEED_PATCH */), [
      [_vShow, _ctx.composing]
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["9a39034cc2b2056b75f4ca4d142f95af8b5833240f9595880ee63df84f0141dd"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective5541ec178ad9b6927a9e4553f859eab610a2070c2d6151779e315f0dd9ecfeccD0","name":"v-show","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective5541ec178ad9b6927a9e4553f859eab610a2070c2d6151779e315f0dd9ecfecc","replacementKey":"citryReplacement2b00dbad8710e20ecb9e964057377cb48493d20273de0d964142bef1e101d1a2","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCalld11924a9d5eb0b7e","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"event","name":"@compositionstart","value":"composing=true;last='Composition started'","sourceStart":355,"sourceEnd":416},{"kind":"event","name":"@compositionend","value":"composing=false;last='Composition ended'","sourceStart":417,"sourceEnd":475},{"kind":"event","name":"@paste","value":"last='Paste received'","sourceStart":476,"sourceEnd":506},{"kind":"prop","name":":onValueChange","value":"(next,detail)=>\n                  last=`${detail.source}: ${JSON.stringify(next)}`","sourceStart":507,"sourceEnd":606},{"kind":"prop","name":":onValueInvalid","value":"(reason,detail)=>\n                  last=`Rejected ${reason}: ${detail.candidate || 'batch'}`","sourceStart":607,"sourceEnd":718}]},{"localId":"citryCalldb159210e56046c1","typeKey":"CField_81c723","componentTag":"citry-c-field-862570d8","bindings":[],"fills":[{"name":"citrySlot6f90e269deb4619c","localDescendants":["citryCalld11924a9d5eb0b7e"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote2526e6f745e4169","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlote7646b39489ca911","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tags_input_paste_and_ime_b3038388 = _resolveComponent("citry-tags-input-paste-and-ime-b3038388")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tags_input_paste_and_ime_b3038388, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall2b0d40cd6bffded3.id,
      key: _ctx.$citryPrepared.calls.citryCall2b0d40cd6bffded3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["286f856ef54bf16b9bd90dd5020559760dd4443b637987c7ee68d21f4069ece3"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2b0d40cd6bffded3","typeKey":"TagsInputPasteAndIme_13eb6c","componentTag":"citry-tags-input-paste-and-ime-b3038388","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
