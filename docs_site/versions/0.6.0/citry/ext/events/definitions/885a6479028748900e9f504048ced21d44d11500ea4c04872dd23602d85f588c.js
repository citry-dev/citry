(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-command-palette-host",
    "data-citry-command-palette-host": ""
  }, [
    _createElementVNode("dialog", _mergeProps({
      class: "cui-command-palette",
      "data-citry-command-palette-root": "",
      "data-citry-ui-part": "command-palette"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("section", {
        class: "cui-command-palette__surface",
        "data-citry-ui-part": "command-palette-surface"
      }, [
        _createElementVNode("header", {
          class: "cui-command-palette__header",
          "data-citry-ui-part": "command-palette-header"
        }, [
          _createElementVNode("h2", _mergeProps({ "data-citry-ui-part": "command-palette-title" }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText0), 17 /* TEXT, FULL_PROPS */),
          _createElementVNode("button", _mergeProps({
            type: "button",
            "data-citry-command-palette-close": "",
            "data-citry-ui-part": "command-palette-close"
          }, _ctx.$citryPrepared.citryAttrs2), [
            _createElementVNode("span", { "aria-hidden": "true" }, "×")
          ], 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("search", { "data-citry-ui-part": "command-palette-search" }, [
          _createElementVNode("label", _mergeProps({
            class: "cui-command-palette__visually-hidden",
            "data-citry-ui-part": "command-palette-search-label"
          }, _ctx.$citryPrepared.citryAttrs3), [
            _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
          ], 16 /* FULL_PROPS */),
          _withDirectives(_createElementVNode("input", _mergeProps({
            type: "text",
            role: "combobox",
            autocomplete: "off",
            autofocus: "",
            disabled: "",
            "aria-autocomplete": "list",
            "data-citry-ui-part": "command-palette-input"
          }, _ctx.$citryPrepared.citryAttrs4), null, 16 /* FULL_PROPS */), [
            [_directive_citry_vue_owned, ['checked','value']]
          ])
        ]),
        _createElementVNode("div", _mergeProps({
          role: "listbox",
          "data-citry-ui-part": "command-palette-listbox"
        }, _ctx.$citryPrepared.citryAttrs5), [
          _createElementVNode("div", _mergeProps({
            role: "option",
            "aria-selected": "false",
            "data-citry-ui-part": "command-palette-command"
          }, _ctx.$citryPrepared.citryAttrs6), [
            _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs7)), _toDisplayString(_ctx.$citryPrepared.citryText2), 17 /* TEXT, FULL_PROPS */)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("div", _mergeProps({
            role: "option",
            "aria-selected": "false",
            "data-citry-ui-part": "command-palette-command"
          }, _ctx.$citryPrepared.citryAttrs8), [
            _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs9)), _toDisplayString(_ctx.$citryPrepared.citryText3), 17 /* TEXT, FULL_PROPS */)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("div", _mergeProps({
            role: "option",
            "aria-selected": "false",
            "data-citry-ui-part": "command-palette-command"
          }, _ctx.$citryPrepared.citryAttrs10), [
            _createElementVNode("span", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs11)), _toDisplayString(_ctx.$citryPrepared.citryText4), 17 /* TEXT, FULL_PROPS */)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */),
        _createElementVNode("div", {
          hidden: "",
          role: "status",
          "data-citry-command-palette-visual": "",
          "data-citry-ui-part": "command-palette-empty"
        }, [
          (_ctx.$citryPrepared.selectedSlots['citrySlot5d40b05a1c222f74'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot5d40b05a1c222f74", { key: 0 })
            : (_ctx.$citryPrepared.selectedSlots['citrySlot5d40b05a1c222f74'] === 'fallback')
              ? (_openBlock(), _createElementBlock("span", { key: 1 }, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */))
            : _createCommentVNode("v-if", true)
        ])
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["ee5c901680050ef8b1c301f96d351c595c2ce0c62674f15535af3dec51f0757e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, resolveComponent: _resolveComponent, vModelCheckbox: _vModelCheckbox, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_command_palette_dae9e17c = _resolveComponent("citry-c-command-palette-dae9e17c")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("section", { class: "command-palette-actions" }, [
    _createElementVNode("h2", null, "Action transaction"),
    _createElementVNode("div", {
      role: "group",
      "aria-label": "Action behavior"
    }, [
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement5eeaeb98e097d6596262e600f4cad3806870e8d84dc4b7e21b67ae8940817b99",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.throwNext) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.throwNext],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Throw in next action")
      ]),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement3dae2b4181a619308bd48b1a8a070bc34f52b168c63c6f92017372d1da8189fe",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.moveFocus) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.moveFocus],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Move owner focus")
      ])
    ]),
    _createElementVNode("button", {
      ref: "focusTarget",
      id: "command-action-focus-target",
      type: "button"
    }, "Owner focus target", 512 /* NEED_PATCH */),
    (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
      open: _ctx.open,
      onOpenChange: (value,detail)=>{
        _ctx.events.push(`open:${value}:${detail.reason}`);
        _ctx.open=value;
      },
      onQueryChange: (value,detail)=>_ctx.events.push(`query:${value}:${detail.reason}`),
      onAction: (value,detail)=>{
        _ctx.events.push(`action:${value}:${detail.source}:${detail.closeOnAction}`);
        if (_ctx.moveFocus) _ctx.$refs.focusTarget.focus();
        if (_ctx.throwNext) { _ctx.throwNext=false; throw new Error('Application action failed'); }
      },
      "citry-id": _ctx.$citryPrepared.calls.citryCall1324962ae81c7ddc.id,
      key: _ctx.$citryPrepared.calls.citryCall1324962ae81c7ddc.key
    }, null, 8 /* PROPS */, ["open", "onOpenChange", "onQueryChange", "onAction", "citry-id"])),
    _createElementVNode("output", {
      "aria-live": "polite",
      textContent: _toDisplayString(_ctx.events.slice(-4).join(' | ') || 'No actions yet')
    }, " No actions yet ", 8 /* PROPS */, ["textContent"])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3b6b89fb4b866b805873b6bf8fc65f120f5940d6ce07919e03e7f8872080468e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectivee75061b44a79a23c856e0c532cdf60aba26a9eff07970374c9eafb69fbd91a2aD0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirectivee45040b0f678a4ae0637e9bddf7a5ef1eb5b3df5ae49669abbb36f4fd791adb4D0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectivee45040b0f678a4ae0637e9bddf7a5ef1eb5b3df5ae49669abbb36f4fd791adb4","replacementKey":"citryReplacement3dae2b4181a619308bd48b1a8a070bc34f52b168c63c6f92017372d1da8189fe","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirectivee75061b44a79a23c856e0c532cdf60aba26a9eff07970374c9eafb69fbd91a2a","replacementKey":"citryReplacement5eeaeb98e097d6596262e600f4cad3806870e8d84dc4b7e21b67ae8940817b99","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCall1324962ae81c7ddc","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[{"kind":"prop","name":":open","value":"open","sourceStart":495,"sourceEnd":507},{"kind":"prop","name":":onOpenChange","value":"(value,detail)=>{\n        events.push(`open:${value}:${detail.reason}`);\n        open=value;\n      }","sourceStart":508,"sourceEnd":624},{"kind":"prop","name":":onQueryChange","value":"(value,detail)=>events.push(`query:${value}:${detail.reason}`)","sourceStart":625,"sourceEnd":704},{"kind":"prop","name":":onAction","value":"(value,detail)=>{\n        events.push(`action:${value}:${detail.source}:${detail.closeOnAction}`);\n        if (moveFocus) $refs.focusTarget.focus();\n        if (throwNext) { throwNext=false; throw new Error('Application action failed'); }\n      }","sourceStart":705,"sourceEnd":963}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_command_actions_acc1ca52 = _resolveComponent("citry-command-actions-acc1ca52")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_command_actions_acc1ca52, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall8fd6650f7c4877d6.id,
      key: _ctx.$citryPrepared.calls.citryCall8fd6650f7c4877d6.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f9df4559d6dc15aff4a1085290859bead75e5a927c211be74712807120f42a41"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall8fd6650f7c4877d6","typeKey":"CommandActions_f7e0ff","componentTag":"citry-command-actions-acc1ca52","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
