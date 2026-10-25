"""
Open overlays follow the server's `open` and `disabled` inputs and stay open
when a server event re-renders the component that contains them without
removing them.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui.components.ccommand_palette import CCommandPaletteCommand

pytestmark = pytest.mark.e2e

# Each component's owner template. The default branch renders one overlay
# that takes the server's `open` (when the component has one) and `disabled`
# inputs and logs every `onOpenChange` call; the `pair` branch renders two such
# overlays that log their instance number; the controlled branch drives `open`
# from the owner's Vue data instead. The overlay's own markup never changes
# between renders; only the owner's step counter and the server inputs do.
_TEMPLATES: dict[str, str] = {
    "chover_card": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CHoverCard
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <a href="#card" c-bind="activator_attrs">Open overlay</a>
              </c-fill>
              <c-fill name="default">Card body</c-fill>
            </c-CHoverCard>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CHoverCard
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <a href="#card" c-bind="activator_attrs">Open overlay</a>
                </c-fill>
                <c-fill name="default">Card body</c-fill>
              </c-CHoverCard>
            </div>
            <div class="instance">
              <c-CHoverCard
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <a href="#card" c-bind="activator_attrs">Open overlay</a>
                </c-fill>
                <c-fill name="default">Card body</c-fill>
              </c-CHoverCard>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CHoverCard
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <a href="#card" c-bind="activator_attrs">Open overlay</a>
                </c-fill>
                <c-fill name="default">Card body</c-fill>
              </c-CHoverCard>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "ctooltip": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CTooltip
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <a href="#tip" c-bind="activator_attrs">Open overlay</a>
              </c-fill>
              <c-fill name="default">Tooltip text</c-fill>
            </c-CTooltip>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CTooltip
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <a href="#tip" c-bind="activator_attrs">Open overlay</a>
                </c-fill>
                <c-fill name="default">Tooltip text</c-fill>
              </c-CTooltip>
            </div>
            <div class="instance">
              <c-CTooltip
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <a href="#tip" c-bind="activator_attrs">Open overlay</a>
                </c-fill>
                <c-fill name="default">Tooltip text</c-fill>
              </c-CTooltip>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CTooltip
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <a href="#tip" c-bind="activator_attrs">Open overlay</a>
                </c-fill>
                <c-fill name="default">Tooltip text</c-fill>
              </c-CTooltip>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "cselect": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CSelect
              c-options="select_options"
              placeholder="Pick one"
              c-trigger_attrs="{'aria-label': 'Open overlay'}"
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            />
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CSelect
                c-options="select_options"
                placeholder="Pick one"
                c-trigger_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              />
            </div>
            <div class="instance">
              <c-CSelect
                c-options="select_options"
                placeholder="Pick one"
                c-trigger_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              />
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CSelect
                c-options="select_options"
                placeholder="Pick one"
                c-trigger_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              />
            </div>
          </c-else>
        </div>
      </section>
    """,
    "cmulti_select": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CMultiSelect
              c-options="multi_select_options"
              placeholder="Pick some"
              c-trigger_attrs="{'aria-label': 'Open overlay'}"
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            />
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CMultiSelect
                c-options="multi_select_options"
                placeholder="Pick some"
                c-trigger_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              />
            </div>
            <div class="instance">
              <c-CMultiSelect
                c-options="multi_select_options"
                placeholder="Pick some"
                c-trigger_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              />
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CMultiSelect
                c-options="multi_select_options"
                placeholder="Pick some"
                c-trigger_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              />
            </div>
          </c-else>
        </div>
      </section>
    """,
    "ccombobox": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CCombobox
              c-options="combobox_options"
              c-input_attrs="{'aria-label': 'Open overlay'}"
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            />
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CCombobox
                c-options="combobox_options"
                c-input_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              />
            </div>
            <div class="instance">
              <c-CCombobox
                c-options="combobox_options"
                c-input_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              />
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CCombobox
                c-options="combobox_options"
                c-input_attrs="{'aria-label': 'Open overlay'}"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              />
            </div>
          </c-else>
        </div>
      </section>
    """,
    "ccascader": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CCascader
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-CCascaderOption value="earth" label="Earth">
                <c-CCascaderOption value="north" label="North" />
              </c-CCascaderOption>
            </c-CCascader>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CCascader
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-CCascaderOption value="earth" label="Earth">
                  <c-CCascaderOption value="north" label="North" />
                </c-CCascaderOption>
              </c-CCascader>
            </div>
            <div class="instance">
              <c-CCascader
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-CCascaderOption value="earth" label="Earth">
                  <c-CCascaderOption value="north" label="North" />
                </c-CCascaderOption>
              </c-CCascader>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CCascader
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-CCascaderOption value="earth" label="Earth">
                  <c-CCascaderOption value="north" label="North" />
                </c-CCascaderOption>
              </c-CCascader>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "ccolor_picker": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CColorPicker
              label="Accent"
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            />
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CColorPicker
                label="Accent"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              />
            </div>
            <div class="instance">
              <c-CColorPicker
                label="Accent"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              />
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CColorPicker
                label="Accent"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              />
            </div>
          </c-else>
        </div>
      </section>
    """,
    "cdate_picker": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CDatePicker
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            />
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CDatePicker
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              />
            </div>
            <div class="instance">
              <c-CDatePicker
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              />
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CDatePicker
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              />
            </div>
          </c-else>
        </div>
      </section>
    """,
    "cdate_range": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CDateRange
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            />
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CDateRange
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              />
            </div>
            <div class="instance">
              <c-CDateRange
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              />
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CDateRange
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              />
            </div>
          </c-else>
        </div>
      </section>
    """,
    "ctime_picker": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CTimePicker
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            />
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CTimePicker
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              />
            </div>
            <div class="instance">
              <c-CTimePicker
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              />
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CTimePicker
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              />
            </div>
          </c-else>
        </div>
      </section>
    """,
    "cdialog": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CDialog
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
              </c-fill>
              <c-fill name="title">Overlay dialog</c-fill>
              <c-fill name="default">Dialog body</c-fill>
            </c-CDialog>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CDialog
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay dialog</c-fill>
                <c-fill name="default">Dialog body</c-fill>
              </c-CDialog>
            </div>
            <div class="instance">
              <c-CDialog
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay dialog</c-fill>
                <c-fill name="default">Dialog body</c-fill>
              </c-CDialog>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CDialog
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay dialog</c-fill>
                <c-fill name="default">Dialog body</c-fill>
              </c-CDialog>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "ccommand_palette": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CCommandPalette
              label="Overlay commands"
              c-entries="palette_entries"
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
              </c-fill>
            </c-CCommandPalette>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CCommandPalette
                label="Overlay commands"
                c-entries="palette_entries"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
              </c-CCommandPalette>
            </div>
            <div class="instance">
              <c-CCommandPalette
                label="Overlay commands"
                c-entries="palette_entries"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
              </c-CCommandPalette>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CCommandPalette
                label="Overlay commands"
                c-entries="palette_entries"
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
              </c-CCommandPalette>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "calert_dialog": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CAlertDialog
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
              </c-fill>
              <c-fill name="title">Overlay alert</c-fill>
              <c-fill name="description">Alert body</c-fill>
              <c-fill name="cancel" data="{ cancel_attrs }">
                <c-CButton c-attrs="cancel_attrs">Cancel</c-CButton>
              </c-fill>
              <c-fill name="action" data="{ action_attrs }">
                <c-CButton c-attrs="action_attrs">Confirm</c-CButton>
              </c-fill>
            </c-CAlertDialog>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CAlertDialog
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay alert</c-fill>
                <c-fill name="description">Alert body</c-fill>
                <c-fill name="cancel" data="{ cancel_attrs }">
                  <c-CButton c-attrs="cancel_attrs">Cancel</c-CButton>
                </c-fill>
                <c-fill name="action" data="{ action_attrs }">
                  <c-CButton c-attrs="action_attrs">Confirm</c-CButton>
                </c-fill>
              </c-CAlertDialog>
            </div>
            <div class="instance">
              <c-CAlertDialog
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay alert</c-fill>
                <c-fill name="description">Alert body</c-fill>
                <c-fill name="cancel" data="{ cancel_attrs }">
                  <c-CButton c-attrs="cancel_attrs">Cancel</c-CButton>
                </c-fill>
                <c-fill name="action" data="{ action_attrs }">
                  <c-CButton c-attrs="action_attrs">Confirm</c-CButton>
                </c-fill>
              </c-CAlertDialog>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CAlertDialog
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay alert</c-fill>
                <c-fill name="description">Alert body</c-fill>
                <c-fill name="cancel" data="{ cancel_attrs }">
                  <c-CButton c-attrs="cancel_attrs">Cancel</c-CButton>
                </c-fill>
                <c-fill name="action" data="{ action_attrs }">
                  <c-CButton c-attrs="action_attrs">Confirm</c-CButton>
                </c-fill>
              </c-CAlertDialog>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "cdrawer": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CDrawer
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <button type="button" c-bind="activator_attrs">Open overlay</button>
              </c-fill>
              <c-fill name="title">Overlay drawer</c-fill>
              <c-fill name="default">Drawer body</c-fill>
            </c-CDrawer>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CDrawer
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="title">Overlay drawer</c-fill>
                <c-fill name="default">Drawer body</c-fill>
              </c-CDrawer>
            </div>
            <div class="instance">
              <c-CDrawer
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="title">Overlay drawer</c-fill>
                <c-fill name="default">Drawer body</c-fill>
              </c-CDrawer>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CDrawer
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="title">Overlay drawer</c-fill>
                <c-fill name="default">Drawer body</c-fill>
              </c-CDrawer>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "cpopover": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CPopover
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
              </c-fill>
              <c-fill name="title">Overlay popover</c-fill>
              <c-fill name="default">Popover body</c-fill>
            </c-CPopover>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CPopover
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay popover</c-fill>
                <c-fill name="default">Popover body</c-fill>
              </c-CPopover>
            </div>
            <div class="instance">
              <c-CPopover
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay popover</c-fill>
                <c-fill name="default">Popover body</c-fill>
              </c-CPopover>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CPopover
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
                </c-fill>
                <c-fill name="title">Overlay popover</c-fill>
                <c-fill name="default">Popover body</c-fill>
              </c-CPopover>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "cmenu": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CMenu
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <button type="button" c-bind="activator_attrs">Open overlay</button>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="one">One</c-CMenuItem>
              </c-fill>
            </c-CMenu>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CMenu
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="one">One</c-CMenuItem>
                </c-fill>
              </c-CMenu>
            </div>
            <div class="instance">
              <c-CMenu
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="one">One</c-CMenuItem>
                </c-fill>
              </c-CMenu>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CMenu
                c-open="server_open"
                c-disabled="disabled"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="one">One</c-CMenuItem>
                </c-fill>
              </c-CMenu>
            </div>
          </c-else>
        </div>
      </section>
    """,
    "ctour": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <button
          id="enable-on-server"
          type="button"
          @c-click="enable_on_server"
        >Enable on server</button>
        <button
          id="disable-and-open-on-server"
          type="button"
          @c-click="disable_and_open_on_server"
        >Disable and open on server</button>
        <button
          id="disable-and-close-on-server"
          type="button"
          @c-click="disable_and_close_on_server"
        >Disable and close on server</button>
        <button
          id="remove-on-server"
          type="button"
          @c-click="remove_on_server"
        >Remove on server</button>
        <div id="overlay-slot">
          <c-if cond="not show"></c-if>
          <c-elif cond="controlled">
            <c-CTour
              :open="clientOpen"
              :onOpenChange="(open, detail) => { log(open, detail); clientOpen = open; }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <button type="button" c-bind="activator_attrs">Open overlay</button>
              </c-fill>
              <c-fill name="default">
                <c-CTourStep value="one">
                  <c-fill name="title">Tour step one</c-fill>
                  <c-fill name="default">First step.</c-fill>
                </c-CTourStep>
                <c-CTourStep value="two">
                  <c-fill name="title">Tour step two</c-fill>
                  <c-fill name="default">Second step.</c-fill>
                </c-CTourStep>
              </c-fill>
            </c-CTour>
          </c-elif>
          <c-elif cond="pair">
            <div class="instance">
              <c-CTour
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 1)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="default">
                  <c-CTourStep value="one">
                    <c-fill name="title">Tour step one</c-fill>
                    <c-fill name="default">First step.</c-fill>
                  </c-CTourStep>
                  <c-CTourStep value="two">
                    <c-fill name="title">Tour step two</c-fill>
                    <c-fill name="default">Second step.</c-fill>
                  </c-CTourStep>
                </c-fill>
              </c-CTour>
            </div>
            <div class="instance">
              <c-CTour
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail, 2)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="default">
                  <c-CTourStep value="one">
                    <c-fill name="title">Tour step one</c-fill>
                    <c-fill name="default">First step.</c-fill>
                  </c-CTourStep>
                  <c-CTourStep value="two">
                    <c-fill name="title">Tour step two</c-fill>
                    <c-fill name="default">Second step.</c-fill>
                  </c-CTourStep>
                </c-fill>
              </c-CTour>
            </div>
          </c-elif>
          <c-else>
            <div class="instance">
              <c-CTour
                c-open="server_open"
                :onOpenChange="(open, detail) => log(open, detail)"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button type="button" c-bind="activator_attrs">Open overlay</button>
                </c-fill>
                <c-fill name="default">
                  <c-CTourStep value="one">
                    <c-fill name="title">Tour step one</c-fill>
                    <c-fill name="default">First step.</c-fill>
                  </c-CTourStep>
                  <c-CTourStep value="two">
                    <c-fill name="title">Tour step two</c-fill>
                    <c-fill name="default">Second step.</c-fill>
                  </c-CTourStep>
                </c-fill>
              </c-CTour>
            </div>
          </c-else>
        </div>
      </section>
    """,
}

