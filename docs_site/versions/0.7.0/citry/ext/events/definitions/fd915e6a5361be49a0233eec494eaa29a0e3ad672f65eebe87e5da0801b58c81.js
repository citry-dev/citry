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
              (_ctx.$citryPrepared.selectedSlots['citrySlotf3f6a9c55ca4d958'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotf3f6a9c55ca4d958", { key: 0 })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotf3f6a9c55ca4d958'] === 'fallback')
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
              (_ctx.$citryPrepared.selectedSlots['citrySlot212f0c3e14afbc14'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot212f0c3e14afbc14", { key: 2 })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot212f0c3e14afbc14'] === 'fallback')
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
              (_ctx.$citryPrepared.selectedSlots['citrySlotcf969a672fdfc3c6'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotcf969a672fdfc3c6", { key: 4 })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotcf969a672fdfc3c6'] === 'fallback')
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
              (_ctx.$citryPrepared.selectedSlots['citrySlot3c92fc7e65074401'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot3c92fc7e65074401", { key: _ctx.$citryPrepared.slotKeys['citrySlot3c92fc7e65074401'], key: _ctx.$citryPrepared.slotKeys['citrySlot3c92fc7e65074401'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot3c92fc7e65074401'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot3c92fc7e65074401'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs11), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot677c6900256bbfb8'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot677c6900256bbfb8", { key: _ctx.$citryPrepared.slotKeys['citrySlot677c6900256bbfb8'], key: _ctx.$citryPrepared.slotKeys['citrySlot677c6900256bbfb8'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot677c6900256bbfb8'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot677c6900256bbfb8'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs12), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot4959e252211328d0'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot4959e252211328d0", { key: _ctx.$citryPrepared.slotKeys['citrySlot4959e252211328d0'], key: _ctx.$citryPrepared.slotKeys['citrySlot4959e252211328d0'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot4959e252211328d0'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4959e252211328d0'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText8), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs13, { key: _ctx.$citryPrepared.citryKey1 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs14), [
              (_ctx.$citryPrepared.selectedSlots['citrySlota2ea17de35f5d0a5'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlota2ea17de35f5d0a5", { key: _ctx.$citryPrepared.slotKeys['citrySlota2ea17de35f5d0a5'], key: _ctx.$citryPrepared.slotKeys['citrySlota2ea17de35f5d0a5'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlota2ea17de35f5d0a5'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlota2ea17de35f5d0a5'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs15), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot743acc591a049368'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot743acc591a049368", { key: _ctx.$citryPrepared.slotKeys['citrySlot743acc591a049368'], key: _ctx.$citryPrepared.slotKeys['citrySlot743acc591a049368'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot743acc591a049368'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot743acc591a049368'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText10), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs16), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot45f81948e1f13334'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot45f81948e1f13334", { key: _ctx.$citryPrepared.slotKeys['citrySlot45f81948e1f13334'], key: _ctx.$citryPrepared.slotKeys['citrySlot45f81948e1f13334'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot45f81948e1f13334'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot45f81948e1f13334'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText11), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs17, { key: _ctx.$citryPrepared.citryKey2 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs18), [
              (_ctx.$citryPrepared.selectedSlots['citrySlota00de8ab24e36821'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlota00de8ab24e36821", { key: _ctx.$citryPrepared.slotKeys['citrySlota00de8ab24e36821'], key: _ctx.$citryPrepared.slotKeys['citrySlota00de8ab24e36821'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlota00de8ab24e36821'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlota00de8ab24e36821'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText12), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs19), [
              (_ctx.$citryPrepared.selectedSlots['citrySlote4a80b719c0f8e5e'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlote4a80b719c0f8e5e", { key: _ctx.$citryPrepared.slotKeys['citrySlote4a80b719c0f8e5e'], key: _ctx.$citryPrepared.slotKeys['citrySlote4a80b719c0f8e5e'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlote4a80b719c0f8e5e'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlote4a80b719c0f8e5e'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText13), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs20), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot80812943235d2d83'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot80812943235d2d83", { key: _ctx.$citryPrepared.slotKeys['citrySlot80812943235d2d83'], key: _ctx.$citryPrepared.slotKeys['citrySlot80812943235d2d83'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot80812943235d2d83'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot80812943235d2d83'] + ':fallback' }, [
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
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["e7351d6b50212225da2b878ee85df73fd7626137bc2e240b49352af5d9592838"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
      onSortChange: _ctx.applySort,
      onSelectionChange: (selected)=>_ctx.notice=`Selected: ${selected.join(', ') || 'none'}`,
      "citry-id": _ctx.$citryPrepared.calls.citryCall380f176871c98420.id,
      key: _ctx.$citryPrepared.calls.citryCall380f176871c98420.key
    }, null, 8 /* PROPS */, ["sort", "onSortChange", "onSelectionChange", "citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2468adff8370228c95b5ef855aeaeead2b998c58acddc5b3f3f7710a858d3b41"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall380f176871c98420","typeKey":"CDataGrid_52b9be","componentTag":"citry-c-data-grid-674331b8","bindings":[{"kind":"prop","name":":sort","value":"sort","sourceStart":119,"sourceEnd":131},{"kind":"prop","name":":onSortChange","value":"applySort","sourceStart":132,"sourceEnd":157},{"kind":"prop","name":":onSelectionChange","value":"(selected)=>notice=`Selected: ${selected.join(', ') || 'none'}`","sourceStart":158,"sourceEnd":242}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_data_grid_sorting_selection_3d6b3323 = _resolveComponent("citry-data-grid-sorting-selection-3d6b3323")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_data_grid_sorting_selection_3d6b3323, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall147b22aea4cb5bb4.id,
      key: _ctx.$citryPrepared.calls.citryCall147b22aea4cb5bb4.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["43e4fe26c0ece7052628ae877e15dda99b7f0ca5fc7d35ec27967ec8a2e0d297"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall147b22aea4cb5bb4","typeKey":"DataGridSortingSelection_d300c0","componentTag":"citry-data-grid-sorting-selection-3d6b3323","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
