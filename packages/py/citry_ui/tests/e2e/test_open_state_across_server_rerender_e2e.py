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
}

# Components whose server render takes an `open` input, and those that take
# `disabled`.
_SERVER_OPEN = [name for name in _OPENING if name not in {"cdate_picker", "cdate_range", "ctime_picker"}]
_DISABLED = [name for name in _OPENING if name not in {"cdialog", "calert_dialog", "cdrawer", "cpopover", "ctour"}]

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
# closed, so the check returns null and the caller fails.
_IS_OPEN = """([scope, selector]) => {
  const popup = document.querySelector(scope + ' ' + selector);
  if (!popup) return false;
  if (popup.tagName === 'DIALOG') {
    if (popup.matches(':modal') && !popup.open) return null;
    return popup.open;
  }
  if (popup.hidden) return false;
  return popup.hasAttribute('popover') ? popup.matches(':popover-open') : true;
}"""


def _owner_page(component: str, *, controlled: bool = False, pair: bool = False) -> tuple[Citry, str]:
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

    return app, str(Page())


def _scope(controlled: bool = False) -> str:
    # The controlled overlay is the slot's only child; the others sit in an
    # `.instance` wrapper.
    return "#overlay-slot" if controlled else _FIRST


def _is_open(page: Any, component: str, scope: str = _FIRST) -> bool:
    state = page.evaluate(_IS_OPEN, [scope, _OPENING[component][1]])
    if state is None:
        pytest.fail(f"{component} left a hidden dialog in the top layer, still blocking the page")
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
        arg=[scope, _OPENING[component][1]],
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


@pytest.mark.parametrize("component", list(_OPENING))
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


@pytest.mark.parametrize("component", list(_OPENING))
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


@pytest.mark.parametrize("component", list(_OPENING))
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


@pytest.mark.parametrize("component", list(_OPENING))
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
