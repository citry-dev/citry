"""Exercise caller-owned SVG beneath ordinary Alpine and slot boundaries."""

from __future__ import annotations

from typing import Any

from citry import Component


def fixtures(module: Any, case: str) -> type[Component]:
    """Use the unchanged selected HeroIcon with client behavior only on its callers."""

    class BrowserReceiver(Component):
        citry = module.app
        name = "browser-receiver"
        template = """
<section class="receiver" x-data="{ owner: 'receiver', receiverCount: 0 }">
    <c-slot name="body" />
    <c-slot name="missing">
        <button class="fallback-button" @click="receiverCount += 1">
            <c-heroicons name="home" c-attrs="{'class': 'fallback-icon'}" />
        </button>
        <output class="receiver-count" x-text="receiverCount"></output>
    </c-slot>
</section>
"""

    class BrowserPage(Component):
        citry = module.app
        template = """
<html><body>
    <div id="teleport-target"></div>
    <main id="caller" x-data="{ owner: 'caller', count: 0, show: true }">
        <button class="direct-button" @click="count += 1">
            <c-heroicons name="home" c-attrs="{'class': 'direct-icon'}" />
        </button>
        <output class="caller-count" x-text="count"></output>
        <c-browser-receiver>
            <c-fill name="body">
                <button class="fill-button" @click="count += 1">
                    <c-heroicons name="home" c-attrs="{'class': 'fill-icon'}" />
                </button>
                <template x-teleport="#teleport-target">
                    <button class="teleport-button" @click="count += 1">
                        <c-heroicons name="home" c-attrs="{'class': 'teleport-icon'}" />
                    </button>
                </template>
            </c-fill>
        </c-browser-receiver>
        <button class="toggle" @click="show = !show">toggle</button>
        <template x-if="show">
            <button class="conditional-button" @click="count += 1">
                <c-heroicons name="home" c-attrs="{'class': 'conditional-icon'}" />
            </button>
        </template>
    </main>
</body></html>
"""

    if case != "teleport":
        start = BrowserPage.template.index("                <template x-teleport=")
        end = BrowserPage.template.index("</template>", start) + len("</template>")
        BrowserPage.template = BrowserPage.template[:start] + BrowserPage.template[end:]
    if case != "conditional":
        start = BrowserPage.template.index('        <button class="toggle"')
        end = BrowserPage.template.index("</template>", start) + len("</template>")
        BrowserPage.template = BrowserPage.template[:start] + BrowserPage.template[end:]
    return BrowserPage
