(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuPositioningAndRtl_639e56", "0508d0243d3ce562a601d8755af2c0aa8843a8df64efb287efd56bbe6bb27694")({data(){return {
    surfaceDir:'ltr',
    targetDir:'rtl',
    externalOpen:false,
    lastPoint:'none',
    lastInvocation:'none',
  };},
  // This block holds the menus' callbacks and the fixture controls.
  // The controls need window or document, which template expressions
  // cannot reach.
  methods: {
    // Only an opening has a point worth showing, so a close leaves the
    // last accepted point on screen.
    recordAcceptedPoint(next, detail) {
      if (next) {
        this.lastPoint = `${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
        this.lastInvocation = detail.reason === 'contextmenu' ? 'pointer' : detail.reason;
      }
    },
    // This menu is controlled, so owner state follows every request.
    // Returning true claims an opening, which blocks the browser's own
    // menu; a close needs no claim.
    claimExternalOpen(next, detail) {
      this.externalOpen = next;
      this.recordAcceptedPoint(next, detail);
      if (next) return true;
    },
    openFromOwnerState() {
      this.externalOpen=true;
      this.lastInvocation='external';
      // Read the point after the open state has rendered and positioned.
      this.$nextTick(()=>setTimeout(()=>{
        const point=document.querySelector('#context-position-external-point');
        const box=point?.getBoundingClientRect();
        if (box) this.lastPoint=`${Math.round(box.x)}, ${Math.round(box.y)}`;
      }));
    },
    resizeRepairFixture() {
      window.dispatchEvent(new Event('resize'));
    },
    testOffscreenRejection() {
      const target=this.$el.querySelector('[data-context-menu-offscreen-target]');
      target.focus();
      target.dispatchEvent(new KeyboardEvent('keydown', {
        bubbles:true,
        key:'F10',
        shiftKey:true,
      }));
    },
    viewportSummary() {
      const width=Math.round(visualViewport?.width ?? innerWidth);
      const height=Math.round(visualViewport?.height ?? innerHeight);
      return `Visual viewport: ${width} x ${height} CSS px`;
    },
  },
});

})();