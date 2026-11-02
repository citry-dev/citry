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
      ]),
      _withDirectives(_createElementVNode("option", _mergeProps({ selected: "" }, _ctx.$citryPrepared.citryAttrs3), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */), [
        [_directive_citry_vue_owned, 'value']
      ]),
      _withDirectives(_createElementVNode("option", _mergeProps({ selected: "" }, _ctx.$citryPrepared.citryAttrs4), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */), [
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
        }, _ctx.$citryPrepared.citryAttrs5), [
          _createElementVNode("span", { "data-citry-ui-part": "tag-label" }, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            tabindex: "-1",
            "data-citry-ui-part": "remove"
          }, _ctx.$citryPrepared.citryAttrs6), "×", 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("span", _mergeProps({
          class: "cui-tags-input__tag",
          "data-citry-ui-part": "tag"
        }, _ctx.$citryPrepared.citryAttrs7), [
          _createElementVNode("span", { "data-citry-ui-part": "tag-label" }, _toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            tabindex: "-1",
            "data-citry-ui-part": "remove"
          }, _ctx.$citryPrepared.citryAttrs8), "×", 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("span", _mergeProps({
          class: "cui-tags-input__tag",
          "data-citry-ui-part": "tag"
        }, _ctx.$citryPrepared.citryAttrs9), [
          _createElementVNode("span", { "data-citry-ui-part": "tag-label" }, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            tabindex: "-1",
            "data-citry-ui-part": "remove"
          }, _ctx.$citryPrepared.citryAttrs10), "×", 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)
      ]),
      _withDirectives(_createElementVNode("input", _mergeProps({
        class: "cui-tags-input__input",
        type: "text",
        "data-citry-ui-part": "input"
      }, _ctx.$citryPrepared.citryAttrs11), null, 16 /* FULL_PROPS */), [
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
window.__citryRuntimeDefinitions["1d506dbbb4d8a928d085df6c2eeb6209ba4e9f4da273a18190db64e3bc642c88"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_tags_input_9b0c5a93 = _resolveComponent("citry-c-tags-input-9b0c5a93")
  
  return (_openBlock(), _createElementBlock("section", { class: "tags-input-keyboard" }, [
    _createElementVNode("article", null, [
      _createElementVNode("h3", null, "Left-to-right navigation"),
      _createElementVNode("p", null, " At an empty start position, Backspace selects the last tag. Press it again to remove. Arrow keys, Home, End, Delete, and Escape operate while focus stays in the editor. "),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        onFocusin: $event => (_ctx.last='LTR editor focused'),
        onValueChange: (next,detail)=>
          _ctx.last=`${detail.source}: ${JSON.stringify(next)}`,
        "citry-id": _ctx.$citryPrepared.calls.citryCall844281fa17225bd4.id,
        key: _ctx.$citryPrepared.calls.citryCall844281fa17225bd4.key
      }, null, 8 /* PROPS */, ["onFocusin", "onValueChange", "citry-id"]))
    ]),
    _createElementVNode("article", { dir: "rtl" }, [
      _createElementVNode("h3", null, "Right-to-left navigation"),
      _createElementVNode("p", null, "Physical arrows follow the visual row while value order stays stable."),
      (_openBlock(), _createBlock(_component_citry_c_tags_input_9b0c5a93, {
        onFocusin: $event => (_ctx.last='RTL editor focused'),
        "citry-id": _ctx.$citryPrepared.calls.citryCall21b40e22772914fa.id,
        key: _ctx.$citryPrepared.calls.citryCall21b40e22772914fa.key
      }, null, 8 /* PROPS */, ["onFocusin", "citry-id"]))
    ]),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.last)
    }, " Focus an editor to begin ", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["96467710ed86518764ef49ed31da96b0407c89065e5fe6d2cb1ed4349cbc0a7e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall844281fa17225bd4","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"event","name":"@focusin","value":"last='LTR editor focused'","sourceStart":326,"sourceEnd":362},{"kind":"prop","name":":onValueChange","value":"(next,detail)=>\n          last=`${detail.source}: ${JSON.stringify(next)}`","sourceStart":363,"sourceEnd":454}]},{"localId":"citryCall21b40e22772914fa","typeKey":"CTagsInput_0e1d1e","componentTag":"citry-c-tags-input-9b0c5a93","bindings":[{"kind":"event","name":"@focusin","value":"last='RTL editor focused'","sourceStart":794,"sourceEnd":830}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_tags_input_keyboard_and_focus_b26ec7cf = _resolveComponent("citry-tags-input-keyboard-and-focus-b26ec7cf")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_tags_input_keyboard_and_focus_b26ec7cf, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall5fbbbcb5fb5697ae.id,
      key: _ctx.$citryPrepared.calls.citryCall5fbbbcb5fb5697ae.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c2483f98c17721d4db6089c1286f869e325e7d5957a48290c485c6de157822d7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall5fbbbcb5fb5697ae","typeKey":"TagsInputKeyboardAndFocus_dad9db","componentTag":"citry-tags-input-keyboard-and-focus-b26ec7cf","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
