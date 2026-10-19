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
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs13, { key: _ctx.$citryPrepared.citryKey2 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs14), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot0e9e4e34e563e862'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot0e9e4e34e563e862", { key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'], key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot0e9e4e34e563e862'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText10), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs15), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot337dc8f15fb8787e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot337dc8f15fb8787e", { key: _ctx.$citryPrepared.slotKeys['citrySlot337dc8f15fb8787e'], key: _ctx.$citryPrepared.slotKeys['citrySlot337dc8f15fb8787e'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot337dc8f15fb8787e'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot337dc8f15fb8787e'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText11), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs16), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot72a484a29980908d'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot72a484a29980908d", { key: _ctx.$citryPrepared.slotKeys['citrySlot72a484a29980908d'], key: _ctx.$citryPrepared.slotKeys['citrySlot72a484a29980908d'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot72a484a29980908d'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot72a484a29980908d'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText12), 1 /* TEXT */)
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
          }, _ctx.$citryPrepared.citryAttrs17), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot27ef2fcc7067d7bf'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot27ef2fcc7067d7bf", { key: 25 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "footer-cell" }, _ctx.$citryPrepared.citryAttrs18), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotbcfeeb7e5b64201e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotbcfeeb7e5b64201e", { key: 26 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "footer-cell" }, _ctx.$citryPrepared.citryAttrs19), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotade72a00d45d8822'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotade72a00d45d8822", { key: 27 })
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ])
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6b48ba3ef6fa18bb0071e43ae29bcc0d8b0670ff28a32413f0da01360ac5343c"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_table_4c1a3c3a = _resolveComponent("citry-c-table-4c1a3c3a")
  
  return (_openBlock(), _createElementBlock("section", { class: "survey-totals" }, [
    (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall878a158c418d9d9b.id,
      key: _ctx.$citryPrepared.calls.citryCall878a158c418d9d9b.key
    }, {
      ['citrySlot30ca1818c630188d']: _withCtx(() => [
        _createTextVNode(" Telescope survey time ")
      ]),
      ['citrySlot27ef2fcc7067d7bf']: _withCtx(() => [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */)
      ]),
      ['citrySlotbcfeeb7e5b64201e']: _withCtx(() => [
        _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
      ]),
      ['citrySlotade72a00d45d8822']: _withCtx(() => [
        _createElementVNode("strong", null, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */)
      ]),
      _: 2 /* DYNAMIC */
    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["cfe2d7c1d35fd8f457270db51f886874d457b2576870522c57aae6ac791562a7"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall878a158c418d9d9b","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[],"fills":[{"name":"citrySlot27ef2fcc7067d7bf","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot30ca1818c630188d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotade72a00d45d8822","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlotbcfeeb7e5b64201e","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_survey_totals_cbd6fa18 = _resolveComponent("citry-survey-totals-cbd6fa18")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_survey_totals_cbd6fa18, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall107473fb94a719d3.id,
      key: _ctx.$citryPrepared.calls.citryCall107473fb94a719d3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["f4ecd62515dca3b08615a1d37f55550ebcaacf8c02cb0b5d21b6aa7160177bde"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall107473fb94a719d3","typeKey":"SurveyTotals_e468d2","componentTag":"citry-survey-totals-cbd6fa18","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
