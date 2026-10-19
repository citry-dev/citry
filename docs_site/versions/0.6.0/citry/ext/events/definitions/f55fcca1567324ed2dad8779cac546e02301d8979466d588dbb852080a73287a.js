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
  
  return (_openBlock(), _createElementBlock("section", { class: "command-palette-controlled" }, [
    _createElementVNode("h2", null, "Switch workspace"),
    _createElementVNode("div", {
      role: "group",
      "aria-label": "Controlled palette settings"
    }, [
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement5eeaeb98e097d6596262e600f4cad3806870e8d84dc4b7e21b67ae8940817b99",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.acceptClose) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.acceptClose],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Accept close")
      ]),
      _createElementVNode("label", null, [
        _withDirectives(_createElementVNode("input", {
          key: "citryReplacement3dae2b4181a619308bd48b1a8a070bc34f52b168c63c6f92017372d1da8189fe",
          type: "checkbox",
          "onUpdate:modelValue": $event => ((_ctx.acceptQuery) = $event)
        }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
          [_vModelCheckbox, _ctx.acceptQuery],
          [_directive_citry_vue_owned, 'checked']
        ]),
        _createTextVNode(" Accept query edits")
      ]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.controlOpen=false)
      }, "Release open control", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.controlQuery=false)
      }, "Release query control", 8 /* PROPS */, ["onClick"]),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => {_ctx.controlOpen=true;_ctx.open=true}
      }, "Open from owner", 8 /* PROPS */, ["onClick"])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_command_palette_dae9e17c, {
      open: _ctx.controlOpen ? _ctx.open : null,
      query: _ctx.controlQuery ? _ctx.query : null,
      onOpenChange: (value,detail)=>{
        _ctx.requests.push(`open:${value}:${detail.reason}`);
        if (!_ctx.controlOpen || value || _ctx.acceptClose) _ctx.open=value;
      },
      onQueryChange: (value,detail)=>{
        _ctx.requests.push(`query:${value}:${detail.reason}`);
        if (!_ctx.controlQuery || _ctx.acceptQuery || detail.reason==='close') _ctx.query=value;
      },
      "citry-id": _ctx.$citryPrepared.calls.citryCallc0ac0c0891ddbb6b.id,
      key: _ctx.$citryPrepared.calls.citryCallc0ac0c0891ddbb6b.key
    }, null, 8 /* PROPS */, ["open", "query", "onOpenChange", "onQueryChange", "citry-id"])),
    _createElementVNode("output", { "aria-live": "polite" }, [
      _createTextVNode(" Owner: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.open ? 'open' : 'closed')
      }, "open", 8 /* PROPS */, ["textContent"]),
      _createTextVNode("; query: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.query || 'empty')
      }, "work", 8 /* PROPS */, ["textContent"]),
      _createTextVNode("; requests: "),
      _createElementVNode("span", {
        textContent: _toDisplayString(_ctx.requests.slice(-3).join(' | ') || 'none')
      }, "none", 8 /* PROPS */, ["textContent"])
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["13e422c6794c9ce8668532c12352561df86e1cd9767179dfc8c0b45a95480539"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectivee75061b44a79a23c856e0c532cdf60aba26a9eff07970374c9eafb69fbd91a2aD0","name":"v-model","arg":null,"modifiers":[]},{"siteId":"citryDirectivee45040b0f678a4ae0637e9bddf7a5ef1eb5b3df5ae49669abbb36f4fd791adb4D0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectivee45040b0f678a4ae0637e9bddf7a5ef1eb5b3df5ae49669abbb36f4fd791adb4","replacementKey":"citryReplacement3dae2b4181a619308bd48b1a8a070bc34f52b168c63c6f92017372d1da8189fe","localDescendants":[],"localDescendantRuns":[]},{"siteId":"citryDirectivee75061b44a79a23c856e0c532cdf60aba26a9eff07970374c9eafb69fbd91a2a","replacementKey":"citryReplacement5eeaeb98e097d6596262e600f4cad3806870e8d84dc4b7e21b67ae8940817b99","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[{"localId":"citryCallc0ac0c0891ddbb6b","typeKey":"CCommandPalette_28a050","componentTag":"citry-c-command-palette-dae9e17c","bindings":[{"kind":"prop","name":":open","value":"controlOpen ? open : null","sourceStart":658,"sourceEnd":691},{"kind":"prop","name":":query","value":"controlQuery ? query : null","sourceStart":692,"sourceEnd":728},{"kind":"prop","name":":onOpenChange","value":"(value,detail)=>{\n        requests.push(`open:${value}:${detail.reason}`);\n        if (!controlOpen || value || acceptClose) open=value;\n      }","sourceStart":729,"sourceEnd":889},{"kind":"prop","name":":onQueryChange","value":"(value,detail)=>{\n        requests.push(`query:${value}:${detail.reason}`);\n        if (!controlQuery || acceptQuery || detail.reason==='close') query=value;\n      }","sourceStart":890,"sourceEnd":1072}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_command_palette_e208698d = _resolveComponent("citry-controlled-command-palette-e208698d")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_command_palette_e208698d, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall7d2ecfcf9d24606e.id,
      key: _ctx.$citryPrepared.calls.citryCall7d2ecfcf9d24606e.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3c0acd9c66dea92f359a08632c65f1da7fb80544eb8b4add85a1b0e99e44558a"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7d2ecfcf9d24606e","typeKey":"ControlledCommandPalette_b54960","componentTag":"citry-controlled-command-palette-e208698d","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
