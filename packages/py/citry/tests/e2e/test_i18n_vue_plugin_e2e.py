"""Exercise native Vue i18n forwarding, bindings, revisions, and cleanup."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e


def _client_bundle_source(vue_root: Path) -> str:
    fragments_source = (vue_root / "fragments.js").read_text(encoding="utf-8")
    client_source = (vue_root / "client.js").read_text(encoding="utf-8")
    return f"{fragments_source}\n{client_source}"


def test_two_serialized_i18n_apps_keep_independent_locales(page: Any) -> None:
    english = Citry(
        autodiscover=False, extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}}
    )
    czech = Citry(autodiscover=False, extensions_defaults={"i18n": {"source_locale": "cs", "locales": ("cs",)}})

    class EnglishPage(Component):
        citry = english
        template = (
            '<c-i18n c-client="True" tag="section"><output class="english" v-text="$i18n.context.lo'
            'cale"></output></c-i18n>'
        )

    class CzechPage(Component):
        citry = czech
        template = (
            '<c-i18n c-client="True" tag="section"><output class="czech" v-text="$i18n.context.loca'
            'le"></output></c-i18n>'
        )

    body = EnglishPage().render().serialize() + CzechPage().render().serialize()
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.route("http://citry.test/", lambda route: route.fulfill(body=body, content_type="text/html"))
    page.goto("http://citry.test/", wait_until="commit")
    page.wait_for_timeout(500)
    assert page.locator(".english").text_content() == "en-US"
    assert page.locator(".czech").text_content() == "cs"
    assert len(page.evaluate("() => [...CitryStable._apps.keys()]")) == 2
    assert faults == []


def test_simple_spread_preserves_plain_output_between_caller_i18n_bindings(
    page: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "simple_i18n_catalog"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "simple-i18n-test"\nsource_locale = "en-US"\n', encoding="utf8"
    )
    for locale, label in (("en-US", "Save"), ("cs-CZ", "Uložit")):
        locale_root = package / "locales" / locale
        locale_root.mkdir(parents=True)
        (locale_root / "common.ftl").write_text(f"save = {label}\n", encoding="utf8")
    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop("simple_i18n_catalog", None)

    engine = Citry(
        autodiscover=False,
        mode="development",
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
                "catalogs": ("simple_i18n_catalog",),
            }
        },
    )

    class Label(Component):
        citry = engine
        simple = True
        template = '<span id="plain" c-bind="attrs">{{ text }}</span>'

    class Page(Component):
        citry = engine
        template = """<c-i18n c-client="True" tag="main">
          <p class="translated" $c-tr:save>{{ tr("save") }}</p>
          <c-label c-attrs="attrs" text="plain" />
          <p class="translated" $c-tr:save>{{ tr("save") }}</p>
          <button id="switch" @click="$i18n.switchLocale('cs-CZ')">switch</button>
        </c-i18n>"""
        messages = "save = Save"

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.route(
        "http://citry.test/",
        lambda route: route.fulfill(
            body=Page(attrs={"title": "ordinary"}).render().serialize(), content_type="text/html"
        ),
    )
    page.goto("http://citry.test/", wait_until="commit")
    page.wait_for_function(
        "document.querySelector('#plain')?.textContent === 'plain' && "
        "document.querySelector('#plain')?.title === 'ordinary' && "
        "[...document.querySelectorAll('.translated')].every(node => node.textContent === 'Save')"
    )
    page.locator("#switch").click()
    page.wait_for_function(
        "[...document.querySelectorAll('.translated')].every(node => node.textContent === 'Uložit')"
    )
    assert page.locator("#plain").text_content() == "plain"
    assert page.locator("#plain").get_attribute("title") == "ordinary"
    assert faults == []


def test_real_serialized_apps_own_separate_stylesheet_nodes(page: Any, serve_live: Any) -> None:
    engine = Citry(autodiscover=False)
    engine.set_mounted_prefix("/citry")

    class Styled(Component):
        citry = engine
        template = '<output class="owned-style">styled</output>'
        css = ".owned-style { color: rgb(7, 8, 9); }"
        js = "$component({});"

    first = Styled().render().serialize()
    second = Styled().render().serialize()

    def prepared_configuration(serialized: str) -> dict[str, Any]:
        payload = serialized.split("CitryStable.startPrepared(", 1)[1].split(").catch", 1)[0]
        return json.loads(payload)

    first_styles = prepared_configuration(first)["manifest"]["styles"]
    second_styles = prepared_configuration(second)["manifest"]["styles"]
    assert len(first_styles) == len(second_styles) == 1
    style_url = first_styles[0]["source"]["url"]
    assert second_styles[0]["source"]["url"] == style_url
    html = f'<link id="authored-style" rel="stylesheet" href="{style_url}">{first}{second}'
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, html, "") + "/")
    page.wait_for_function("CitryStable._apps.size === 2")
    assert page.locator("[data-citry-vue-style-app][data-citry-css-url]").count() == 2
    assert page.locator("#authored-style").count() == 1
    color = page.locator(".owned-style").first.evaluate("element => getComputedStyle(element).color")
    assert color == "rgb(7, 8, 9)"
    result = page.evaluate(
        """() => {
          const apps=[...CitryStable._apps.values()];
          apps[1].vueApp.unmount();
"""
        "          const afterSecond={apps:CitryStable._apps.size,owned:document.querySelectorA"
        "ll('[data-citry-vue-style-app]').length,\n"
        """            authored:!!document.querySelector('#authored-style')};
          apps[0].vueApp.unmount();
          return {afterSecond,final:{apps:CitryStable._apps.size,
            owned:document.querySelectorAll('[data-citry-vue-style-app]').length,authored:!!document.querySelector('#authored-style')}};
        }"""
    )
    assert result == {
        "afterSecond": {"apps": 1, "owned": 1, "authored": True},
        "final": {"apps": 0, "owned": 0, "authored": True},
    }
    assert faults == []


def test_i18n_plugin_mounts_through_start_prepared(page: Any) -> None:
    engine = Citry(
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )

    class Page(Component):
        citry = engine
        template = """<html><body><c-i18n c-client="True" tag="main">
          <output id="locale" v-text="$i18n?.context?.locale ?? 'none'"></output>
        </c-i18n></body></html>"""

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    html = Page().render().serialize()
    page.route("http://citry.test/", lambda route: route.fulfill(body=html, content_type="text/html"))
    page.goto("http://citry.test/", wait_until="commit")
    page.wait_for_timeout(500)
    assert page.locator("#locale").count() == 1, (faults, page.content())
    debug = page.evaluate("""() => [...CitryStable._apps.values()].map(app =>
      [...app.mounted].map(([id, value]) => ({id, name:value.component.$options.name,
        locale:value.component.$i18n?.context?.locale ?? null, options: Object.keys(value.component.$options)})))""")
    assert page.locator("#locale").text_content() == "en-US", (faults, [(x["name"], x["locale"]) for x in debug[0]])
    service_proof = page.evaluate("""async () => {
      const service = [...CitryStable._apps.values()].flatMap(app => [...app.mounted.values()])
        .map(value => value.component.$i18n).find(Boolean);
      let notifications = 0;
      const unsubscribe = service.subscribe(() => { notifications += 1; });
      const switched = await service.switchLocale('en-US');
      unsubscribe();
      return {
        methods: ['bind','ensureMessages','resolve','subscribe','switchLocale','tr']
          .every(name => typeof service[name] === 'function'),
        formatter: typeof service.format.number === 'function',
        parser: typeof service.parse.number === 'function',
        notifications,
        status: switched.status,
      };
    }""")
    assert service_proof == {
        "methods": True,
        "formatter": True,
        "parser": True,
        "notifications": 1,
        "status": "committed",
    }
    assert faults == []


def test_declarative_binding_keeps_last_valid_values_and_recovers(page: Any) -> None:
    engine = Citry(
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )

    class Page(Component):
        citry = engine
        template = (
            """<c-i18n c-client="True" tag="main">
