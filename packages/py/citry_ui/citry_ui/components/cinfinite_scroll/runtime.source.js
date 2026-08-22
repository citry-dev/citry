$component({
  props: {hasMore: {}, loading: {}, error: {}, disabled: {}, auto: {}, onLoadMore: {}},
  init: ({els, data, props, effect}) => {
    const root = els[0];
    if (!(root instanceof HTMLElement)) throw new Error('[citry-ui] CInfiniteScroll settled anatomy is invalid.');
    const content = root.querySelector(':scope > [data-citry-ui-part="content"]');
    const status = root.querySelector(':scope > [data-citry-ui-part="status"]');
    const action = root.querySelector(':scope > [data-citry-infinite-scroll-action]');
    const sentinel = root.querySelector(':scope > [data-citry-infinite-scroll-sentinel]');
    if (!content || !status || !(action instanceof HTMLButtonElement) || !sentinel) {
      throw new Error('[citry-ui] CInfiniteScroll required parts are missing.');
    }
    const statusParts = [...status.children];
    const loadLabel = action.children[0];
    const retryLabel = action.children[1];
    const invalid = new Set();
    let state = {hasMore:data.has_more, loading:data.loading, error:data.error, disabled:data.disabled, auto:data.auto};
    let callback = null;
    let requested = false;
    let observer = null;
    let lastReset = JSON.stringify([state.hasMore,state.loading,state.error]);
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CInfiniteScroll ${name} received invalid client value.`, value, root);
    };
    const release = () => { requested = false; };
    const request = (reason, sourceEvent) => {
      if (requested || state.disabled || state.loading || !state.hasMore || !callback || (state.error && reason !== 'retry')) return;
      requested = true;
      try {
        const result = callback({reason, sourceEvent});
        if (result && typeof result.then === 'function') Promise.resolve(result).catch(error => {
          console.error('[citry-ui] CInfiniteScroll onLoadMore promise failed.', error, root);
        }).finally(release);
      } catch (error) {
        release();
        console.error('[citry-ui] CInfiniteScroll onLoadMore callback failed.', error, root);
      }
    };
    const syncObserver = () => {
      if (observer) { observer.disconnect(); observer = null; }
      if (!state.auto || !callback || state.disabled || state.loading || state.error || !state.hasMore || !('IntersectionObserver' in window)) return;
      observer = new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting)) request('intersection', null);
      }, {root:null, rootMargin:data.root_margin, threshold:data.threshold});
      observer.observe(sentinel);
    };
    const sync = () => {
      content.setAttribute('aria-busy', String(state.loading));
      root.toggleAttribute('data-loading', state.loading);
      root.toggleAttribute('data-error', state.error && !state.loading);
      root.toggleAttribute('data-end', !state.hasMore && !state.loading && !state.error);
      root.toggleAttribute('data-disabled', state.disabled);
      root.toggleAttribute('data-auto', state.auto);
      action.hidden = !state.hasMore || state.loading;
      action.disabled = state.disabled;
      loadLabel.hidden = state.error;
      retryLabel.hidden = !state.error;
      statusParts[0].hidden = !state.loading;
      statusParts[1].hidden = !state.error || state.loading;
      statusParts[2].hidden = state.hasMore || state.loading || state.error;
      const resetKey = JSON.stringify([state.hasMore,state.loading,state.error]);
      if (resetKey !== lastReset) { requested = false; lastReset = resetKey; }
      syncObserver();
    };
    const onClick = event => request(state.error ? 'retry' : 'button', event);
    action.addEventListener('click', onClick);
    const mutations = new MutationObserver(release);
    mutations.observe(content, {childList:true, subtree:true});
    root.setAttribute('data-citry-infinite-scroll-initialized', '');
    effect(() => {
      const next = {
        hasMore: props.hasMore, loading: props.loading, error: props.error,
        disabled: props.disabled, auto: props.auto, onLoadMore: props.onLoadMore,
      };
      for (const name of ['hasMore','loading','error','disabled','auto']) {
        if (next[name] !== undefined && typeof next[name] !== 'boolean') report(name, next[name]);
        else { invalid.delete(name); state[name] = typeof next[name] === 'boolean' ? next[name] : data[{hasMore:'has_more',loading:'loading',error:'error',disabled:'disabled',auto:'auto'}[name]]; }
      }
      if (next.onLoadMore === undefined || next.onLoadMore === null) { callback = null; invalid.delete('onLoadMore'); }
      else if (typeof next.onLoadMore === 'function') { callback = next.onLoadMore; invalid.delete('onLoadMore'); }
      else report('onLoadMore', next.onLoadMore);
      sync();
    });
    return () => {
      action.removeEventListener('click', onClick);
      if (observer) observer.disconnect();
      mutations.disconnect();
      root.removeAttribute('data-citry-infinite-scroll-initialized');
    };
  },
});
