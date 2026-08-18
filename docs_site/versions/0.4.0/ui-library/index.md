---
title: Citry UI
url: https://citry.dev/v/0.4.0/ui-library/
description: "Build application interfaces with Citry's first-party styled component library."
---
# Citry UI

Citry UI is the first-party styled component library for Citry. Its components
render useful HTML on the server, add browser behavior through Citry's client
runtime, and expose documented CSS variables and parts for application themes.

The library is a separate Python distribution. Install it when an application
wants the built-in design system, while keeping the core `citry` package small.

## Start with the library

1. [Install and register Citry UI](/v/0.4.0/ui-library/installation/).
2. Use a component from the [Components](#components) section.
3. [Set colors, spacing, and component parts](/v/0.4.0/ui-library/theming/) for your
   application.

## Components


<section aria-labelledby="ui-library-actions">
  <h2 id="ui-library-actions">Actions</h2>
  <ul>
    <li>
      <a href="/ui-library/components/button/">Button</a> - Render styled native actions, links, and form submitters with Citry UI Button.
    </li><li>
      <a href="/ui-library/components/button-group/">Button Group</a> - Arrange related Citry UI actions as one named group.
    </li><li>
      <a href="/ui-library/components/split-button/">Split Button</a> - Keep one dominant action visible beside a Menu of related actions.
    </li><li>
      <a href="/ui-library/components/toggle/">Toggle</a> - Build standalone or grouped pressed Buttons with Citry UI.
    </li><li>
      <a href="/ui-library/components/toolbar/">Toolbar</a> - Group persistent controls under one name and one page Tab stop.
    </li>
  </ul>
</section><section aria-labelledby="ui-library-forms-inputs">
  <h2 id="ui-library-forms-inputs">Forms and inputs</h2>
  <ul>
    <li>
      <a href="/ui-library/components/field-input/">Field and Input</a> - Build labelled native text controls with Citry UI Field and Input.
    </li><li>
      <a href="/ui-library/components/textarea/">Textarea</a> - Enter multiline plain text with native editing, forms, validation, and optional browser control.
    </li><li>
      <a href="/ui-library/components/native-select/">Native Select</a> - Choose one value with native keyboard, touch, forms, validation, and an optional controlled browser value.
    </li><li>
      <a href="/ui-library/components/checkbox/">Checkbox</a> - Choose independent Boolean options with native forms, mixed state, and controlled browser checkedness.
    </li><li>
      <a href="/ui-library/components/radio/">Radio</a> - Select one visible option with native Citry UI Radio Groups and Radios.
    </li><li>
      <a href="/ui-library/components/switch/">Switch</a> - Change an immediate on or off setting with a native Citry UI Switch.
    </li><li>
      <a href="/ui-library/components/combobox/">Combobox</a> - Search a local or remote collection and submit one stable option value.
    </li><li>
      <a href="/ui-library/components/listbox/">Listbox</a> - Choose one or more values from a persistent collection.
    </li><li>
      <a href="/ui-library/components/select/">Select</a> - Choose one value from a compact, styled form control.
    </li><li>
      <a href="/ui-library/components/multi-select/">MultiSelect</a> - Choose several fixed values from a compact, styled form control.
    </li><li>
      <a href="/ui-library/components/tags-input/">TagsInput</a> - Create and submit an ordered list of free-form text tags.
    </li><li>
      <a href="/ui-library/components/editable/">Editable</a> - Edit one short text value in place without giving up native form behavior.
    </li><li>
      <a href="/ui-library/components/file-input/">File input and drop target</a> - Select files with a native picker or an accessible drop-backed picker.
    </li><li>
      <a href="/ui-library/components/form/">Form</a> - Compose native submission, validation, reset, and shared control state with Citry UI Form.
    </li>
  </ul>
</section><section aria-labelledby="ui-library-layout">
  <h2 id="ui-library-layout">Layout</h2>
  <ul>
    <li>
      <a href="/ui-library/components/stack-group/">Stack and Group</a> - Arrange Citry UI content in predictable vertical stacks and wrapping horizontal groups.
    </li><li>
      <a href="/ui-library/components/container-grid/">Container and Grid</a> - Constrain page content, build responsive equal grids, and add asymmetric spans when needed.
    </li><li>
      <a href="/ui-library/components/scroll-area/">ScrollArea</a> - Keep bounded content reachable through native scrolling.
    </li><li>
      <a href="/ui-library/components/divider/">Divider</a> - Separate sections semantically or visually with Citry UI.
    </li><li>
      <a href="/ui-library/components/splitter/">Splitter</a> - Resize two or more adjacent application panels.
    </li>
  </ul>
</section><section aria-labelledby="ui-library-data-display">
  <h2 id="ui-library-data-display">Data display</h2>
  <ul>
    <li>
      <a href="/ui-library/components/avatar/">Avatar</a> - Present image identities with explicit names and reliable fallbacks.
    </li><li>
      <a href="/ui-library/components/image/">Image</a> - Render native responsive images with stable geometry and explicit alternative text.
    </li><li>
      <a href="/ui-library/components/badge/">Badge</a> - Present compact status, category, count, and metadata labels with Citry UI.
    </li><li>
      <a href="/ui-library/components/card/">Card</a> - Group related content, media, metadata, and actions in a flexible Citry UI surface.
    </li><li>
      <a href="/ui-library/components/carousel/">Carousel</a> - Browse composed content with native Scroll Snap and explicit controls.
    </li><li>
      <a href="/ui-library/components/icon/">Icon</a> - Render a consistent, accessible set of local SVG symbols with Citry UI Icon.
    </li><li>
      <a href="/ui-library/components/list/">List</a> - Compose semantic content, navigation, and action lists with Citry UI.
    </li><li>
      <a href="/ui-library/components/table/">Table</a> - Present finite server-owned records in a styled native Table.
    </li><li>
      <a href="/ui-library/components/tag/">Tag and TagGroup</a> - Present descriptive, selectable, actionable, and removable Tag collections.
    </li><li>
      <a href="/ui-library/components/tree/">Tree</a> - Explore and select hierarchical application data.
    </li>
  </ul>
</section><section aria-labelledby="ui-library-navigation">
  <h2 id="ui-library-navigation">Navigation</h2>
  <ul>
    <li>
      <a href="/ui-library/components/breadcrumbs/">Breadcrumbs</a> - Show hierarchical page location with semantic Citry UI Breadcrumbs.
    </li><li>
      <a href="/ui-library/components/pagination/">Pagination</a> - Navigate finite page sequences with native links or client-owned controls.
    </li><li>
      <a href="/ui-library/components/stepper/">Stepper</a> - Communicate and optionally navigate ordered workflow progress.
    </li><li>
      <a href="/ui-library/components/tabs/">Tabs</a> - Organize keyboard-accessible views with Citry UI Tabs.
    </li><li>
      <a href="/ui-library/components/navigation-menu/">NavigationMenu</a> - Compose native website navigation with rich disclosure panels.
    </li>
  </ul>
</section><section aria-labelledby="ui-library-feedback-status">
  <h2 id="ui-library-feedback-status">Feedback and status</h2>
  <ul>
    <li>
      <a href="/ui-library/components/alert/">Alert</a> - Present persistent feedback with clear intent, optional actions, and deliberate announcement urgency.
    </li><li>
      <a href="/ui-library/components/progress/">Progress</a> - Communicate determinate and indeterminate task progress with a native Citry UI progress element.
    </li><li>
      <a href="/ui-library/components/skeleton/">Skeleton</a> - Compose precise loading placeholders from visible primitives.
    </li><li>
      <a href="/ui-library/components/spinner/">Spinner</a> - Show compact unknown-duration activity with a labelled Citry UI Spinner.
    </li><li>
      <a href="/ui-library/components/toast/">Toast</a> - Deliver queued, timed application feedback with Citry UI.
    </li>
  </ul>
</section><section aria-labelledby="ui-library-overlays-disclosure">
  <h2 id="ui-library-overlays-disclosure">Overlays and disclosure</h2>
  <ul>
    <li>
      <a href="/ui-library/components/accordion/">Accordion</a> - Organize related sections with native headings, controlled expansion, stable panel content, and nested groups.
    </li><li>
      <a href="/ui-library/components/disclosure/">Disclosure</a> - Reveal one independent block of supporting content.
    </li><li>
      <a href="/ui-library/components/alert-dialog/">AlertDialog</a> - Ask for an immediate cancel-or-action decision in an urgent modal prompt.
    </li><li>
      <a href="/ui-library/components/dialog/">Dialog</a> - Build accessible native modal workflows with Citry UI Dialog.
    </li><li>
      <a href="/ui-library/components/drawer/">Drawer</a> - Build accessible modal side Drawers and Sheets with Citry UI.
    </li><li>
      <a href="/ui-library/components/menu/">Menu</a> - Present commands, links, application choices, and nested command collections from one Button.
    </li><li>
      <a href="/ui-library/components/context-menu/">ContextMenu</a> - Offer target-relative application commands while preserving browser context actions.
    </li><li>
      <a href="/ui-library/components/command-palette/">CommandPalette</a> - Search and run grouped application commands in a modal dialog.
    </li><li>
      <a href="/ui-library/components/popover/">Popover</a> - Place accessible interactive content beside a Button with Citry UI Popover.
    </li><li>
      <a href="/ui-library/components/tooltip/">Tooltip</a> - Add accessible, noninteractive descriptions to focusable controls with Citry UI Tooltip.
    </li><li>
      <a href="/ui-library/components/hover-card/">HoverCard</a> - Preview supplementary content behind a link or control.
    </li>
  </ul>
</section>


Citry UI is currently a preview. Review the package version before upgrading
and test the component states your application depends on.