"""
            '          <output id="greeting" $c-tr:greeting="{ name: invalid ? {bad:true} : name }"'
            '>{{ tr("greeting", name="Server") }}</output>\n'
            """          <button id="change" @click="name='Grace'">change</button>
          <button id="invalidate" @click="invalid=true">invalid</button>
          <button id="recover" @click="invalid=false">recover</button>
        </c-i18n>"""
        )
        messages = "# @param {str} $name\ngreeting = Hello { $name }"
        js = "$component({data(){return {name:'Ada',invalid:false}}});"

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    html = Page().render().serialize()
    page.route("http://citry.test/", lambda route: route.fulfill(body=html, content_type="text/html"))
    page.goto("http://citry.test/", wait_until="commit")
    page.wait_for_timeout(500)
    assert page.locator("#greeting").text_content() == "Hello \u2068Ada\u2069", (faults, page.content())
    page.locator("#invalidate").click()
    page.wait_for_timeout(50)
    assert page.locator("#greeting").text_content() == "Hello \u2068Ada\u2069"
    page.locator("#change").click()
    assert page.locator("#greeting").text_content() == "Hello \u2068Ada\u2069"
    page.locator("#recover").click()
    page.wait_for_function("document.querySelector('#greeting')?.textContent.includes('Grace')")
    assert faults == []


def test_real_child_events_revision_retains_outer_i18n_and_replaces_callback_scope(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="vue-i18n-child-revision-secret",  # noqa: S106
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US", "cs")}},
    )
    engine.set_mounted_prefix("/citry")

    class ChildState:
        count: int = 0

        def render(self):
            return Child(count=self.count)

    class Child(Component):
        citry = engine
        template = (
            '<button id="child-revision" @c-click="refresh">'
            '<span id="child-locale" v-text="$i18n.context.locale"></span>:'
            '<span id="child-count">{{ count }}</span></button>'
        )
        js = """$component({onServerRender({component}){
          const run=globalThis.__childCallbackRuns=(globalThis.__childCallbackRuns||0)+1;
          (globalThis.__childBindingEvaluations??={})[run]=0;
          component.$i18n.bind({message:'missing',values(){
            globalThis.__childBindingEvaluations[run]+=1;
            (globalThis.__childBindingSignal??=Citry.vue.ref(0)).value;
            return {};
          },onChange(){}});
          return ()=>{
            globalThis.__childCallbackCleanups=(globalThis.__childCallbackCleanups||0)+1;
            if(globalThis.__throwChildCleanup) throw Error('authored cleanup failure');
          };
        }});"""
        State = ChildState

        class Events:
            def refresh(self, state: ChildState):
                state.count += 1
                return state.render()

        def template_data(self, kwargs, slots):
            return {"count": kwargs.get("count", 0)}

    engine.register(Child)

    class Page(Component):
        citry = engine
        template = '<c-i18n c-client="True" locale="en-US" tag="main"><c-child /></c-i18n>'

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    page.locator("#child-revision").wait_for()
    page.wait_for_function("globalThis.__childCallbackRuns === 1")
    page.locator("#child-revision").click()
    page.wait_for_function("document.querySelector('#child-count')?.textContent === '1'")
    page.wait_for_function("globalThis.__childCallbackRuns === 2 && globalThis.__childCallbackCleanups === 1")
    assert page.locator("#child-locale").text_content() == "en-US"
    before = page.evaluate("structuredClone(globalThis.__childBindingEvaluations)")
    page.evaluate(
        """async () => {
          const app=[...CitryStable._apps.values()][0];
          const child=[...app.mounted.values()].find(value=>value.component.$el?.id==='child-revision');
          globalThis.__childBindingSignal.value+=1;
        }"""
    )
    page.wait_for_function("globalThis.__childBindingEvaluations[2] > 1")
    after = page.evaluate("structuredClone(globalThis.__childBindingEvaluations)")
    assert after["1"] == before["1"]
    assert after["2"] > before["2"]
    retirement = page.evaluate(
        """async () => {
          const app=[...CitryStable._apps.values()][0];
          const child=[...app.mounted.values()].find(value=>value.component.$el?.id==='child-revision');
          const childId=child.record.occurrenceId;
          globalThis.__throwChildCleanup=true;
          let message='';
          app.vueApp.config.errorHandler=error=>{message=error.message};
          app.vueApp.unmount();
          const evaluations=globalThis.__childBindingEvaluations[2];
          globalThis.__childBindingSignal.value+=1;
          await Citry.vue.nextTick();
          const stopped=globalThis.__childBindingEvaluations[2]===evaluations;
          const retired=!app.mounted.has(childId);
          return {message,stopped,retired,apps:CitryStable._apps.size};
        }"""
    )
    assert retirement == {"message": "authored cleanup failure", "stopped": True, "retired": True, "apps": 0}
    assert faults == []


def test_retained_forwarding_cells_follow_provider_and_barrier_changes(page: Any) -> None:
    root = Path(__file__).parents[2] / "citry"
    vue_source = (root / "_vue" / "vue.js").read_text(encoding="utf-8")
    plugin_source = (root / "ext" / "i18n" / "client" / "vue-plugin.source.js").read_text(encoding="utf-8")
    page.set_content('<main id="app"></main><div id="teleport"></div>')

    result = page.evaluate(
        (
            """async ({vueSource, pluginSource}) => {
          window.eval(vueSource);
          let factory, registrations = 0;
          window.CitryStable = {
            registerBrowserPlugin(name, version, value) {
              if (name !== 'i18n' || version !== 1) throw new Error('unexpected plugin identity');
              registrations += 1;
              factory = value;
            },
          };
          window.eval(pluginSource);
          window.eval(pluginSource);
          if (registrations !== 1) throw new Error('i18n plugin registered more than once');
          const registrationId = window[Symbol.for('Citry.i18n.vue-plugin.registered')];
          let changedBuild = '';
          try { window.eval(pluginSource.replace(registrationId, '0'.repeat(64))); }
          catch (error) { changedBuild = error.message; }
          if (!changedBuild.includes('different Citry Vue i18n plugin build'))
            throw new Error('a different i18n build was not rejected');
          const occurrences = new Map([
            ['root', {id: 'root', parentId: null, placementKey: null}],
            ['provider', {id: 'provider', parentId: 'root', placementKey: 'provider'}],
            ['middle', {id: 'middle', parentId: 'provider', placementKey: 'middle'}],
            ['consumer', {id: 'consumer', parentId: 'middle', placementKey: 'consumer'}],
            ['teleported', {id: 'teleported', parentId: 'provider', placementKey: 'teleported'}],
            ['sibling', {id: 'sibling', parentId: 'root', placementKey: 'sibling'}],
          ]);
          const host = {
            appId: 'proof', vue: Vue, occurrenceId: component => component.citryId,
            occurrence: id => occurrences.get(id) || null, revision: () => 0,
          };
          const plugin = factory(host);
          const Consumer = plugin.decorateTypeOptions('consumer', {
            props: {citryId: String},
            render() { return Vue.h('span', {class: 'local'}, this.$i18n?.context?.locale ?? 'none'); },
          });
          const Provider = plugin.decorateTypeOptions('provider', {
            props: {citryId: String},
                render() {
                  return Vue.h('section', null, [
                    (window.__proofService = this.$i18n, null),
                    Vue.h('strong', {class: 'provider-own'}, this.$i18n?.context?.locale ?? 'none'),
                Vue.h(Consumer, {citryId: 'consumer'}),
                Vue.h(Vue.Teleport, {to: '#teleport'}, Vue.h(Consumer, {citryId: 'teleported'})),
              ]);
            },
          });
          const Root = plugin.decorateTypeOptions('root', {
            props: {citryId: String},
            render() { return Vue.h(Provider, {citryId: 'provider'}); },
          });
          const snapshot = {occurrences: [...occurrences.values()]};
          const context = locale => ({catalog_revision:'catalog',direction:'ltr',fallback_locales:[],
            formats_revision:'formats',locale,time_zone:null,tzdb_revision:'none'});
"""
            "          const parser = locale => ({formats_revision:'formats',locale,number:{},perce"
            "nt:{},revision:'parser',schema_version:1});\n"
            """          const payload = (providers, barriers = []) => ({providers, barriers, requirements: [],
            catalog_revision:'catalog',contexts:{en:context('en'),fr:context('fr')},
            formats:{date:{display:{fields:'year_month_day',input:null,length:'medium'}}},
            formats_revision:'formats',locales:['en','fr'],messages_url:null,
            parsers:{en:parser('en'),fr:parser('fr')},runtime:'@fluent/bundle@0.19.1'});
"""
            "          const provider = locale => ({id:'provider',parent:null,serverProviderId:'ser"
            "ver-provider',context:context(locale),\n"
            """\
            policy:{direction:{mode:'inherit'},locale:{mode:'explicit',value:locale},time_zone:{mode:'inherit'}}});
