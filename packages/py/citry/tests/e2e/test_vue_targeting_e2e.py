from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("corruption", "message"),
    [
        ("partial", "revision occurrence address is invalid or duplicated"),
        ("retained-duplicate", "address is invalid or duplicated"),
    ],
)
def test_address_preflight_rejects_before_immediate_state_commit(
    page: Any, serve_live: Any, corruption: str, message: str
) -> None:
    engine = Citry(secret="vue-address-preflight-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    target_render_id = ""
    retained_render_id = ""

    class Leaf(Component):
        citry = engine
        template = "<i>leaf</i>"

    class Panel(Component):
        citry = engine
        template = '<section id="target-panel">{{ child }}</section>'

        def template_data(self, kwargs, slots):
            nonlocal target_render_id, retained_render_id
            if kwargs.get("role") == "target":
                target_render_id = self.id
            elif kwargs.get("role") == "retained":
                retained_render_id = self.id
            return kwargs

    class CallerState:
        count: int = 0

    class Caller(Component):
        citry = engine
        State = CallerState
        template = '<button id="corrupt-address" @c-click="refresh">refresh</button>'

        class Events:
            def refresh(self, state: CallerState):
                state.count += 1
                return actions.Render(Panel(role="replacement", child=Leaf()), target=f"render:{target_render_id}")

    target = Panel(role="target", child=Leaf())
    retained = Panel(role="retained", child=Leaf())

    class Page(Component):
        citry = engine
        template = "<main>{{ caller }}{{ target }}{{ retained }}</main>"

        def template_data(self, kwargs, slots):
            return {"caller": Caller(), "target": target, "retained": retained}

    dispatcher_for(engine)
    request_tokens: list[str | None] = []
    response_tokens: list[str] = []

    def corrupt(route: Any) -> None:
        request_tokens.append(route.request.post_data_json["calls"][0].get("stateToken"))
        response = route.fetch()
        payload = response.json()
        state_action = next(
            action
            for action in payload["results"][0]["actions"]
            if action["action"] == "state"
            and not (isinstance(action.get("delay"), (int, float)) and action["delay"] > 0)
            and action.get("wait") is not False
        )
        response_tokens.append(state_action["stateToken"])
        prepared = next(
            action["prepared"] for action in payload["results"][0]["actions"] if action["action"] == "render"
        )
        if corruption == "partial":
            del prepared["occurrences"][-1]["renderId"]
        else:
            prepared["occurrences"][0]["renderId"] = retained_render_id
            prepared["occurrences"][0].pop("eventContext", None)
        route.fulfill(
            status=response.status,
            headers=response.headers,
            body=json.dumps(payload),
            content_type="application/citry-events+json",
        )

    page.route("**/ext/events/call", corrupt)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("""window.__addressErrors=[];
      addEventListener('error',event=>__addressErrors.push(String(event.error||event.message)));
      addEventListener('unhandledrejection',event=>__addressErrors.push(String(event.reason)));""")
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    revision = page.evaluate("[...CitryStable._apps.values()][0].revision")
    html = page.locator("#target-panel").first.inner_html()

    page.locator("#corrupt-address").click()
    page.wait_for_function(
        "needle => window.__addressErrors?.some(value => value.includes(needle))",
        arg=message,
    )
    with page.expect_request("**/ext/events/call"):
        page.locator("#corrupt-address").click()
    page.wait_for_function(
        "needle => window.__addressErrors?.filter(value => value.includes(needle)).length >= 2",
        arg=message,
    )

    assert len(request_tokens) == 2
    assert len(response_tokens) == 2
    assert response_tokens[0] != request_tokens[0]
    assert request_tokens[1] == request_tokens[0]
    assert page.evaluate("[...CitryStable._apps.values()][0].revision") == revision
    assert page.locator("#target-panel").first.inner_html() == html
    assert any(message in value for value in page.evaluate("window.__addressErrors"))
    assert any(message in value for value in errors)


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("runtime_binding", "runtime_handler", "table_name", "runtime_prefix"),
    [
        ("@c-click", "ping", "eventBindings", "citryRuntimeEvent"),
        ("@c-poll.1s", "poll", "pollBindings", "citryRuntimePoll"),
    ],
)
def test_runtime_event_reference_preflight_rejects_before_state_and_dom_commit(
    page: Any,
    serve_live: Any,
    runtime_binding: str,
    runtime_handler: str,
    table_name: str,
    runtime_prefix: str,
) -> None:
    engine = Citry(secret="vue-runtime-event-preflight-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    target_render_id = ""
    caller_render_id = ""

    class Leaf(Component):
        citry = engine
        template = "<i>leaf</i>"

    class Panel(Component):
        citry = engine
        template = '<section id="target-panel"><button c-bind="attrs">runtime</button>{{ child }}</section>'

        class Events:
            def ping(self):
                return None

            def poll(self):
                return None

        def template_data(self, kwargs, slots):
            nonlocal target_render_id
            if kwargs.get("role") == "target":
                target_render_id = self.id
            return {**kwargs, "attrs": {runtime_binding: runtime_handler}}

    class CallerState:
        count: int = 0

    class Caller(Component):
        citry = engine
        State = CallerState
        template = '<button id="preflight-refresh" @c-click="refresh">refresh</button>'

        def template_data(self, kwargs, slots):
            nonlocal caller_render_id
            caller_render_id = self.id
            return kwargs

        class Events:
            def refresh(self, state: CallerState):
                state.count += 1
                return actions.Render(Panel(role="replacement", child=Leaf()), target=f"render:{target_render_id}")

    target = Panel(role="target", child=Leaf())

    class Page(Component):
        citry = engine
        template = "<main>{{ caller }}{{ target }}</main>"

        def template_data(self, kwargs, slots):
            return {"caller": Caller(), "target": target}

    dispatcher_for(engine)
    request_tokens: list[str | None] = []
    response_tokens: list[str] = []

    def corrupt(route: Any) -> None:
        request_tokens.append(route.request.post_data_json["calls"][0].get("stateToken"))
        response = route.fetch()
        payload = response.json()
        actions_in_response = payload["results"][0]["actions"]
        state_action = next(action for action in actions_in_response if action["action"] == "state")
        render_action = next(action for action in actions_in_response if action["action"] == "render")
        assert actions_in_response.index(state_action) < actions_in_response.index(render_action)
        response_tokens.append(state_action["stateToken"])

        prepared = render_action["prepared"]
        [definition] = [item for item in prepared["definitions"] if item["runtimeEventSites"]]
        [site] = definition["runtimeEventSites"]
        assert site["steps"] == []
        [occurrence] = [item for item in prepared["occurrences"] if item["definitionId"] == definition["id"]]
        binding_id = occurrence["preparedData"][site["bindingKey"]]
        assert binding_id.startswith(runtime_prefix)
        assert binding_id in occurrence["preparedData"][table_name]
        replacement_id = binding_id[:-1] + ("0" if binding_id[-1] != "0" else "1")
        occurrence["preparedData"][site["bindingKey"]] = replacement_id
        route.fulfill(
            status=response.status,
            headers=response.headers,
            body=json.dumps(payload),
            content_type="application/citry-events+json",
        )

    page.route("**/ext/events/call", corrupt)
    message = "runtime event references do not match definition sites"
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(
        """window.__runtimeEventErrors=[];
          addEventListener('error',event=>window.__runtimeEventErrors.push(String(event.error||event.message)));
          addEventListener('unhandledrejection',event=>window.__runtimeEventErrors.push(String(event.reason)));"""
    )
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    target_html = page.locator("#target-panel").inner_html()

    def caller_state_and_app_context() -> dict[str, Any]:
        return page.evaluate(
            """renderId => {
              const app=[...CitryStable._apps.values()][0];
              const occurrence=[...app.occurrences.values()].find(item=>item.renderId===renderId);
              if(!occurrence)throw new Error('caller occurrence is missing from the mounted app');
              return {count:app.mounted.get(occurrence.id).component.$state.count,
                stateToken:occurrence.eventContext.stateToken,revision:app.revision};
            }""",
            caller_render_id,
        )

    initial = caller_state_and_app_context()
    assert initial["count"] == 0
    assert initial["stateToken"]

    page.locator("#preflight-refresh").click()
    page.wait_for_function(
        "needle => window.__runtimeEventErrors?.some(value => value.includes(needle))",
        arg=message,
    )
    with page.expect_request("**/ext/events/call"):
        page.locator("#preflight-refresh").click()
    page.wait_for_function(
        "needle => window.__runtimeEventErrors?.filter(value => value.includes(needle)).length >= 2",
        arg=message,
    )

    after = caller_state_and_app_context()
    assert len(request_tokens) == 2
    assert len(response_tokens) == 2
    assert request_tokens == [initial["stateToken"], initial["stateToken"]]
    assert all(token != request_tokens[0] for token in response_tokens)
    assert after == initial
    assert page.locator("#target-panel").inner_html() == target_html
    assert any(message in value for value in page.evaluate("window.__runtimeEventErrors"))
    assert any(message in value for value in errors)


def test_i18n_plugin_translates_only_occurrence_references_without_mutating_input(page: Any) -> None:
    source = (Path(__file__).parents[2] / "citry" / "ext" / "i18n" / "client" / "vue-plugin.source.js").read_text(
        encoding="utf-8"
    )
    result = page.evaluate(
        """source => {
          let factory;
          window.CitryStable={registerBrowserPlugin(_name,_version,value){factory=value}};
          window.eval(source);
          const plugin=factory({vue:{shallowRef:value=>({value})},
            occurrence(){return null},occurrenceId(){return null}});
          const retained={serverProviderId:'server-retained'};
          const payload={providers:[{id:'one',parent:'two',serverProviderId:'server-one'}],barriers:['two'],
            requirements:[{owner:'one',provider:retained,bindings:[]}],opaque:{value:'one'}};
          const original=structuredClone(payload);
          const translated=plugin.translateRevision(payload,id=>({one:'nextOne',two:'nextTwo'})[id]);
          return {translated,original,payload,retainedSame:translated.requirements[0].provider.serverProviderId};
        }""",
        source,
    )
    assert result["payload"] == result["original"]
    assert result["translated"]["providers"][0]["id"] == "nextOne"
    assert result["translated"]["providers"][0]["parent"] == "nextTwo"
    assert result["translated"]["barriers"] == ["nextTwo"]
    assert result["translated"]["requirements"][0]["owner"] == "nextOne"
    assert result["retainedSame"] == "server-retained"
    assert result["translated"]["opaque"] == {"value": "one"}


def test_real_coordinator_persists_i18n_translation_into_plugin_preparation(page: Any) -> None:
    root = Path(__file__).parents[2] / "citry"
    result = page.evaluate(
        """async ({runtimeSource,i18nSource}) => {
          window.eval(runtimeSource);
          const seen=[];let enterI18n;
          const register=CitryStable.registerBrowserPlugin.bind(CitryStable);
          CitryStable.registerBrowserPlugin=(name,version,factory,names)=>register(name,version,host=>{
            const plugin=factory(host),prepare=plugin.prepareRevision.bind(plugin);
            plugin.prepareRevision=(payload,snapshot)=>{seen.push(structuredClone(payload));
              if(window.__stallI18n)return new Promise((resolve,reject)=>{enterI18n();window.__resolveI18n=()=>{
                try{resolve(prepare(payload,snapshot))}catch(error){reject(error)}}});
              return prepare(payload,snapshot)};
            return plugin;
          },names);
          window.eval(i18nSource);
          const helper=CitryStable.compilerRuntime.helperContract,digest='a'.repeat(64),definitionId='definition';
          CitryStableDefinitions={[definitionId]:{render(){return Vue.h('div')},target:'ordinary-vnodes/1',
            helperContract:helper,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,{});
          let capturedHost;
          const realEvents=CitryVueEvents;
          window.CitryVueEvents={...realEvents,createVueEventsBridge(options){
            capturedHost=options.host;return realEvents.createVueEventsBridge(options)}};
          const context=()=>({catalog_revision:'catalog',direction:'ltr',fallback_locales:[],
            formats_revision:'formats',
            locale:'en',time_zone:null,tzdb_revision:'none'});
          const parser=()=>({formats_revision:'formats',locale:'en',number:{},percent:{},revision:'parser',
            schema_version:1});
          const i18n=id=>({providers:[{id,parent:null,serverProviderId:'server-provider',context:context(),
              policy:{direction:{mode:'inherit'},locale:{mode:'explicit',value:'en'},time_zone:{mode:'inherit'}}}],
            barriers:[],requirements:[],catalog_revision:'catalog',contexts:{en:context()},formats:{},
            formats_revision:'formats',locales:['en'],messages_url:null,parsers:{en:parser()},runtime:'@fluent/bundle@0.19.1'});
          const occurrence=(id,renderId)=>({id,renderId,typeKey:'Root',definitionId,parentId:null,placementKey:null,
            serverData:{},preparedData:{calls:{},callRuns:{}},eventContext:{serverRenderId:renderId,stateToken:null,
              publicState:{},componentClassId:'Root',descriptor:{componentClassId:'Root',eventHandlers:{ping:{httpMethod:'POST'}}}}});
          const definition={id:definitionId,url:'/unused.js',sha256:digest,target:'ordinary-vnodes/1',
            helperContract:helper,
            dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]};
          const extensions=id=>({i18n:{schemaVersion:1,payload:i18n(id),
            templateContextNames:['$citryI18nBinding','$i18n']}});
          const baseStyle=id=>({lazyAllowed:true,owner:{kind:'component',typeKey:'Root',occurrenceIds:[id]},
            source:{kind:'external',url:'data:text/css,.target%7Bcolor:green%7D',attrs:{rel:'stylesheet'}}});
          const initial={protocol:'citry-vue-prepared/1',appId:'app',revision:0,
            rootId:'citryOccurrenceRoot',markers:[],
            occurrences:[occurrence('citryOccurrenceRoot','server_root')],definitions:[definition],replacements:[],scripts:[],
            styles:[baseStyle('citryOccurrenceRoot')],
            typePolicies:[{typeKey:'Root',lazyAllowed:false}],extensions:extensions('citryOccurrenceRoot')};
          document.body.innerHTML='<div id="app"></div>';
          await CitryStable.startPrepared({manifest:initial,host:'#app',tags:{Root:'c-root'},endpoint:'/events',
            loadInitialAssets:true,allowLazyTypeAssets:true});
          if(!capturedHost)throw new Error('real Events host was not captured after bootstrap');
          const incomingId='citryOccurrenceIncoming';
          const revision={...initial,revision:1,baseRevision:0,rootId:incomingId,
            occurrences:[occurrence(incomingId,'server_fresh')],updatedIds:[incomingId],
            styles:[baseStyle(incomingId)],extensions:extensions(incomingId)};
          const action={action:'render',target:'render:server_root',swap:'morph',renderer:'vue-prepared/1',
            prepared:revision};
          const mounted=CitryStable._apps.get('app').mounted.get('citryOccurrenceRoot');
          const source={stableId:'citryOccurrenceRoot',generation:mounted.record.generation};
          const failure=mutate=>{const candidate=structuredClone(action);mutate(candidate.prepared);
            try{capturedHost.preflightResult({ok:true,sendSequence:1,actions:[candidate]},source);return ''}
            catch(error){return error.message}};
          const missingAddress=failure(value=>{delete value.occurrences[0].renderId});
          const malformedId=failure(value=>{value.rootId='bad:id';value.occurrences[0].id='bad:id';
            value.updatedIds=['bad:id'];value.extensions.i18n.payload.providers[0].id='bad:id'});
          const lazyAsset=failure(value=>{value.styles=[{lazyAllowed:false,
            owner:{kind:'component',typeKey:'Root',occurrenceIds:[incomingId]},
            source:{kind:'external',url:'/unseen.css',attrs:{rel:'stylesheet'}}}]});
          const duplicateAsset=failure(value=>{value.styles=[
            {lazyAllowed:true,owner:{kind:'component',typeKey:'Root',occurrenceIds:[incomingId]},
              source:{kind:'external',url:'/duplicate.css',attrs:{rel:'stylesheet'}}},
            {lazyAllowed:true,owner:{kind:'component',typeKey:'Root',occurrenceIds:[incomingId]},
              source:{kind:'external',url:'/duplicate.css',attrs:{rel:'stylesheet',media:'print'}}}]});
          const currentCollision=failure(value=>{value.styles[0].source.attrs.media='print'});
          const original=structuredClone(revision.extensions.i18n.payload);
          const planned=capturedHost.preflightResult({ok:true,sendSequence:1,actions:[action]},source);
          window.__stallI18n=true;
          const entered=new Promise(resolve=>{enterI18n=resolve});
          const stalePending=capturedHost.prepareRender(action,source,new AbortController().signal,planned.renderPlan)
            .then(()=>'',error=>error.message);
          await entered;
          const app=CitryStable._apps.get('app'),savedMounted=app.mounted.get('citryOccurrenceRoot');
          app.mounted.delete('citryOccurrenceRoot');window.__resolveI18n();
          const staleTarget=await stalePending;
          app.mounted.set('citryOccurrenceRoot',savedMounted);window.__stallI18n=false;
          const prepared=await capturedHost.prepareRender(action,source,
            new AbortController().signal,planned.renderPlan);
          capturedHost.abortRender(prepared,source);
          return {originalUnchanged:JSON.stringify(original)===JSON.stringify(revision.extensions.i18n.payload),
            planned:planned.renderPlan.envelope.extensions.i18n.payload.providers[0].id,
            prepared:seen.at(-1).providers[0].id,missingAddress,malformedId,lazyAsset,duplicateAsset,currentCollision,staleTarget,
            revisionAfterStale:app.revision};
        }""",
        {
            "runtimeSource": (root / "_vue" / "runtime.js").read_text(encoding="utf-8"),
            "i18nSource": (root / "ext" / "i18n" / "client" / "vue-plugin.source.js").read_text(encoding="utf-8"),
        },
    )
    assert result["originalUnchanged"] is True
    assert result["planned"] == "citryOccurrenceRoot"
    assert result["prepared"] == "citryOccurrenceRoot"
    assert "address" in result["missingAddress"]
    assert "occurrence ID is invalid" in result["malformedId"]
    assert "disallows lazy loading" in result["lazyAsset"]
    assert result["duplicateAsset"] == "prepared styles identity conflicts across Render targets"
    assert "URL identity collision" in result["currentCollision"]
    assert "target became stale while rendering" in result["staleTarget"]
    assert result["revisionAfterStale"] == 0


@pytest.mark.e2e
def test_cross_target_new_child_can_send_its_own_event(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-new-child-target-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    target_render_id = ""

    class NewChild(Component):
        citry = engine
        template = '<button id="new-child" @c-click="advance">{{ label }}</button>'

        class Events:
            def advance(self):
                return actions.Render(NewChild(label="child-updated"))

        def template_data(self, kwargs, slots):
            return kwargs

    class Target(Component):
        citry = engine
        template = '<section id="target">{{ child }}</section>'

        def template_data(self, kwargs, slots):
            nonlocal target_render_id
            if kwargs.get("capture_target"):
                target_render_id = self.id
            return kwargs

    class Controller(Component):
        citry = engine
        template = '<button id="add-child" @c-click="add">add</button>'

        class Events:
            def add(self):
                return actions.Render(
                    Target(child=NewChild(label="child-ready"), capture_target=False),
                    target=f"render:{target_render_id}",
                )

    target = Target(child=None, capture_target=True)

    class Page(Component):
        citry = engine
        template = "<main>{{ controller }}{{ target }}</main>"

        def template_data(self, kwargs, slots):
            return {"controller": Controller(), "target": target}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")

    page.locator("#add-child").click()
    page.wait_for_function("document.querySelector('#new-child')?.textContent === 'child-ready'")
    page.locator("#new-child").click()
    page.wait_for_function("document.querySelector('#new-child')?.textContent === 'child-updated'")

    assert page.locator("#add-child").count() == 1
    assert faults == []


@pytest.mark.e2e
def test_unchanged_definition_renders_new_js_data_key(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-new-data-key-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Shape(Component):
        citry = engine
        template = '<button id="shape" @c-click="refresh" v-text="label"></button>'

        class Events:
            def refresh(self):
                return actions.Render(Shape(label="ready"))

        def js_data(self, kwargs, slots):
            return kwargs

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Shape().render().serialize(), "") + "/")
    page.locator("#shape").click()
    page.wait_for_function("document.querySelector('#shape')?.textContent === 'ready'")

    assert page.locator("#shape").text_content() == "ready"
    assert faults == []
