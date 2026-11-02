(function() {

      (()=>{const r=Symbol.for("citry-ui:scroll-geometry"),i=globalThis[r];
      if(i!==void 0){if(i.generation!==1)throw new Error(
      "[citry-ui] incompatible scroll geometry runtime; reload the page.");
      return}const l=(o,n)=>Math.max(0,o-n),t=(o,n)=>Math.min(Math.max(Number.isFinite(o)?o:0,0),n),
      c=(o,n,e)=>t(e?-o:o,n),m=(o,n,e)=>{const a=t(o,n);return e?-a:a};
      globalThis[r]={generation:1,maximum:l,clamp:t,horizontalFromRaw:c,horizontalToRaw:m}})();
    
})();