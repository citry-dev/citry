from __future__ import annotations

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputMorphAndCleanup(Component):
    class Kwargs:
        step: int = 0

    class Slots:
        pass

    class Events:
        def refresh(self) -> TagsInputMorphAndCleanup:
            return TagsInputMorphAndCleanup()

        def advance(self) -> TagsInputMorphAndCleanup:
            return TagsInputMorphAndCleanup(step=2)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        baseline = ("server-one", "server-two")
        if kwargs.step >= 2:
            baseline = ("new-server-baseline",)
        return {"baseline": baseline, "step": kwargs.step}

    template = """
      <section
        class="tags-input-morph"
        x-data="{
          controlled:false,
          tags:['owner-one'],
          mounted:true,
        }"
      >
        <div class="tags-input-morph__controls">
          <button type="button" @c-click="refresh">
            Morph with the same baseline
          </button>
          <button type="button" @c-click="advance">
            Morph to a new baseline
          </button>
          <button type="button" @click="controlled=!controlled">
            Toggle controlled handoff
          </button>
          <button type="button" @click="mounted=!mounted">
            Remove or restore the fixture
          </button>
        </div>

        <p>Server step: <output>{{ step }}</output></p>

        <template x-if="mounted">
          <div>
            <c-CTagsInput
              #c-key="'tags-input-morph-target'"
              id="tags-input-morph-target"
              c-value="baseline"
              input_value="unfinished"
              c-input_attrs="{'aria-label':'Morph labels'}"
              $c-props="{
                value:controlled ? tags : null,
                onValueChange:(next)=>{
                  if (controlled) tags=next;
                },
              }"
            />
          </div>
        </template>

        <p>
          Unchanged server baselines preserve uncontrolled tags, draft,
          selection, and focus. Step two supplies a new baseline. An active
          composition keeps the exact editor node through either morph.
        </p>
      </section>
    """

    css = """
      :where(.tags-input-morph) {
        display: grid;
        gap: 1rem;
        max-inline-size: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-morph__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.tags-input-morph p) {
        margin: 0;
      }
    """


preview = TagsInputMorphAndCleanup()

preview  # noqa: B018
