(function(Vue){
const { createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("svg", _mergeProps({
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    focusable: "false",
    "data-citry-ui-part": "icon"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("g", { class: "cui-icon__glyph" }, [
      _createElementVNode("path", { d: "M8 2v3" }),
      _createElementVNode("path", { d: "M16 2v3" }),
      _createElementVNode("rect", {
        height: "18",
        rx: "2",
        width: "18",
        x: "3",
        y: "3"
      }),
      _createElementVNode("path", { d: "M3 9h18" })
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["14d2d2ea05d6309ac465fcb4f9b72aeefe4e38081e3bbbbe81b24decf3b697ec"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, withDirectives: _withDirectives, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    role: "group",
    "data-citry-ui-part": "calendar"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-calendar__header",
      "data-citry-ui-part": "header"
    }, [
      _createElementVNode("button", _mergeProps({
        class: "cui-calendar__navigation",
        type: "button",
        "data-citry-ui-part": "previous"
      }, _ctx.$citryPrepared.citryAttrs1), [
        _createElementVNode("span", {
          class: "cui-calendar__arrow",
          "aria-hidden": "true"
        }, "‹")
      ], 16 /* FULL_PROPS */),
      _createElementVNode("h2", _mergeProps({
        class: "cui-calendar__heading",
        "aria-live": "polite",
        "aria-atomic": "true",
        "data-citry-ui-part": "heading"
      }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */),
      _createElementVNode("button", _mergeProps({
        class: "cui-calendar__navigation",
        type: "button",
        "data-citry-ui-part": "next"
      }, _ctx.$citryPrepared.citryAttrs3), [
        _createElementVNode("span", {
          class: "cui-calendar__arrow",
          "aria-hidden": "true"
        }, "›")
      ], 16 /* FULL_PROPS */)
    ]),
    _createElementVNode("table", _mergeProps({
      class: "cui-calendar__grid",
      role: "grid",
      "data-citry-ui-part": "grid"
    }, _ctx.$citryPrepared.citryAttrs4), [
      _createElementVNode("thead", null, [
        _createElementVNode("tr", { "data-citry-ui-part": "weekday-row" }, [
          _createElementVNode("th", {
            scope: "col",
            "aria-hidden": "true"
          }, " "),
          _createElementVNode("th", {
            scope: "col",
            "aria-hidden": "true"
          }, " "),
          _createElementVNode("th", {
            scope: "col",
            "aria-hidden": "true"
          }, " "),
          _createElementVNode("th", {
            scope: "col",
            "aria-hidden": "true"
          }, " "),
          _createElementVNode("th", {
            scope: "col",
            "aria-hidden": "true"
          }, " "),
          _createElementVNode("th", {
            scope: "col",
            "aria-hidden": "true"
          }, " "),
          _createElementVNode("th", {
            scope: "col",
            "aria-hidden": "true"
          }, " ")
        ])
      ]),
      _createElementVNode("tbody")
    ], 16 /* FULL_PROPS */),
    _withDirectives(_createElementVNode("input", _mergeProps({
      class: "cui-calendar__fallback",
      type: "date",
      "data-citry-ui-part": "fallback-input"
    }, _ctx.$citryPrepared.citryAttrs5), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, 'value']
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2130e0e06ffa737cf634b3159006e5aff6d8b5359773b2573e854b4fb6eab0d1"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { createElementVNode: _createElementVNode, renderSlot: _renderSlot, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", {
    class: "cui-popover-host",
    "data-citry-popover-host": ""
  }, [
    (_ctx.$citryPrepared.selectedSlots['citrySlot371618f8b14ff656'] === 'supplied')
      ? _renderSlot(_ctx.$slots, "citrySlot371618f8b14ff656", { key: 0 })
      : _createCommentVNode("v-if", true),
    _createElementVNode("div", _mergeProps({
      popover: "manual",
      role: "dialog",
      tabindex: "-1",
      "data-citry-ui-part": "popover"
    }, _ctx.$citryPrepared.citryAttrs0), [
      _createElementVNode("header", {
        class: "cui-popover__header",
        "data-citry-ui-part": "header"
      }, [
        _createElementVNode("h2", _mergeProps({
          class: "cui-popover__title",
          "data-citry-ui-part": "title"
        }, _ctx.$citryPrepared.citryAttrs1), [
          (_ctx.$citryPrepared.selectedSlots['citrySlot6797d7221c481487'] === 'supplied')
            ? _renderSlot(_ctx.$slots, "citrySlot6797d7221c481487", { key: 1 })
            : _createCommentVNode("v-if", true)
        ], 16 /* FULL_PROPS */)
      ]),
      _createElementVNode("div", {
        class: "cui-popover__body",
        "data-citry-ui-part": "body"
      }, [
        (_ctx.$citryPrepared.selectedSlots['citrySlot324bf05fa215c365'] === 'supplied')
          ? _renderSlot(_ctx.$slots, "citrySlot324bf05fa215c365", { key: 2 })
          : _createCommentVNode("v-if", true)
      ])
    ], 16 /* FULL_PROPS */)
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["8bbe852e7c3fb9ade7145f12547662b478a36a61502bd444cc9505b6732aa024"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveDirective: _resolveDirective, resolveComponent: _resolveComponent, withDirectives: _withDirectives, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, mergeProps: _mergeProps, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, withCtx: _withCtx } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_icon_f8b347d7 = _resolveComponent("citry-c-icon-f8b347d7")
  const _component_citry_c_calendar_798611d2 = _resolveComponent("citry-c-calendar-798611d2")
  const _component_citry_c_popover_e1fe086e = _resolveComponent("citry-c-popover-e1fe086e")
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("div", _mergeProps({
    class: "cui-date-range",
    role: "group",
    "data-citry-ui-part": "date-range"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _createElementVNode("div", {
      class: "cui-date-range__fallback",
      "data-citry-ui-part": "fallback-group"
    }, [
      _createElementVNode("label", { class: "cui-date-range__fallback-field" }, [
        _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
        _withDirectives(_createElementVNode("input", _mergeProps({
          type: "date",
          "data-citry-ui-part": "start-input"
        }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
          [_directive_citry_vue_owned, 'value']
        ])
      ]),
      _createElementVNode("label", { class: "cui-date-range__fallback-field" }, [
        _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */),
        _withDirectives(_createElementVNode("input", _mergeProps({
          type: "date",
          "data-citry-ui-part": "end-input"
        }, _ctx.$citryPrepared.citryAttrs2), null, 16 /* FULL_PROPS */), [
          [_directive_citry_vue_owned, 'value']
        ])
      ])
    ]),
    _createElementVNode("div", {
      class: "cui-date-range__enhanced",
      "data-citry-ui-part": "enhanced-control"
    }, [
      (_openBlock(), _createBlock(_component_citry_c_popover_e1fe086e, {
        open: _ctx.dateRangeOpen && !(_ctx.dateRangeAwaitingRun && _ctx.serverDefaults.disabled),
        dismissible: _ctx.dateRangeDismissible,
        placement: _ctx.dateRangePlacement,
        matchWidth: _ctx.dateRangeMatchWidth,
        onOpenChange: _ctx.dateRangeOnPopoverOpenChange,
        "citry-id": _ctx.$citryPrepared.calls.citryCall5c15ea1cdc098dee.id,
        key: _ctx.$citryPrepared.calls.citryCall5c15ea1cdc098dee.key
      }, {
        ['citrySlot371618f8b14ff656']: _withCtx(() => [
          _createElementVNode("button", _mergeProps({
            class: "cui-date-range__control",
            type: "button",
            "data-citry-date-range-trigger": "",
            "data-citry-ui-part": "control"
          }, _ctx.$citryPrepared.citryAttrs3), [
            _createElementVNode("span", {
              class: "cui-date-range__value",
              "data-citry-ui-part": "value"
            }, _toDisplayString(_ctx.$citryPrepared.citryText2), 1 /* TEXT */),
            (_openBlock(), _createBlock(_component_citry_c_icon_f8b347d7, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall7f3d0d21ba9341e7.id,
              key: _ctx.$citryPrepared.calls.citryCall7f3d0d21ba9341e7.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ], 16 /* FULL_PROPS */)
        ]),
        ['citrySlot6797d7221c481487']: _withCtx(() => [
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText3), 1 /* TEXT */)
        ]),
        ['citrySlot324bf05fa215c365']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_calendar_798611d2, {
            value: _ctx.dateRangeCalendarValue,
            disabled: _ctx.dateRangeCalendarDisabled,
            readonly: _ctx.dateRangeCalendarReadonly,
            rangeStart: _ctx.dateRangeRangeStart,
            rangeEnd: _ctx.dateRangeRangeEnd,
            rangePreview: _ctx.dateRangeRangePreview,
            rangeStartLabel: _ctx.dateRangeStartLabel,
            rangeEndLabel: _ctx.dateRangeEndLabel,
            accessibleLabel: _ctx.dateRangeAccessibleLabel,
            onValueChange: _ctx.dateRangeOnCalendarValueChange,
            "citry-id": _ctx.$citryPrepared.calls.citryCallcf496ab8dd122493.id,
            key: _ctx.$citryPrepared.calls.citryCallcf496ab8dd122493.key
          }, null, 8 /* PROPS */, ["value", "disabled", "readonly", "rangeStart", "rangeEnd", "rangePreview", "rangeStartLabel", "rangeEndLabel", "accessibleLabel", "onValueChange", "citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "dismissible", "placement", "matchWidth", "onOpenChange", "citry-id"])),
      _createElementVNode("button", _mergeProps({
        class: "cui-date-range__clear",
        type: "button",
        "data-citry-ui-part": "clear"
      }, _ctx.$citryPrepared.citryAttrs4), [
        _createElementVNode("span", { "aria-hidden": "true" }, "×")
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["c964b0f992eba075e13ced6687fff94ab4356071d54bbf8d98827e748a4bde4f"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall7f3d0d21ba9341e7","typeKey":"CIcon_8e5345","componentTag":"citry-c-icon-f8b347d7","bindings":[]},{"localId":"citryCallcf496ab8dd122493","typeKey":"CCalendar_6c8cea","componentTag":"citry-c-calendar-798611d2","bindings":[{"kind":"prop","name":":value","value":"dateRangeCalendarValue","sourceStart":1855,"sourceEnd":1886},{"kind":"prop","name":":disabled","value":"dateRangeCalendarDisabled","sourceStart":1887,"sourceEnd":1924},{"kind":"prop","name":":readonly","value":"dateRangeCalendarReadonly","sourceStart":1925,"sourceEnd":1962},{"kind":"prop","name":":rangeStart","value":"dateRangeRangeStart","sourceStart":1963,"sourceEnd":1996},{"kind":"prop","name":":rangeEnd","value":"dateRangeRangeEnd","sourceStart":1997,"sourceEnd":2026},{"kind":"prop","name":":rangePreview","value":"dateRangeRangePreview","sourceStart":2027,"sourceEnd":2064},{"kind":"prop","name":":rangeStartLabel","value":"dateRangeStartLabel","sourceStart":2065,"sourceEnd":2103},{"kind":"prop","name":":rangeEndLabel","value":"dateRangeEndLabel","sourceStart":2104,"sourceEnd":2138},{"kind":"prop","name":":accessibleLabel","value":"dateRangeAccessibleLabel","sourceStart":2139,"sourceEnd":2182},{"kind":"prop","name":":onValueChange","value":"dateRangeOnCalendarValueChange","sourceStart":2183,"sourceEnd":2230}]},{"localId":"citryCall5c15ea1cdc098dee","typeKey":"CPopover_d4bf44","componentTag":"citry-c-popover-e1fe086e","bindings":[{"kind":"prop","name":":open","value":"dateRangeOpen && !(dateRangeAwaitingRun && serverDefaults.disabled)","sourceStart":780,"sourceEnd":855},{"kind":"prop","name":":dismissible","value":"dateRangeDismissible","sourceStart":856,"sourceEnd":891},{"kind":"prop","name":":placement","value":"dateRangePlacement","sourceStart":892,"sourceEnd":923},{"kind":"prop","name":":matchWidth","value":"dateRangeMatchWidth","sourceStart":924,"sourceEnd":957},{"kind":"prop","name":":onOpenChange","value":"dateRangeOnPopoverOpenChange","sourceStart":958,"sourceEnd":1002}],"fills":[{"name":"citrySlot324bf05fa215c365","localDescendants":["citryCallcf496ab8dd122493"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot371618f8b14ff656","localDescendants":["citryCall7f3d0d21ba9341e7"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6797d7221c481487","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_date_range_56cb8e0c = _resolveComponent("citry-c-date-range-56cb8e0c")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("p", null, [
      _createTextVNode("Range: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.value ? `${_ctx.value.start} through ${_ctx.value.end}` : 'empty')
      }, null, 8 /* PROPS */, ["textContent"]),
      _createTextVNode("; popup: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.open ? 'open' : 'closed')
      }, null, 8 /* PROPS */, ["textContent"])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_date_range_56cb8e0c, {
      value: _ctx.value,
      open: _ctx.open,
      onValueChange: (next,detail)=>{_ctx.last=`${detail.source}: ${JSON.stringify(next)}`;_ctx.value=next},
      onOpenChange: (next,detail)=>{_ctx.last=`${detail.reason}: ${next}`;_ctx.open=next},
      "citry-id": _ctx.$citryPrepared.calls.citryCall323178ddc087eca3.id,
      key: _ctx.$citryPrepared.calls.citryCall323178ddc087eca3.key
    }, null, 8 /* PROPS */, ["value", "open", "onValueChange", "onOpenChange", "citry-id"])),
    _createElementVNode("div", null, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.value={start:'2026-08-25',end:'2026-08-29'})
      }, "Set August 25 through 29", 8 /* PROPS */, ["onClick"]),
      _createTextVNode(),
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.open=!_ctx.open)
      }, "Toggle popup", 8 /* PROPS */, ["onClick"])
    ]),
    _createElementVNode("output", {
      textContent: _toDisplayString(_ctx.last)
    }, "No request yet", 8 /* PROPS */, ["textContent"])
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["2bb23f2ebe2752891250dcb5a61d4c1b8c6b0cb7aa075e6d55ffb2f3d74a3c07"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall323178ddc087eca3","typeKey":"CDateRange_f0cd44","componentTag":"citry-c-date-range-56cb8e0c","bindings":[{"kind":"prop","name":":value","value":"value","sourceStart":201,"sourceEnd":215},{"kind":"prop","name":":open","value":"open","sourceStart":216,"sourceEnd":228},{"kind":"prop","name":":onValueChange","value":"(next,detail)=>{last=`${detail.source}: ${JSON.stringify(next)}`;value=next}","sourceStart":229,"sourceEnd":322},{"kind":"prop","name":":onOpenChange","value":"(next,detail)=>{last=`${detail.reason}: ${next}`;open=next}","sourceStart":323,"sourceEnd":398}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_date_range_d380014a = _resolveComponent("citry-controlled-date-range-d380014a")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_date_range_d380014a, {
      "citry-id": _ctx.$citryPrepared.calls.citryCalla0cecccea302562b.id,
      key: _ctx.$citryPrepared.calls.citryCalla0cecccea302562b.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0bba999fe9cfcf04fee8a24ae02ebec1a9362282b46837be4d959aa00058f4f0"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCalla0cecccea302562b","typeKey":"ControlledDateRange_1ea1d1","componentTag":"citry-controlled-date-range-d380014a","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
