import { renderCitryServerToCanvas } from "../src/server-adapter.js";

export const renderToCanvas = renderCitryServerToCanvas;

/** @type {import('@storybook/server-webpack5').Preview} */
const preview = {
  parameters: {
    controls: {
      expanded: true,
    },
    server: {
      url: "/citry/ext/storybook_scenarios/render",
    },
  },
};

export default preview;
