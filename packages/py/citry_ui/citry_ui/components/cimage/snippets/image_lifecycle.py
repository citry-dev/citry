from __future__ import annotations

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ImageLifecycle(Component):
    class Kwargs:
        step: int = 0

    class Slots:
        pass

    class Events:
        def retain(self) -> ImageLifecycle:
            return ImageLifecycle(step=1)

        def change_resource(self) -> ImageLifecycle:
            return ImageLifecycle(step=2)

        def replace(self) -> ImageLifecycle:
            return ImageLifecycle(step=3)

        def remove(self) -> ImageLifecycle:
            return ImageLifecycle(step=4)

        def restore(self) -> ImageLifecycle:
            return ImageLifecycle(step=5)

        def remove_again(self) -> ImageLifecycle:
            return ImageLifecycle(step=6)

        def restore_again(self) -> ImageLifecycle:
            return ImageLifecycle(step=7)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        source = "/static/img/ui/image/horsehead-nebula-1280.jpg?plate=baseline"
        if kwargs.step >= 2:
            source = "/static/img/ui/image/orion-nebula-1280.jpg?plate=changed"
        image_key = "image-lifecycle-retained" if kwargs.step < 3 else f"image-lifecycle-{kwargs.step}"
        return {
            "image_key": image_key,
            "include_image": kwargs.step not in {4, 6},
            "source": source,
            "step": kwargs.step,
        }

    template = """
      <section
        class="image-lifecycle"
        x-data="{status:'waiting',selected:'none'}"
      >
        <div class="image-lifecycle__controls">
          <button type="button" @c-click="retain">Retain equal server output</button>
          <button type="button" @c-click="change_resource">Change the resource</button>
          <button type="button" @c-click="replace">Replace native ownership</button>
          <button type="button" @c-click="remove">Remove the Image</button>
          <button type="button" @c-click="restore">Restore a fresh Image</button>
          <button type="button" @c-click="remove_again">Remove it again</button>
          <button type="button" @c-click="restore_again">Restore it again</button>
          <button
            type="button"
            @click="
              const root=$root.querySelector('#image-lifecycle-target');
              if (root) root.setAttribute('data-status','forged');
            "
          >Test hostile status fail-closed</button>
          <button
            type="button"
            @click="
              const root=$root.querySelector('#image-lifecycle-target');
              if (root) root.after(root.cloneNode(true));
            "
          >Insert an unowned clone</button>
        </div>

        <p>Signed server step: <output data-image-lifecycle-step>{{ step }}</output></p>

        <c-if cond="include_image">
          <c-CImage
            #c-key="image_key"
            c-src="source"
            alt="Nightly Northstar calibration plate"
            c-width="1280"
            c-height="720"
            c-attrs="{
              'id':'image-lifecycle-target',
              'data-quality-states':
                'lifecycle retained-root replacement-root morph-target removal restore '
                + 'cleanup owner-token shadow-root clone hostile-fail-closed',
            }"
            $c-props="{
              onStatusChange:(detail)=>{
                status=detail.status;
                selected=(detail.current_src || detail.src).split('/').pop().split('?')[0];
              },
            }"
          >
            <c-fill name="placeholder">Loading calibration plate</c-fill>
            <c-fill name="fallback">Calibration plate unavailable</c-fill>
          </c-CImage>
        </c-if>

        <output x-text="`Status ${status}; selected ${selected}`">
          Status waiting; selected none
        </output>
        <div id="image-lifecycle-shadow-host" aria-label="Open ShadowRoot move fixture"></div>
      </section>
    """

    css = """
      :where(.image-lifecycle) {
        display: grid;
        gap: 1rem;
        max-inline-size: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.image-lifecycle__controls) { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      :where(.image-lifecycle p) { margin: 0; }
      :where(.image-lifecycle [data-citry-ui-part="image-root"]) { inline-size: 100%; }
    """


preview = ImageLifecycle()

preview  # noqa: B018
