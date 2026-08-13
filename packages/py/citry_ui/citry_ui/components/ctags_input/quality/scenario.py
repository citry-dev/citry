"""Shared TagsInput scenario used by repository quality tools."""

from __future__ import annotations

from typing import Any

from citry import Citry, Component


def tags_input_states_component(app: Citry) -> type[Component]:
    """Create the reusable TagsInput state and environment scenario."""

    class CitryUiTagsInputStates(Component):
        citry = app

        class Kwargs:
            include_lifecycle: bool = True
            morph_step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def refresh(self, state: Any) -> CitryUiTagsInputStates:
                state.morph_step += 1
                component_type: Any = CitryUiTagsInputStates
                return component_type(
                    include_lifecycle=state.morph_step not in {2, 4},
                    morph_step=state.morph_step,
                )

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "include_lifecycle": kwargs.include_lifecycle,
                "morph_step": kwargs.morph_step,
            }

        template = """
          <section
            class="citry-ui-quality-stack tags-input-quality"
            aria-labelledby="tags-input-states-title"
            @c-quality-morph="refresh"
            x-data="{
              controlledTags:['controlled-one'],
              controlledDraft:'owner draft',
              acceptControlled:false,
              submits:0,
              resets:0,
              last:'No TagsInput action yet',
            }"
          >
            <h1 id="tags-input-states-title">TagsInput states</h1>
            <output hidden data-quality-morph-step>{{ morph_step }}</output>

            <form
              id="tags-input-quality-form"
              class="tags-input-quality__form"
              @submit.prevent="
                submits += 1;
                last = JSON.stringify(
                  Array.from(new FormData($event.target).entries())
                );
              "
              @reset="resets += 1"
            >
              <c-CField required>
                <c-fill name="label">Required survey labels</c-fill>
                <c-fill name="description">
                  Add labels with Enter, comma, or a pasted newline.
                </c-fill>
                <c-fill name="default">
                  <c-CTagsInput
                    name="labels"
                    c-value="['alpine', 'ordered']"
                    c-attrs="{
                      'data-quality-states':
                        'required ordered form-data repeated-values editable reset field description'
                    }"
                    $c-props="{
                      onValueChange:(next,detail)=>
                        last=`${detail.source}: ${JSON.stringify(next)}`,
                      onValueInvalid:(reason)=>last=`Rejected ${reason}`,
                    }"
                  />
                </c-fill>
              </c-CField>
              <button type="submit">Submit quality Form</button>
              <button type="reset">Reset quality Form</button>
            </form>

            <c-CTagsInput
              id="tags-input-quality-external"
              name="external-labels"
              form="tags-input-quality-form"
              c-value="['external-one', 'external-two']"
              c-input_attrs="{'aria-label':'External Form labels'}"
              c-attrs="{
                'data-quality-states':
                  'external-form external-owner ordered repeated-values'
              }"
            />

            <div class="citry-ui-quality-grid">
              <c-CTagsInput
                id="tags-input-quality-draft"
                input_value="unfinished draft"
                max_tags="4"
                c-value="['paste-base']"
                c-input_attrs="{'aria-label':'Paste and draft labels'}"
                c-attrs="{
                  'data-quality-states':
                    'draft unfinished-validity paste selection ime delimiter maximum'
                }"
              />

              <c-CTagsInput
                id="tags-input-quality-controlled"
                c-input_attrs="{'aria-label':'Controlled labels'}"
                c-attrs="{
                  'data-quality-states':
                    'controlled controlled-value controlled-draft refusal acceptance'
                }"
                $c-props="{
                  value:controlledTags,
                  inputValue:controlledDraft,
                  onValueChange:(next,detail)=>{
                    last=`Requested ${JSON.stringify(next)}`;
                    if (acceptControlled) {
                      controlledTags=next;
                      controlledDraft=detail.nextInputValue;
                    }
                  },
                  onInputValueChange:(next)=>controlledDraft=next,
                }"
              />

              <c-CTagsInput
                id="tags-input-quality-readonly"
                name="readonly-labels"
                form="tags-input-quality-form"
                readonly
                input_value="dormant draft"
                c-value="['readonly-one', 'readonly-two']"
                c-input_attrs="{'aria-label':'Readonly labels'}"
                c-attrs="{
                  'data-quality-states':
                    'readonly dormant-draft hidden-transport repeated-values'
                }"
              />

              <c-CTagsInput
                id="tags-input-quality-disabled"
                name="disabled-labels"
                form="tags-input-quality-form"
                disabled
                c-value="['omitted-value']"
                c-input_attrs="{'aria-label':'Disabled labels'}"
                c-attrs="{
                  'data-quality-states':'disabled omitted-transport'
                }"
              />

              <c-CTagsInput
                id="tags-input-quality-empty"
                required
                variant="plain"
                size="sm"
                c-input_attrs="{'aria-label':'Empty required labels'}"
                c-attrs="{
                  'data-quality-states':'empty required plain sm invalid-focus'
                }"
              />

              <fieldset disabled>
                <legend>Disabled native ancestry</legend>
                <c-CField required>
                  <c-fill name="label">Fieldset labels</c-fill>
                  <c-fill name="default">
                    <c-CTagsInput
                      name="fieldset-labels"
                      c-value="['fieldset']"
                      c-attrs="{
                        'data-quality-states':
                          'fieldset-disabled field disabled required'
                      }"
                    />
                  </c-fill>
                </c-CField>
              </fieldset>
            </div>

            <div class="tags-input-quality__brand-grid">
              <div
                class="tags-input-quality__orchard"
                style="color-scheme:light"
              >
                <c-CTagsInput
                  variant="outline"
                  size="md"
                  c-value="['orchard', 'pollinator']"
                  c-input_attrs="{'aria-label':'Orchard labels'}"
                  c-attrs="{
                    'data-quality-states':
                      'brand-orchard light outline md selector-override'
                  }"
                />
              </div>

              <div
                class="tags-input-quality__harbor"
                style="color-scheme:dark"
                dir="rtl"
              >
                <c-CTagsInput
                  variant="filled"
                  size="lg"
                  c-value="[
                    'وسم-طويل-جدا-لسجل-الميناء-الساحلي-الذي-يبقى-داخل-العنصر',
                    'ميناء',
                  ]"
                  c-input_attrs="{'aria-label':'وسوم الميناء'}"
                  c-attrs="{
                    'data-quality-states':
                      'brand-harbor dark rtl narrow long-content filled lg keyboard touch'
                  }"
                />
              </div>
            </div>

            <c-if cond="include_lifecycle">
              <div>
                <c-CTagsInput
                  #c-key="'tags-input-quality-lifecycle'"
                  id="tags-input-quality-lifecycle"
                  input_value="preserved draft"
                  c-value="['preserved-one', 'preserved-two']"
                  c-input_attrs="{'aria-label':'Lifecycle labels'}"
                  c-attrs="{
                    'data-quality-states':
                      'lifecycle morph-target cleanup removal restore composition-node selection-preservation'
                  }"
                />
              </div>
            </c-if>

            <label>
              <input type="checkbox" x-model="acceptControlled" />
              Accept controlled value requests
            </label>
            <output
              id="tags-input-quality-log"
              aria-live="polite"
              x-text="`Submits: ${submits}; resets: ${resets}; last: ${last}`"
            >Submits: 0; resets: 0; last: No TagsInput action yet</output>
          </section>
        """

        css = """
          :where(.tags-input-quality__form) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            align-items: end;
          }

          :where(.tags-input-quality__brand-grid) {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
            gap: 1rem;
          }

          :where(.tags-input-quality__orchard, .tags-input-quality__harbor) {
            min-block-size: 12rem;
            min-inline-size: 0;
            padding: 1rem;
            border-radius: 0.875rem;
          }

          :where(.tags-input-quality__orchard) {
            background: #f5f0df;
            --cui-tags-input-background: #fffdf5;
            --cui-tags-input-border-color: #78916d;
            --cui-tags-input-focus-color: #315f37;
            --cui-tags-input-tag-background: #d9e9cf;
          }

          :where(.tags-input-quality__harbor) {
            inline-size: min(100%, 20rem);
            background: #102b38;
            --cui-tags-input-background: #173c4c;
            --cui-tags-input-foreground: #eefaff;
            --cui-tags-input-border-color: #72b5ce;
            --cui-tags-input-focus-color: #c6ecff;
            --cui-tags-input-tag-background: #29586b;
            --cui-tags-input-tag-foreground: #eefaff;
          }

          .tags-input-quality__orchard
          [data-citry-ui-part="remove"] {
            border-radius: 999px;
          }

          @media (forced-colors: active) {
            :where(.tags-input-quality__orchard, .tags-input-quality__harbor) {
              border: 1px solid CanvasText;
            }
          }

          @media (prefers-reduced-motion: reduce) {
            :where(.tags-input-quality) * {
              transition-duration: 0ms !important;
            }
          }

          @media print {
            :where(.tags-input-quality__orchard, .tags-input-quality__harbor) {
              min-block-size: auto;
              background: transparent;
              color: black;
            }
          }
        """

    return CitryUiTagsInputStates
