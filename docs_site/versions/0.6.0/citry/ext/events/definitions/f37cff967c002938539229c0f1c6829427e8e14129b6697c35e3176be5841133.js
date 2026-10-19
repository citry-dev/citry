(function() {

const runtime = globalThis[Symbol.for('citry-ui:button-runtime')];
if (runtime?.generation !== 1 || runtime?.fingerprint !== '994a3b610f9ec0ad34f31907a9d7f3a3fc17036378e2628e6936b33fa2d46509') {
  throw new Error("[citry-ui] CButton runtime dependency did not load.");
}
__citryRuntime.registerTypeOptions.bind(null, "CButton_353146", "f166460efcf4eb1af63abc327e07f19611cc36a541fe5ef1663845502c43f186")(runtime.definition);

})();