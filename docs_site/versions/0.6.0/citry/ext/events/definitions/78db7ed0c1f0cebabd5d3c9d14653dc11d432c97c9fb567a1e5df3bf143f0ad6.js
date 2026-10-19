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
          ], 16 /* FULL_PROPS */),
          _createElementVNode("th", _mergeProps({
            scope: "col",
            "data-citry-ui-part": "header-cell"
          }, _ctx.$citryPrepared.citryAttrs5), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotbe066a0a25702c00'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotbe066a0a25702c00", { key: 7 })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotbe066a0a25702c00'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: 8 }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText4), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ])
      ]),
      _createElementVNode("tbody", { "data-citry-ui-part": "body" }, [
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs6, { key: _ctx.$citryPrepared.citryKey0 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs7), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotdde491840ab91039'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotdde491840ab91039", { key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'], key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotdde491840ab91039'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotdde491840ab91039'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText5), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs8), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot52f119fc369ed4ab", { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'], key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot52f119fc369ed4ab'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot52f119fc369ed4ab'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText6), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs9), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot4a218bd5d5fd80e3'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot4a218bd5d5fd80e3", { key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'], key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot4a218bd5d5fd80e3'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4a218bd5d5fd80e3'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText7), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs10), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot99631f867f035ec7'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot99631f867f035ec7", { key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'], key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot99631f867f035ec7'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot99631f867f035ec7'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText8), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs11, { key: _ctx.$citryPrepared.citryKey1 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs12), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot26986917026e6110'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot26986917026e6110", { key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'], key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot26986917026e6110'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot26986917026e6110'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText9), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs13), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotf8a3c42ec2ab8b3d'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotf8a3c42ec2ab8b3d", { key: _ctx.$citryPrepared.slotKeys['citrySlotf8a3c42ec2ab8b3d'], key: _ctx.$citryPrepared.slotKeys['citrySlotf8a3c42ec2ab8b3d'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotf8a3c42ec2ab8b3d'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotf8a3c42ec2ab8b3d'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText10), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs14), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot337dc8f15fb8787e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot337dc8f15fb8787e", { key: _ctx.$citryPrepared.slotKeys['citrySlot337dc8f15fb8787e'], key: _ctx.$citryPrepared.slotKeys['citrySlot337dc8f15fb8787e'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot337dc8f15fb8787e'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot337dc8f15fb8787e'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText11), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs15), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot72a484a29980908d'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot72a484a29980908d", { key: _ctx.$citryPrepared.slotKeys['citrySlot72a484a29980908d'], key: _ctx.$citryPrepared.slotKeys['citrySlot72a484a29980908d'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot72a484a29980908d'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot72a484a29980908d'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText12), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs16, { key: _ctx.$citryPrepared.citryKey2 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs17), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot0e9e4e34e563e862'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot0e9e4e34e563e862", { key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'], key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot0e9e4e34e563e862'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot0e9e4e34e563e862'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText13), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs18), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot4cb2c5c68e406dac'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot4cb2c5c68e406dac", { key: _ctx.$citryPrepared.slotKeys['citrySlot4cb2c5c68e406dac'], key: _ctx.$citryPrepared.slotKeys['citrySlot4cb2c5c68e406dac'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot4cb2c5c68e406dac'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4cb2c5c68e406dac'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText14), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs19), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot6152d5a35abad0ad'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot6152d5a35abad0ad", { key: _ctx.$citryPrepared.slotKeys['citrySlot6152d5a35abad0ad'], key: _ctx.$citryPrepared.slotKeys['citrySlot6152d5a35abad0ad'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot6152d5a35abad0ad'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot6152d5a35abad0ad'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText15), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs20), [
            (_ctx.$citryPrepared.selectedSlots['citrySlote2be512662875056'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlote2be512662875056", { key: _ctx.$citryPrepared.slotKeys['citrySlote2be512662875056'], key: _ctx.$citryPrepared.slotKeys['citrySlote2be512662875056'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlote2be512662875056'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlote2be512662875056'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText16), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs21, { key: _ctx.$citryPrepared.citryKey3 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs22), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotc3655592e1c40cc9'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotc3655592e1c40cc9", { key: _ctx.$citryPrepared.slotKeys['citrySlotc3655592e1c40cc9'], key: _ctx.$citryPrepared.slotKeys['citrySlotc3655592e1c40cc9'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotc3655592e1c40cc9'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotc3655592e1c40cc9'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText17), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs23), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot6fc03e1b2842742d'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot6fc03e1b2842742d", { key: _ctx.$citryPrepared.slotKeys['citrySlot6fc03e1b2842742d'], key: _ctx.$citryPrepared.slotKeys['citrySlot6fc03e1b2842742d'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot6fc03e1b2842742d'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot6fc03e1b2842742d'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText18), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs24), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot1d2bb71d977c6462'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot1d2bb71d977c6462", { key: _ctx.$citryPrepared.slotKeys['citrySlot1d2bb71d977c6462'], key: _ctx.$citryPrepared.slotKeys['citrySlot1d2bb71d977c6462'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot1d2bb71d977c6462'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot1d2bb71d977c6462'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText19), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs25), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot305344e44ddf802e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot305344e44ddf802e", { key: _ctx.$citryPrepared.slotKeys['citrySlot305344e44ddf802e'], key: _ctx.$citryPrepared.slotKeys['citrySlot305344e44ddf802e'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot305344e44ddf802e'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot305344e44ddf802e'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText20), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs26, { key: _ctx.$citryPrepared.citryKey4 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs27), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot293bf28dda8ac4af'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot293bf28dda8ac4af", { key: _ctx.$citryPrepared.slotKeys['citrySlot293bf28dda8ac4af'], key: _ctx.$citryPrepared.slotKeys['citrySlot293bf28dda8ac4af'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot293bf28dda8ac4af'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot293bf28dda8ac4af'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText21), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs28), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot9d5e9ef3f1c48e45'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot9d5e9ef3f1c48e45", { key: _ctx.$citryPrepared.slotKeys['citrySlot9d5e9ef3f1c48e45'], key: _ctx.$citryPrepared.slotKeys['citrySlot9d5e9ef3f1c48e45'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot9d5e9ef3f1c48e45'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot9d5e9ef3f1c48e45'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText22), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs29), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot26353455ba7d6822'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot26353455ba7d6822", { key: _ctx.$citryPrepared.slotKeys['citrySlot26353455ba7d6822'], key: _ctx.$citryPrepared.slotKeys['citrySlot26353455ba7d6822'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot26353455ba7d6822'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot26353455ba7d6822'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText23), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs30), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot01d68fea81ec9098'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot01d68fea81ec9098", { key: _ctx.$citryPrepared.slotKeys['citrySlot01d68fea81ec9098'], key: _ctx.$citryPrepared.slotKeys['citrySlot01d68fea81ec9098'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot01d68fea81ec9098'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot01d68fea81ec9098'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText24), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs31, { key: _ctx.$citryPrepared.citryKey5 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs32), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot6b615a5bfc995c9f'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot6b615a5bfc995c9f", { key: _ctx.$citryPrepared.slotKeys['citrySlot6b615a5bfc995c9f'], key: _ctx.$citryPrepared.slotKeys['citrySlot6b615a5bfc995c9f'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot6b615a5bfc995c9f'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot6b615a5bfc995c9f'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText25), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs33), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot4cc5c89c894c584a'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot4cc5c89c894c584a", { key: _ctx.$citryPrepared.slotKeys['citrySlot4cc5c89c894c584a'], key: _ctx.$citryPrepared.slotKeys['citrySlot4cc5c89c894c584a'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot4cc5c89c894c584a'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4cc5c89c894c584a'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText26), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs34), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotbb1093c9d53e5993'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotbb1093c9d53e5993", { key: _ctx.$citryPrepared.slotKeys['citrySlotbb1093c9d53e5993'], key: _ctx.$citryPrepared.slotKeys['citrySlotbb1093c9d53e5993'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotbb1093c9d53e5993'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotbb1093c9d53e5993'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText27), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs35), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot4b92e6095736e0c6'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot4b92e6095736e0c6", { key: _ctx.$citryPrepared.slotKeys['citrySlot4b92e6095736e0c6'], key: _ctx.$citryPrepared.slotKeys['citrySlot4b92e6095736e0c6'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot4b92e6095736e0c6'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4b92e6095736e0c6'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText28), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs36, { key: _ctx.$citryPrepared.citryKey6 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs37), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotb77f4169e42ec434'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotb77f4169e42ec434", { key: _ctx.$citryPrepared.slotKeys['citrySlotb77f4169e42ec434'], key: _ctx.$citryPrepared.slotKeys['citrySlotb77f4169e42ec434'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotb77f4169e42ec434'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotb77f4169e42ec434'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText29), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs38), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot8f920a2667041d45'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot8f920a2667041d45", { key: _ctx.$citryPrepared.slotKeys['citrySlot8f920a2667041d45'], key: _ctx.$citryPrepared.slotKeys['citrySlot8f920a2667041d45'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot8f920a2667041d45'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot8f920a2667041d45'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText30), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs39), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot05d0de9dd440eafb'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot05d0de9dd440eafb", { key: _ctx.$citryPrepared.slotKeys['citrySlot05d0de9dd440eafb'], key: _ctx.$citryPrepared.slotKeys['citrySlot05d0de9dd440eafb'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot05d0de9dd440eafb'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot05d0de9dd440eafb'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText31), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs40), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot5ac973d6ce1f9b34'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot5ac973d6ce1f9b34", { key: _ctx.$citryPrepared.slotKeys['citrySlot5ac973d6ce1f9b34'], key: _ctx.$citryPrepared.slotKeys['citrySlot5ac973d6ce1f9b34'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot5ac973d6ce1f9b34'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot5ac973d6ce1f9b34'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText32), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */)),
        (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs41, { key: _ctx.$citryPrepared.citryKey7 }), [
          _createElementVNode("th", _mergeProps({
            scope: "row",
            "data-citry-ui-part": "cell"
          }, _ctx.$citryPrepared.citryAttrs42), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot8dcbcd1a7d9b9b5e'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot8dcbcd1a7d9b9b5e", { key: _ctx.$citryPrepared.slotKeys['citrySlot8dcbcd1a7d9b9b5e'], key: _ctx.$citryPrepared.slotKeys['citrySlot8dcbcd1a7d9b9b5e'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot8dcbcd1a7d9b9b5e'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot8dcbcd1a7d9b9b5e'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText33), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs43), [
            (_ctx.$citryPrepared.selectedSlots['citrySlote13a8b51ce1d8981'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlote13a8b51ce1d8981", { key: _ctx.$citryPrepared.slotKeys['citrySlote13a8b51ce1d8981'], key: _ctx.$citryPrepared.slotKeys['citrySlote13a8b51ce1d8981'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlote13a8b51ce1d8981'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlote13a8b51ce1d8981'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText34), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs44), [
            (_ctx.$citryPrepared.selectedSlots['citrySlotdd17621ed484a8c9'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlotdd17621ed484a8c9", { key: _ctx.$citryPrepared.slotKeys['citrySlotdd17621ed484a8c9'], key: _ctx.$citryPrepared.slotKeys['citrySlotdd17621ed484a8c9'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlotdd17621ed484a8c9'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotdd17621ed484a8c9'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText35), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */),
          _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs45), [
            (_ctx.$citryPrepared.selectedSlots['citrySlot1ffe7f1d3bfb59dc'] === 'supplied')
              ? _renderSlot(_ctx.$slots, "citrySlot1ffe7f1d3bfb59dc", { key: _ctx.$citryPrepared.slotKeys['citrySlot1ffe7f1d3bfb59dc'], key: _ctx.$citryPrepared.slotKeys['citrySlot1ffe7f1d3bfb59dc'] })
              : (_ctx.$citryPrepared.selectedSlots['citrySlot1ffe7f1d3bfb59dc'] === 'fallback')
                ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot1ffe7f1d3bfb59dc'] + ':fallback' }, [
                  _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText36), 1 /* TEXT */)
                ], 64 /* STABLE_FRAGMENT */))
              : _createCommentVNode("v-if", true)
          ], 16 /* FULL_PROPS */)
        ], 16 /* FULL_PROPS */))
      ])
    ])
  ], 16 /* FULL_PROPS */))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["0357abe56c62d08bca4a8d2c5f5456f5716e6615f5e13f8ffeec9331bd9274d6"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_table_4c1a3c3a = _resolveComponent("citry-c-table-4c1a3c3a")
  
  return (_openBlock(), _createElementBlock("section", { class: "sticky-tables" }, [
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, "Bounded catalog"),
      _createElementVNode("p", null, "Scroll this region in either direction."),
      (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
        "citry-id": _ctx.$citryPrepared.calls.citryCall87c598a1d31d4d0b.id,
        key: _ctx.$citryPrepared.calls.citryCall87c598a1d31d4d0b.key
      }, {
        ['citrySlot30ca1818c630188d']: _withCtx(() => [
          _createTextVNode(" Confirmed exoplanets ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ]),
    _createElementVNode("article", null, [
      _createElementVNode("h2", null, "Page-sticky mode"),
      _createElementVNode("p", null, "The header follows page scroll instead of an inner scroller."),
      (_openBlock(), _createBlock(_component_citry_c_table_4c1a3c3a, {
        "citry-id": _ctx.$citryPrepared.calls.citryCallf0ef377bf4fe3760.id,
        key: _ctx.$citryPrepared.calls.citryCallf0ef377bf4fe3760.key
      }, {
        ['citrySlot30ca1818c630188d']: _withCtx(() => [
          _createTextVNode(" Nearby exoplanets ")
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["citry-id"]))
    ])
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["64d392c991d68b5d73bc70737e1b06682a279d7901a15b07af6a7cc39af31d25"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall87c598a1d31d4d0b","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[],"fills":[{"name":"citrySlot30ca1818c630188d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]},{"localId":"citryCallf0ef377bf4fe3760","typeKey":"CTable_6b499b","componentTag":"citry-c-table-4c1a3c3a","bindings":[],"fills":[{"name":"citrySlot30ca1818c630188d","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_sticky_overflow_table_43b9e4d2 = _resolveComponent("citry-sticky-overflow-table-43b9e4d2")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_sticky_overflow_table_43b9e4d2, {
      "citry-id": _ctx.$citryPrepared.calls.citryCall806d6d43b0ff17d0.id,
      key: _ctx.$citryPrepared.calls.citryCall806d6d43b0ff17d0.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["febb2d86673016951d0d7eaf42536706f15f9ae67591a52e2d8970881e6edae1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall806d6d43b0ff17d0","typeKey":"StickyOverflowTable_dd4436","componentTag":"citry-sticky-overflow-table-43b9e4d2","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
