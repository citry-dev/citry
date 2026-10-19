(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContactForm_dbfa6e", "1b48ad2e4e81a8aef9d90aa1e98e07618ced4a9cc8e49ba06031156067f0fbf2")({
  methods: {
    async submit() {
      // Clear the message first, so a screen reader announces
      // it again when the same name is submitted twice.
      this.thanks = "";
      await this.$nextTick();
      // A real form would post to the server and show its
      // reply. This one builds the reply from the entered name.
      const name = this.name.trim() || "stranger";
      this.thanks = `Thank you for your submission, ${name}!`;
    },
  },
});

})();