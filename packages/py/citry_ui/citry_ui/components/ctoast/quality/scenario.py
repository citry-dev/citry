"""Shared Toast scenario used by Citry UI quality tools."""

from __future__ import annotations

from citry import Citry, Component


def toast_states_component(app: Citry) -> type[Component]:
    """Create the reusable Toast state catalog."""

    class CitryUiToastStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack toast-quality"
            aria-labelledby="toast-states-title"
            x-data="{
              notices: [
                {id:'neutral', title:'Draft retained', durationMs:0},
                {id:'success', title:'Field note saved', description:'Aurora Ridge synchronized.',
                 intent:'success', durationMs:0},
                {id:'warn', title:'Connection is slow', intent:'warn', priority:'assertive',
                 actionLabel:'Retry', closeOnAction:false, durationMs:0},
                {id:'queued', title:'Queued observation', durationMs:0},
              ],
              placement:'block-end-end', limit:3, result:'No action yet'
            }"
          >
            <h1 id="toast-states-title">Toast states</h1>
            <div class="toast-quality__controls">
              <c-CButton @click="notices = [...notices, {
                id:`fresh-${notices.length}`, title:'Fresh notification', intent:'info'
              }]">Add notification</c-CButton>
              <c-CButton variant="outline" @click="placement = placement.endsWith('end')
                ? 'block-start-start' : 'block-end-end'">Move logical corner</c-CButton>
              <output x-text="result"></output>
            </div>
            <c-CToastRegion
              id="quality-toast-region"
              class_="toast-quality__region"
              c-attrs="{'data-quality-states':
                'queue polite assertive neutral info success warn error action dismissal '
                'persistent timed visible-limit pause f6 block-start-start block-end-end '
                'long-content rtl brand'}"
              $c-props="{
                items:notices, placement, limit,
                onAction:(id) => result = `Action: ${id}`,
                onDismiss:(id) => notices = notices.filter(item => item.id !== id),
              }"
            />
          </section>
        """

        css = """
          :where(.toast-quality) { min-block-size:28rem; }
          :where(.toast-quality__controls) {
            display:flex; flex-wrap:wrap; gap:.75rem; align-items:center;
          }
          :where(.toast-quality__region) {
            --cui-toast-background: light-dark(#f0f9ff, #102a34);
            --cui-toast-foreground: light-dark(#17343e, #e6f7fb);
            --cui-toast-border-color: light-dark(#76b7c7, #5ea5b6);
          }
        """

    return CitryUiToastStates