"""
            "          const childProvider = (id='consumer', parent={serverProviderId:'server-provi"
            "der'}, serverProviderId='server-child') =>\n"
            """            ({id,parent,serverProviderId,context:context('fr'),
              policy:{direction:{mode:'inherit'},locale:{mode:'explicit',value:'fr'},time_zone:{mode:'inherit'}}});
          const inheritedProvider = (id, parent, serverProviderId) =>
            ({id,parent,serverProviderId,context:context('en'),
              policy:{direction:{mode:'inherit'},locale:{mode:'inherit'},time_zone:{mode:'inherit'}}});
          let malformedFormat = '';
          try { await plugin.prepareRevision({...payload([provider('en')]), formats:{number:42}}, snapshot); }
          catch (error) { malformedFormat = error.message; }
          let malformedProfile = '';
"""
            "          try { await plugin.prepareRevision({...payload([provider('en')]), formats:{n"
            "umber:{default:42}}}, snapshot); }\n"
            """          catch (error) { malformedProfile = error.message; }
          let stage = await plugin.prepareRevision(payload([provider('en')]), snapshot);
          plugin.activateRevision(stage);
          const app = Vue.createApp(Root, {citryId: 'root'});
          app.use(plugin);
          app.mount('#app');
          await Vue.nextTick();
          const proofService = window.__proofService;
              const read = () => [...document.querySelectorAll('.local')].map(node => node.textContent);
              const readOwn = () => document.querySelector('.provider-own').textContent;
              const initial = read();
                  const initialOwn = readOwn();
          stage = await plugin.prepareRevision(payload([
            provider('en'), childProvider('middle', 'provider', 'server-middle'),
            inheritedProvider('teleported', 'middle', 'server-teleported'),
          ]), {...snapshot, occurrences:snapshot.occurrences.map(value =>
            value.id === 'teleported' ? {...value, parentId:'middle'} : value)});
          plugin.activateRevision(stage); plugin.commitRevision(stage); await Vue.nextTick();
          const nested = read();
          occurrences.get('teleported').parentId = 'provider';
          const middleSnapshot = {...snapshot, baseRevision:0, rootId:'middle'};
          const removal = await plugin.prepareRevision(payload([]), middleSnapshot);
          plugin.activateRevision(removal); await Vue.nextTick();
          const reparented = read();
          plugin.rollbackRevision(removal); await Vue.nextTick();
          const rolledBack = read();
          plugin.activateRevision(removal); plugin.commitRevision(removal); await Vue.nextTick();
          const recommitted = read();
          stage = await plugin.prepareRevision(payload([provider('en')]), snapshot);
          plugin.activateRevision(stage); plugin.commitRevision(stage); await Vue.nextTick();
          const watched = Vue.ref(0); let evaluations = 0;
          const callbackScope = Vue.effectScope();
