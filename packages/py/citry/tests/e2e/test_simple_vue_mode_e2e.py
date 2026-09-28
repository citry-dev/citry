from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e


def test_simple_vue_occurrences_keep_local_state_through_parent_render_replacement(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="simple-vue-occurrence-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = engine
        simple = "vue"
        template = '<section class="simple-leaf"><button>toggle</button><output></output></section>'
        js = """$component({
          data(){return {open:false};},
          mounted(){
            const root=this.$el, button=root.querySelector('button'), output=root.querySelector('output');
            const update=()=>{root.dataset.open=String(this.open);output.textContent=this.open?'open':'closed';};
            const click=()=>{this.open=!this.open;update();};
            button.addEventListener('click',click);
            this._simpleVueCleanup=()=>button.removeEventListener('click',click);
            (globalThis.__simpleVueInstances ||= []).push(this);
            update();
          },
          beforeUnmount(){
            this._simpleVueCleanup?.();
            (globalThis.__simpleVueUnmounted ||= []).push(this);
          }
        });"""

    class ParentState:
        show_first: bool = True
        show_second: bool = True

        def render(self):
            return Parent(show_first=self.show_first, show_second=self.show_second)

    class Parent(Component):
        citry = engine
        State = ParentState
        template = (
            '<main><button id="remove-first" @c-click="remove_first">remove first</button>'
            '<c-if cond="show_first"><c-leaf/></c-if>'
            '<c-if cond="show_second"><c-leaf/></c-if></main>'
        )

        def template_data(self, kwargs, slots):
            return {
                "show_first": kwargs.get("show_first", True),
                "show_second": kwargs.get("show_second", True),
            }

        class Events:
            def remove_first(self, state: ParentState):
                state.show_first = False
                return state.render()

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.add_init_script(
        "window.__simpleVueReady = 0; document.addEventListener('citry:ready', () => window.__simpleVueReady++);"
    )
    page.goto(serve_live(engine, Parent().render().serialize(), "") + "/")
    page.wait_for_function(
        "document.querySelectorAll('.simple-leaf').length === 2 && "
        "globalThis.__simpleVueInstances?.length === 2 && globalThis.__simpleVueReady === 1"
    )

    assert page.evaluate("__simpleVueInstances[0] !== __simpleVueInstances[1]")
    page.locator(".simple-leaf button").nth(0).click()
    assert page.locator(".simple-leaf").nth(0).get_attribute("data-open") == "true"
    assert page.locator(".simple-leaf").nth(1).get_attribute("data-open") == "false"
    page.locator(".simple-leaf button").nth(1).click()
    assert page.locator(".simple-leaf").nth(0).get_attribute("data-open") == "true"
    assert page.locator(".simple-leaf").nth(1).get_attribute("data-open") == "true"
    page.evaluate("globalThis.__firstSimpleVueInstance = __simpleVueInstances[0]")

    page.locator("#remove-first").click()
    page.wait_for_function(
        "document.querySelectorAll('.simple-leaf').length === 1 && globalThis.__simpleVueUnmounted?.length === 1"
    )
    assert page.evaluate("__simpleVueUnmounted[0] === __firstSimpleVueInstance")
    assert page.locator(".simple-leaf").get_attribute("data-open") == "true"
    assert page.evaluate("__simpleVueInstances[1].$el === document.querySelector('.simple-leaf')")

    page.evaluate("__firstSimpleVueInstance.$el.querySelector('button').click()")
    assert page.evaluate("__firstSimpleVueInstance.open") is True
    assert faults == []


def test_simple_vue_direct_root_hydrates_without_python_component_instance(
    page: Any, serve_document: Any, monkeypatch: Any
) -> None:
    engine = Citry(autodiscover=False)
    component_init_calls: list[str] = []

    class Root(Component):
        citry = engine
        simple = "vue"
        template = (
            '<main class="direct-root"><span role="button" tabindex="0" '
            'aria-expanded="false">Toggle</span><em>closed</em></main>'
        )
        js = """$component({
          data(){return {open:false};},
          mounted(){
            const toggle=this.$el.querySelector('[role="button"]');
            const label=this.$el.querySelector('em');
            const sync=value=>{
              toggle.setAttribute('aria-expanded',String(value));
              label.textContent=value?'open':'closed';
            };
            sync(this.open);
            this.$watch('open',sync);
            toggle.addEventListener('click',()=>{this.open=!this.open;});
            globalThis.__directSimpleVueRoot=this;
          }
        });"""

    from citry.component import Component as ComponentBase

    component_init = ComponentBase.__init__

    def observe_component_init(self: object, *args: object, **kwargs: object) -> None:
        if type(self) is Root:
            component_init_calls.append("Root")
        component_init(self, *args, **kwargs)

    monkeypatch.setattr(ComponentBase, "__init__", observe_component_init)
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    rendered = Root().render()
    assert rendered.owner_citry is engine
    assert rendered.context.component is None
    assert component_init_calls == []

    control_html = rendered.serialize(ssr=False)
    assert '"hydrate":true' not in control_html
    page.add_init_script(
        "window.__simpleVueReadyApps=[];"
        "document.addEventListener('citry:ready',event=>window.__simpleVueReadyApps.push(event.detail.appId));"
    )
    warnings: list[str] = []
    faults: list[str] = []
    page.on("console", lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None)
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(control_html))
    page.wait_for_function("window.__simpleVueReadyApps?.length === 1")
    control_facts = page.evaluate(
        """() => {
          const root=document.querySelector('[id^="citry-vue-"]').firstElementChild;
          return [root,...root.querySelectorAll('*')].map(element=>({
            tag:element.tagName.toLowerCase(),text:element.textContent,
            attrs:[...element.attributes].filter(attr=>!attr.name.startsWith('data-cid-'))
              .map(attr=>[attr.name,attr.value]).sort(([a],[b])=>a.localeCompare(b))}));
        }"""
    )
    assert page.locator('[id^="citry-vue-"] [role="button"]').get_attribute("aria-expanded") == "false"
    assert page.locator('[id^="citry-vue-"] em').text_content() == "closed"
    assert warnings == [], warnings
    assert faults == [], faults
    warnings.clear()
    faults.clear()

    hydrated_html = rendered.serialize(ssr=True)
    assert component_init_calls == []
    assert '"hydrate":true' in hydrated_html
    app_id = hydrated_html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    before_bootstrap = hydrated_html.index('<script type="application/json" data-citry-vue-document=')
    bootstrap_tag = before_bootstrap
    capture = (
        f'<script>const host=document.querySelector("#citry-vue-{app_id}");'
        "window.__preHydrationRoot=host.firstElementChild;"
        'window.__preHydrationNodes=[window.__preHydrationRoot,...window.__preHydrationRoot.querySelectorAll("*")];'
        "window.__preHydrationHtml=host.innerHTML;</script>"
    )
    hydrated_html = hydrated_html[:bootstrap_tag] + capture + hydrated_html[bootstrap_tag:]
    page.goto(serve_document(hydrated_html))
    page.wait_for_function("window.__simpleVueReadyApps?.length === 1")
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    hydrated = page.evaluate(
        """control => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const root=host.firstElementChild;
          const nodes=[root,...root.querySelectorAll('*')];
          const facts=nodes.map(element=>({tag:element.tagName.toLowerCase(),text:element.textContent,
            attrs:[...element.attributes].filter(attr=>!attr.name.startsWith('data-cid-'))
              .map(attr=>[attr.name,attr.value]).sort(([a],[b])=>a.localeCompare(b))}));
          return {sameRoot:root===window.__preHydrationRoot,
            sameNodes:nodes.length===window.__preHydrationNodes.length
              && nodes.every((node,index)=>node===window.__preHydrationNodes[index]),
            sameDom:JSON.stringify(facts)===JSON.stringify(control),
            initialHtml:window.__preHydrationHtml,
            probe:window.__citryHydrationReport,
            open:window.__directSimpleVueRoot.open,
            aria:root.querySelector('[role="button"]').getAttribute('aria-expanded'),
            text:root.querySelector('em').textContent};
        }""",
        control_facts,
    )
    assert hydrated["sameRoot"], hydrated
    assert hydrated["sameNodes"], hydrated
    assert hydrated["sameDom"], hydrated
    assert hydrated["initialHtml"].startswith('<main class="direct-root"')
    assert hydrated["probe"]["mountError"] is None
    assert hydrated["probe"]["mismatchCount"] == 0
    assert hydrated["probe"]["reusedElementCount"] >= 3
    assert hydrated["probe"]["replacedElementCount"] == 0
    assert hydrated["open"] is False
    assert hydrated["aria"] == "false"
    assert hydrated["text"] == "closed"

    page.locator('[id^="citry-vue-"] [role="button"]').click()
    page.wait_for_function(
        "document.querySelector('[id^=citry-vue-] [role=button]')?.getAttribute('aria-expanded') === 'true'"
        " && document.querySelector('[id^=citry-vue-] em')?.textContent === 'open'"
    )
    assert page.evaluate("window.__directSimpleVueRoot.open") is True
    assert component_init_calls == []
    assert warnings == [], warnings
    assert faults == [], faults


