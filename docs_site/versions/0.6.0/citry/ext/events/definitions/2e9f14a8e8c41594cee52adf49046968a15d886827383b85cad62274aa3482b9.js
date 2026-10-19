(function(Vue){
const { createElementVNode: _createElementVNode, openBlock: _openBlock, createElementBlock: _createElementBlock, createTextVNode: _createTextVNode, createCommentVNode: _createCommentVNode } = Vue

function render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock("div", { class: "frag-widget" }, [
    _createElementVNode("strong", { class: "frag-widget__title" }, [
      _createTextVNode(" Loaded over the wire "),
      (_ctx.scriptRan)
        ? (_openBlock(), _createElementBlock("span", { key: 0 }, "(JS ran)"))
        : _createCommentVNode("v-if", true)
    ]),
    _createElementVNode("p", null, " This widget's HTML, CSS, and JS arrived as an HTML fragment. ")
  ]))
}
window.__citryRuntimeDefinitions=window.__citryRuntimeDefinitions||{};
window.__citryRuntimeDefinitions["9c036e55fc8aea75dd2139535254ee9988c575d9efc50d58d552e3f7489a132b"]={render:render,target:"ordinary-vnodes/1",helperContract:"b103179315e9ac0096610edd010fca48bc708a210cc9a159d35dc92e398a91d5",directiveSignature:[],replacementSites:[],localCallRuns:[],localCalls:[],dynamicElements:[],opaqueHtmlSites:[],runtimeEventSites:[]};
})(window.__citryRuntime.compilerRuntime.runtimeForDynamicElements([]));
