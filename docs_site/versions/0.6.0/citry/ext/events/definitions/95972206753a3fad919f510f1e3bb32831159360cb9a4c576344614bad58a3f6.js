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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5b90a26d559daa49420a43a53f2857ada1854ae162088658bdea9ea8c59d478c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5d1e4c450c44c708d055c50726f840f493d658d181ebefc26e50c2f022dd5b83"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
        "citry-id": _ctx.$citryPrepared.calls.citryCall52cdd23ef63c8c28.id,
        key: _ctx.$citryPrepared.calls.citryCall52cdd23ef63c8c28.key
      }, null, 8 /* PROPS */, ["onValueChange", "citry-id"])),
      _createElementVNode("output", {
        textContent: _toDisplayString(_ctx.uncontrolledLast)
      }, "Uncontrolled", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Controlled draft"),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        inputValue: _ctx.draft,
        onInputValueChange: (next)=>{
          _ctx.draft=next;
          _ctx.draftLast=`Draft: ${next}`;
        },
        "citry-id": _ctx.$citryPrepared.calls.citryCall77b376217267d647.id,
        key: _ctx.$citryPrepared.calls.citryCall77b376217267d647.key
      }, null, 8 /* PROPS */, ["inputValue", "onInputValueChange", "citry-id"])),
      _createElementVNode("output", {
        textContent: _toDisplayString(_ctx.draftLast)
      }, "Draft owned", 8 /* PROPS */, ["textContent"])
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Controlled tags, uncontrolled draft"),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        value: _ctx.valueTags,
        onValueChange: (next,detail)=>{
          _ctx.valueLast=`Requested ${JSON.stringify(next)}`;
          if (_ctx.accept) _ctx.valueTags=next;
        },
        "citry-id": _ctx.$citryPrepared.calls.citryCall370eb58aa316f570.id,
        key: _ctx.$citryPrepared.calls.citryCall370eb58aa316f570.key
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
        onValueChange: (next,detail)=>{
          _ctx.fullyControlledTags=next;
          _ctx.fullyControlledDraft=detail.nextInputValue || 'owner note';
          _ctx.fullyControlledLast=`Accepted ${JSON.stringify(next)}`;
        },
        onInputValueChange: (next)=>_ctx.fullyControlledDraft=next,
        "citry-id": _ctx.$citryPrepared.calls.citryCall825cd2621c6e477b.id,
        key: _ctx.$citryPrepared.calls.citryCall825cd2621c6e477b.key
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
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["8576666d9625435aebc12d90c7bdc0b3010ed31a14e8c4283feb6a94d1cfbc9f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirective04f82c6cb303971054c5327432cbdbeb7009cae58594bab3b95e8595c1f8698fD0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirective04f82c6cb303971054c5327432cbdbeb7009cae58594bab3b95e8595c1f8698f","replacementKey":"citryReplacementbb48c03292494d4b22e153e6fc82c204c2697e2ea9d28ff94c28d2792b6e41cb","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall52cdd23ef63c8c28","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":onValueChange","value":"(next)=>uncontrolledLast=JSON.stringify(next)","sourceStart":127,"sourceEnd":189}]},{"localId":"citryCall77b376217267d647","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":inputValue","value":"draft","sourceStart":490,"sourceEnd":509},{"kind":"prop","name":":onInputValueChange","value":"(next)=>{\n          draft=next;\n          draftLast=`Draft: ${next}`;\n        }","sourceStart":510,"sourceEnd":611}]},{"localId":"citryCall370eb58aa316f570","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":value","value":"valueTags","sourceStart":923,"sourceEnd":941},{"kind":"prop","name":":onValueChange","value":"(next,detail)=>{\n          valueLast=`Requested ${JSON.stringify(next)}`;\n          if (accept) valueTags=next;\n        }","sourceStart":942,"sourceEnd":1080}]},{"localId":"citryCall825cd2621c6e477b","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"prop","name":":value","value":"fullyControlledTags","sourceStart":1531,"sourceEnd":1559},{"kind":"prop","name":":inputValue","value":"fullyControlledDraft","sourceStart":1560,"sourceEnd":1594},{"kind":"prop","name":":onValueChange","value":"(next,detail)=>{\n          fullyControlledTags=next;\n          fullyControlledDraft=detail.nextInputValue || 'owner note';\n          fullyControlledLast=`Accepted ${JSON.stringify(next)}`;\n        }","sourceStart":1595,"sourceEnd":1810},{"kind":"prop","name":":onInputValueChange","value":"(next)=>fullyControlledDraft=next","sourceStart":1811,"sourceEnd":1866}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_tags_input_axes_7f9fd9a8 = _resolveComponent("citry-controlled-tags-input-axes-7f9fd9a8")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_tags_input_axes_7f9fd9a8, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallcedfc10452bd8457.id,
      key: _ctx.$citryPrepared.calls.citryCallcedfc10452bd8457.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["7ac1173110ef8ea34e4fa271aa0de21d6b447e68bd3faeb14fd33966ca65fe18"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallcedfc10452bd8457","typeKey":"ControlledTagsInputAxes_1063f9","componentTag":"citry-controlled-tags-input-axes-7f9fd9a8","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
