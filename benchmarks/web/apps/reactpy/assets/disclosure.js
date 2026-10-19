/* A supported ReactPy JavaScript component owns only the local disclosure. */
export function LocalDisclosure() {}

export function bind(node) {
  let mounted = false;
  return {
    create(type, props, children) { return { type, props, children }; },
    render() {
      if (mounted) return;
      mounted = true;
      node.innerHTML = `
        <aside id="local-disclosure">
          <button type="button" data-bench-action="disclosure" aria-expanded="false">Local details</button>
          <p id="disclosure-content" hidden>This disclosure needs no server request.</p>
          <label for="preserved-input">Local draft</label>
          <input id="preserved-input" value="Unchanged draft">
        </aside>`;
      const button = node.querySelector("button");
      button.addEventListener("click", () => {
        const open = button.getAttribute("aria-expanded") !== "true";
        button.setAttribute("aria-expanded", String(open));
        node.querySelector("#disclosure-content").hidden = !open;
      });
      window.__reactpyBoardObserver.localReady();
    },
    unmount() { node.replaceChildren(); mounted = false; },
  };
}
