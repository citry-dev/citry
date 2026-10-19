(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuTouchAndPen_290450", "0358499b3371817859209122f13a42bba5653bcb750f537974a6cd0e2054cd13")({
  data(){return {touchState:{phase:'idle',log:[],targetClicks:0}};},
  methods: {
    simulate(kind) {
      const state=this.touchState;
      state.phase='armed: synthetic probe';
      state.log.unshift(`armed synthetic ${kind}`);
      const target=document.querySelector(
        kind === 'scroll'
          ? '[data-context-menu-scroll-target]'
          : '[data-context-menu-touch-target]'
      );
      const fire=(type,id,x,y,buttons=1)=>target.dispatchEvent(
        new PointerEvent(type, {
          bubbles:true,
          pointerType:'touch',
          pointerId:id,
          clientX:x,
          clientY:y,
          buttons,
        })
      );
      fire('pointerdown',81,12,12);
      if (kind === 'hold') {
        state.log.unshift('synthetic hold: pointerup after 700 ms');
        setTimeout(()=>{
          fire('pointerup',81,12,12,0);
          state.phase='synthetic hold complete: use a trusted device';
        },725);
      } else if (kind === 'move') {
        fire('pointermove',81,28,12);
        fire('pointerup',81,28,12,0);
        state.phase='canceled: movement';
        state.log.unshift('canceled movement');
      } else if (kind === 'scroll') {
        const scroller=document.querySelector('.context-menu-touch__scroller');
        scroller.scrollTop += 24;
        scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
        fire('pointerup',81,12,12,0);
      } else if (kind === 'lost-up') {
        state.phase='armed: lost-up deadline pending';
        state.log.unshift('synthetic lost-up: absolute 10 s guard');
      } else {
        fire('pointerdown',82,14,14);
        fire('pointercancel',81,12,12,0);
        fire('pointercancel',82,14,14,0);
        state.phase='canceled: second pointer';
        state.log.unshift('canceled second pointer');
      }
    },
  },
});

})();