"""Shared Splitter scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def splitter_states_component(app: Citry) -> type[Component]:
    class CitryUiSplitterStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-splitter-ready>
            <h1>Splitter states</h1>
            <c-CSplitter c-sizes="[30, 70]" variant="outline">
              <c-CSplitterPanel id="nav" label="Navigation">Navigation</c-CSplitterPanel>
              <c-CSplitterPanel id="main" label="Main content">Main content</c-CSplitterPanel>
            </c-CSplitter>
            <c-CSplitter c-sizes="[20, 45, 35]" variant="soft" size="sm">
              <c-CSplitterPanel id="one" label="First panel">First</c-CSplitterPanel>
              <c-CSplitterPanel id="two" label="Second panel">Second</c-CSplitterPanel>
              <c-CSplitterPanel id="three" label="Third panel">Third</c-CSplitterPanel>
            </c-CSplitter>
            <c-CSplitter orientation="vertical" c-sizes="[35, 65]" size="lg">
              <c-CSplitterPanel id="top" label="Top panel">Top</c-CSplitterPanel>
              <c-CSplitterPanel id="bottom" label="Bottom panel">Bottom</c-CSplitterPanel>
            </c-CSplitter>
            <fieldset disabled>
              <legend>Disabled Splitter</legend>
              <c-CSplitter>
                <c-CSplitterPanel id="a" label="A">A</c-CSplitterPanel>
                <c-CSplitterPanel id="b" label="B">B</c-CSplitterPanel>
              </c-CSplitter>
            </fieldset>
            <div dir="rtl">
              <c-CSplitter c-sizes="[40, 60]">
                <c-CSplitterPanel id="right" label="Right">Right</c-CSplitterPanel>
                <c-CSplitterPanel id="left" label="Left">Left</c-CSplitterPanel>
              </c-CSplitter>
            </div>
            <div style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem">
              <c-CSplitter c-sizes="[45, 55]" variant="outline">
                <c-CSplitterPanel id="dark-a" label="Dark A">Dark A</c-CSplitterPanel>
                <c-CSplitterPanel id="dark-b" label="Dark B">Dark B</c-CSplitterPanel>
              </c-CSplitter>
            </div>
          </section>
        """

    return CitryUiSplitterStates
