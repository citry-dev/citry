try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonFocusAndKeyboard_a72c91", "e8acb7544a889b00718090f325182505d50cee756956775eac94005d95b55e83")({
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
__citryRuntime.finishScript("7b71a29551d45adf8e0c834b474f4a73e1a472373168d88092ab4155f8790c72");
} catch (error) {
__citryRuntime.finishScript("7b71a29551d45adf8e0c834b474f4a73e1a472373168d88092ab4155f8790c72", error);
}