# How a user opens each component, and the element that is the open popup.
# Each check reads the popup itself, so an expanded trigger alone does not
# count as open.
_OPENING: dict[str, tuple[str, str]] = {
    "chover_card": ("focus", ".cui-hover-card"),
    "ctooltip": ("focus", ".cui-tooltip"),
    "cselect": ("click", ".cui-select__popup"),
    "cmulti_select": ("click", ".cui-multi-select__popup"),
    "ccombobox": ("keyboard", '[data-citry-ui-part="popup"]'),
    "ccascader": ("first-button", '[data-citry-ui-part="popup"]'),
    "ccolor_picker": ("first-button", '[data-citry-ui-part="popup"]'),
    "cdate_picker": ("first-button", ".cui-date-picker__popover"),
    "cdate_range": ("first-button", ".cui-date-range__popover"),
    "ctime_picker": ("first-button", ".cui-time-picker__popover"),
    "cdialog": ("button", "dialog"),
    "calert_dialog": ("button", "dialog"),
    "cdrawer": ("button", "dialog"),
    "cpopover": ("button", ".cui-popover"),
    "cmenu": ("button", "[role=menu]"),
    "ctour": ("button", "dialog"),
    "ccommand_palette": ("button", "dialog"),
}

# Components whose open popup is a modal dialog. CTour's dialog is not modal.
_MODAL = {"cdialog", "calert_dialog", "cdrawer", "ccommand_palette"}

