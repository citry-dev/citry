import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ReactiveImage(Component):
    template = """
      <section
        class="image-reactive"

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
          :src="source" :onStatusChange="(detail)=>{
              callbacks++;
              status=detail.status;
              selected=redact(detail.current_src || detail.src);
              if (detail.status === 'loaded') nativeLoads++;
              if (detail.status === 'error') nativeErrors++;
            }"
        >
          <c-fill name="fallback">Survey frame unavailable</c-fill>
        </c-CImage>

        <output
          v-text="
            `Status ${status}; selected ${selected}; callbacks ${callbacks};
            native load/error ${nativeLoads}/${nativeErrors}`
          "
        >Status waiting; selected none; callbacks 0; native load/error 0/0</output>
        <p>
          The output redacts paths to filenames. onStatusChange reports the
          accepted native load or error settlement for the current image.
        </p>
        <div id="image-reactive-shadow-host" aria-label="Open ShadowRoot fixture"></div>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            source:'/static/img/ui/image/horsehead-nebula-1280.jpg?frame=slow-red',
            status:'waiting',
            selected:'none',
            callbacks:0,
            nativeLoads:0,
            nativeErrors:0,
            redact:(value)=>value ? value.split('/').pop().split('?')[0] : 'none',
          };
        },
      });
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
