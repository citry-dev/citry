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
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs10, { key: _ctx.$citryPrepared.citryKey2 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs11), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot0e9e4e34e563e862'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot0e9e4e34e563e862", { key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'], key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot0e9e4e34e563e862'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs12), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot99631f867f035ec7'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot99631f867f035ec7", { key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'], key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot99631f867f035ec7'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText8), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ]),
      _createElementVNode("tfoot", { "data-citry-ui-part": "footer" }, [
        _createElementVNode("tr", { "data-citry-ui-part": "footer-row" }, [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "footer-cell"
          }, _ctx.$citryPrepared.citryAttrs13), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotec9272da58628bee'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotec9272da58628bee", { key: 17 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotec9272da58628bee'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 18 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "footer-cell" }, _ctx.$citryPrepared.citryAttrs14), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot78eb0132e077960e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot78eb0132e077960e", { key: 19 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot78eb0132e077960e'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 20 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText10), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ])
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["cd85f40187c331e1e0c20c9ada4a1f08a290be90379fb369558bf57de75fb811"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_table_4c1a3c3a = _resolveComponent("citry-c-table-4c1a3c3a")
  
  return (_openBlock(), _createElementBlock("section", { class: "observatory-tables" }, [
    _createElementVNode("article", { class: "observatory-tables__night" }, [
      _createElementVNode("h2", null, "Night observation"),
      (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall50e872d3b5955aee.id,
        key: _ctx.$citryPrepared.calls.citryCall50e872d3b5955aee.key
      }, {
        ['citrySlot30ca1818c630188d']: _withCtx(() => [
          _createTextVNode(" Winter sky ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", { class: "observatory-tables__day" }, [
      _createElementVNode("h2", null, "Solar observation"),
      (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall7579708be02a0121.id,
        key: _ctx.$citryPrepared.calls.citryCall7579708be02a0121.key
      }, {
        ['citrySlot30ca1818c630188d']: _withCtx(() => [
          _createTextVNode(" Daylight calibration ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["73b8c250d38238e64223b16590b73aaa9481f985f7536812cf87ee1764b3a600"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall50e872d3b5955aee","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[],"fills":[{"name":"citrySlot30ca1818c630188d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCall7579708be02a0121","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[],"fills":[{"name":"citrySlot30ca1818c630188d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_observatory_tables_3714a523 = _resolveComponent("citry-observatory-tables-3714a523")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_observatory_tables_3714a523, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall437d877e59a4739c.id,
      key: _ctx.$citryPrepared.calls.citryCall437d877e59a4739c.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["7776e55b861854b6363676c6751a313d3529a8eff6e34f8c3e825cf0e4bb8c48"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall437d877e59a4739c","typeKey":"ObservatoryTables_b7b452","componentTag":"citry-observatory-tables-3714a523","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
