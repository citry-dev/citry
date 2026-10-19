(function(Vue){
const { resolveDirective: _resolveDirective, vModelText: _vModelText, withDirectives: _withDirectives, withModifiers: _withModifiers, toDisplayString: _toDisplayString, createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createTextVNode: _createTextVNode, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _directive_citry_vue_owned = _resolveDirective("citry-vue-owned")
  
  return (_openBlock(), _createElementBlock("form", {
    class: "contact-form",
    onSubmit: _withModifiers(_ctx.submit, ["prevent"])
  }, [
    _createElementVNode("label", { class: "contact-form__label" }, [
      _createTextVNode(" Name "),
      _withDirectives(_createElementVNode("input", {
        key: "citryReplacementccbaa8e849dcd952e40e40b03470c427bf4fa636cd89432bb08685cef7cd0797",
        "onUpdate:modelValue": $event => ((_ctx.name) = $event),
        name: "name",
        class: "contact-form__input",
        type: "text",
        placeholder: "Ada Lovelace"
      }, null, 8 /* PROPS */, ["onUpdate:modelValue"]), [
        [_vModelText, _ctx.name],
        [_directive_citry_vue_owned, 'value']
      ])
    ]),
    _createElementVNode("button", {
      class: "contact-form__button",
      type: "submit"
    }, " Submit "),
    _createElementVNode("div", {
      role: "status",
      "aria-live": "polite"
    }, [
      (_ctx.thanks)
        ? (_openBlock(), _createElementBlock("p", {
          key: 0,
          class: "contact-form__thanks",
          textContent: _toDisplayString(_ctx.thanks)
        }, null, 8 /* PROPS */, ["textContent"]))
        : _createCommentVNode("v-if", true)
    ])
  ], 40 /* PROPS, NEED_HYDRATION */, ["onSubmit"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["bc3ec811d9751bf6eba83cfb843c393551e30803f9fb50b68f0cfaa772288d29"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[{"siteId":"citryDirectiveccf32a60f468b25d6f71af863bae7011b92f1f9c374378a8238441c75c34f81fD0","name":"v-model","arg":null,"modifiers":[]}],replacementSites:[{"siteId":"citryDirectiveccf32a60f468b25d6f71af863bae7011b92f1f9c374378a8238441c75c34f81f","replacementKey":"citryReplacementccbaa8e849dcd952e40e40b03470c427bf4fa636cd89432bb08685cef7cd0797","localDescendants":[],"localDescendantRuns":[]}],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));

(function(Vue){
const { resolveComponent: _resolveComponent, openBlock: _openBlock, createBlock: _createBlock } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_citry_contact_form_6eb19ed9 = _resolveComponent("citry-contact-form-6eb19ed9")
  
  return (_openBlock(), _createBlock(_component_citry_contact_form_6eb19ed9, {
    "citry-id": _ctx.$citryPrepared.calls.citryCallae6584a92d46a2f8.id,
    key: _ctx.$citryPrepared.calls.citryCallae6584a92d46a2f8.key
  }, null, 8 /* PROPS */, ["citry-id"]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["45ee220d641972f0df83e10e40ffeff1e7d3d21935c8a7b26db408693476ba2e"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[{"localId":"citryCallae6584a92d46a2f8","typeKey":"ContactForm_dbfa6e","componentTag":"citry-contact-form-6eb19ed9","bindings":[]}],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
