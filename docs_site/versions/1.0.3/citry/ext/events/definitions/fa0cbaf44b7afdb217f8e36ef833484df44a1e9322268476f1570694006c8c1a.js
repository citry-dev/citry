try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonFocusAndKeyboard_efc8af", "e8acb7544a889b00718090f325182505d50cee756956775eac94005d95b55e83")({
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
__citryRuntime.finishScript("0c165f2ab84fd9d2131623ee55ab359fdc4ebce1c2888e32e8d2bdc8250b057d");
} catch (error) {
__citryRuntime.finishScript("0c165f2ab84fd9d2131623ee55ab359fdc4ebce1c2888e32e8d2bdc8250b057d", error);
}