from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ReactiveImage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "image_attrs": {
                "@load": "$dispatch('image-native-load')",
                "@error": "$dispatch('image-native-error')",
                "data-native-events": "bridged",
            }
        }

    template = """
      <section
        class="image-reactive"
        x-data="{
          source:'/static/img/ui/image/horsehead-nebula-1280.jpg?frame=slow-red',
          status:'waiting',
          selected:'none',
          callbacks:0,
          nativeLoads:0,
          nativeErrors:0,
          redact:(value)=>value ? value.split('/').pop().split('?')[0] : 'none',
        }"
        @image-native-load="nativeLoads++"
        @image-native-error="nativeErrors++"
      >
        <div class="image-reactive__controls">
          <button
            type="button"
            @click="source='/static/img/ui/image/horsehead-nebula-1280.jpg?frame=slow-red'"
          >Frame A</button>
          <button
            type="button"
            @click="source='/static/img/ui/image/orion-nebula-1280.jpg?frame=fast-blue'"
          >Frame B</button>
          <button
            type="button"
            @click="source='/static/img/ui/image/missing-live-frame.jpg?frame=broken'"
          >Broken</button>
          <button
            type="button"
            @click="
              source='/static/img/ui/image/horsehead-nebula-1280.jpg?frame=rapid-a';
              queueMicrotask(()=>source='/static/img/ui/image/orion-nebula-640.jpg?frame=rapid-b');
            "
          >Rapid A then B</button>
        </div>

        <c-CImage
          src="/static/img/ui/image/horsehead-nebula-1280.jpg"
          alt="Live survey frame from Northstar Ridge"
          c-width="1280"
          c-height="720"
          c-img_attrs="image_attrs"
          $c-props="{
            src:source,
            onStatusChange:(detail)=>{
              callbacks++;
              status=detail.status;
              selected=redact(detail.current_src || detail.src);
            },
          }"
        >
          <c-fill name="fallback">Survey frame unavailable</c-fill>
        </c-CImage>

        <output
          x-text="
            `Status ${status}; selected ${selected}; callbacks ${callbacks};
            native load/error ${nativeLoads}/${nativeErrors}`
          "
        >Status waiting; selected none; callbacks 0; native load/error 0/0</output>
        <p>
          The output redacts paths to filenames. Native events use an img_attrs
          $dispatch bridge; onStatusChange is the owner-local cached-race surface.
        </p>
        <div id="image-reactive-shadow-host" aria-label="Open ShadowRoot fixture"></div>
      </section>
    """

    css = """
      :where(.image-reactive) {
        display: grid;
        gap: 1rem;
        max-inline-size: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-reactive__controls) { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      :where(.image-reactive p) { margin: 0; }
      :where(.image-reactive [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ReactiveImage()

preview  # noqa: B018
