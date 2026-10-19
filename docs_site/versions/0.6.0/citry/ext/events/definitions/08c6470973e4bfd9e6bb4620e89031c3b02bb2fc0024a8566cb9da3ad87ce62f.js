(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuPositioningAndRtl_bf8030", "4124b3fa219b76e695886bf1ba48da6117dad3de8141a1b378549d84ab2ceb46")({data(){return {
    surfaceDir:'ltr',
    targetDir:'rtl',
    externalOpen:false,
    lastPoint:'none',
    lastInvocation:'none',
  };},
  // Template expressions cannot reach window or document, so the
  // fixture controls that need them live here.
  methods: {
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