from typing import TypedDict
from citry import CitryRender, Component


class InvitePanel(Component):
    template = """
      <section class="invite-panel">
        <h2>{{ title }}</h2>

        <c-for each="member in members">
          <c-MemberChip
            #c-key="member['name']"
            c-name="member['name']"
            c-online="member['online']"
            c-status="<>
              <small c-title='title'>
                Available now
              </small>
            </>"
            :compact="compact"
          />
        </c-for>

        <p>{{ missing_summary }}</p>

        <form
          @submit.prevent="$sendEvent('invite', { email })"
          :aria-busy="$loading('invite')"
        >
          <input v-model="email" type="email" />
          <button :disabled="inviting || queuedInvite">
            Invite member
          </button>
          <small v-show="$error('invte')">
            Could not send invite.
          </small>
        </form>
      </section>
    """

    js = """
      $component({
        props: { compact: { type: Boolean } },
        data() {
          return { email: "" };
        },
      });
    """

    class Kwargs:
        title: str
        members: list[Member]

    class Events:
        def invite(self, data: InviteIn) -> None:
            send_invite(data["email"])

    def template_data(self, kwargs, slots):
        return {
            "title": kwargs.title,
            "members": kwargs.members,
        }

    def js_data(self, kwargs, slots):
        return {"inviting": False}


class MemberChip(Component):
    class Kwargs:
        name: str
        online: bool
        status: CitryRender

    template = """
      <span
        class="member-chip"
        :class="{ 'member-chip--compact': compact }"
      >
        {{ name }}
        <c-if cond="online">{{ status }}</c-if>
      </span>
    """

    js = """
      $component({
        props: { compact: { type: Boolean } },
      });
    """


class Member(TypedDict):
    name: str
    online: bool


class InviteIn(TypedDict):
    email: str
