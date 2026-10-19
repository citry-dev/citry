(function() {

const runtime = globalThis[Symbol.for('citry-ui:menu-root-runtime')];
if (runtime?.generation !== 1 || runtime?.fingerprint !== '0911f55d695ff8f002f8ece3399e44e7af23d761819beee30477dbdba49dd9af') {
  throw new Error("[citry-ui] CMenu runtime dependency did not load.");
}
__citryRuntime.registerTypeOptions.bind(null, "CMenu_4350e4", "2ea2ba14e1a2139cc5e5a1566882c8e596bf37d022ca16d322fd9a3bb6275ec5")(runtime.definition);

})();