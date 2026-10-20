// A ReactPy JavaScript component: the browser renders the API line from the
// props the Python side passes. ReactPy turns a prop's snake_case name into
// camelCase on the way, so Python's `api_base` arrives as `apiBase`.
export function ApiLine(props) {
  return "API: " + props.apiBase;
}

// ReactPy calls bind() with the element it reserved for the component, then
// create() and render() each time the props change.
export function bind(node) {
  return {
    create: (type, props) => type(props),
    render: (text) => {
      node.textContent = text;
    },
    unmount: () => node.replaceChildren(),
  };
}
