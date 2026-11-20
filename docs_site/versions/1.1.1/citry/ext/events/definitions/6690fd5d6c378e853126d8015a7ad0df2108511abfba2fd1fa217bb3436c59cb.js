try {
(function() {

const runtime = globalThis[Symbol.for('citry-ui:menu-root-runtime')];
if (runtime?.generation !== 1 || runtime?.fingerprint !== 'ad9976b6df9296cbf6e587bb081f8f4b43146ae2559528adff363897f01b5db8') {
  throw new Error("[citry-ui] CMenu runtime dependency did not load.");
}
__citryRuntime.registerTypeOptions.bind(null, "CMenu_4350e4", "60b5da4b850c3e44a310dad265b44a47bd6e6440506b888dd4231f027ca0a524")(runtime.definition);

})();
__citryRuntime.finishScript("584637fb0f269879a4215c7e6f7793f8dafcb641f8ae1b3f96fb0fc298a7eb92");
} catch (error) {
__citryRuntime.finishScript("584637fb0f269879a4215c7e6f7793f8dafcb641f8ae1b3f96fb0fc298a7eb92", error);
}