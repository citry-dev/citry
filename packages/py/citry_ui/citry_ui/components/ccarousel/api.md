---
title: Carousel
description: Browse composed content with native Scroll Snap and explicit controls.
---

# Carousel

Use `CCarousel` and `CCarouselSlide` for a named sequence of content cards,
stories, or media. It uses native scrolling and Scroll Snap, so touch and
trackpad navigation work without an application-widget keyboard model.

## Carousel at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/at_a_glance.py" title="Carousel at a glance" />

## Compose content cards

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/cards.py" title="Carousel content cards" />

## Control the current Slide

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/controlled.py" title="Controlled Carousel" />

## Choose orientation

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/orientation.py" title="Carousel orientations" />

## Configure controls and indicators

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/controls.py" title="Carousel controls" />

## Loop and disable

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/states.py" title="Carousel states" />

## Variants and sizes

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/variants.py" title="Carousel variants and sizes" />

## Put forms in Slides

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/forms.py" title="Carousel form content" />

## Customize Carousel

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccarousel/snippets/customization.py" title="Customize Carousel" />

## Accessibility and interaction

Give the root a concise `label` and every Slide a content-specific `label`.
Previous/next and picker controls are native Buttons that keep focus in place.
The native scroll viewport is also a Tab stop, so keyboard and Safari users can
focus and scroll it directly without a scripted Arrow-key model.
All Slides remain in the accessibility tree; offscreen content is never
incorrectly presented as hidden. Disable indicators for large collections to
avoid adding too many Tab stops. Autoplay is intentionally not part of v1.

<!-- UI_LIBRARY_API_REFERENCE -->
