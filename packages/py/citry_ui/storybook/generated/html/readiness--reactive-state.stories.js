import {
  loadCitryScenario,
  renderCitryScenario,
} from "../../src/html-adapter.js";

const meta = {
  title: "Citry UI/Readiness/Reactive state",
  argTypes: {
  "generation": {
    "control": {
      "type": "select"
    },
    "description": "Replacement generation used by the lifecycle audit.",
    "options": [
      "first",
      "second",
      "delayed",
      "never",
      "slow"
    ]
  }
},
  parameters: {
  "citry": {
    "catalogSchemaVersion": 2,
    "clientInteractive": true,
    "generatorVersion": 1,
    "scenarioId": "readiness/reactive-state",
    "sourceDigest": "d0318e68bf1d239351359d42716d16c3f2e6cc072df431ab29f0e4c20f18bebe",
    "readySelector": ".citry-ui-readiness-probe[data-ready=\"true\"]",
    "readyTimeoutMs": 1500
  },
  "docs": {
    "description": {
      "component": "Contributor-only pressure probe for client state, fragment assets, replacement, and cleanup."
    },
    "source": {
      "code": "# Contributor-only readiness probe. Production component specifications\n# are authored separately before they enter the public Citry UI catalog.",
      "language": "python"
    }
  }
},
  tags: ["autodocs"],
};

export default meta;

export const Preview = {
  name: "Preview",
  args: {
  "generation": "first"
},
  loaders: [loadCitryScenario],
  render: renderCitryScenario,
};
