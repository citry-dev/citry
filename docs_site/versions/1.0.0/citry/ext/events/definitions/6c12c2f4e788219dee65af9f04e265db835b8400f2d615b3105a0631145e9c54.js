try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonFocusAndKeyboard_d54938", "e8acb7544a889b00718090f325182505d50cee756956775eac94005d95b55e83")({
  data(){return {trace:[], loading:false, primaryDisabled:false, menuDisabled:false};},
  onServerRender({component}) {
    const removers=[];
    for (const [name,label] of [['ltrSplit','LTR'],['rtlSplit','RTL']]) {
      const host=component.$refs[name].$el;
      for (const [selector,part] of [
        ['[data-citry-ui-part="split-button-primary"]','primary'],
        ['[data-citry-ui-part="split-button-menu-trigger"]','menu'],
      ]) {
        const element=host.querySelector(selector);
        const listener=()=>component.trace.push(`${label} ${part}`);
        element.addEventListener('focus',listener);
        removers.push(()=>element.removeEventListener('focus',listener));
      }
    }
    return ()=>removers.forEach((remove)=>remove());
  },
});

})();
__citryRuntime.finishScript("ed441a9ac233bb83a8a84e2c8742b6bbd3daf4cc93d31f49b1747fec69d0d16f");
} catch (error) {
__citryRuntime.finishScript("ed441a9ac233bb83a8a84e2c8742b6bbd3daf4cc93d31f49b1747fec69d0d16f", error);
}