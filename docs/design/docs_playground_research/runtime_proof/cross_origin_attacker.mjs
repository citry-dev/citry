parent.postMessage(
  {
    type: "runner-ready",
    version: 1,
    session: location.hash.slice(1),
  },
  "*",
);