# Components whose server render takes an `open` input, and those that take
# `disabled`.
# CTooltip takes part only in the dialog tests at the end of this file. The
# re-render tests above find a separate gap in how it reports a disable and a
# change to the server's `open` input (#367).
_DIALOG_TESTS_ONLY = {"ctooltip"}
_OVERLAYS = [name for name in _OPENING if name not in _DIALOG_TESTS_ONLY]
_SERVER_OPEN = [name for name in _OVERLAYS if name not in {"cdate_picker", "cdate_range", "ctime_picker"}]
_DISABLED = [name for name in _OVERLAYS if name not in {"cdialog", "calert_dialog", "cdrawer", "cpopover", "ctour"}]

# The reason each component reports when disabling closes it. CSelect and
# CMultiSelect already report a forced "ancestor" close when they are
# disabled while open; the others use "disabled", as CMenu does.
_DISABLED_REASON = {name: "ancestor" if name in {"cselect", "cmulti_select"} else "disabled" for name in _DISABLED}

# The overlay root of the first (or only) instance and of the second one.
_FIRST = "#overlay-slot > .instance:nth-child(1)"
_SECOND = "#overlay-slot > .instance:nth-child(2)"

# A popup is open when it is an open dialog, or a showing popover or popup
# part that is not hidden. A popover left in the top layer with `hidden` set
# is not visible, so it does not count. A dialog that is still modal but no
# longer `open` is hidden yet keeps blocking the page; it is neither open nor
# closed, so the check returns null and the caller fails. The dialog of a
# component in `_MODAL` that is `open` but not modal is shown without
# blocking the page or taking Escape; that is not a real open either, so it
# also returns null.
_IS_OPEN = """([scope, selector, modal]) => {
  const popup = document.querySelector(scope + ' ' + selector);
  if (!popup) return false;
  if (popup.tagName === 'DIALOG') {
    if (popup.matches(':modal') && !popup.open) return null;
    if (modal && popup.open && !popup.matches(':modal')) return null;
    return popup.open;
  }
  if (popup.hidden) return false;
  return popup.hasAttribute('popover') ? popup.matches(':popover-open') : true;
}"""


def _owner_page(
    component: str,
    *,
    controlled: bool = False,
    pair: bool = False,
    in_dialog: bool = False,
    server_open: bool = False,
) -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-open-state-rerender-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class OverlayOwner(Component):
        citry = app

        class Kwargs:
            step: int = 0
            server_open: bool = False
            disabled: bool = False
            controlled: bool = False
            pair: bool = False
            show: bool = True

        class State(Kwargs):
            pass

        class Events:
            # Every event re-renders the owner with the next step, so the test
            # can wait for the new render by its counter.
            def advance(self, state: Any) -> OverlayOwner:
                return _next(state)

            def open_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, server_open=True)

            def close_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, server_open=False)

            def disable_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, disabled=True)

            def enable_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, disabled=False)

            def disable_and_open_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, disabled=True, server_open=True)

            def disable_and_close_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, disabled=True, server_open=False)

            def remove_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, show=False)

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                "step": kwargs.step,
                "server_open": kwargs.server_open,
                "disabled": kwargs.disabled,
                "controlled": kwargs.controlled,
                "pair": kwargs.pair,
                "show": kwargs.show,
                "select_options": [citry_ui.CSelectOption("a", "Alpha"), citry_ui.CSelectOption("b", "Beta")],
                "multi_select_options": [
                    citry_ui.CMultiSelectOption("a", "Alpha"),
                    citry_ui.CMultiSelectOption("b", "Beta"),
                ],
                "combobox_options": [citry_ui.CComboboxOption("a", "Alpha"), citry_ui.CComboboxOption("b", "Beta")],
                "palette_entries": [CCommandPaletteCommand("a", "Alpha")],
            }

        template = _TEMPLATES[component]
        js = """
          $component({
            data() {
              return { clientOpen: false };
            },
            mounted() {
              window.__owner = this;
            },
            methods: {
              // Every overlay reports through here; an overlay of a pair also
              // says which one it is.
              log(open, detail, instance) {
                const entry = { open, reason: detail?.reason };
                if (instance !== undefined) entry.instance = instance;
                window.__openChanges.push(entry);
              },
            },
          });
        """

    def _next(state: Any, **changes: Any) -> OverlayOwner:
        values = {
            "step": state.step + 1,
            "server_open": state.server_open,
            "disabled": state.disabled,
            "controlled": state.controlled,
            "pair": state.pair,
            "show": state.show,
        }
        values.update(changes)
        return OverlayOwner(**values)

    class Page(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"controlled": controlled, "pair": pair}

        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body>
              <c-overlay-owner
                c-controlled="controlled"
                c-pair="pair"
              />
              <c-js />
            </body>
          </html>
        """
        js = """
          $component({
            data() {
              window.__openChanges = [];
              return {};
            },
          });
        """

    # The same owner inside a dialog that the server opens and closes, like a
    # form inside a CDialog. Closing the dialog re-renders the owner too, so
    # the overlay's browser code runs again and takes over its open state.
    class DialogOwner(Component):
        citry = app

        class Kwargs:
            dialog_step: int = 0
            dialog_open: bool = False

        class State(Kwargs):
            pass

        class Events:
            def open_dialog_on_server(self, state: Any) -> DialogOwner:
                return DialogOwner(dialog_step=state.dialog_step + 1, dialog_open=True)

            def close_dialog_on_server(self, state: Any) -> DialogOwner:
                return DialogOwner(dialog_step=state.dialog_step + 1, dialog_open=False)

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                "dialog_step": kwargs.dialog_step,
                "dialog_open": kwargs.dialog_open,
                "inner_controlled": controlled,
                "inner_open": server_open,
            }

        template = """
          <section>
            <output id="dialog-step">{{ dialog_step }}</output>
            <button
              id="open-dialog-on-server"
              type="button"
              @c-click="open_dialog_on_server"
            >Open dialog on server</button>
            <button
              id="close-dialog-on-server"
              type="button"
              @c-click="close_dialog_on_server"
            >Close dialog on server</button>
            <c-CDialog
              c-open="dialog_open"
              :onOpenChange="(open, detail) => log(open, detail)"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <button type="button" c-bind="activator_attrs">Open dialog</button>
              </c-fill>
              <c-fill name="title">Form dialog</c-fill>
              <c-fill name="default">
                <c-overlay-owner
                  c-controlled="inner_controlled"
                  c-server_open="inner_open"
                />
              </c-fill>
            </c-CDialog>
          </section>
        """
        js = """
          $component({
            methods: {
              log(open, detail) {
                window.__openChanges.push({ open, reason: detail?.reason, instance: "dialog" });
              },
            },
          });
        """

    class DialogPage(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body>
              <c-dialog-owner />
              <c-js />
            </body>
          </html>
        """
        js = """
          $component({
            data() {
              window.__openChanges = [];
              return {};
            },
          });
        """

    return app, str(DialogPage() if in_dialog else Page())


