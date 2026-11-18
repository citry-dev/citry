try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "RemoteStarCatalog_f7178b", "cdeeeea1d954b52f87724aedc756d197b5884ad1d98729bf04c21ef008eab56c")({
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
__citryRuntime.finishScript("5a308d4854ab0082c7b8d94d095ba067e2ced3570c2123314d2228a02730e683");
} catch (error) {
__citryRuntime.finishScript("5a308d4854ab0082c7b8d94d095ba067e2ced3570c2123314d2228a02730e683", error);
}