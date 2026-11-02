(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuTouchAndPen_340485", "e9893bf0d5e5774c315a415950d562289c4a4afab4e50210d66e97bfeebacf91")({
  data(){return {touchState:{phase:'idle',log:[],targetClicks:0}};},
  methods: {
    // Log every open and close, so the ledger shows which requests
    // the touch card accepted.
    recordTouchRequest(next, detail) {
      const state = this.touchState;
      state.phase = next ? 'accepted' : 'idle';
      state.log.unshift(`${next ? 'accepted' : 'closed'} ${detail.reason}`);
    },
    // The scrollable card stays closed, so its menu shows that a
    // refused request keeps the browser's own menu. Any return other
    // than true refuses; returning false makes the refusal explicit.
    refuseScrollCardRequest(next, detail) {
      this.touchState.phase = 'controlled refused';
      this.touchState.log.unshift(`refused ${detail.reason}`);
      return false;
    },
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