"""
            "          callbackScope.run(() => window.__proofService.bind({message:'missing', value"
            "s(){ evaluations += 1; watched.value; return {}; }, onChange(){}}));\n"
            """          const beforeScopeStop = evaluations;
          callbackScope.stop(); watched.value += 1; await Vue.nextTick();
          const scopeReleased = evaluations === beforeScopeStop;
          await proofService.switchLocale('fr');
          const childSnapshot = {...snapshot, baseRevision:0, rootId:'consumer'};
          stage = await plugin.prepareRevision(payload([childProvider()]), childSnapshot);
          plugin.activateRevision(stage); plugin.commitRevision(stage);
          await Vue.nextTick();
          const childOnly = read();
          const rejection = async (providers, barriers=[]) => {
            try { await plugin.prepareRevision(payload(providers, barriers), childSnapshot); return '' }
            catch (error) { return error.message }
          };
          const stale = await rejection([childProvider('consumer', {serverProviderId:'missing'})]);
          const barrierSkip = await rejection([childProvider()], ['middle']);
          const providerSkip = await rejection([childProvider(), childProvider('middle', null, 'server-middle')]);
"""
            "          const selectedExternal = await rejection([childProvider('consumer', {serverP"
            "roviderId:'server-child'}, 'replacement')]);\n"
            """\
          const duplicateRaw = await rejection([childProvider(), childProvider('middle', null, 'server-child')]);
          const sibling = await rejection([childProvider('sibling')]);
"""
            "          const retainedRawReuse = await rejection([childProvider('consumer', {serverP"
            "roviderId:'server-provider'}, 'server-provider')]);\n"
            """          stage = await plugin.prepareRevision(payload([]), snapshot);
          plugin.activateRevision(stage);
          await Vue.nextTick();
              const removed = read();
              const removedOwn = readOwn();
          stage = await plugin.prepareRevision(payload([provider('fr')]), snapshot);
          plugin.activateRevision(stage);
          await Vue.nextTick();
              const restored = read();
              const restoredOwn = readOwn();
          stage = await plugin.prepareRevision(payload([], ['consumer', 'teleported']), snapshot);
          plugin.activateRevision(stage);
          await Vue.nextTick();
          const barrier = read();
          const disposeSignal = Vue.ref(0); let disposeEvaluations = 0; let disposeNotifications = 0;
