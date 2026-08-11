from typing import TypedDict
from citry import CitryRender, Component


class InvitePanel(Component):
    template = """
      <section class="invite-panel">
        <h2>{{ title }}</h2>

        <template x-for="member in visibleMembers">
          <c-MemberChip
            c-name="member.name"
            c-status="<>
              <small c-title='title'>
                Available now
              </small>
            </>"
            $c-props="{ online: member.online }"
          />
        </template>

        <p>{{ missing_summary }}</p>

        <form
          @submit.prevent="$sendEvent('invite', { email })"
          :aria-busy="$loading('invite')"
        >
          <input x-model="email" type="email" />
          <button :disabled="inviting || queuedInvite">
            Invite member
          </button>
          <small x-show="$error('invte')">
            Could not send invite.
          </small>
        </form>
      </section>
    """

    js = """
      $component({
        props: { compact: { type: Boolean } },
        init: ({ data, scope, props, effect }) => {
          scope.email = "";
          effect(() => {
            scope.visibleMembers = props.compact
              ? data.members.slice(0, 3)
              : data.members;
          });
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
        return {"title": kwargs.title}

    def js_data(self, kwargs, slots):
        return {
            "members": kwargs.members,
            "inviting": False,
        }


class MemberChip(Component):
    class Kwargs:
        name: str
        status: CitryRender

    template = """
      <span class="member-chip">
        {{ name }}
        {{ status }}
      </span>
    """

    js = """
      $component({
        props: { online: { type: Boolean } },
      });
    """


class Member(TypedDict):
    name: str
    online: bool


class InviteIn(TypedDict):
    email: str
