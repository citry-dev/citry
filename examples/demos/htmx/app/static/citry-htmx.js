(function () {
  "use strict";

  const markerPattern = /<!--(citry:g1:[0-9a-f]{8}:[0-9]+:[ir]:[0-9]+:[se])-->/g;
  const placeholderSelector = "template[data-citry-htmx-cap]";

  function swapStyle(xhr, element) {
    const responseOverride = xhr.getResponseHeader("HX-Reswap");
    const swapOwner = element.closest("[hx-swap], [data-hx-swap]");
    const configured = responseOverride ||
      swapOwner?.getAttribute("hx-swap") ||
      swapOwner?.getAttribute("data-hx-swap") ||
      htmx.config.defaultSwapStyle;
    return configured.trim().split(/\s+/, 1)[0];
  }

  function preserveCitryComments(response) {
    return response.replace(markerPattern, (_match, marker) => {
      return `<template data-citry-htmx-cap="${marker}"></template>`;
    });
  }

  function restoreCitryComments(target) {
    target.querySelectorAll(placeholderSelector).forEach((placeholder) => {
      const marker = placeholder.getAttribute("data-citry-htmx-cap");
      if (marker) {
        placeholder.replaceWith(document.createComment(marker));
      }
    });
  }

  htmx.defineExtension("citry-fragments", {
    transformResponse(response, xhr, element) {
      if (response.includes("<!--citry:g1:") && swapStyle(xhr, element) !== "innerHTML") {
        throw new Error(
          'This HTMX response contains a Citry component. Set hx-swap="innerHTML" on a wrapper that remains on the page.'
        );
      }
      return preserveCitryComments(response);
    },
    onEvent(name, event) {
      if (name === "htmx:afterSwap") {
        restoreCitryComments(event.detail.target);
      }
    },
  });
})();
