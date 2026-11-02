(function() {

      // A form's named field can hide the form's own parentElement, so read them from
      // Node.prototype.
      const nodeParentElement=Object.getOwnPropertyDescriptor(Node.prototype,"parentElement").get;
      const parentElementOf=node=>nodeParentElement.call(node);
      (()=>{const k=Symbol.for("citry-ui:reveal"),x=globalThis[k];if(x!==void 0){if(x.generation!==1)
      throw new Error("[citry-ui] incompatible reveal runtime; reload the page.");return}
      const n=(s,e,a,b)=>s<a?s-a:e>b?Math.min(e-b,s-a):0,r=(el,c)=>{
      if(!(el instanceof Element)||el===c||!c?.contains(el))return;
      for(let b=parentElementOf(el);b;b=b===c?null:parentElementOf(b)){const st=getComputedStyle(b),
      i=el.getBoundingClientRect(),o=b.getBoundingClientRect(),t=o.top+b.clientTop,l=o.left+b.clientLeft;
      if(b.scrollHeight>b.clientHeight&&/auto|scroll/.test(st.overflowY))b.scrollTop+=n(i.top,i.bottom,t,t+b.clientHeight);
      if(b.scrollWidth>b.clientWidth&&/auto|scroll/.test(st.overflowX))b.scrollLeft+=n(i.left,i.right,l,l+b.clientWidth)}};
      globalThis[k]={generation:1,reveal:r}})();
    
})();