"""
            "          proofService.bind({message:'missing',values(){disposeEvaluations += 1; dispo"
            "seSignal.value; return{}},onChange(){}});\n"
            """          proofService.subscribe(()=>{disposeNotifications += 1});
          const beforeDispose = {disposeEvaluations, disposeNotifications};
          plugin.dispose(); plugin.dispose(); disposeSignal.value += 1; await Vue.nextTick();
          const disposedReleased = disposeEvaluations === beforeDispose.disposeEvaluations &&
            disposeNotifications === beforeDispose.disposeNotifications;
"""
            "              return {initial, initialOwn, nested, reparented, rolledBack, recommitted"
            ", childOnly, removed, removedOwn, restored, restoredOwn, barrier,\n"
            """                malformedFormat, malformedProfile,
                rejected:[stale,barrierSkip,providerSkip,selectedExternal,duplicateRaw,sibling,retainedRawReuse].every(Boolean),scopeReleased,disposedReleased};
        }"""
        ),
        {"vueSource": vue_source, "pluginSource": plugin_source},
    )

    assert result == {
        "initial": ["en", "en"],
        "initialOwn": "en",
        "nested": ["en", "fr"],
        "reparented": ["en", "en"],
        "rolledBack": ["en", "fr"],
        "recommitted": ["en", "en"],
        "childOnly": ["fr", "fr"],
        "removed": ["none", "none"],
        "removedOwn": "none",
        "restored": ["fr", "fr"],
        "restoredOwn": "fr",
        "barrier": ["none", "none"],
        "malformedFormat": "[Citry] i18n: i18n formats.number must be an object.",
        "malformedProfile": "[Citry] i18n: i18n formats.number.default must be an object.",
        "rejected": True,
        "scopeReleased": True,
        "disposedReleased": True,
    }


def test_start_prepared_disposes_plugin_when_install_fails(page: Any) -> None:
    root = Path(__file__).parents[2] / "citry"
    result = page.evaluate(
        (
            """async ({vueSource, clientSource}) => {
          window.eval(vueSource); window.eval(clientSource);
          const helperContract=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest = 'a'.repeat(64), definitionId = 'definition';
          window.CitryStableDefinitions = {[definitionId]: {
            render(){ return Vue.h('div'); }, target:'ordinary-vnodes/1',
            helperContract:helperContract,
"""
            "            dynamicElements:[], directiveSignature:[], replacementSites:[], localCalls"
            ":[], localCallRuns:[],opaqueHtmlSites:[],\n"
            """          }};
          CitryStable.registerTypeOptions('Root', digest, {});
          let disposed = 0;
          CitryStable.registerBrowserPlugin('probe', 1, () => ({
            install(){ throw new Error('install failure'); },
            prepareRevision(){ return {}; }, activateRevision(){}, commitRevision(){}, abortRevision(){},
            rollbackRevision(){}, dispose(){ disposed += 1; },
          }));
          document.body.innerHTML='<div id="app"></div>';
          const manifest = {protocol:'citry-vue-prepared/1',appId:'failure-app',revision:0,rootId:'root',
            occurrences:[{id:'root',typeKey:'Root',definitionId,parentId:null,placementKey:null,serverData:{},
              preparedData:{calls:{},selectedSlots:{}}}],
            definitions:[{id:definitionId,url:'/unused.js',sha256:digest,target:'ordinary-vnodes/1',
              helperContract:helperContract,
              dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}],
            replacements:[],scripts:[],styles:[],typePolicies:[{typeKey:'Root',lazyAllowed:false}],
            extensions:{probe:{schemaVersion:1,payload:{},templateContextNames:[]}}};
          let message='';
          try { await CitryStable.startPrepared({manifest,host:'#app',tags:{Root:'c-root'}}); }
          catch (error) { message=error.message; }
          let healthyDisposed=0;
          CitryStable.registerBrowserPlugin('healthy', 1, () => ({install(){},prepareRevision(){return{};},
            activateRevision(){},commitRevision(){},abortRevision(){},rollbackRevision(){},
            dispose(){healthyDisposed+=1;}}));
"""
            "          const healthy={...manifest,appId:'healthy-app',extensions:{healthy:{schemaVe"
            "rsion:1,payload:{},templateContextNames:[]}}};\n"
            """          document.body.innerHTML='<div id="healthy"></div>';
          await CitryStable.startPrepared({manifest:healthy,host:'#healthy',tags:{Root:'c-root'}});
          let duplicate='';
          try { await CitryStable.startPrepared({manifest:healthy,host:'#healthy',tags:{Root:'c-root'}}); }
          catch(error){duplicate=error.message;}
          return {message,disposed,apps:CitryStable._apps.size,healthyDisposed,duplicate};
        }"""
        ),
        {
            "vueSource": (root / "_vue" / "vue.js").read_text(encoding="utf-8"),
            "clientSource": _client_bundle_source(root / "_vue"),
        },
    )
    assert result == {
        "message": "install failure",
        "disposed": 1,
        "apps": 1,
        "healthyDisposed": 0,
        "duplicate": "duplicate Citry Vue app",
    }


def test_invalid_graph_and_type_policy_do_not_fetch_or_execute_definitions(page: Any) -> None:
    root = Path(__file__).parents[2] / "citry"
    result = page.evaluate(
        (
            """async ({vueSource,clientSource})=>{
          window.eval(vueSource);window.eval(clientSource);
          const helperContract=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest='e'.repeat(64),executed=[],requested=[];
          const nativeAppend=document.head.append.bind(document.head);
"""
            "          document.head.append=(...nodes)=>{for(const node of nodes)if(node.tagName==="
            "'SCRIPT')requested.push(node.src);return nativeAppend(...nodes)};\n"
            "          const definition={id:'remote',url:'data:text/javascript,executed.push(1)',sh"
            "a256:digest,target:'ordinary-vnodes/1',\n"
            """            helperContract:helperContract,dynamicElements:[],
            directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]};
