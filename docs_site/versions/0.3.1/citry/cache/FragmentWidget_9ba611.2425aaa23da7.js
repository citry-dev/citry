
      Citry.manager.registerComponent("FragmentWidget_9ba611", ({ els }) => {
        // Proof the fragment's own JS ran after it was inserted.
        els[0].dataset.ready = "1";
        els[0].querySelector(".frag-widget__title").textContent += " (JS ran)";
      });
    