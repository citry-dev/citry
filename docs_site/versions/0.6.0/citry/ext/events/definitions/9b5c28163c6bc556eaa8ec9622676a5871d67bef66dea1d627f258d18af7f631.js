(function(Vue){
const { toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, normalizeProps: _normalizeProps, guardReactiveProps: _guardReactiveProps, openBlock: _openBlock, createElementBlock: _createElementBlock, Fragment: _Fragment, createCommentVNode: _createCommentVNode, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-data-grid",
    "data-citry-ui-part": "data-grid"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("span", {
      role: "status",
      "aria-live": "polite",
      "aria-atomic": "true",
      "data-citry-ui-part": "status"
    }),
    _createElementVNode("div", _mergeProps({ "data-citry-ui-part": "viewport" }, _ctx.$citryPrepared.citryAttrs1), [
      _createElementVNode("table", _mergeProps({
        role: "grid",
        "data-citry-ui-part": "table"
      }, _ctx.$citryPrepared.citryAttrs2), [
        _createElementVNode("colgroup", null, [
          _createElementVNode("col", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs3)), null, 16 /* FULL_PROPS */),
          _createElementVNode("col", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs4)), null, 16 /* FULL_PROPS */),
          _createElementVNode("col", _normalizeProps(_guardReactiveProps(_ctx.$citryPrepared.citryAttrs5)), null, 16 /* FULL_PROPS */)
        ]),
        _createElementVNode("thead", { "data-citry-ui-part": "header" }, [
          _createElementVNode("tr", {
            "aria-rowindex": "1",
            "data-citry-ui-part": "header-row"
          }, [
            _createElementVNode("th", _mergeProps({
              tabindex: "-1",
              "data-citry-ui-part": "header-cell"
            }, _ctx.$citryPrepared.citryAttrs6), [
              (_ctx.$citryPrepared.selectedSlots['citrySlote9e4c0cdfe46d6b7'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlote9e4c0cdfe46d6b7", { key: 0 })
                : (_ctx.$citryPrepared.selectedSlots['citrySlote9e4c0cdfe46d6b7'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true),
              _createElementVNode("span", {
                "aria-hidden": "true",
                "data-citry-ui-part": "sort-indicator"
              }, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("th", _mergeProps({
              tabindex: "-1",
              "data-citry-ui-part": "header-cell"
            }, _ctx.$citryPrepared.citryAttrs7), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot0600ea03159b47e6'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot0600ea03159b47e6", { key: 2 })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot0600ea03159b47e6'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 3 }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true),
              _createElementVNode("span", {
                "aria-hidden": "true",
                "data-citry-ui-part": "sort-indicator"
              }, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("th", _mergeProps({
              tabindex: "-1",
              "data-citry-ui-part": "header-cell"
            }, _ctx.$citryPrepared.citryAttrs8), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot6ceb137e36276fe5'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot6ceb137e36276fe5", { key: 4 })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot6ceb137e36276fe5'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 5 }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true),
              _createElementVNode("span", {
                "aria-hidden": "true",
                "data-citry-ui-part": "sort-indicator"
              }, _toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
            ], 16 /* FULL_PROPS */)
          ])
        ]),
        _createElementVNode("tbody", { "data-citry-ui-part": "body" }, [
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs9, { key: _ctx.$citryPrepared.citryKey0 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs10), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotbb4dc4491645aedf'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotbb4dc4491645aedf", { key: _ctx.$citryPrepared.slotKeys['citrySlotbb4dc4491645aedf'], key: _ctx.$citryPrepared.slotKeys['citrySlotbb4dc4491645aedf'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotbb4dc4491645aedf'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotbb4dc4491645aedf'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs11), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotaecdd83b8f109700'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotaecdd83b8f109700", { key: _ctx.$citryPrepared.slotKeys['citrySlotaecdd83b8f109700'], key: _ctx.$citryPrepared.slotKeys['citrySlotaecdd83b8f109700'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotaecdd83b8f109700'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotaecdd83b8f109700'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs12), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot0960743a4f3182ab'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot0960743a4f3182ab", { key: _ctx.$citryPrepared.slotKeys['citrySlot0960743a4f3182ab'], key: _ctx.$citryPrepared.slotKeys['citrySlot0960743a4f3182ab'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot0960743a4f3182ab'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot0960743a4f3182ab'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText8), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs13, { key: _ctx.$citryPrepared.citryKey1 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs14), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot815b6002637c36e7'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot815b6002637c36e7", { key: _ctx.$citryPrepared.slotKeys['citrySlot815b6002637c36e7'], key: _ctx.$citryPrepared.slotKeys['citrySlot815b6002637c36e7'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot815b6002637c36e7'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot815b6002637c36e7'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs15), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot7d3c09a5d377da35'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot7d3c09a5d377da35", { key: _ctx.$citryPrepared.slotKeys['citrySlot7d3c09a5d377da35'], key: _ctx.$citryPrepared.slotKeys['citrySlot7d3c09a5d377da35'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot7d3c09a5d377da35'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot7d3c09a5d377da35'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText10), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs16), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotc1bdb38a0e1f6f40'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotc1bdb38a0e1f6f40", { key: _ctx.$citryPrepared.slotKeys['citrySlotc1bdb38a0e1f6f40'], key: _ctx.$citryPrepared.slotKeys['citrySlotc1bdb38a0e1f6f40'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotc1bdb38a0e1f6f40'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotc1bdb38a0e1f6f40'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText11), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs17, { key: _ctx.$citryPrepared.citryKey2 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs18), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot0e0aa64f818778f2'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot0e0aa64f818778f2", { key: _ctx.$citryPrepared.slotKeys['citrySlot0e0aa64f818778f2'], key: _ctx.$citryPrepared.slotKeys['citrySlot0e0aa64f818778f2'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot0e0aa64f818778f2'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot0e0aa64f818778f2'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText12), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs19), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot31f09c90c67e7604'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot31f09c90c67e7604", { key: _ctx.$citryPrepared.slotKeys['citrySlot31f09c90c67e7604'], key: _ctx.$citryPrepared.slotKeys['citrySlot31f09c90c67e7604'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot31f09c90c67e7604'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot31f09c90c67e7604'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText13), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs20), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot0593c8872997859e'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot0593c8872997859e", { key: _ctx.$citryPrepared.slotKeys['citrySlot0593c8872997859e'], key: _ctx.$citryPrepared.slotKeys['citrySlot0593c8872997859e'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot0593c8872997859e'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot0593c8872997859e'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText14), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */))
        ])
      ], 16 /* FULL_PROPS */)
    ], 16 /* FULL_PROPS */)
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["3cde2b7b80ff1fab962834e9923da70e2df9715c00bc95c6ac1a2fa0edf5a63e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_data_grid_674331b8 = _resolveComponent("citry-c-data-grid-674331b8")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.notice)
    }, "Activate a sortable header or select a row", 8 /* PROPS */, ["textContent"]),
    (_openBlock(), _createBlock(_component_citry_c_data_grid_674331b8, {
      sort: _ctx.sort,
      onSortChange: (next)=>{
        _ctx.sort=next;
        _ctx.notice=next.length
          ? `Sorted: ${next.map((item,index)=>`${index + 1}. ${item.key} ${item.direction}`).join(', ')}`
          : 'Server row order restored';
      },
      onSelectionChange: (selected)=>_ctx.notice=`Selected: ${selected.join(', ') || 'none'}`,
      "citry-id": _ctx.$citryPrepared.calls.citryCall4946bf834b5429b4.id,
      key: _ctx.$citryPrepared.calls.citryCall4946bf834b5429b4.key
    }, null, 8 /* PROPS */, ["sort", "onSortChange", "onSelectionChange", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["c1eaccbe1a5914b154161087029d677f6e40801c5844051d36ec190c924c96dc"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall4946bf834b5429b4","typeKey":"CDataGrid_52b9be","componentTag":"citry-c-data-grid-674331b8","bindings":[{"kind":"prop","name":":sort","value":"sort","sourceStart":119,"sourceEnd":131},{"kind":"prop","name":":onSortChange","value":"(next)=>{\n        sort=next;\n        notice=next.length\n          ? `Sorted: ${next.map((item,index)=>`${index + 1}. ${item.key} ${item.direction}`).join(', ')}`\n          : 'Server row order restored';\n      }","sourceStart":132,"sourceEnd":358},{"kind":"prop","name":":onSelectionChange","value":"(selected)=>notice=`Selected: ${selected.join(', ') || 'none'}`","sourceStart":359,"sourceEnd":443}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_data_grid_sorting_selection_1178b668 = _resolveComponent("citry-data-grid-sorting-selection-1178b668")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_data_grid_sorting_selection_1178b668, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallfee162aa4adf7a98.id,
      key: _ctx.$citryPrepared.calls.citryCallfee162aa4adf7a98.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["a3f2d3f809fd93ca068cf564d33d04815a99c7a10070496ef59049f91bea517f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallfee162aa4adf7a98","typeKey":"DataGridSortingSelection_8b46a1","componentTag":"citry-data-grid-sorting-selection-1178b668","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