def test_simple_vue_direct_root_hydrates_dynamic_dom_props_and_click_state(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Root(Component):
        citry = engine
        simple = "vue"
        template = (
            '<main><button :title="title" :aria-expanded="open" :disabled="closed" '
            '@click="open=!open">x</button></main>'
        )
        js = """$component({
          data(){return {title:null,open:false};},
          computed:{closed(){return this.open;}},
          mounted(){
            globalThis.__boundRoot=this;
            globalThis.__boundMountCount=(globalThis.__boundMountCount||0)+1;
          },
          updated(){globalThis.__boundUpdateCount=(globalThis.__boundUpdateCount||0)+1;}
        });"""

    rendered = Root().render()
    assert rendered.owner_citry is engine
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.add_init_script(
        "window.__boundReadyApps=[];window.__boundMountCount=0;window.__boundUpdateCount=0;"
        "document.addEventListener('citry:ready',event=>window.__boundReadyApps.push(event.detail.appId));"
    )
    warnings: list[str] = []
    faults: list[str] = []
    page.on("console", lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None)
    page.on("pageerror", lambda error: faults.append(str(error)))

    control_html = rendered.serialize(ssr=False)
    assert '"hydrate":true' not in control_html
    page.goto(serve_document(control_html))
    page.wait_for_function("window.__boundReadyApps?.length === 1")
    control_state = page.evaluate(
        """() => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const main=host.firstElementChild, button=main.querySelector('button');
          return {mainTag:main.tagName.toLowerCase(),buttonTag:button.tagName.toLowerCase(),
            buttonText:button.textContent,title:button.getAttribute('title'),
            ariaExpanded:button.getAttribute('aria-expanded'),
            disabledAttr:button.hasAttribute('disabled'),disabledProp:button.disabled,
            local:{title:window.__boundRoot.title,open:window.__boundRoot.open,closed:window.__boundRoot.closed},
            mountCount:window.__boundMountCount,updateCount:window.__boundUpdateCount};
        }"""
    )
    assert control_state == {
        "mainTag": "main",
        "buttonTag": "button",
        "buttonText": "x",
        "title": None,
        "ariaExpanded": "false",
        "disabledAttr": False,
        "disabledProp": False,
        "local": {"title": None, "open": False, "closed": False},
        "mountCount": 1,
        "updateCount": 0,
    }
    assert warnings == [], warnings
    assert faults == [], faults

    warnings.clear()
    faults.clear()

    hydrated_html = rendered.serialize(ssr=True)
    assert '"hydrate":true' in hydrated_html
    app_id = hydrated_html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    host_open = f'<div id="citry-vue-{app_id}">'
    host_start = hydrated_html.index(host_open)
    host_end = hydrated_html.index("</div>", host_start) + len("</div>")
    initial_host = hydrated_html[host_start:host_end]
    # The adopted row carries no data-cid-<id> marker, like the client-mounted host.
    assert "data-cid-" not in initial_host
    assert "<button>x</button>" in initial_host
    assert "<button " not in initial_host
    before_bootstrap = hydrated_html.index('<script type="application/json" data-citry-vue-document=')
    bootstrap_tag = before_bootstrap
    capture = (
        f'<script>const host=document.querySelector("#citry-vue-{app_id}");'
        "window.__preHydrationMain=host.firstElementChild;"
        'window.__preHydrationButton=host.querySelector("button");'
        'window.__preHydrationNodes=[window.__preHydrationMain,...window.__preHydrationMain.querySelectorAll("*")];'
        "window.__preHydrationHtml=host.innerHTML;</script>"
    )
    hydrated_html = hydrated_html[:bootstrap_tag] + capture + hydrated_html[bootstrap_tag:]
    page.goto(serve_document(hydrated_html))
    page.wait_for_function("window.__boundReadyApps?.length === 1")
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    initial_hydrated = page.evaluate(
        """control => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const main=host.firstElementChild, button=main.querySelector('button');
          const nodes=[main,...main.querySelectorAll('*')];
          return {sameMain:main===window.__preHydrationMain,
            sameButton:button===window.__preHydrationButton,
            sameNodes:nodes.length===window.__preHydrationNodes.length
              && nodes.every((node,index)=>node===window.__preHydrationNodes[index]),
            preHydrationHtml:window.__preHydrationHtml,
            buttonText:button.textContent,title:button.getAttribute('title'),
            ariaExpanded:button.getAttribute('aria-expanded'),
            disabledAttr:button.hasAttribute('disabled'),disabledProp:button.disabled,
            local:{title:window.__boundRoot.title,open:window.__boundRoot.open,closed:window.__boundRoot.closed},
            mountCount:window.__boundMountCount,updateCount:window.__boundUpdateCount,
            dynamicProps:window.__boundRoot.$.subTree.children[0].dynamicProps,
            probe:window.__citryHydrationReport,
            matchesControl:button.textContent===control.buttonText
              && button.getAttribute('title')===control.title
              && button.getAttribute('aria-expanded')===control.ariaExpanded
              && button.hasAttribute('disabled')===control.disabledAttr
              && button.disabled===control.disabledProp};
        }""",
        control_state,
    )
    assert initial_hydrated["sameMain"], initial_hydrated
    assert initial_hydrated["sameButton"], initial_hydrated
    assert initial_hydrated["sameNodes"], initial_hydrated
    assert initial_hydrated["matchesControl"], initial_hydrated
    assert initial_hydrated["preHydrationHtml"].find("<button>x</button>") >= 0
    assert initial_hydrated["title"] is None
    assert initial_hydrated["ariaExpanded"] == "false"
    assert initial_hydrated["disabledAttr"] is False
    assert initial_hydrated["disabledProp"] is False
    assert initial_hydrated["local"] == {"title": None, "open": False, "closed": False}
    assert initial_hydrated["mountCount"] == 1
    assert initial_hydrated["updateCount"] == 0
    assert initial_hydrated["dynamicProps"] == ["title", "aria-expanded", "disabled", "onClick"]
    assert initial_hydrated["probe"]["mountError"] is None
    assert initial_hydrated["probe"]["mismatchCount"] == 0
    assert initial_hydrated["probe"]["reusedElementCount"] >= 2
    assert initial_hydrated["probe"]["replacedElementCount"] == 0

    page.locator('[id^="citry-vue-"] button').click()
    page.wait_for_function(
        "document.querySelector('[id^=citry-vue-] button')?.getAttribute('aria-expanded') === 'true'"
        " && document.querySelector('[id^=citry-vue-] button')?.hasAttribute('disabled')"
        " && window.__boundUpdateCount === 1"
    )
    toggled = page.evaluate(
        """() => {
          const main=document.querySelector('[id^="citry-vue-"]').firstElementChild;
          const button=main.querySelector('button');
          return {sameMain:main===window.__preHydrationMain,
            sameButton:button===window.__preHydrationButton,
            title:button.getAttribute('title'),ariaExpanded:button.getAttribute('aria-expanded'),
            disabledAttr:button.hasAttribute('disabled'),disabledProp:button.disabled,
            local:{title:window.__boundRoot.title,open:window.__boundRoot.open,closed:window.__boundRoot.closed},
            mountCount:window.__boundMountCount,updateCount:window.__boundUpdateCount};
        }"""
    )
    assert toggled == {
        "sameMain": True,
        "sameButton": True,
        "title": None,
        "ariaExpanded": "true",
        "disabledAttr": True,
        "disabledProp": True,
        "local": {"title": None, "open": True, "closed": True},
        "mountCount": 1,
        "updateCount": 1,
    }
    assert warnings == [], warnings
    assert faults == [], faults


def test_simple_vue_direct_root_hydrates_whitespace_interpolation_between_text(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Root(Component):
        citry = engine
        simple = "vue"
        template = "<main>left{{ value }}right</main>"
        js = "$component({});"

    rendered = Root(value=" \t ").render()
    assert rendered.owner_citry is engine
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.add_init_script(
        "window.__whitespaceReadyApps=[];"
        "document.addEventListener('citry:ready',event=>window.__whitespaceReadyApps.push(event.detail.appId));"
    )
    warnings: list[str] = []
    faults: list[str] = []
    page.on("console", lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None)
    page.on("pageerror", lambda error: faults.append(str(error)))

    control_html = rendered.serialize(ssr=False)
    assert '"hydrate":true' not in control_html
    page.goto(serve_document(control_html))
    page.wait_for_function("window.__whitespaceReadyApps?.length === 1")
    control_text = page.locator('[id^="citry-vue-"] main').text_content()
    assert control_text == "left \t right"
    assert warnings == [], warnings
    assert faults == [], faults
    warnings.clear()
    faults.clear()

    hydrated_html = rendered.serialize(ssr=True)
    assert '"hydrate":true' in hydrated_html
    app_id = hydrated_html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    host_open = f'<div id="citry-vue-{app_id}">'
    host_start = hydrated_html.index(host_open)
    host_end = hydrated_html.index("</div>", host_start) + len("</div>")
    initial_host = hydrated_html[host_start:host_end]
    assert "left \t right" in initial_host
    before_bootstrap = hydrated_html.index('<script type="application/json" data-citry-vue-document=')
    bootstrap_tag = before_bootstrap
    capture = (
        f'<script>const host=document.querySelector("#citry-vue-{app_id}");'
        "window.__whitespacePreHydrationMain=host.firstElementChild;"
        "window.__whitespacePreHydrationText=host.firstElementChild.firstChild;"
        "window.__whitespacePreHydrationHtml=host.innerHTML;</script>"
    )
    hydrated_html = hydrated_html[:bootstrap_tag] + capture + hydrated_html[bootstrap_tag:]
    page.goto(serve_document(hydrated_html))
    page.wait_for_function("window.__whitespaceReadyApps?.length === 1")
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    hydrated = page.evaluate(
        """controlText => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const main=host.firstElementChild;
          return {sameMain:main===window.__whitespacePreHydrationMain,
            sameTextNode:main.firstChild===window.__whitespacePreHydrationText,
            text:main.textContent,preHydrationHtml:window.__whitespacePreHydrationHtml,
            matchesControl:main.textContent===controlText,
            probe:window.__citryHydrationReport};
        }""",
        control_text,
    )
    assert hydrated["sameMain"], hydrated
    assert hydrated["sameTextNode"], hydrated
    assert hydrated["text"] == "left \t right"
    assert hydrated["matchesControl"]
    assert "left \t right" in hydrated["preHydrationHtml"]
    assert hydrated["probe"]["mountError"] is None
    assert hydrated["probe"]["mismatchCount"] == 0
    assert hydrated["probe"]["reusedElementCount"] >= 1
    assert hydrated["probe"]["replacedElementCount"] == 0
    assert warnings == [], warnings
    assert faults == [], faults


def test_simple_vue_leaves_from_python_expressions_mount_their_own_instances(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Leaf(Component):
        citry = engine
        simple = "vue"
        template = """
          <button class="leaf" @click="n++">{{ x }}</button>
        """
        js = "$component({data(){return {n:0};},mounted(){(globalThis.__pythonLeaves ||= []).push(this);}});"

        class Kwargs:
            x: int

        class Slots:
            pass

        @staticmethod
        def template_data(kwargs: Any, _slots: object) -> dict[str, object]:
            return {"x": kwargs.x}

    class Page(Component):
        citry = engine
        template = """
          <main>
            <c-leaf c-x="0" />
            <c-for each="i in items">{{ Leaf(x=i) }}</c-for>
          </main>
        """

        def template_data(self, kwargs: object, slots: object) -> dict[str, object]:
            return {"Leaf": Leaf, "items": [1, 2]}

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    # A hydration mismatch shows up only as a console warning.
    page.on("console", lambda message: faults.append(message.text) if message.type in {"warning", "error"} else None)
    # Init scripts run on every navigation, so one registration covers both loads.
    page.add_init_script(
        "window.__pythonLeafReady=0;document.addEventListener('citry:ready',()=>window.__pythonLeafReady++);"
    )
    # Check both the browser-built page and the server-written page that Vue adopts.
    for ssr in (False, True):
        page.goto(serve_document(Page().render().serialize(ssr=ssr)))
        page.wait_for_function("window.__pythonLeafReady === 1 && globalThis.__pythonLeaves?.length === 3")
        assert page.evaluate("[...document.querySelectorAll('.leaf')].map(b => b.textContent)") == ["0", "1", "2"]
        assert page.evaluate("new Set(globalThis.__pythonLeaves).size") == 3
        # Each leaf owns its state, so a click changes that leaf alone.
        page.locator(".leaf").nth(1).click()
        clicks = page.evaluate("globalThis.__pythonLeaves.map(leaf => [leaf.$el.textContent, leaf.n]).sort()")
        assert clicks == [["0", 0], ["1", 1], ["2", 0]]
    assert faults == [], faults
