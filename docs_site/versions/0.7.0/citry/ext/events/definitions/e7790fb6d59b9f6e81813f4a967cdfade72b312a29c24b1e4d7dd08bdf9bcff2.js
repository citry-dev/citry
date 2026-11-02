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
            (_ctx.$citryPrepared.selectedSlots['citrySlotbfaa6bc83e1ec860'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotbfaa6bc83e1ec860", { key: 0 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotbfaa6bc83e1ec860'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs2), [
            (_ctx.$citryPrepared.selectedSlots['citrySlote1da6b980bf22d3d'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlote1da6b980bf22d3d", { key: 2 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlote1da6b980bf22d3d'] === 'fallback')
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
            (_ctx.$citryPrepared.selectedSlots['citrySlotec83e1ac9a5c9459'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotec83e1ac9a5c9459", { key: _ctx.$citryPrepared.slotKeys['citrySlotec83e1ac9a5c9459'], key: _ctx.$citryPrepared.slotKeys['citrySlotec83e1ac9a5c9459'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotec83e1ac9a5c9459'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotec83e1ac9a5c9459'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs5), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot9d10365b88801066'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot9d10365b88801066", { key: _ctx.$citryPrepared.slotKeys['citrySlot9d10365b88801066'], key: _ctx.$citryPrepared.slotKeys['citrySlot9d10365b88801066'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot9d10365b88801066'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot9d10365b88801066'] + ':fallback' }, [
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
            (_ctx.$citryPrepared.selectedSlots['citrySlot0d6b985347bc6be4'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot0d6b985347bc6be4", { key: _ctx.$citryPrepared.slotKeys['citrySlot0d6b985347bc6be4'], key: _ctx.$citryPrepared.slotKeys['citrySlot0d6b985347bc6be4'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot0d6b985347bc6be4'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot0d6b985347bc6be4'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs8), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotddaabf35d867f06e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotddaabf35d867f06e", { key: _ctx.$citryPrepared.slotKeys['citrySlotddaabf35d867f06e'], key: _ctx.$citryPrepared.slotKeys['citrySlotddaabf35d867f06e'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotddaabf35d867f06e'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotddaabf35d867f06e'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["8ffc40f36802365c27dd9fb4a26590dc0a6bab82a7c00ff24c5fca82498f7f26"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
        (_ctx.$citryPrepared.selectedSlots['citrySlote55880009f923480'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlote55880009f923480", { key: 0 })
          : _createCommentVNode("v-if", true)
      ], 16 /* FULL_PROPS */),
      _createElementVNode("thead", { "data-citry-ui-part": "header" }, [
        _createElementVNode("tr", { "data-citry-ui-part": "header-row" }, [
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs2), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotbfaa6bc83e1ec860'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotbfaa6bc83e1ec860", { key: 1 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotbfaa6bc83e1ec860'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs3), [
            (_ctx.$citryPrepared.selectedSlots['citrySlote1da6b980bf22d3d'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlote1da6b980bf22d3d", { key: 3 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlote1da6b980bf22d3d'] === 'fallback')
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
            (_ctx.$citryPrepared.selectedSlots['citrySlotec83e1ac9a5c9459'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotec83e1ac9a5c9459", { key: _ctx.$citryPrepared.slotKeys['citrySlotec83e1ac9a5c9459'], key: _ctx.$citryPrepared.slotKeys['citrySlotec83e1ac9a5c9459'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotec83e1ac9a5c9459'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotec83e1ac9a5c9459'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs6), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot9d10365b88801066'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot9d10365b88801066", { key: _ctx.$citryPrepared.slotKeys['citrySlot9d10365b88801066'], key: _ctx.$citryPrepared.slotKeys['citrySlot9d10365b88801066'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot9d10365b88801066'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot9d10365b88801066'] + ':fallback' }, [
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
            (_ctx.$citryPrepared.selectedSlots['citrySlot0d6b985347bc6be4'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot0d6b985347bc6be4", { key: _ctx.$citryPrepared.slotKeys['citrySlot0d6b985347bc6be4'], key: _ctx.$citryPrepared.slotKeys['citrySlot0d6b985347bc6be4'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot0d6b985347bc6be4'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot0d6b985347bc6be4'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs9), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotddaabf35d867f06e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotddaabf35d867f06e", { key: _ctx.$citryPrepared.slotKeys['citrySlotddaabf35d867f06e'], key: _ctx.$citryPrepared.slotKeys['citrySlotddaabf35d867f06e'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotddaabf35d867f06e'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotddaabf35d867f06e'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["501281f049b8a3e7e107c0969f205ec7f3c4c5bdbf603ebf54b54f237c53e19c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
        ['citrySlote55880009f923480']: _withCtx(() => [
          _createTextVNode(" Hover highlights, but never selects, a row. ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["e968a791648defe98a8aec957f2d18ab2e43b43bc8f5ad4238503f5e5bb8aff4"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall1dbed4dfac1faf98","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[]},{"localId":"citryCallf9d0844f0ed86455","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[]},{"localId":"citryCall96bf0f458ffca912","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[]},{"localId":"citryCall540a77f39a15d9d0","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[],"fills":[{"name":"citrySlote55880009f923480","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_table_appearance_213cdf96 = _resolveComponent("citry-table-appearance-213cdf96")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_table_appearance_213cdf96, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallf2ef72ff8ab6dfca.id,
      key: _ctx.$citryPrepared.calls.citryCallf2ef72ff8ab6dfca.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["7107960bee34a2ccdcaac90509b4fda840b4ffdcda56d9ea6b2bd041b9544f3f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallf2ef72ff8ab6dfca","typeKey":"TableAppearance_b45767","componentTag":"citry-table-appearance-213cdf96","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
