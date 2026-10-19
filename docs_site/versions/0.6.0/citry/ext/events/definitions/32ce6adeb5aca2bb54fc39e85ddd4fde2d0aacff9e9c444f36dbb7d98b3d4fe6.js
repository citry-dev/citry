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
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs21, { key: _ctx.$citryPrepared.citryKey3 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs22), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot30f8b6425eb82881'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot30f8b6425eb82881", { key: _ctx.$citryPrepared.slotKeys['citrySlot30f8b6425eb82881'], key: _ctx.$citryPrepared.slotKeys['citrySlot30f8b6425eb82881'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot30f8b6425eb82881'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot30f8b6425eb82881'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText15), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs23), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot375efa59666184b5'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot375efa59666184b5", { key: _ctx.$citryPrepared.slotKeys['citrySlot375efa59666184b5'], key: _ctx.$citryPrepared.slotKeys['citrySlot375efa59666184b5'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot375efa59666184b5'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot375efa59666184b5'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText16), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs24), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot50575550247c4641'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot50575550247c4641", { key: _ctx.$citryPrepared.slotKeys['citrySlot50575550247c4641'], key: _ctx.$citryPrepared.slotKeys['citrySlot50575550247c4641'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot50575550247c4641'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot50575550247c4641'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText17), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs25, { key: _ctx.$citryPrepared.citryKey4 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs26), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot4657eff9b99d8aba'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot4657eff9b99d8aba", { key: _ctx.$citryPrepared.slotKeys['citrySlot4657eff9b99d8aba'], key: _ctx.$citryPrepared.slotKeys['citrySlot4657eff9b99d8aba'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot4657eff9b99d8aba'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4657eff9b99d8aba'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText18), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs27), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotdbeb9a311ba5fe52'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotdbeb9a311ba5fe52", { key: _ctx.$citryPrepared.slotKeys['citrySlotdbeb9a311ba5fe52'], key: _ctx.$citryPrepared.slotKeys['citrySlotdbeb9a311ba5fe52'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotdbeb9a311ba5fe52'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotdbeb9a311ba5fe52'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText19), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs28), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot767bbeeb46f3f267'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot767bbeeb46f3f267", { key: _ctx.$citryPrepared.slotKeys['citrySlot767bbeeb46f3f267'], key: _ctx.$citryPrepared.slotKeys['citrySlot767bbeeb46f3f267'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot767bbeeb46f3f267'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot767bbeeb46f3f267'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText20), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs29, { key: _ctx.$citryPrepared.citryKey5 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs30), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot5e8b1518f2bc4bd1'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot5e8b1518f2bc4bd1", { key: _ctx.$citryPrepared.slotKeys['citrySlot5e8b1518f2bc4bd1'], key: _ctx.$citryPrepared.slotKeys['citrySlot5e8b1518f2bc4bd1'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot5e8b1518f2bc4bd1'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot5e8b1518f2bc4bd1'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText21), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs31), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotc87a3986719acb42'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotc87a3986719acb42", { key: _ctx.$citryPrepared.slotKeys['citrySlotc87a3986719acb42'], key: _ctx.$citryPrepared.slotKeys['citrySlotc87a3986719acb42'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotc87a3986719acb42'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotc87a3986719acb42'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText22), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs32), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot5f9c8b5d00898ccd'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot5f9c8b5d00898ccd", { key: _ctx.$citryPrepared.slotKeys['citrySlot5f9c8b5d00898ccd'], key: _ctx.$citryPrepared.slotKeys['citrySlot5f9c8b5d00898ccd'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot5f9c8b5d00898ccd'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot5f9c8b5d00898ccd'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText23), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs33, { key: _ctx.$citryPrepared.citryKey6 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs34), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotad34a1acd3f6d827'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotad34a1acd3f6d827", { key: _ctx.$citryPrepared.slotKeys['citrySlotad34a1acd3f6d827'], key: _ctx.$citryPrepared.slotKeys['citrySlotad34a1acd3f6d827'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotad34a1acd3f6d827'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotad34a1acd3f6d827'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText24), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs35), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotc95a153ce1b1043a'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotc95a153ce1b1043a", { key: _ctx.$citryPrepared.slotKeys['citrySlotc95a153ce1b1043a'], key: _ctx.$citryPrepared.slotKeys['citrySlotc95a153ce1b1043a'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotc95a153ce1b1043a'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotc95a153ce1b1043a'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText25), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs36), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot28e120608f2fef9b'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot28e120608f2fef9b", { key: _ctx.$citryPrepared.slotKeys['citrySlot28e120608f2fef9b'], key: _ctx.$citryPrepared.slotKeys['citrySlot28e120608f2fef9b'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot28e120608f2fef9b'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot28e120608f2fef9b'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText26), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs37, { key: _ctx.$citryPrepared.citryKey7 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs38), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot39634829af92a749'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot39634829af92a749", { key: _ctx.$citryPrepared.slotKeys['citrySlot39634829af92a749'], key: _ctx.$citryPrepared.slotKeys['citrySlot39634829af92a749'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot39634829af92a749'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot39634829af92a749'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText27), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs39), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotbde2f143b5dd3ec2'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotbde2f143b5dd3ec2", { key: _ctx.$citryPrepared.slotKeys['citrySlotbde2f143b5dd3ec2'], key: _ctx.$citryPrepared.slotKeys['citrySlotbde2f143b5dd3ec2'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotbde2f143b5dd3ec2'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotbde2f143b5dd3ec2'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText28), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs40), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot4ec5fcc3a6e64f33'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot4ec5fcc3a6e64f33", { key: _ctx.$citryPrepared.slotKeys['citrySlot4ec5fcc3a6e64f33'], key: _ctx.$citryPrepared.slotKeys['citrySlot4ec5fcc3a6e64f33'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot4ec5fcc3a6e64f33'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot4ec5fcc3a6e64f33'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText29), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs41, { key: _ctx.$citryPrepared.citryKey8 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs42), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot105481c4269bdad1'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot105481c4269bdad1", { key: _ctx.$citryPrepared.slotKeys['citrySlot105481c4269bdad1'], key: _ctx.$citryPrepared.slotKeys['citrySlot105481c4269bdad1'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot105481c4269bdad1'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot105481c4269bdad1'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText30), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs43), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot528768cdb19cd6b9'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot528768cdb19cd6b9", { key: _ctx.$citryPrepared.slotKeys['citrySlot528768cdb19cd6b9'], key: _ctx.$citryPrepared.slotKeys['citrySlot528768cdb19cd6b9'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot528768cdb19cd6b9'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot528768cdb19cd6b9'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText31), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs44), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotf9845679ed5e49f2'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotf9845679ed5e49f2", { key: _ctx.$citryPrepared.slotKeys['citrySlotf9845679ed5e49f2'], key: _ctx.$citryPrepared.slotKeys['citrySlotf9845679ed5e49f2'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotf9845679ed5e49f2'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotf9845679ed5e49f2'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText32), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs45, { key: _ctx.$citryPrepared.citryKey9 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs46), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot721670a05912ffd1'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot721670a05912ffd1", { key: _ctx.$citryPrepared.slotKeys['citrySlot721670a05912ffd1'], key: _ctx.$citryPrepared.slotKeys['citrySlot721670a05912ffd1'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot721670a05912ffd1'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot721670a05912ffd1'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText33), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs47), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotea8a128cf6132250'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotea8a128cf6132250", { key: _ctx.$citryPrepared.slotKeys['citrySlotea8a128cf6132250'], key: _ctx.$citryPrepared.slotKeys['citrySlotea8a128cf6132250'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotea8a128cf6132250'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotea8a128cf6132250'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText34), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs48), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotfffd965efb2938cc'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotfffd965efb2938cc", { key: _ctx.$citryPrepared.slotKeys['citrySlotfffd965efb2938cc'], key: _ctx.$citryPrepared.slotKeys['citrySlotfffd965efb2938cc'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotfffd965efb2938cc'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotfffd965efb2938cc'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText35), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs49, { key: _ctx.$citryPrepared.citryKey10 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs50), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotb78c814441c0a23f'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotb78c814441c0a23f", { key: _ctx.$citryPrepared.slotKeys['citrySlotb78c814441c0a23f'], key: _ctx.$citryPrepared.slotKeys['citrySlotb78c814441c0a23f'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotb78c814441c0a23f'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotb78c814441c0a23f'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText36), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs51), [
              (_ctx.$citryPrepared.selectedSlots['citrySlote8d36293d5917c2d'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlote8d36293d5917c2d", { key: _ctx.$citryPrepared.slotKeys['citrySlote8d36293d5917c2d'], key: _ctx.$citryPrepared.slotKeys['citrySlote8d36293d5917c2d'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlote8d36293d5917c2d'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlote8d36293d5917c2d'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText37), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs52), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot825164fd8f74c943'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot825164fd8f74c943", { key: _ctx.$citryPrepared.slotKeys['citrySlot825164fd8f74c943'], key: _ctx.$citryPrepared.slotKeys['citrySlot825164fd8f74c943'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot825164fd8f74c943'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot825164fd8f74c943'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText38), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs53, { key: _ctx.$citryPrepared.citryKey11 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs54), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotdc8d49a361c6d96e'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotdc8d49a361c6d96e", { key: _ctx.$citryPrepared.slotKeys['citrySlotdc8d49a361c6d96e'], key: _ctx.$citryPrepared.slotKeys['citrySlotdc8d49a361c6d96e'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotdc8d49a361c6d96e'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotdc8d49a361c6d96e'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText39), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs55), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot3c139d23bf622e56'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot3c139d23bf622e56", { key: _ctx.$citryPrepared.slotKeys['citrySlot3c139d23bf622e56'], key: _ctx.$citryPrepared.slotKeys['citrySlot3c139d23bf622e56'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot3c139d23bf622e56'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot3c139d23bf622e56'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText40), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs56), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot61a81d551cc676e9'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot61a81d551cc676e9", { key: _ctx.$citryPrepared.slotKeys['citrySlot61a81d551cc676e9'], key: _ctx.$citryPrepared.slotKeys['citrySlot61a81d551cc676e9'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot61a81d551cc676e9'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot61a81d551cc676e9'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText41), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs57, { key: _ctx.$citryPrepared.citryKey12 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs58), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotd02bd7b8f81ac069'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotd02bd7b8f81ac069", { key: _ctx.$citryPrepared.slotKeys['citrySlotd02bd7b8f81ac069'], key: _ctx.$citryPrepared.slotKeys['citrySlotd02bd7b8f81ac069'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotd02bd7b8f81ac069'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotd02bd7b8f81ac069'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText42), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs59), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot01178565d72cf9fe'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot01178565d72cf9fe", { key: _ctx.$citryPrepared.slotKeys['citrySlot01178565d72cf9fe'], key: _ctx.$citryPrepared.slotKeys['citrySlot01178565d72cf9fe'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot01178565d72cf9fe'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot01178565d72cf9fe'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText43), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs60), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot86fedfffa4547f20'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot86fedfffa4547f20", { key: _ctx.$citryPrepared.slotKeys['citrySlot86fedfffa4547f20'], key: _ctx.$citryPrepared.slotKeys['citrySlot86fedfffa4547f20'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot86fedfffa4547f20'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot86fedfffa4547f20'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText44), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs61, { key: _ctx.$citryPrepared.citryKey13 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs62), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot6428c35e3313148c'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot6428c35e3313148c", { key: _ctx.$citryPrepared.slotKeys['citrySlot6428c35e3313148c'], key: _ctx.$citryPrepared.slotKeys['citrySlot6428c35e3313148c'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot6428c35e3313148c'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot6428c35e3313148c'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText45), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs63), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotbcefa931c3bbddaf'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotbcefa931c3bbddaf", { key: _ctx.$citryPrepared.slotKeys['citrySlotbcefa931c3bbddaf'], key: _ctx.$citryPrepared.slotKeys['citrySlotbcefa931c3bbddaf'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotbcefa931c3bbddaf'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotbcefa931c3bbddaf'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText46), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs64), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot8ea49902baab889c'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot8ea49902baab889c", { key: _ctx.$citryPrepared.slotKeys['citrySlot8ea49902baab889c'], key: _ctx.$citryPrepared.slotKeys['citrySlot8ea49902baab889c'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot8ea49902baab889c'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot8ea49902baab889c'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText47), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs65, { key: _ctx.$citryPrepared.citryKey14 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs66), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot70fcbde1111e7004'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot70fcbde1111e7004", { key: _ctx.$citryPrepared.slotKeys['citrySlot70fcbde1111e7004'], key: _ctx.$citryPrepared.slotKeys['citrySlot70fcbde1111e7004'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot70fcbde1111e7004'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot70fcbde1111e7004'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText48), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs67), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotdeb779bb124741f6'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotdeb779bb124741f6", { key: _ctx.$citryPrepared.slotKeys['citrySlotdeb779bb124741f6'], key: _ctx.$citryPrepared.slotKeys['citrySlotdeb779bb124741f6'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotdeb779bb124741f6'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotdeb779bb124741f6'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText49), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs68), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot5407530cfd1dfa67'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot5407530cfd1dfa67", { key: _ctx.$citryPrepared.slotKeys['citrySlot5407530cfd1dfa67'], key: _ctx.$citryPrepared.slotKeys['citrySlot5407530cfd1dfa67'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot5407530cfd1dfa67'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot5407530cfd1dfa67'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText50), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */)
          ], 16 /* FULL_PROPS */)),
          (_openBlock(), _createElementBlock("tr", _mergeProps({ "data-citry-ui-part": "row" }, _ctx.$citryPrepared.citryAttrs69, { key: _ctx.$citryPrepared.citryKey15 }), [
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs70), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot2cc4ffb7caf26183'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot2cc4ffb7caf26183", { key: _ctx.$citryPrepared.slotKeys['citrySlot2cc4ffb7caf26183'], key: _ctx.$citryPrepared.slotKeys['citrySlot2cc4ffb7caf26183'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot2cc4ffb7caf26183'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot2cc4ffb7caf26183'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText51), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs71), [
              (_ctx.$citryPrepared.selectedSlots['citrySlotf99ebbf92dc0f145'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlotf99ebbf92dc0f145", { key: _ctx.$citryPrepared.slotKeys['citrySlotf99ebbf92dc0f145'], key: _ctx.$citryPrepared.slotKeys['citrySlotf99ebbf92dc0f145'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlotf99ebbf92dc0f145'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlotf99ebbf92dc0f145'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText52), 1 /* TEXT */)
                  ], 64 /* STABLE_FRAGMENT */))
                : _createCommentVNode("v-if", true)
            ], 16 /* FULL_PROPS */),
            _createElementVNode("td", _mergeProps({ "data-citry-ui-part": "cell" }, _ctx.$citryPrepared.citryAttrs72), [
              (_ctx.$citryPrepared.selectedSlots['citrySlot6493977c80e4c4f4'] === 'supplied')
                ? _renderSlot(_ctx.$slots, "citrySlot6493977c80e4c4f4", { key: _ctx.$citryPrepared.slotKeys['citrySlot6493977c80e4c4f4'], key: _ctx.$citryPrepared.slotKeys['citrySlot6493977c80e4c4f4'] })
                : (_ctx.$citryPrepared.selectedSlots['citrySlot6493977c80e4c4f4'] === 'fallback')
                  ? (_openBlock(), _createElementBlock(_Fragment, { key: _ctx.$citryPrepared.slotKeys['citrySlot6493977c80e4c4f4'] + ':fallback' }, [
                    _createTextVNode(_toDisplayString(_ctx.$citryPrepared.citryText53), 1 /* TEXT */)
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
window.__citryRuntimeDefinitions["c8eb36be04510edeed652f4afbc805167428216a23db127640fa9243c74429c0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_data_grid_674331b8 = _resolveComponent("citry-c-data-grid-674331b8")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.notice)
    }, "This static preview supplies one complete window", 8 /* PROPS */, ["textContent"]),
    (_openBlock(), _createBlock(_component_citry_c_data_grid_674331b8, {
      onRangeChange: (detail)=>_ctx.notice=`Requested ${detail.startIndex}-${detail.endIndex - 1}`,
      "citry-id": _ctx.$citryPrepared.calls.citryCall2f56bb60d42ea985.id,
      key: _ctx.$citryPrepared.calls.citryCall2f56bb60d42ea985.key
    }, null, 8 /* PROPS */, ["onRangeChange", "citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["6040c3c027d127c40b44711ecb9db8e25251f5ada8ec1929e8e6ca2454996162"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall2f56bb60d42ea985","typeKey":"CDataGrid_52b9be","componentTag":"citry-c-data-grid-674331b8","bindings":[{"kind":"prop","name":":onRangeChange","value":"(detail)=>notice=`Requested ${detail.startIndex}-${detail.endIndex - 1}`","sourceStart":125,"sourceEnd":214}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_windowed_data_grid_a1a378cf = _resolveComponent("citry-windowed-data-grid-a1a378cf")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_windowed_data_grid_a1a378cf, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallead4e897ff2f5ac3.id,
      key: _ctx.$citryPrepared.calls.citryCallead4e897ff2f5ac3.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["086eba846eba5c16edf8d423ddeff7da34e28fdf00764cbb2b4ab1e6d4c265ab"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallead4e897ff2f5ac3","typeKey":"WindowedDataGrid_8816f6","componentTag":"citry-windowed-data-grid-a1a378cf","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
