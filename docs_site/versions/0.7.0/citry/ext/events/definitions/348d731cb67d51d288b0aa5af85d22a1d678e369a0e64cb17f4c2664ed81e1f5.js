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
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

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
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
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
      }),
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-tags-input__input",
        type: "text",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */), [
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
window.__citryRuntimeDefinitions["e4ca9baac44aa76a4da9d2292fda412de880ef780c5517852522886f9960aa26"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, resolveDirective: _resolveDirective, vModelCheckbox: _vModelCheckbox, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_tags_input_9b0c5a93 = _resolveComponent("citry-c-tags-input-9b0c5a93")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "tags-input-controlled" }, [
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Uncontrolled tags and draft"),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        onValueChange: (next)=>_ctx.uncontrolledLast=JSON.stringify(next),
        "citry-id": _ctx.$citryPrepared.calls.citryCalla941ec15d9e761bd.id,
        key: _ctx.$citryPrepared.calls.citryCalla941ec15d9e761bd.key
      }, null, 8 /* PROPS */, ["onValueChange", "citry-id"])),
      _createElementVNode("output", {
        textContent: _toDisplayString(_ctx.uncontrolledLast)
      }, "Uncontrolled", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Controlled draft"),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        inputValue: _ctx.draft,
        onInputValueChange: _ctx.updateDraft,
        "citry-id": _ctx.$citryPrepared.calls.citryCall2fcda9c890ebe23b.id,
        key: _ctx.$citryPrepared.calls.citryCall2fcda9c890ebe23b.key
      }, null, 8 /* PROPS */, ["inputValue", "onInputValueChange", "citry-id"])),
      _createElementVNode("output", {
        textContent: _toDisplayString(_ctx.draftLast)
      }, "Draft owned", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Controlled tags, uncontrolled draft"),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        value: _ctx.valueTags,
        onValueChange: _ctx.applyValueRequest,
        "citry-id": _ctx.$citryPrepared.calls.citryCalldde865a6f24dc52c.id,
        key: _ctx.$citryPrepared.calls.citryCalldde865a6f24dc52c.key
      }, null, 8 /* PROPS */, ["value", "onValueChange", "citry-id"])),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacementbb48c03292494d4b22e153e6fc82c204c2697e2ea9d28ff94c28d2792b6e41cb",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.accept) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.accept],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Accept the next value request ")
      ]),
      _createElementVNode("output", {
        textContent: _toDisplayString(_ctx.valueLast)
      }, "Value request not sent", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Controlled tags and draft"),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        value: _ctx.fullyControlledTags,
        inputValue: _ctx.fullyControlledDraft,
        onValueChange: _ctx.acceptFullyControlledTags,
        onInputValueChange: (next)=>_ctx.fullyControlledDraft=next,
        "citry-id": _ctx.$citryPrepared.calls.citryCall81db5cbfbd66aaf6.id,
        key: _ctx.$citryPrepared.calls.citryCall81db5cbfbd66aaf6.key
      }, null, 8 /* PROPS */, ["value", "inputValue", "onValueChange", "onInputValueChange", "citry-id"])),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.fullyControlledTags=['owner','ordered'])
      }, " Replace tags from the owner ", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("output", {
        textContent: _toDisplayString(_ctx.fullyControlledLast)
      }, "Both axes owned", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["ef7a62481a243a2897ace2938c5e992dda8b37d96e0ed0a5c931199fdd5dd364"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective04f82c6cb303971054c5327432cbdbeb7009cae58594bab3b95e8595c1f8698fD0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective04f82c6cb303971054c5327432cbdbeb7009cae58594bab3b95e8595c1f8698f","replacementKey":"citryReplacementbb48c03292494d4b22e153e6fc82c204c2697e2ea9d28ff94c28d2792b6e41cb","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCalla941ec15d9e761bd","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":onValueChange","value":"(next)=>uncontrolledLast=JSON.stringify(next)","sourceStart":127,"sourceEnd":189}]},{"localId":"citryCall2fcda9c890ebe23b","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":inputValue","value":"draft","sourceStart":490,"sourceEnd":509},{"kind":"prop","name":":onInputValueChange","value":"updateDraft","sourceStart":510,"sourceEnd":543}]},{"localId":"citryCalldde865a6f24dc52c","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":value","value":"valueTags","sourceStart":855,"sourceEnd":873},{"kind":"prop","name":":onValueChange","value":"applyValueRequest","sourceStart":874,"sourceEnd":908}]},{"localId":"citryCall81db5cbfbd66aaf6","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":value","value":"fullyControlledTags","sourceStart":1359,"sourceEnd":1387},{"kind":"prop","name":":inputValue","value":"fullyControlledDraft","sourceStart":1388,"sourceEnd":1422},{"kind":"prop","name":":onValueChange","value":"acceptFullyControlledTags","sourceStart":1423,"sourceEnd":1465},{"kind":"prop","name":":onInputValueChange","value":"(next)=>fullyControlledDraft=next","sourceStart":1466,"sourceEnd":1521}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_tags_input_axes_a2b47eec = _resolveComponent("citry-controlled-tags-input-axes-a2b47eec")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_tags_input_axes_a2b47eec, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallb652b5cfc0eb3f71.id,
      key: _ctx.$citryPrepared.calls.citryCallb652b5cfc0eb3f71.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["00c44535204fcef19c928a7bd909711f014a6e2036e68add2c8490f7dbef499c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallb652b5cfc0eb3f71","typeKey":"ControlledTagsInputAxes_b81a36","componentTag":"citry-controlled-tags-input-axes-a2b47eec","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
