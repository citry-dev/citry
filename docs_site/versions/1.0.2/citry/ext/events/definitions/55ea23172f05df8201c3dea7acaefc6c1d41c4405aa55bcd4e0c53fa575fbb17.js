try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "RemoteStarCatalog_57534a", "cdeeeea1d954b52f87724aedc756d197b5884ad1d98729bf04c21ef008eab56c")({
  data() {
    return {
      async loadStars({ query, signal }) {
        await new Promise((resolve, reject) => {
          const timer = setTimeout(resolve, 350);
          signal.addEventListener('abort', () => {
            clearTimeout(timer);
            reject(new DOMException('Aborted', 'AbortError'));
          }, { once: true });
        });
        if (query.toLowerCase() === 'offline') {
          throw new Error('Catalog unavailable');
        }
        const stars = [
          { value: 'vega', label: 'Vega', description: 'Blue-white star in Lyra' },
          { value: 'rigel', label: 'Rigel', description: 'Blue supergiant in Orion' },
          { value: 'sirius', label: 'Sirius', description: 'Brightest star in the night sky' },
          { value: 'betelgeuse', label: 'Betelgeuse', description: 'Red supergiant in Orion' },
        ];
        const needle = query.toLowerCase();
        return stars.filter((star) => star.label.toLowerCase().includes(needle));
      },
    };
  },
});

})();
__citryRuntime.finishScript("4782305ace56e6dd3a00c936a9248f21a82e9698bfed053cac6eed3831e2a830");
} catch (error) {
__citryRuntime.finishScript("4782305ace56e6dd3a00c936a9248f21a82e9698bfed053cac6eed3831e2a830", error);
}