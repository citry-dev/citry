/** @type {import('@storybook/server-webpack5').StorybookConfig} */
const config = {
  stories: ["../generated/server/**/*.stories.json"],
  addons: ["@storybook/addon-a11y", "@storybook/addon-docs"],
  framework: {
    name: "@storybook/server-webpack5",
    options: {},
  },
  core: {
    disableTelemetry: true,
  },
};

export default config;
