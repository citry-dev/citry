(function() {

__citryRuntime.registerTypeOptions.bind(null, "RemoteStarCatalog_0ebba2", "cdeeeea1d954b52f87724aedc756d197b5884ad1d98729bf04c21ef008eab56c")({
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