import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledTagsInputAxes(Component):
    template = """
      <section class="tags-input-controlled">
        <article >
          <h3>Uncontrolled tags and draft</h3>
          <c-CTagsInput
            c-value="['alpine']"
            c-input_attrs="{'aria-label':'Uncontrolled labels'}"
            :onValueChange="(next)=>uncontrolledLast=JSON.stringify(next)"
          />
          <output v-text="uncontrolledLast">Uncontrolled</output>
        </article>

        <article >
          <h3>Controlled draft</h3>
          <c-CTagsInput
            c-value="['alpine']"
            c-input_attrs="{'aria-label':'Draft-owned labels'}"
            :inputValue="draft" :onInputValueChange="(next)=>{
                draft=next;
                draftLast=`Draft: ${next}`;
              }"
          />
          <output v-text="draftLast">Draft owned</output>
        </article>

        <article
        >
          <h3>Controlled tags, uncontrolled draft</h3>
          <c-CTagsInput
            c-input_attrs="{'aria-label':'Value-owned labels'}"
            :value="valueTags" :onValueChange="(next,detail)=>{
                valueLast=`Requested ${JSON.stringify(next)}`;
                if (accept) valueTags=next;
              }"
          />
          <label>
            <input type="checkbox" v-model="accept" />
            Accept the next value request
          </label>
          <output v-text="valueLast">Value request not sent</output>
        </article>

        <article
        >
          <h3>Controlled tags and draft</h3>
          <c-CTagsInput
            c-input_attrs="{'aria-label':'Fully controlled labels'}"
            :value="fullyControlledTags" :inputValue="fullyControlledDraft" :onValueChange="(next,detail)=>{
                fullyControlledTags=next;
                fullyControlledDraft=detail.nextInputValue || 'owner note';
                fullyControlledLast=`Accepted ${JSON.stringify(next)}`;
              }" :onInputValueChange="(next)=>fullyControlledDraft=next"
          />
          <button type="button" @click="fullyControlledTags=['owner','ordered']">
            Replace tags from the owner
          </button>
          <output v-text="fullyControlledLast">Both axes owned</output>
        </article>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            uncontrolledLast:'Uncontrolled',
            draft:'coastal',draftLast:'Draft owned',
            accept:false,
            valueTags:['alpine'],
            valueLast:'Value request not sent',
            fullyControlledTags:['alpine'],
            fullyControlledDraft:'harbor',
            fullyControlledLast:'Both axes owned',
          };
        },
      });
    """

    css = """
      :where(.tags-input-controlled) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-controlled article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
      }

      :where(.tags-input-controlled h3) {
        margin: 0;
      }
    """


preview = ControlledTagsInputAxes()

preview  # noqa: B018
