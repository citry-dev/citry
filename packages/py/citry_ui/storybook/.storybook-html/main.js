/** @type {import('@storybook/html-vite').StorybookConfig} */
const config = {
  stories: ["../generated/html/**/*.stories.js"],
  addons: ["@storybook/addon-a11y", "@storybook/addon-docs"],
  framework: {
    name: "@storybook/html-vite",
    options: {},
  },
  core: {
    disableTelemetry: true,
  },
};

export default config;
