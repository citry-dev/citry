"""Separate-file message owner for the local i18n editor fixture."""

from citry import ComponentLibrary, LibraryComponent


class DemoExternalMessages(LibraryComponent):
    """Own a message that another component uses through the shared app catalog."""

    template = """
      <template></template>
    """

    messages = """
      demo-account-other-file-note =
          This message is owned by a component in another Python file.
    """


i18n_demo_library = ComponentLibrary(
    "i18n-demo-messages",
    (DemoExternalMessages,),
    required_extensions=("i18n",),
)
