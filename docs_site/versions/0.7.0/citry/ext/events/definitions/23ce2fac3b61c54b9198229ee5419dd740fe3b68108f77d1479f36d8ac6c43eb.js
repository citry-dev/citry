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
    class: "cui-calendar",
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
window.__citryRuntimeDefinitions["a08ecce785b968a50f4f6edcca8044c6b09a2a00821c7cdd4cc76c59861d8ff3"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
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
    class: "cui-date-picker",
    "data-citry-ui-part": "date-picker"
  }, _ctx.$citryPrepared.citryAttrs0), [
    _withDirectives(_createElementVNode("input", _mergeProps({
      class: "cui-date-picker__fallback",
      type: "date",
      "data-citry-ui-part": "fallback-input"
    }, _ctx.$citryPrepared.citryAttrs1), null, 16 /* FULL_PROPS */), [
      [_directive_citry_vue_owned, 'value']
    ]),
    _createElementVNode("div", {
      class: "cui-date-picker__enhanced",
      "data-citry-ui-part": "enhanced-control"
    }, [
      (_openBlock(), _createBlock(_component_citry_c_popover_e1fe086e, {
        open: _ctx.datePickerOpen,
        dismissible: _ctx.datePickerDismissible,
        placement: _ctx.datePickerPlacement,
        matchWidth: _ctx.datePickerMatchWidth,
        onOpenChange: _ctx.datePickerOnPopoverOpenChange,
        "citry-id": _ctx.$citryPrepared.calls.citryCall8571dc885875a8da.id,
        key: _ctx.$citryPrepared.calls.citryCall8571dc885875a8da.key
      }, {
        ['citrySlot371618f8b14ff656']: _withCtx(() => [
          _createElementVNode("button", _mergeProps({
            class: "cui-date-picker__control",
            type: "button",
            "data-citry-date-picker-trigger": "",
            "data-citry-ui-part": "control"
          }, _ctx.$citryPrepared.citryAttrs2), [
            _createElementVNode("span", {
              class: "cui-date-picker__value",
              "data-citry-ui-part": "value"
            }, _toDisplayString(_ctx.$citryPrepared.citryText0), 1 /* TEXT */),
            (_openBlock(), _createBlock(_component_citry_c_icon_f8b347d7, {
              "citry-id": _ctx.$citryPrepared.calls.citryCall792df2f2ad6f431c.id,
              key: _ctx.$citryPrepared.calls.citryCall792df2f2ad6f431c.key
            }, null, 8 /* PROPS */, ["citry-id"]))
          ], 16 /* FULL_PROPS */)
        ]),
        ['citrySlot6797d7221c481487']: _withCtx(() => [
          _createElementVNode("span", null, _toDisplayString(_ctx.$citryPrepared.citryText1), 1 /* TEXT */)
        ]),
        ['citrySlot324bf05fa215c365']: _withCtx(() => [
          (_openBlock(), _createBlock(_component_citry_c_calendar_798611d2, {
            value: _ctx.datePickerCalendarValue,
            visibleDate: _ctx.datePickerVisibleDate,
            min: _ctx.datePickerMin,
            max: _ctx.datePickerMax,
            unavailableDates: _ctx.datePickerUnavailableDates,
            disabled: _ctx.datePickerDisabled,
            readonly: _ctx.datePickerReadonly,
            firstDayOfWeek: _ctx.datePickerFirstDayOfWeek,
            showAdjacentDays: _ctx.datePickerShowAdjacentDays,
            fixedWeeks: _ctx.datePickerFixedWeeks,
            onValueChange: _ctx.datePickerOnCalendarValueChange,
            onVisibleDateChange: _ctx.datePickerOnVisibleDateChange,
            "citry-id": _ctx.$citryPrepared.calls.citryCalld35426cb6838943e.id,
            key: _ctx.$citryPrepared.calls.citryCalld35426cb6838943e.key
          }, null, 8 /* PROPS */, ["value", "visibleDate", "min", "max", "unavailableDates", "disabled", "readonly", "firstDayOfWeek", "showAdjacentDays", "fixedWeeks", "onValueChange", "onVisibleDateChange", "citry-id"]))
        ]),
        _: 2 /* DYNAMIC */
      }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["open", "dismissible", "placement", "matchWidth", "onOpenChange", "citry-id"])),
      _createElementVNode("button", _mergeProps({
        class: "cui-date-picker__clear",
        type: "button",
        "data-citry-ui-part": "clear"
      }, _ctx.$citryPrepared.citryAttrs3), [
        _createElementVNode("span", { "aria-hidden": "true" }, "×")
      ], 16 /* FULL_PROPS */)
    ])
  ], 16 /* FULL_PROPS */))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["a5d12256c00148fb7a902eacbf46d2752c639ed895f07d7f353b0c6c8939a737"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall792df2f2ad6f431c","typeKey":"CIcon_8e5345","componentTag":"citry-c-icon-f8b347d7","bindings":[]},{"localId":"citryCalld35426cb6838943e","typeKey":"CCalendar_6c8cea","componentTag":"citry-c-calendar-798611d2","bindings":[{"kind":"prop","name":":value","value":"datePickerCalendarValue","sourceStart":1395,"sourceEnd":1427},{"kind":"prop","name":":visibleDate","value":"datePickerVisibleDate","sourceStart":1428,"sourceEnd":1464},{"kind":"prop","name":":min","value":"datePickerMin","sourceStart":1465,"sourceEnd":1485},{"kind":"prop","name":":max","value":"datePickerMax","sourceStart":1486,"sourceEnd":1506},{"kind":"prop","name":":unavailableDates","value":"datePickerUnavailableDates","sourceStart":1507,"sourceEnd":1553},{"kind":"prop","name":":disabled","value":"datePickerDisabled","sourceStart":1554,"sourceEnd":1584},{"kind":"prop","name":":readonly","value":"datePickerReadonly","sourceStart":1585,"sourceEnd":1615},{"kind":"prop","name":":firstDayOfWeek","value":"datePickerFirstDayOfWeek","sourceStart":1616,"sourceEnd":1658},{"kind":"prop","name":":showAdjacentDays","value":"datePickerShowAdjacentDays","sourceStart":1659,"sourceEnd":1705},{"kind":"prop","name":":fixedWeeks","value":"datePickerFixedWeeks","sourceStart":1706,"sourceEnd":1740},{"kind":"prop","name":":onValueChange","value":"datePickerOnCalendarValueChange","sourceStart":1741,"sourceEnd":1789},{"kind":"prop","name":":onVisibleDateChange","value":"datePickerOnVisibleDateChange","sourceStart":1790,"sourceEnd":1842}]},{"localId":"citryCall8571dc885875a8da","typeKey":"CPopover_d4bf44","componentTag":"citry-c-popover-e1fe086e","bindings":[{"kind":"prop","name":":open","value":"datePickerOpen","sourceStart":366,"sourceEnd":388},{"kind":"prop","name":":dismissible","value":"datePickerDismissible","sourceStart":389,"sourceEnd":425},{"kind":"prop","name":":placement","value":"datePickerPlacement","sourceStart":426,"sourceEnd":458},{"kind":"prop","name":":matchWidth","value":"datePickerMatchWidth","sourceStart":459,"sourceEnd":493},{"kind":"prop","name":":onOpenChange","value":"datePickerOnPopoverOpenChange","sourceStart":494,"sourceEnd":539}],"fills":[{"name":"citrySlot324bf05fa215c365","localDescendants":["citryCalld35426cb6838943e"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot371618f8b14ff656","localDescendants":["citryCall792df2f2ad6f431c"],"localDescendantRuns":[],"slotOutlets":[]},{"name":"citrySlot6797d7221c481487","localDescendants":[],"localDescendantRuns":[],"slotOutlets":[]}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock, createTextVNode: _createTextVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_c_date_picker_0e49baed = _resolveComponent("citry-c-date-picker-0e49baed")
  
  return (_openBlock(), _createElementBlock("section", null, [
    _createElementVNode("p", null, [
      _createTextVNode("Value: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.value || 'empty')
      }, null, 8 /* PROPS */, ["textContent"]),
      _createTextVNode("; popup: "),
      _createElementVNode("strong", {
        textContent: _toDisplayString(_ctx.open ? 'open' : 'closed')
      }, null, 8 /* PROPS */, ["textContent"])
    ]),
    (_openBlock(), _createBlock(_component_citry_c_date_picker_0e49baed, {
      value: _ctx.value,
      open: _ctx.open,
      onValueChange: (next,detail)=>{_ctx.last=`${detail.source}: ${next}`;_ctx.value=next},
      onOpenChange: (next,detail)=>{_ctx.last=`${detail.reason}: ${next}`;_ctx.open=next},
      "citry-id": _ctx.$citryPrepared.calls.citryCall748e868e37149fa2.id,
      key: _ctx.$citryPrepared.calls.citryCall748e868e37149fa2.key
    }, null, 8 /* PROPS */, ["value", "open", "onValueChange", "onOpenChange", "citry-id"])),
    _createElementVNode("div", null, [
      _createElementVNode("button", {
        type: "button",
        onClick: $event => (_ctx.value='2026-08-25')
      }, "Set August 25", 8 /* PROPS */, ["onClick"]),
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
window.__citryRuntimeDefinitions["f78782e1ea95e57d974b1301912a540b301d051a61bcaac2eb236e4db122bbda"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCall748e868e37149fa2","typeKey":"CDatePicker_42b9f6","componentTag":"citry-c-date-picker-0e49baed","bindings":[{"kind":"prop","name":":value","value":"value","sourceStart":163,"sourceEnd":177},{"kind":"prop","name":":open","value":"open","sourceStart":178,"sourceEnd":190},{"kind":"prop","name":":onValueChange","value":"(next,detail)=>{last=`${detail.source}: ${next}`;value=next}","sourceStart":191,"sourceEnd":268},{"kind":"prop","name":":onOpenChange","value":"(next,detail)=>{last=`${detail.reason}: ${next}`;open=next}","sourceStart":269,"sourceEnd":344}]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createElementBlock: _createElementBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_controlled_date_picker_2575a1fe = _resolveComponent("citry-controlled-date-picker-2575a1fe")
  
  return (_openBlock(), _createElementBlock("main", null, [
    (_openBlock(), _createBlock(_component_citry_controlled_date_picker_2575a1fe, {
      "citry-id": _ctx.$citryPrepared.calls.citryCallddd3634bd0e83b24.id,
      key: _ctx.$citryPrepared.calls.citryCallddd3634bd0e83b24.key
    }, null, 8 /* PROPS */, ["citry-id"]))
  ]))
}
Object.prototype.hasOwnProperty.call(window,"__citryRuntimeDefinitions")||(window.__citryRuntimeDefinitions={});
window.__citryRuntimeDefinitions["0de62365186a1151270de2bc2164390746e01f699d4ee91d0bce195d6d3baf60"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallddd3634bd0e83b24","typeKey":"ControlledDatePicker_ccc778","componentTag":"citry-controlled-date-picker-2575a1fe","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
