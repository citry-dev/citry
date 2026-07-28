import {
  loadCitryScenario,
  renderCitryScenario,
} from "../../src/html-adapter.js";

const meta = {
  title: "Citry UI/Tabs/Server-selected",
  argTypes: {
  "selected": {
    "control": {
      "type": "select"
    },
    "description": "Server-selected tab.",
    "options": [
      "account",
      "security"
    ]
  },
  "orientation": {
    "control": {
      "type": "select"
    },
    "description": "Tab-list orientation metadata.",
    "options": [
      "horizontal",
      "vertical"
    ]
  },
  "direction": {
    "control": {
      "type": "select"
    },
    "description": "Writing direction metadata.",
    "options": [
      "ltr",
      "rtl"
    ]
  },
  "activation": {
    "control": {
      "type": "select"
    },
    "description": "Activation metadata only in this static component.",
    "options": [
      "automatic",
      "manual"
    ]
  }
},
  parameters: {
  "citry": {
    "catalogSchemaVersion": 2,
    "clientInteractive": false,
    "generatorVersion": 1,
    "scenarioId": "tabs/server-selected",
    "sourceDigest": "f30a1a3bf159799b5a348c7689ce27b9cf167171a6ea2f6c4c143be18b6776dd"
  },
  "docs": {
    "description": {
      "component": "Static ARIA relationships and server-selected state; keyboard behavior is not implemented yet."
    },
    "source": {
      "code": "from citry import Component\n\nclass AccountTabs(Component):\n    template = \"\"\"\n      <c-CTabs default_value=\"account\">\n        {# CTabList, CTab, and CTabPanel children #}\n      </c-CTabs>\n    \"\"\"",
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
  "selected": "account",
  "orientation": "horizontal",
  "direction": "ltr",
  "activation": "automatic"
},
  loaders: [loadCitryScenario],
  render: renderCitryScenario,
};
