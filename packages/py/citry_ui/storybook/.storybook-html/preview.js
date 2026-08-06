import { renderCitryHtmlToCanvas } from "../src/html-adapter.js";

export const renderToCanvas = renderCitryHtmlToCanvas;

/** @type {import('@storybook/html-vite').Preview} */
const preview = {
  parameters: {
    controls: {
      expanded: true,
    },
  },
};

export default preview;