def _scope(controlled: bool = False) -> str:
    # The controlled overlay is the slot's only child; the others sit in an
    # `.instance` wrapper.
    return "#overlay-slot" if controlled else _FIRST


def _is_open(page: Any, component: str, scope: str = _FIRST) -> bool:
    state = page.evaluate(_IS_OPEN, [scope, _OPENING[component][1], component in _MODAL])
    if state is None:
        pytest.fail(f"{component} left its dialog half open: hidden but modal, or shown but not modal")
    return bool(state)


def _assert_page_released(page: Any, component: str) -> None:
    # A closed overlay must leave nothing modal behind: no dialog in the top
    # layer, no scroll lock on the page, and real clicks reach the page again.
    # Playwright's click checks that the target receives the pointer, so it
    # fails when a hidden modal dialog still covers the page.
    leftover = page.evaluate(
        """() => ({
          modal: [...document.querySelectorAll(':modal')].map(element => element.tagName),
          overflow: document.documentElement.style.overflow,
        })"""
    )
    assert leftover == {"modal": [], "overflow": ""}, f"{component} left modal state behind: {leftover}"
    page.locator("#owner-step").click(timeout=2_000)


def _wait_open(page: Any, component: str, *, open_: bool = True, scope: str = _FIRST) -> None:
    page.wait_for_function(
        f"args => ({_IS_OPEN})(args) === {'true' if open_ else 'false'}",
        arg=[scope, _OPENING[component][1], component in _MODAL],
    )


def _open_by_user(page: Any, component: str, scope: str = _FIRST) -> None:
    opening = _OPENING[component][0]
    root = page.locator(scope)
    if opening == "focus":
        # Focus opens the card only when focus arrives, so drop focus left on
        # the activator by an earlier open first.
        page.evaluate("document.activeElement?.blur()")
        root.get_by_text("Open overlay").focus()
    elif opening == "click":
        root.get_by_role("combobox", name="Open overlay").click()
    elif opening == "keyboard":
        root.get_by_role("combobox", name="Open overlay").click()
        page.keyboard.press("ArrowDown")
    elif opening == "button":
        root.get_by_role("button", name="Open overlay").click()
    else:
        root.locator("button").first.click()
    _wait_open(page, component, scope=scope)


def _load(page: Any, serve_citry_ui_live: Any, wait_for_citry_ready: Any, component: str, **options: Any) -> None:
    app, html = _owner_page(component, **options)
    page.goto(serve_citry_ui_live(app, html) + "/")
    wait_for_citry_ready()


def _server_event(page: Any, send_event: Any, button: str, handler: str, step: int) -> None:
    # A script click sends the event without pointer or focus changes that
    # would close the overlay on their own.
    send_event(lambda: page.locator(button).evaluate("element => element.click()"), handler=handler)
    page.wait_for_function(f"document.querySelector('#owner-step').textContent === '{step}'")


def _rerender_while_open(page: Any, component: str, send_event: Any, wait_for_count: Any, scope: str) -> None:
    # Hold the server's answer until the overlay is known to be open, so the
    # re-render always lands on an open overlay. Only the call is held: the
    # render may also fetch new component definitions under /ext/events/.
    held: list[Any] = []
    page.route("**/ext/events/call", lambda route: held.append(route))
    page.locator("#advance-owner").evaluate("element => element.click()")
    wait_for_count(held, 1)
    assert _is_open(page, component, scope)
    send_event(lambda: held[0].continue_(), handler="advance")
    page.unroute("**/ext/events/call")
    page.wait_for_function("document.querySelector('#owner-step').textContent === '1'")


def _close_by_user(page: Any, component: str, scope: str = _FIRST) -> None:
    # Escape is the one close request every overlay here accepts. It goes to
    # the element that has focus, so focus something inside the popup (or,
    # for a popup that takes no focus, the control that opened it) first.
    page.evaluate(
        """([scope, selector]) => {
          const root = document.querySelector(scope);
          const popup = root.querySelector(selector);
          const candidates = [
            ...(popup?.querySelectorAll('[tabindex], button, input, [role=menuitem]') ?? []),
            ...root.querySelectorAll('[role=combobox], input, button, a'),
          ];
          // Take the first candidate that really receives focus; an option
          // in a listbox, for example, does not.
          for (const candidate of candidates) {
            candidate.focus();
            if (document.activeElement === candidate) return;
          }
        }""",
        [scope, _OPENING[component][1]],
    )
    page.keyboard.press("Escape")
    _wait_open(page, component, open_=False, scope=scope)


