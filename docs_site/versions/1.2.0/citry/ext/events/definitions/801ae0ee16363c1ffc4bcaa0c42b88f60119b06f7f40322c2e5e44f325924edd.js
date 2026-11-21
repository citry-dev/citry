try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonFocusAndKeyboard_92d46b", "e8acb7544a889b00718090f325182505d50cee756956775eac94005d95b55e83")({
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
__citryRuntime.finishScript("5ec3d9a6b0e5b2853d6744c3d203ff05d1d800612c27a12934ee32721534f3a2");
} catch (error) {
__citryRuntime.finishScript("5ec3d9a6b0e5b2853d6744c3d203ff05d1d800612c27a12934ee32721534f3a2", error);
}