(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-table-root",
    "data-citry-ui-part": "root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", {
      class: "cui-table-announcer",
      role: "status",
      "aria-live": "polite",
      "aria-atomic": "true"
    }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
    _createElementVNode("table", {
      class: "cui-table",
      "data-citry-ui-part": "table"
    }, [
      _createElementVNode("caption", _mergeProps({ "data-citry-ui-part": "caption" }, _ctx.$citryPrepared.citryAttrs1), _toDisplayString(_ctx.$citryPrepared.citryText1), 17 /* TEXT, FULL_PROPS */),
      _createElementVNode("thead", { "data-citry-ui-part": "header" }, [
        _createElementVNode("tr", { "data-citry-ui-part": "header-row" }, [
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs2), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotd6a153c162496e8f'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotd6a153c162496e8f", { key: 0 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotd6a153c162496e8f'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ])
      ]),
      _createElementVNode("tbody", { "data-citry-ui-part": "body" }, [
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs3, { key: _ctx.$citryPrepared.citryKey0 }), [
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs4), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot52f119fc369ed4ab", { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'], key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["b3dbeda4dcf2df175c19eb90169ff1997c332a53ccc87dcc0746ba49ae5e3f3c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createBlock: _createBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_table_4c1a3c3a = _resolveComponent("citry-c-table-4c1a3c3a")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-table-root",
    "data-citry-ui-part": "root"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", {
      class: "cui-table-announcer",
      role: "status",
      "aria-live": "polite",
      "aria-atomic": "true"
    }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
    _createElementVNode("table", {
      class: "cui-table",
      "data-citry-ui-part": "table"
    }, [
      _createElementVNode("caption", _mergeProps({ "data-citry-ui-part": "caption" }, _ctx.$citryPrepared.citryAttrs1), [
        (_ctx.$citryPrepared.selectedSlots['citrySlot30ca1818c630188d'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot30ca1818c630188d", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("thead", { "data-citry-ui-part": "header" }, [
        _createElementVNode("tr", { "data-citry-ui-part": "header-row" }, [
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs2), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotd6a153c162496e8f'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotd6a153c162496e8f", { key: 1 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotd6a153c162496e8f'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs3), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot4ed6faa8110a9126'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot4ed6faa8110a9126", { key: 3 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot4ed6faa8110a9126'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 4 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs4), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot587d0a45e58fcb72'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot587d0a45e58fcb72", { key: 5 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot587d0a45e58fcb72'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 6 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ])
      ]),
      _createElementVNode("tbody", { "data-citry-ui-part": "body" }, [
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs5, { key: _ctx.$citryPrepared.citryKey0 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs6), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotdde491840ab91039'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotdde491840ab91039", { key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'], key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotdde491840ab91039'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs7), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot52f119fc369ed4ab", { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'], key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs8), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot4a218bd5d5fd80e3'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot4a218bd5d5fd80e3", { key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'], key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot4a218bd5d5fd80e3'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs9, { key: _ctx.$citryPrepared.citryKey1 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs10), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot26986917026e6110'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot26986917026e6110", { key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'], key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot26986917026e6110'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs11), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot99631f867f035ec7'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot99631f867f035ec7", { key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'], key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot99631f867f035ec7'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText8), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs12), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotf8a3c42ec2ab8b3d'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotf8a3c42ec2ab8b3d", { key: _ctx.$citryPrepared.slotKeys['citrySlotf8a3c42ec2ab8b3d'], key: _ctx.$citryPrepared.slotKeys['citrySlotf8a3c42ec2ab8b3d'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotf8a3c42ec2ab8b3d'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotf8a3c42ec2ab8b3d'] + ':fallback' }, [
                  (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
                    "citry-id": _ctx.$citryPrepared.calls.citryCall4f4140e4be517705.id,
                    key: _ctx.$citryPrepared.calls.citryCall4f4140e4be517705.key
                  }, null, 8 /* PROPS */, ["citry-id"]))
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["5d3fb37118fc59492b7f362e7983923f78bf815ca88d899b04e1eaaeb235f020"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4f4140e4be517705","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_table_4c1a3c3a = _resolveComponent("citry-c-table-4c1a3c3a")
  
  return (_openBlock(), _createElementBlock("section", {
    class: "table-environment",
    dir: "rtl"
  }, [
    _createElementVNode("h2", null, "أسماء النجوم"),
    (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallbbc8fd5f4c7febc0.id,
      key: _ctx.$citryPrepared.calls.citryCallbbc8fd5f4c7febc0.key
    }, {
      ['citrySlot30ca1818c630188d']: _withCtx(() => [
        _createTextVNode(" أسماء عربية وتقليدية للنجوم ")
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1f7b09edd9fb4e8a3cd3d3efe03d04c18168334f142b920284224843fe02927"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallbbc8fd5f4c7febc0","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[],"fills":[{"name":"citrySlot30ca1818c630188d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_table_environment_a8b98a42 = _resolveComponent("citry-table-environment-a8b98a42")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_table_environment_a8b98a42, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall8527b346f579a019.id,
      key: _ctx.$citryPrepared.calls.citryCall8527b346f579a019.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["694168289b7c1c1c6dc37daa934b883c6dead78c3c57c82317c2d8ab530fd4da"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall8527b346f579a019","typeKey":"TableEnvironment_f73c3b","componentTag":"citry-table-environment-a8b98a42","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
