import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledTagsInputAxes(Component):
    template = """
      <section class="tags-input-controlled">
        <article x-data="{last:'Uncontrolled'}">
          <h3>Uncontrolled tags and draft</h3>
          <c-CTagsInput
            c-value="['alpine']"
            c-input_attrs="{'aria-label':'Uncontrolled labels'}"
            $c-props="{
              onValueChange:(next)=>last=JSON.stringify(next),
            }"
          />
          <output x-text="last">Uncontrolled</output>
        </article>

        <article x-data="{draft:'coastal',last:'Draft owned'}">
          <h3>Controlled draft</h3>
          <c-CTagsInput
            c-value="['alpine']"
            c-input_attrs="{'aria-label':'Draft-owned labels'}"
            $c-props="{
              inputValue:draft,
              onInputValueChange:(next)=>{
                draft=next;
                last=`Draft: ${next}`;
              },
            }"
          />
          <output x-text="last">Draft owned</output>
        </article>

        <article
          x-data="{
            tags:['alpine'],
            accept:false,
            last:'Value request not sent',
          }"
        >
          <h3>Controlled tags, uncontrolled draft</h3>
          <c-CTagsInput
            c-input_attrs="{'aria-label':'Value-owned labels'}"
            $c-props="{
              value:tags,
              onValueChange:(next,detail)=>{
                last=`Requested ${JSON.stringify(next)}`;
                if (accept) tags=next;
              },
            }"
          />
          <label>
            <input type="checkbox" x-model="accept" />
            Accept the next value request
          </label>
          <output x-text="last">Value request not sent</output>
        </article>

        <article
          x-data="{
            tags:['alpine'],
            draft:'harbor',
            last:'Both axes owned',
          }"
        >
          <h3>Controlled tags and draft</h3>
          <c-CTagsInput
            c-input_attrs="{'aria-label':'Fully controlled labels'}"
            $c-props="{
              value:tags,
              inputValue:draft,
              onValueChange:(next,detail)=>{
                tags=next;
                draft=detail.nextInputValue || 'owner note';
                last=`Accepted ${JSON.stringify(next)}`;
              },
              onInputValueChange:(next)=>draft=next,
            }"
          />
          <button type="button" @click="tags=['owner','ordered']">
            Replace tags from the owner
          </button>
          <output x-text="last">Both axes owned</output>
        </article>
      </section>
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
