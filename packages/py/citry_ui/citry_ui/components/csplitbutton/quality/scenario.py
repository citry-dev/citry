"""Shared SplitButton scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def split_button_states_component(app: Citry) -> type[Component]:
    """Create the reusable SplitButton state and environment scenario."""

    class CitryUiSplitButtonStates(Component):
        citry = app

        class Kwargs:
            include_lifecycle: bool = True

        class Slots:
            pass

        class Events:
            def refresh(self) -> None:
                return None

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {"include_lifecycle": kwargs.include_lifecycle}

        template = """
          <section
            class="citry-ui-quality-stack split-button-quality"
            aria-labelledby="split-button-states-title"
            @c-quality-morph="refresh"
            x-data="{
              controlledOpen:false,
              submits:0,
              resets:0,
              last:'No action yet',
            }"
          >
            <h1 id="split-button-states-title">Split Button states</h1>

            <div class="split-button-quality__controls">
              <button type="button" @click="controlledOpen=!controlledOpen">
                Toggle controlled Menu
              </button>
            </div>

            <form
              id="split-button-quality-form"
              class="split-button-quality__form"
              @submit.prevent="submits += 1"
              @reset="resets += 1"
            >
              <label>Accession <input name="accession" value="G-104" required /></label>
              <c-CSplitButton
                id="quality-split-submit"
                label="Accession submit actions"
                menu_label="More accession submit actions"
                type="submit"
                c-primary_attrs="{'name':'action','value':'save'}"
                c-attrs="{
                  'data-quality-states':
                    'submit open-layer commands link choices group separator submenu danger form-data submitter'
                }"
                open
                $c-props="{onAction:(value)=>last=value}"
              >
                <c-fill name="default">Save accession</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="copy">Copy accession</c-CMenuItem>
                  <c-CMenuItem href="#split-button-quality-log">Open action log</c-CMenuItem>
                  <c-CMenuCheckboxItem value="public" checked="mixed">
                    Public record
                  </c-CMenuCheckboxItem>
                  <c-CMenuRadioGroup value="tiff">
                    <c-fill name="label">Export format</c-fill>
                    <c-fill name="default">
                      <c-CMenuRadioItem value="tiff">TIFF</c-CMenuRadioItem>
                      <c-CMenuRadioItem value="jpeg">JPEG</c-CMenuRadioItem>
                    </c-fill>
                  </c-CMenuRadioGroup>
                  <c-CMenuSeparator />
                  <c-CMenuGroup>
                    <c-fill name="label">Archive</c-fill>
                    <c-fill name="default">
                      <c-CMenuSubmenu value="regional">
                        <c-fill name="label">Regional archive</c-fill>
                        <c-fill name="default">
                          <c-CMenuItem value="alpine">Alpine collection</c-CMenuItem>
                          <c-CMenuSubmenu value="remote">
                            <c-fill name="label">Remote archive</c-fill>
                            <c-fill name="default">
                              <c-CMenuItem value="island">Island collection</c-CMenuItem>
                            </c-fill>
                          </c-CMenuSubmenu>
                        </c-fill>
                      </c-CMenuSubmenu>
                    </c-fill>
                  </c-CMenuGroup>
                  <c-CMenuItem value="withdraw" intent="danger">Withdraw accession</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>

              <c-CSplitButton
                label="Accession reset actions"
                menu_label="More accession reset actions"
                type="reset"
                variant="outline"
                c-attrs="{'data-quality-states':'reset outline md'}"
              >
                <c-fill name="default">Reset accession</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="restore">Restore previous accession</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>
            </form>

            <div class="citry-ui-quality-grid">
              <c-CSplitButton
                label="Controlled publication actions"
                menu_label="More controlled publication actions"
                match_width
                size="sm"
                $c-props="{
                  open:controlledOpen,
                  onOpenChange:(next)=>controlledOpen=next,
                }"
                c-attrs="{'data-quality-states':'controlled match-width sm'}"
              >
                <c-fill name="default">Publish record</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="preview">Preview record</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>

              <c-CSplitButton
                label="Loading image actions"
                menu_label="More loading image actions"
                loading
                loading_pos="start"
                c-attrs="{'data-quality-states':'loading loading-start menu-available'}"
              >
                <c-fill name="default">Save image</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="export">Export while saving</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>

              <c-CSplitButton
                label="Primary-disabled actions"
                menu_label="More primary-disabled actions"
                primary_disabled
                variant="ghost"
                c-attrs="{'data-quality-states':'primary-disabled ghost menu-available'}"
              >
                <c-fill name="default">Unavailable save</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="export-disabled-primary">Export instead</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>

              <c-CSplitButton
                label="Menu-disabled actions"
                menu_label="More menu-disabled actions"
                menu_disabled
                intent="warn"
                c-attrs="{'data-quality-states':'menu-disabled warn primary-available'}"
              >
                <c-fill name="default">Save without alternatives</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="unavailable">Unavailable alternative</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>

              <fieldset disabled>
                <legend>Disabled ancestry</legend>
                <c-CSplitButton
                  label="Disabled fieldset actions"
                  menu_label="More disabled fieldset actions"
                  loading
                  intent="danger"
                  size="lg"
                  c-attrs="{'data-quality-states':'disabled fieldset-disabled loading danger lg'}"
                >
                  <c-fill name="default">Remove specimen</c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="restore-disabled">Restore specimen</c-CMenuItem>
                  </c-fill>
                </c-CSplitButton>
              </fieldset>
            </div>

            <div class="split-button-quality__brand-grid">
              <div class="split-button-quality__orchard" style="color-scheme:light">
                <c-CSplitButton
                  label="Orchard actions"
                  menu_label="More Orchard actions"
                  open
                  c-attrs="{'data-quality-states':'brand-orchard light open'}"
                >
                  <c-fill name="default">Publish Orchard record</c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="orchard">Orchard archive</c-CMenuItem>
                  </c-fill>
                </c-CSplitButton>
              </div>

              <div class="split-button-quality__harbor" style="color-scheme:dark" dir="rtl">
                <c-CSplitButton
                  label="إجراءات سجل هاربور"
                  menu_label="المزيد من إجراءات سجل هاربور"
                  block
                  placement="top-end"
                  c-attrs="{'data-quality-states':'brand-harbor dark rtl narrow long-content block placement'}"
                >
                  <c-fill name="default">نشر سجل العينة الساحلية الطويلة</c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="harbor">أرشيف هاربور</c-CMenuItem>
                  </c-fill>
                </c-CSplitButton>
              </div>
            </div>

            <c-if cond="include_lifecycle">
              <div>
                <c-CSplitButton
                  label="Lifecycle actions"
                  menu_label="More lifecycle actions"
                  c-attrs="{'data-quality-states':'lifecycle removal restore morph-target'}"
                >
                  <c-fill name="default">Commit lifecycle record</c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="lifecycle-copy">Copy lifecycle record</c-CMenuItem>
                  </c-fill>
                </c-CSplitButton>
              </div>
            </c-if>

            <output
              id="split-button-quality-log"
              aria-live="polite"
              x-text="`Submits: ${submits}; resets: ${resets}; last: ${last}`"
            >Submits: 0; resets: 0; last: No action yet</output>
          </section>
        """

        css = """
          :where(.split-button-quality__controls, .split-button-quality__form) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            align-items: center;
          }
          :where(.split-button-quality__brand-grid) {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
            gap: 1rem;
          }
          :where(.split-button-quality__orchard, .split-button-quality__harbor) {
            min-block-size: 14rem;
            padding: 1rem;
            border-radius: 0.875rem;
          }
          :where(.split-button-quality__orchard) {
            background: #f5f0df;
            --cui-button-background: #315f37;
            --cui-button-foreground: #fffdf5;
            --cui-menu-background: #fffdf5;
            --cui-menu-foreground: #203422;
            --cui-menu-focus-background: #d9e9cf;
            --cui-menu-focus-foreground: #17351c;
            --cui-split-button-divider-color: #c5d7bb;
          }
          :where(.split-button-quality__harbor) {
            inline-size: min(100%, 20rem);
            background: #102b38;
            --cui-button-background: #c6ecff;
            --cui-button-foreground: #082633;
            --cui-menu-background: #173c4c;
            --cui-menu-foreground: #eefaff;
            --cui-menu-focus-background: #95d9f4;
            --cui-menu-focus-foreground: #062531;
            --cui-split-button-divider-color: #29586b;
          }
          @media (prefers-reduced-motion: reduce) {
            :where(.split-button-quality) {
              --cui-menu-duration: 0ms;
            }
          }
          @media (forced-colors: active) {
            :where(.split-button-quality__orchard, .split-button-quality__harbor) {
              border: 1px solid CanvasText;
            }
          }
        """

    return CitryUiSplitButtonStates