"""
            "          const occurrence={id:'root',typeKey:'Root',definitionId:'remote',parentId:nu"
            "ll,placementKey:null,serverData:{},preparedData:{calls:{},selectedSlots:{}}};\n"
            """\
          const base=appId=>({protocol:'citry-vue-prepared/1',appId,revision:0,rootId:'root',occurrences:[occurrence],
            definitions:[definition],replacements:[],scripts:[],styles:[],typePolicies:[{typeKey:'Root',lazyAllowed:false}],extensions:{}});
          document.body.innerHTML='<div id="app"></div>';const messages=[];
"""
            "          const badGraph=base('bad-graph');badGraph.occurrences=[occurrence,{...occurr"
            "ence,id:'orphan',parentId:'missing',placementKey:'orphan'}];\n"
            """          try{await CitryStable.startPrepared({manifest:badGraph,host:'#app',tags:{Root:'c-root'}})}
          catch(error){messages.push(error.message)}
          const badPolicy=base('bad-policy');badPolicy.typePolicies=[{typeKey:'Root',lazyAllowed:'yes'}];
          try{await CitryStable.startPrepared({manifest:badPolicy,host:'#app',tags:{Root:'c-root'}})}
          catch(error){messages.push(error.message)}
          return {messages,requested,executed,apps:CitryStable._apps.size};
        }"""
        ),
        {"vueSource": (root / "_vue" / "vue.js").read_text(), "clientSource": _client_bundle_source(root / "_vue")},
    )
    assert result == {
        "messages": ["unknown occurrence parent", "invalid prepared type policy"],
        "requested": [],
        "executed": [],
        "apps": 0,
    }


def test_start_prepared_isolates_plugin_inputs_and_unwinds_attempted_activation(page: Any) -> None:
    root = Path(__file__).parents[2] / "citry"
    result = page.evaluate(
        (
            """async ({vueSource, clientSource}) => {
          window.eval(vueSource); window.eval(clientSource);
          const helperContract=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest='b'.repeat(64), definitionId='definition', log=[];
          window.CitryStableDefinitions={[definitionId]:{render(){return Vue.h('div')},target:'ordinary-vnodes/1',
            helperContract:helperContract,
            dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,{});
          const factory=name=>()=>({install(){},prepareRevision(payload,snapshot){
              log.push(`prepare:${name}:${payload.value}:${Object.isFrozen(payload)}:${Object.isFrozen(snapshot)}`);
              try { payload.value='changed' } catch (_) {}
              return {name};
"""
            "            },activateRevision(){log.push(`activate:${name}`);if(name==='second')throw"
            " new Error('second activation');},\n"
            """            commitRevision(){},abortRevision(){log.push(`abort:${name}`)},
            rollbackRevision(){log.push(`rollback:${name}`)},dispose(){log.push(`dispose:${name}`)}});
          for(const name of ['first','second','third']) CitryStable.registerBrowserPlugin(name,1,factory(name),[]);
          const extensions=Object.fromEntries(['first','second','third'].map(name=>[name,
            {schemaVersion:1,payload:{value:'original'},templateContextNames:[]} ]));
          const manifest={protocol:'citry-vue-prepared/1',appId:'transaction-app',revision:0,rootId:'root',
            occurrences:[{id:'root',typeKey:'Root',definitionId,parentId:null,placementKey:null,serverData:{},preparedData:{calls:{},selectedSlots:{}}}],
            definitions:[{id:definitionId,url:'/unused.js',sha256:digest,target:'ordinary-vnodes/1',
              helperContract:helperContract,
              dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}],
            replacements:[],scripts:[],styles:[],typePolicies:[{typeKey:'Root',lazyAllowed:false}],extensions};
          document.body.innerHTML='<div id="app"></div>';
          let message='';
          try { await CitryStable.startPrepared({manifest,host:'#app',tags:{Root:'c-root'}}) }
          catch(error){message=error.message}
          return {message,log};
        }"""
        ),
        {"vueSource": (root / "_vue" / "vue.js").read_text(), "clientSource": _client_bundle_source(root / "_vue")},
    )
    assert result["message"] == "second activation"
    assert result["log"][:3] == [
        "prepare:first:original:true:true",
        "prepare:second:original:true:true",
        "prepare:third:original:true:true",
    ]
    assert result["log"][3:8] == [
        "activate:first",
        "activate:second",
        "rollback:second",
        "rollback:first",
        "abort:third",
    ]


def test_initial_postpublication_failure_disposes_without_rollback(page: Any) -> None:
    root = Path(__file__).parents[2] / "citry"
    result = page.evaluate(
        (
            """async ({vueSource,clientSource})=>{
"""
            "          window.eval(vueSource);window.eval(clientSource);const helperContract=client"
            'Source.match(/const HELPER_CONTRACT = "([^"]+)"/)[1],d=\'c\'.repeat(64),log=[];\n'
            """          CitryStableDefinitions={definition:{render(){return Vue.h('div')},target:'ordinary-vnodes/1',
            helperContract:helperContract,dynamicElements:[],
            directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',d,{});
          CitryStable.registerBrowserPlugin('probe',1,()=>({install(){},prepareRevision(){return{}},
"""
            "            activateRevision(){log.push('activate')},commitRevision(){log.push('commit"
            "');throw Error('commit failure')},\n"
            """\
            abortRevision(){log.push('abort')},rollbackRevision(){log.push('rollback')},dispose(){log.push('dispose')}}),[]);
          const manifest={protocol:'citry-vue-prepared/1',appId:'published-failure',revision:0,rootId:'root',
            occurrences:[{id:'root',typeKey:'Root',definitionId:'definition',parentId:null,placementKey:null,serverData:{},preparedData:{calls:{},selectedSlots:{}}}],
            definitions:[{id:'definition',url:'/unused.js',sha256:d,target:'ordinary-vnodes/1',
              helperContract:helperContract,dynamicElements:[],
              directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}],replacements:[],scripts:[],styles:[],
            typePolicies:[{typeKey:'Root',lazyAllowed:false}],extensions:{probe:{schemaVersion:1,payload:{},templateContextNames:[]}}};
          document.body.innerHTML='<div id="app"></div>';let message='';
          try{await CitryStable.startPrepared({manifest,host:'#app',tags:{Root:'c-root'}})}
          catch(error){message=error.message} return {message,log,apps:CitryStable._apps.size};
        }"""
        ),
        {"vueSource": (root / "_vue" / "vue.js").read_text(), "clientSource": _client_bundle_source(root / "_vue")},
    )
    assert result == {"message": "commit failure", "log": ["activate", "commit", "dispose"], "apps": 0}


def test_revision_postpublication_callback_failure_disposes_plugin_once(page: Any) -> None:
    root = Path(__file__).parents[2] / "citry"
    result = page.evaluate(
        """async ({vueSource,clientSource})=>{
          window.eval(vueSource);window.eval(clientSource);const digest='f'.repeat(64),log=[];
          const helperContract=CitryStable.compilerRuntime.helperContract;
          CitryStableDefinitions={definition:{render(){return Vue.h('div')},target:'ordinary-vnodes/1',
            helperContract,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,(context)=>{
            log.push(`callback:${Object.keys(context).sort().join(',')}:${context.revision}`);
            if(context.revision===1)throw Error('revision callback failure');
          });
          CitryStable.registerBrowserPlugin('probe',1,()=>({install(){},prepareRevision(){return{}},
            activateRevision(){log.push('activate')},commitRevision(){log.push('commit')},abortRevision(){log.push('abort')},
            rollbackRevision(){log.push('rollback')},dispose(){log.push('dispose')}}),[]);
          const occurrence=value=>({id:'root',typeKey:'Root',definitionId:'definition',parentId:null,placementKey:null,
            serverData:{value},preparedData:{calls:{},selectedSlots:{}}});
          const manifest={protocol:'citry-vue-prepared/1',appId:'revision-published-failure',revision:0,rootId:'root',
            occurrences:[occurrence(0)],definitions:[{id:'definition',url:'/unused.js',sha256:digest,target:'ordinary-vnodes/1',
              helperContract,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}],
            replacements:[],scripts:[],styles:[],typePolicies:[{typeKey:'Root',lazyAllowed:false}],
            extensions:{probe:{schemaVersion:1,payload:{},templateContextNames:[]}}};
          document.body.innerHTML='<div id="app"></div>';
          await CitryStable.startPrepared({manifest,host:'#app',tags:{Root:'c-root'}});
          CitryStable._apps.get(manifest.appId).preparedHost={
            onOccurrenceMounted(){},onOccurrenceUnmounted(){},beforeServerCallbacks(){}
          };
          let message='';
          try{await CitryStable.applyEnvelope(manifest.appId,{...manifest,revision:1,baseRevision:0,
            occurrences:[occurrence(1)],updatedIds:['root'],definitions:[],
            extensions:{probe:{schemaVersion:1,payload:{},templateContextNames:[]}}});}
          catch(error){message=error.message}
          return {message,log,apps:CitryStable._apps.size};
        }""",
        {"vueSource": (root / "_vue" / "vue.js").read_text(), "clientSource": _client_bundle_source(root / "_vue")},
    )
    assert result == {
        "message": "revision callback failure",
        "log": [
            "activate",
            "callback:component,revision:0",
            "commit",
            "callback:component,revision:1",
            "dispose",
        ],
        "apps": 0,
    }


def test_revision_rejects_unbound_child_and_wrong_lexical_parent_before_mutation(page: Any) -> None:
    root = Path(__file__).parents[2] / "citry"
    result = page.evaluate(
        (
            """async ({vueSource,fragmentSource,clientSource})=>{
          window.eval(vueSource);window.eval(fragmentSource);window.eval(clientSource);
          const digest='7'.repeat(64),helperContract=CitryStable.compilerRuntime.helperContract;
          const call={localId:'childCall',typeKey:'Child',componentTag:'c-child',bindings:[]};
          const metadata=(localCalls=[])=>({target:'ordinary-vnodes/1',helperContract,
            dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls,localCallRuns:[],opaqueHtmlSites:[]});
          CitryStableDefinitions={root:{...metadata([call]),render(){
            return Vue.h(Vue.resolveComponent('c-child'),{citryId:'child'});
          }},child:{...metadata(),render(){return Vue.h('span','child')}}};
          CitryStable.registerTypeOptions('Root',digest,{});CitryStable.registerTypeOptions('Child',digest,{});
          const descriptor=(id,localCalls=[])=>({id,url:'/unused.js',sha256:digest,...metadata(localCalls)});
"""
            "          const child={id:'child',typeKey:'Child',definitionId:'child',parentId:'root'"
            ",placementKey:'child',serverData:{},\n"
            """            preparedData:{calls:{},callRuns:{},selectedSlots:{}}};
"""
            "          const rootOccurrence=parentId=>({id:'root',typeKey:'Root',definitionId:'root"
            "',parentId:null,placementKey:null,\n"
            """            serverData:{},preparedData:{calls:{childCall:{id:'child',key:'child',parentId}},
              callRuns:{},selectedSlots:{}}});
          const manifest={protocol:'citry-vue-prepared/1',appId:'topology-negatives',revision:0,
            rootId:'root',occurrences:[rootOccurrence('root'),child],
            definitions:[descriptor('root',[call]),descriptor('child')],replacements:[],scripts:[],styles:[],
            typePolicies:[{typeKey:'Root',lazyAllowed:false},{typeKey:'Child',lazyAllowed:false}],extensions:{}};
          document.body.innerHTML='<div id="app"></div>';
          await CitryStable.startPrepared({manifest,host:'#app',tags:{Root:'c-root',Child:'c-child'}});
          const rejected=[];
          try { await CitryStable.applyEnvelope(manifest.appId,{...manifest,revision:1,baseRevision:0,
            occurrences:[rootOccurrence('child'),child],updatedIds:['root'],definitions:[]}); }
          catch(error){rejected.push(error.message)}
          const rogue={...child,id:'rogue',placementKey:'rogue'};
          try { await CitryStable.applyEnvelope(manifest.appId,{...manifest,revision:1,baseRevision:0,
            occurrences:[rootOccurrence('root'),child,rogue],updatedIds:['rogue'],definitions:[]}); }
          catch(error){rejected.push(error.message)}
          return {rejected,revision:CitryStable._apps.get(manifest.appId).revision,
            text:document.querySelector('#app').textContent};
        }"""
        ),
        {
            "vueSource": (root / "_vue" / "vue.js").read_text(),
            "fragmentSource": (root / "_vue" / "fragments.js").read_text(),
            "clientSource": (root / "_vue" / "client.js").read_text(),
        },
    )
    assert result == {
        "rejected": [
            "prepared local call does not match occurrence placement",
            "prepared occurrence has no local call binding",
        ],
        "revision": 0,
        "text": "child",
    }


@pytest.mark.parametrize("dispose_order", [("first", "second"), ("second", "first")])
def test_prepared_stylesheets_are_owned_per_app_and_never_adopt_authored_links(
    page: Any, dispose_order: tuple[str, str]
) -> None:
    root = Path(__file__).parents[2] / "citry"
    result = page.evaluate(
        (
            """async ({vueSource,clientSource,disposeOrder})=>{
          window.eval(vueSource);window.eval(clientSource);
          const helperContract=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest='d'.repeat(64),url='data:text/css,.owned%7Bcolor:green%7D';
          CitryStableDefinitions={definition:{render(){return Vue.h('div')},target:'ordinary-vnodes/1',
            helperContract:helperContract,dynamicElements:[],
            directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,{});
          document.head.innerHTML=`<link id="authored" rel="stylesheet" href="${url}">
"""
            '            <link id="first-style" rel="stylesheet" href="${url}" data-citry-css-url="'
            '${url}" data-citry-vue-style-app="first">\n'
            '            <link id="second-style" rel="stylesheet" href="${url}" data-citry-css-url='
            '"${url}" data-citry-vue-style-app="second">`;\n'
            """          document.body.innerHTML='<div id="first"></div><div id="second"></div>';
          const manifest=appId=>({protocol:'citry-vue-prepared/1',appId,revision:0,rootId:'root',
            occurrences:[{id:'root',typeKey:'Root',definitionId:'definition',parentId:null,placementKey:null,serverData:{},preparedData:{calls:{},selectedSlots:{}}}],
            definitions:[{id:'definition',url:'/unused.js',sha256:digest,target:'ordinary-vnodes/1',
              helperContract:helperContract,dynamicElements:[],
              directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}],replacements:[],scripts:[],
            styles:[{lazyAllowed:false,owner:{kind:'component',typeKey:'Root',occurrenceIds:['root']},
              source:{kind:'external',url,attrs:{}}}],typePolicies:[{typeKey:'Root',lazyAllowed:false}],extensions:{}});
          const handles={};
"""
            "          for(const appId of ['first','second']) handles[appId]=await CitryStable.star"
            "tPrepared({manifest:manifest(appId),\n"
            """            host:'#'+appId,tags:{Root:'c-root'}});
          handles[disposeOrder[0]].app.unmount();
"""
            "          const afterFirst={authored:!!document.querySelector('#authored'),first:!!doc"
            "ument.querySelector('#first-style'),\n"
            """            second:!!document.querySelector('#second-style'),apps:CitryStable._apps.size};
          handles[disposeOrder[1]].app.unmount();
"""
            "          return {afterFirst,final:{authored:!!document.querySelector('#authored'),fir"
            "st:!!document.querySelector('#first-style'),\n"
            """            second:!!document.querySelector('#second-style'),apps:CitryStable._apps.size}};
        }"""
        ),
        {
            "vueSource": (root / "_vue" / "vue.js").read_text(),
            "clientSource": _client_bundle_source(root / "_vue"),
            "disposeOrder": dispose_order,
        },
    )
    assert result["afterFirst"] == {
        "authored": True,
        "first": dispose_order[0] != "first",
        "second": dispose_order[0] != "second",
        "apps": 1,
    }
    assert result["final"] == {"authored": True, "first": False, "second": False, "apps": 0}
