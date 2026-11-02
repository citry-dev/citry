(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTagsInputAxes_b81a36", "723f12ad2125588fae43686cd5d2564dbdcb4aea9e0692f0c064ee44d33099c1")({
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
  methods: {
    updateDraft(next) {
      this.draft = next;
      this.draftLast = `Draft: ${next}`;
    },
    // Log every request, and change the tags only while
    // "Accept the next value request" is checked.
    applyValueRequest(next) {
      this.valueLast = `Requested ${JSON.stringify(next)}`;
      if (this.accept) this.valueTags = next;
    },
    // The owner accepts every request and fills an empty draft.
    acceptFullyControlledTags(next, detail) {
      this.fullyControlledTags = next;
      this.fullyControlledDraft =
        detail.nextInputValue || 'owner note';
      this.fullyControlledLast =
        `Accepted ${JSON.stringify(next)}`;
    },
  },
});

})();