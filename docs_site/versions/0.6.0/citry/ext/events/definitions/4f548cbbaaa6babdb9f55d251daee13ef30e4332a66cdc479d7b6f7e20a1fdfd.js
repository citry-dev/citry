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
      _createElementVNode("thead", { "data-citry-ui-part": "header" }, [
        _createElementVNode("tr", { "data-citry-ui-part": "header-row" }, [
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs1), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotd6a153c162496e8f'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotd6a153c162496e8f", { key: 0 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotd6a153c162496e8f'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs2), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot4ed6faa8110a9126'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot4ed6faa8110a9126", { key: 2 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot4ed6faa8110a9126'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 3 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ])
      ]),
      _createElementVNode("tbody", { "data-citry-ui-part": "body" }, [
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs3, { key: _ctx.$citryPrepared.citryKey0 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs4), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotdde491840ab91039'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotdde491840ab91039", { key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'], key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotdde491840ab91039'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs5), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot52f119fc369ed4ab", { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'], key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs6, { key: _ctx.$citryPrepared.citryKey1 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs7), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot26986917026e6110'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot26986917026e6110", { key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'], key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot26986917026e6110'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'] + ':fallback' }, [
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
        ], 16 /* FULL_PROPS */))
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c6ebfdd32a9cc7d4469563dc9b7305120d67c11bd75070c8c326c54400ad4979"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

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
          ], 16 /* FULL_PROPS */)
        ])
      ]),
      _createElementVNode("tbody", { "data-citry-ui-part": "body" }, [
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs4, { key: _ctx.$citryPrepared.citryKey0 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs5), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotdde491840ab91039'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotdde491840ab91039", { key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'], key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotdde491840ab91039'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs6), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot52f119fc369ed4ab", { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'], key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs7, { key: _ctx.$citryPrepared.citryKey1 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs8), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot26986917026e6110'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot26986917026e6110", { key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'], key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot26986917026e6110'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs9), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot4a218bd5d5fd80e3'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot4a218bd5d5fd80e3", { key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'], key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot4a218bd5d5fd80e3'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["82b7525929dd064b00a46d71c76504291fa06ef258282b69a1146c2be4a21515"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_table_4c1a3c3a = _resolveComponent("citry-c-table-4c1a3c3a")
  
  return (_openBlock(), _createElementBlock("section", { class: "table-appearance" }, [
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, "Line · comfortable"),
      (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall1dbed4dfac1faf98.id,
        key: _ctx.$citryPrepared.calls.citryCall1dbed4dfac1faf98.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, "Outline · compact"),
      (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallf9d0844f0ed86455.id,
        key: _ctx.$citryPrepared.calls.citryCallf9d0844f0ed86455.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, "Striped · default"),
      (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall96bf0f458ffca912.id,
        key: _ctx.$citryPrepared.calls.citryCall96bf0f458ffca912.key
      }, null, 8 /* PROPS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, "Hover · bottom caption"),
      (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall540a77f39a15d9d0.id,
        key: _ctx.$citryPrepared.calls.citryCall540a77f39a15d9d0.key
      }, {
        ['citrySlot30ca1818c630188d']: _withCtx(() => [
          _createTextVNode(" Hover highlights, but never selects, a row. ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["fc77b8a56e2fdd7e3c84a149d7c12c30d810adcf9dbcc88b75789abe8ab88d58"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1dbed4dfac1faf98","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[]},{"localId":"citryCallf9d0844f0ed86455","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[]},{"localId":"citryCall96bf0f458ffca912","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[]},{"localId":"citryCall540a77f39a15d9d0","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[],"fills":[{"name":"citrySlot30ca1818c630188d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_table_appearance_608af14c = _resolveComponent("citry-table-appearance-608af14c")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_table_appearance_608af14c, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalld19bdead4673b86d.id,
      key: _ctx.$citryPrepared.calls.citryCalld19bdead4673b86d.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["94e9020919fe006543fba76e78fbdefada985f9ec1d8b0d483af54e172c99d7e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalld19bdead4673b86d","typeKey":"TableAppearance_215622","componentTag":"citry-table-appearance-608af14c","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