@pytest.mark.parametrize("component", _OVERLAYS)
def test_server_rerender_that_keeps_an_open_overlay_keeps_it_open(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    wait_for_count: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A server event that re-renders the owner leaves an open overlay open and reports no close."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    _open_by_user(page, component)
    opened = page.evaluate("window.__openChanges")
    assert [change["open"] for change in opened] == [True]

    _rerender_while_open(page, component, send_event, wait_for_count, _FIRST)
    # A close scheduled by the re-render would run on a timer or a frame.
    settle_timers()

    assert _is_open(page, component), f"{component} closed when a server re-render kept it"
    assert page.evaluate("window.__openChanges") == opened


@pytest.mark.parametrize("component", _OVERLAYS)
def test_two_overlays_on_one_page_keep_their_own_open_state(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    wait_for_count: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A re-render keeps the open overlay open and the closed one closed, and each reports only its own changes."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component, pair=True)
    _open_by_user(page, component, _FIRST)

    _rerender_while_open(page, component, send_event, wait_for_count, _FIRST)
    settle_timers()

    assert _is_open(page, component, _FIRST), f"{component} closed the overlay the user opened"
    assert not _is_open(page, component, _SECOND), f"{component} opened the other overlay"
    changes = page.evaluate("window.__openChanges")
    assert [(change["instance"], change["open"]) for change in changes] == [(1, True)]


@pytest.mark.parametrize("component", _SERVER_OPEN)
def test_server_open_input_change_opens_and_closes_the_overlay(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A re-render that changes the server's `open` input opens or closes the overlay to match."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    assert not _is_open(page, component)

    _server_event(page, send_event, "#open-on-server", "open_on_server", 1)
    _wait_open(page, component)

    _server_event(page, send_event, "#close-on-server", "close_on_server", 2)
    _wait_open(page, component, open_=False)
    settle_timers()
    assert not _is_open(page, component)
    _assert_page_released(page, component)
    # The owner changed its own input, so neither change is reported back.
    assert page.evaluate("window.__openChanges") == []


@pytest.mark.parametrize("component", _SERVER_OPEN)
def test_user_close_survives_a_rerender_with_an_unchanged_server_open(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """An overlay the user closed stays closed when a re-render keeps the server's `open` input at true."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    _server_event(page, send_event, "#open-on-server", "open_on_server", 1)
    _wait_open(page, component)

    _close_by_user(page, component)
    closed = page.evaluate("window.__openChanges")
    assert [change["open"] for change in closed] == [False]

    _server_event(page, send_event, "#advance-owner", "advance", 2)
    settle_timers()
    assert not _is_open(page, component), f"{component} reopened when a re-render kept server open at true"
    _assert_page_released(page, component)
    assert page.evaluate("window.__openChanges") == closed


@pytest.mark.parametrize("component", _OVERLAYS)
def test_client_open_binding_still_controls_the_overlay_after_a_rerender(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    wait_for_count: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A client `:open` binding keeps control across a server re-render that lands while the overlay is open."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component, controlled=True)
    scope = _scope(controlled=True)
    _open_by_user(page, component, scope)
    _rerender_while_open(page, component, send_event, wait_for_count, scope)
    settle_timers()
    assert _is_open(page, component, scope), f"{component} closed when a server re-render kept it"

    page.evaluate("window.__owner.clientOpen = false")
    _wait_open(page, component, open_=False, scope=scope)
    settle_timers()
    # Only the user's open was a request; the owner's own close is not reported back.
    assert [change["open"] for change in page.evaluate("window.__openChanges")] == [True]


@pytest.mark.parametrize("component", _DISABLED)
def test_server_disable_closes_an_open_overlay_and_reports_it(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A re-render that disables an open overlay closes it and reports the close to `onOpenChange`."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    _open_by_user(page, component)

    opened = page.evaluate("window.__openChanges")

    _server_event(page, send_event, "#disable-on-server", "disable_on_server", 1)
    settle_timers()

    assert not _is_open(page, component), f"{component} stayed open after the server disabled it"
    assert page.evaluate("window.__openChanges") == [*opened, {"open": False, "reason": _DISABLED_REASON[component]}]


@pytest.mark.parametrize("component", _DISABLED)
def test_server_disable_of_a_closed_overlay_reports_nothing_and_reenabling_allows_opening(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """Disabling a closed overlay reports nothing, and once enabled again the user can open it."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)

    _server_event(page, send_event, "#disable-on-server", "disable_on_server", 1)
    settle_timers()
    assert not _is_open(page, component)
    assert page.evaluate("window.__openChanges") == []

    _server_event(page, send_event, "#enable-on-server", "enable_on_server", 2)
    settle_timers()
    # The control the server enabled again must not keep a `disabled` the
    # component set for the earlier render.
    disabled_controls = page.evaluate(
        "scope => [...document.querySelectorAll(scope + ' button, ' + scope + ' input')]"
        ".filter(element => element.disabled && element.type !== 'hidden')"
        ".map(element => element.outerHTML.slice(0, 80))",
        _FIRST,
    )
    assert disabled_controls == []
    _open_by_user(page, component)
    assert [change["open"] for change in page.evaluate("window.__openChanges")] == [True]


@pytest.mark.parametrize("component", _DISABLED)
def test_reenabled_overlay_can_be_opened_again_after_a_disable_closed_it(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """After a disable closes an open overlay and a later render enables it, the user can reopen it."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    _open_by_user(page, component)
    _server_event(page, send_event, "#disable-on-server", "disable_on_server", 1)
    _wait_open(page, component, open_=False)

    _server_event(page, send_event, "#enable-on-server", "enable_on_server", 2)
    settle_timers()
    assert not _is_open(page, component), f"{component} reopened by itself when the server enabled it"
    _open_by_user(page, component)
    assert [change["open"] for change in page.evaluate("window.__openChanges")] == [
        True,
        False,
        True,
    ]


# Components that take both a server `open` and `disabled` input.
_SERVER_OPEN_AND_DISABLED = [name for name in _SERVER_OPEN if name in _DISABLED]


@pytest.mark.parametrize("opened_by", ["user", "server"])
@pytest.mark.parametrize("component", _SERVER_OPEN_AND_DISABLED)
def test_disable_that_also_changes_server_open_reports_the_close(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
    opened_by: str,
) -> None:
    """A render that disables a showing overlay closes it and reports the close, whatever it does to `open`."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    if opened_by == "user":
        _open_by_user(page, component)
        button, handler = "#disable-and-open-on-server", "disable_and_open_on_server"
    else:
        _server_event(page, send_event, "#open-on-server", "open_on_server", 1)
        _wait_open(page, component)
        button, handler = "#disable-and-close-on-server", "disable_and_close_on_server"
    before = page.evaluate("window.__openChanges")
    step = page.evaluate("Number(document.querySelector('#owner-step').textContent)") + 1

    _server_event(page, send_event, button, handler, step)
    settle_timers()

    assert not _is_open(page, component), f"{component} stayed open after the server disabled it"
    assert page.evaluate("window.__openChanges") == [*before, {"open": False, "reason": _DISABLED_REASON[component]}]


@pytest.mark.parametrize("component", _OVERLAYS)
def test_server_rerender_that_removes_an_open_overlay_reports_nothing_and_releases_the_page(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A re-render that removes an open overlay is silent and leaves no modal, popover, or scroll lock behind."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    _open_by_user(page, component)
    opened = page.evaluate("window.__openChanges")

    _server_event(page, send_event, "#remove-on-server", "remove_on_server", 1)
    # A close the removal schedules would run on a timer or a frame, and a
    # dialog handed over for the next render is released once it is gone.
    settle_timers()
    page.wait_for_function("!document.querySelector(':modal, :popover-open')")

    assert page.evaluate("document.querySelector('#overlay-slot').children.length") == 0
    # Removal is silent: the owner removed the overlay itself.
    assert page.evaluate("window.__openChanges") == opened
    released = page.evaluate(
        """() => ({
          overflow: document.documentElement.style.overflow,
          inert: [...document.querySelectorAll('[inert]')].map(element => element.tagName),
          focusConnected: document.activeElement === null || document.activeElement.isConnected,
        })"""
    )
    assert released == {"overflow": "", "inert": [], "focusConnected": True}


# Overlays inside one another, or side by side. Each level takes its own
# server `open` input (`open_0` for the first level, and so on), so a server
# event can change one level while it leaves the others as they were.
_NESTED_TAGS = {"cdialog": "CDialog", "cdrawer": "CDrawer", "ccommand_palette": "CCommandPalette"}

# The `onOpenChange` log name of each level, from the outermost one.
_LEVEL_NAMES = {2: ("outer", "inner"), 3: ("outer", "middle", "inner")}


def _level_markup(component: str, index: int, name: str, body: str) -> str:
    tag = _NESTED_TAGS[component]
    if component == "ccommand_palette":
        # A palette holds commands rather than content, so it is always the
        # innermost level.
        return f"""
          <div id="{name}-root">
            <c-{tag}
              label="{name.capitalize()} commands"
              c-entries="palette_entries"
              c-open="open_{index}"
              :onOpenChange="(open, detail) => log(open, detail, '{name}')"
            >
              <c-fill name="activator" data="{{ activator_attrs }}">
                <c-CButton c-attrs="activator_attrs">Open {name}</c-CButton>
              </c-fill>
            </c-{tag}>
          </div>
        """
    return f"""
      <div id="{name}-root">
        <c-{tag}
          c-open="open_{index}"
          :onOpenChange="(open, detail) => log(open, detail, '{name}')"
        >
          <c-fill name="activator" data="{{ activator_attrs }}">
            <button
              type="button"
              c-bind="activator_attrs"
            >Open {name}</button>
          </c-fill>
          <c-fill name="title">{name.capitalize()} overlay</c-fill>
          <c-fill name="default">{body or f"{name.capitalize()} body"}</c-fill>
        </c-{tag}>
      </div>
    """


def _nested_page(*levels: str, opens: tuple[bool, ...] = (), siblings: bool = False) -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-nested-overlay-rerender-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)
    names = _LEVEL_NAMES[len(levels)]
    last = len(levels) - 1
    # The level that `open_drawer_on_server` opens and `swap_on_server` closes.
    drawer = levels.index("cdrawer") if "cdrawer" in levels else last
    if siblings:
        markup = "".join(_level_markup(component, index, names[index], "") for index, component in enumerate(levels))
    else:
        markup = ""
        for index in range(last, -1, -1):
            markup = _level_markup(levels[index], index, names[index], markup)
    initial = dict.fromkeys(("open_0", "open_1", "open_2"), False)
    initial.update({f"open_{index}": value for index, value in enumerate(opens)})

    class NestedOwner(Component):
        citry = app

        class Kwargs:
            step: int = 0
            open_0: bool = initial["open_0"]
            open_1: bool = initial["open_1"]
            open_2: bool = initial["open_2"]

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state: Any) -> NestedOwner:
                return _nested_next(state)

            def open_outer_on_server(self, state: Any) -> NestedOwner:
                return _nested_next(state, open_0=True)

            def open_all_on_server(self, state: Any) -> NestedOwner:
                return _nested_next(state, **{f"open_{index}": True for index in range(last + 1)})

            def close_outer_on_server(self, state: Any) -> NestedOwner:
                return _nested_next(state, open_0=False)

            def open_drawer_on_server(self, state: Any) -> NestedOwner:
                return _nested_next(state, **{f"open_{drawer}": True})

            def swap_on_server(self, state: Any) -> NestedOwner:
                # Open all levels except the drawer, and close the drawer, in one render.
                return _nested_next(state, **{f"open_{index}": index != drawer for index in range(last + 1)})

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                "step": kwargs.step,
                "open_0": kwargs.open_0,
                "open_1": kwargs.open_1,
                "open_2": kwargs.open_2,
                "palette_entries": [CCommandPaletteCommand("a", "Alpha")],
            }

        template = (
            """
          <section>
            <output id="owner-step">{{ step }}</output>
            <button
              id="advance-owner"
              type="button"
              @c-click="advance"
            >Advance</button>
            <button
              id="open-outer-on-server"
              type="button"
              @c-click="open_outer_on_server"
            >Open outer on server</button>
            <button
              id="open-all-on-server"
              type="button"
              @c-click="open_all_on_server"
            >Open all on server</button>
            <button
              id="close-outer-on-server"
              type="button"
              @c-click="close_outer_on_server"
            >Close outer on server</button>
            <button
              id="open-drawer-on-server"
              type="button"
              @c-click="open_drawer_on_server"
            >Open drawer on server</button>
            <button
              id="swap-on-server"
              type="button"
              @c-click="swap_on_server"
            >Swap on server</button>
            """
            + markup
            + """
          </section>
        """
        )
        js = """
          $component({
            methods: {
              log(open, detail, instance) {
                window.__openChanges.push({ open, reason: detail?.reason, instance });
              },
            },
          });
        """

    def _nested_next(state: Any, **changes: Any) -> NestedOwner:
        values = {
            "step": state.step + 1,
            "open_0": state.open_0,
            "open_1": state.open_1,
            "open_2": state.open_2,
        }
        values.update(changes)
        return NestedOwner(**values)

    class Page(Component):
        citry = app

        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body>
              <c-nested-owner />
              <c-js />
            </body>
          </html>
        """
        js = """
          $component({
            data() {
              window.__openChanges = [];
              return {};
            },
          });
        """

    return app, str(Page())


# Whether each level's dialog element is open. A level's first dialog in
# document order is its own, because its descendants come after it.
_NESTED_OPEN = """names => Object.fromEntries(names.map(
  name => [name, document.querySelector('#' + name + '-root dialog').open]))"""

# A level's dialog `open` and `:modal` state. A dialog left `open` without
# being modal still shows once its ancestor opens, so tests check both.
_NESTED_SHOWN = """name => {
  const dialog = document.querySelector('#' + name + '-root dialog');
  return {open: dialog.open, modal: dialog.matches(':modal')};
}"""


def _nested_state(page: Any, names: tuple[str, ...]) -> dict[str, bool]:
    return page.evaluate(_NESTED_OPEN, list(names))


def _open_level_by_user(page: Any, name: str) -> None:
    page.locator(f"#{name}-root").get_by_role("button", name=f"Open {name}").first.click()
    page.wait_for_function(f"({_NESTED_SHOWN})('{name}').modal === true")


@pytest.mark.parametrize("opened_by", ["user", "server"])
@pytest.mark.parametrize(
    "levels",
    [
        ("cdialog", "cdialog"),
        ("cdrawer", "cdialog"),
        ("cdialog", "cdrawer"),
        ("cdrawer", "cdrawer"),
        ("cdrawer", "cdialog", "cdrawer"),
    ],
    ids=lambda levels: "-in-".join(reversed(levels)),
)
def test_server_close_of_an_outer_overlay_closes_an_open_inner_one_and_releases_the_page(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    levels: tuple[str, ...],
    opened_by: str,
) -> None:
    """Closing the outer overlay on the server closes the open ones inside it, reports them, and frees the page."""
    app, html = _nested_page(*levels)
    names = _LEVEL_NAMES[len(levels)]
    label = " holding ".join(levels)
    page.goto(serve_citry_ui_live(app, html) + "/")
    wait_for_citry_ready()
    if opened_by == "server":
        _server_event(page, send_event, "#open-all-on-server", "open_all_on_server", 1)
    else:
        _server_event(page, send_event, "#open-outer-on-server", "open_outer_on_server", 1)
        for name in names[1:]:
            _open_level_by_user(page, name)
    page.wait_for_function(f"(({_NESTED_OPEN})({list(names)!r})).inner === true")
    opened = page.evaluate("window.__openChanges")

    _server_event(page, send_event, "#close-outer-on-server", "close_outer_on_server", 2)
    settle_timers()

    assert _nested_state(page, names) == dict.fromkeys(names, False)
    _assert_page_released(page, label)
    # The server closed the outer overlay, which reports nothing; each level
    # inside it closed because its ancestor did, which its owner hears about.
    reports = page.evaluate("window.__openChanges")[len(opened) :]
    assert sorted(reports, key=lambda report: report["instance"]) == sorted(
        ({"open": False, "reason": "ancestor", "instance": name} for name in names[1:]),
        key=lambda report: report["instance"],
    )

    # A later re-render that leaves the inner levels' server `open` unchanged
    # keeps them closed, as the ancestor close left them.
    _server_event(page, send_event, "#advance-owner", "advance", 3)
    settle_timers()
    assert _nested_state(page, names) == dict.fromkeys(names, False)
    _assert_page_released(page, label)


@pytest.mark.parametrize(
    "levels",
    [("cdialog", "cdialog"), ("cdialog", "ccommand_palette"), ("cdrawer", "ccommand_palette")],
    ids=lambda levels: "-in-".join(reversed(levels)),
)
def test_inner_overlay_rendered_open_inside_a_closed_outer_one_starts_closed(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    levels: tuple[str, ...],
) -> None:
    """An inner overlay the server renders open inside a closed outer one is closed, and opens normally later."""
    app, html = _nested_page(*levels, opens=(False, True))
    page.goto(serve_citry_ui_live(app, html) + "/")
    wait_for_citry_ready()

    # The inner overlay never opened for the user, so nothing is reported, and
    # opening the outer one shows only the outer one.
    _open_level_by_user(page, "outer")
    settle_timers()
    assert page.evaluate(_NESTED_SHOWN, "inner") == {"open": False, "modal": False}
    # A re-render that keeps the inner's server `open` unchanged leaves it so.
    _server_event(page, send_event, "#advance-owner", "advance", 1)
    settle_timers()
    assert page.evaluate(_NESTED_SHOWN, "inner") == {"open": False, "modal": False}
    assert [report["instance"] for report in page.evaluate("window.__openChanges")] == ["outer"]

    # The user can still open the inner overlay as usual.
    _open_level_by_user(page, "inner")
    assert page.evaluate(_NESTED_SHOWN, "inner") == {"open": True, "modal": True}


@pytest.mark.parametrize("palette_first", [True, False], ids=["drawer-later", "drawer-earlier"])
def test_palette_opened_by_the_server_while_a_drawer_closes_in_the_same_render_opens(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    palette_first: bool,
) -> None:
    """One server render that opens a palette and closes a drawer beside it leaves the palette open."""
    levels = ("ccommand_palette", "cdrawer") if palette_first else ("cdrawer", "ccommand_palette")
    palette, drawer = ("outer", "inner") if palette_first else ("inner", "outer")
    app, html = _nested_page(*levels, siblings=True)
    page.goto(serve_citry_ui_live(app, html) + "/")
    wait_for_citry_ready()
    _server_event(page, send_event, "#open-drawer-on-server", "open_drawer_on_server", 1)
    page.wait_for_function(f"({_NESTED_SHOWN})('{drawer}').modal === true")

    _server_event(page, send_event, "#swap-on-server", "swap_on_server", 2)
    settle_timers()

    assert page.evaluate(_NESTED_SHOWN, palette) == {"open": True, "modal": True}
    assert page.evaluate(_NESTED_SHOWN, drawer) == {"open": False, "modal": False}
    # Both changes came from the server, so neither overlay reports.
    assert page.evaluate("window.__openChanges") == []


# The popups an app puts inside a dialog. Dialogs, drawers and command
# palettes inside a dialog have their own tests above
# (test_server_close_of_an_outer_overlay_closes_an_open_inner_one_and_releases_the_page).
_IN_DIALOG = [name for name in _OPENING if name not in _MODAL]


def _dialog_event(page: Any, send_event: Any, button: str, handler: str, step: int) -> None:
    send_event(lambda: page.locator(button).evaluate("element => element.click()"), handler=handler)
    page.wait_for_function(f"document.querySelector('#dialog-step').textContent === '{step}'")


@pytest.mark.parametrize("component", _IN_DIALOG)
def test_server_close_of_a_dialog_closes_an_open_popup_inside_and_reports_it(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """Closing a dialog on the server closes an open popup inside it, and the popup's owner hears why."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component, in_dialog=True)
    _dialog_event(page, send_event, "#open-dialog-on-server", "open_dialog_on_server", 1)
    page.wait_for_function("document.querySelector('dialog').matches(':modal')")
    _open_by_user(page, component)
    opened = page.evaluate("window.__openChanges")

    _dialog_event(page, send_event, "#close-dialog-on-server", "close_dialog_on_server", 2)
    settle_timers()

    assert not _is_open(page, component)
    # The server closed the dialog, so the dialog itself reports nothing. The
    # popup closed because the dialog around it did, which its owner hears
    # about once.
    assert page.evaluate("window.__openChanges")[len(opened) :] == [{"open": False, "reason": "ancestor"}]
    leftover = page.evaluate(
        """() => ({
          modal: [...document.querySelectorAll(':modal')].map(element => element.tagName),
          overflow: document.documentElement.style.overflow,
        })"""
    )
    assert leftover == {"modal": [], "overflow": ""}
    # A real click must reach the page, which fails if a hidden modal dialog
    # still covers it.
    page.locator("#dialog-step").click(timeout=2_000)


@pytest.mark.parametrize("component", _IN_DIALOG)
def test_closing_a_dialog_in_the_browser_closes_an_open_popup_inside_and_reports_it(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A dialog closed by page code, with no re-render, closes an open popup inside it the same way."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component, in_dialog=True)
    # The user opens the dialog with its button, so closing it moves focus
    # back to that button, out of the popup's trigger.
    page.get_by_role("button", name="Open dialog", exact=True).click()
    page.wait_for_function("document.querySelector('dialog').matches(':modal')")
    _open_by_user(page, component)
    opened = page.evaluate("window.__openChanges")

    # Page code closes the dialog, as a form with method="dialog" does. The
    # popup closes after the browser fires the dialog's close event, so wait
    # for it to close.
    page.evaluate("document.querySelector('dialog').close()")
    _wait_open(page, component, open_=False)
    settle_timers()
    reports = page.evaluate("window.__openChanges")[len(opened) :]
    # The dialog reports its own close; the popup inside reports that its
    # ancestor closed it, once.
    assert [report for report in reports if report.get("instance") != "dialog"] == [
        {"open": False, "reason": "ancestor"}
    ]


@pytest.mark.parametrize("component", [name for name in _IN_DIALOG if name in _SERVER_OPEN or name == "ctooltip"])
def test_a_popup_rendered_open_inside_a_closed_dialog_starts_closed_and_reports_nothing(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A popup the server renders open inside a closed dialog was never shown, so its owner hears nothing."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component, in_dialog=True, server_open=True)
    settle_timers()

    assert not _is_open(page, component)
    assert page.evaluate("window.__openChanges") == []


@pytest.mark.parametrize("component", _IN_DIALOG)
def test_a_controlled_popup_asked_to_open_inside_a_closed_dialog_is_told_once_per_close(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """An owner that asks for the popup while the dialog is closed hears why once, and again after the next close."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component, in_dialog=True, controlled=True)
    scope = _scope(controlled=True)
    _dialog_event(page, send_event, "#open-dialog-on-server", "open_dialog_on_server", 1)
    page.wait_for_function("document.querySelector('dialog').matches(':modal')")
    _open_by_user(page, component, scope=scope)
    opened = page.evaluate("window.__openChanges")

    _dialog_event(page, send_event, "#close-dialog-on-server", "close_dialog_on_server", 2)
    settle_timers()
    # The owner's handler stores each reported state, so it now holds closed.
    assert page.evaluate("window.__openChanges")[len(opened) :] == [{"open": False, "reason": "ancestor"}]
    closed = page.evaluate("window.__openChanges")

    # Asking again while the dialog stays closed is not answered again. An
    # owner that asks after each report would otherwise loop.
    page.evaluate("window.__owner.clientOpen = true")
    settle_timers()
    assert not _is_open(page, component, scope=scope)
    assert page.evaluate("window.__openChanges")[len(closed) :] == []

    # After the dialog opens and closes again, a new request is answered.
    page.evaluate("window.__owner.clientOpen = false")
    _dialog_event(page, send_event, "#open-dialog-on-server", "open_dialog_on_server", 3)
    page.wait_for_function("document.querySelector('dialog').matches(':modal')")
    _dialog_event(page, send_event, "#close-dialog-on-server", "close_dialog_on_server", 4)
    settle_timers()
    reopened = page.evaluate("window.__openChanges")
    page.evaluate("window.__owner.clientOpen = true")
    settle_timers()
    assert not _is_open(page, component, scope=scope)
    assert page.evaluate("window.__openChanges")[len(reopened) :] == [{"open": False, "reason": "ancestor"}]


@pytest.mark.parametrize("component", _IN_DIALOG)
def test_a_controlled_popup_is_told_again_after_the_dialog_is_shown_and_closed_in_the_browser(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """Showing the dialog again, with no re-render, lets the owner's next request be answered again."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component, in_dialog=True, controlled=True)
    scope = _scope(controlled=True)
    open_dialog = page.get_by_role("button", name="Open dialog", exact=True)
    open_dialog.click()
    page.wait_for_function("document.querySelector('dialog').matches(':modal')")
    _open_by_user(page, component, scope=scope)

    page.evaluate("document.querySelector('dialog').close()")
    _wait_open(page, component, open_=False, scope=scope)
    settle_timers()
    told = page.evaluate("window.__openChanges")
    # Asking while the dialog stays closed is not answered again. The answer
    # to a request comes after Vue applies the new input, so give it a moment.
    page.evaluate("window.__owner.clientOpen = true")
    settle_timers()
    page.wait_for_timeout(200)
    assert [report for report in page.evaluate("window.__openChanges")[len(told) :] if "instance" not in report] == []
    page.evaluate("window.__owner.clientOpen = false")

    # The user shows the dialog again and page code closes it again; the
    # owner's next request is answered. The popup notices it was shown after
    # the browser lays the dialog out, so let two frames pass first.
    open_dialog.click()
    page.wait_for_function("document.querySelector('dialog').matches(':modal')")
    page.evaluate("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    page.evaluate("document.querySelector('dialog').close()")
    settle_timers()
    shown = page.evaluate("window.__openChanges")
    page.evaluate("window.__owner.clientOpen = true")
    settle_timers()
    page.wait_for_function(f"window.__openChanges.length > {len(shown)}")

    assert not _is_open(page, component, scope=scope)
    assert [report for report in page.evaluate("window.__openChanges")[len(shown) :] if "instance" not in report] == [
        {"open": False, "reason": "ancestor"}
    ]


@pytest.mark.parametrize("component", ["chover_card", "ctooltip"])
def test_a_focus_popup_whose_region_collapses_closes_and_reports_the_ancestor(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A focus-opened popup closes, reporting "ancestor", when CSS hides the region around its trigger."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    # A collapsed region hides its content with CSS, as CSidebar does.
    page.add_style_tag(content="[data-collapsed] #overlay-slot { display: none; }")
    _open_by_user(page, component)
    opened = page.evaluate("window.__openChanges")

    page.evaluate("document.body.setAttribute('data-collapsed', '')")
    _wait_open(page, component, open_=False)
    settle_timers()

    assert page.evaluate("window.__openChanges")[len(opened) :] == [{"open": False, "reason": "ancestor"}]
