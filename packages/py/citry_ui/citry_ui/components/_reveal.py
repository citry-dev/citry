"""
A shared browser helper that shows an element by scrolling only its own component.

`element.scrollIntoView()` scrolls every scrolling ancestor, including the
page and any page that holds this one in a frame. A component that brings its
current option or tab into view on a re-render, or when new items arrive,
would then pull a reader who scrolled away back to it. `reveal(element,
container)` scrolls only the scrollable elements from the element up to and
including `container`, by the least distance that shows the element. It does
nothing when `element` is not inside `container`, and it skips boxes whose
overflow is not `auto` or `scroll`.
"""

from __future__ import annotations

from citry.ext.dependencies import Script

# Written short by hand, as `_scroll_geometry.py` is, because every page with
# one of these components downloads it. Readable form:
#
#   reveal(element, container): return unless element is inside container
#   and is not container itself. For each box from element's parent up to
#   container, when the box scrolls (overflow auto or scroll) along an axis,
#   add nearest(item start, item end, visible start, visible end) to its
#   scroll offset. The visible area is inside the border and beside any
#   scrollbar (`clientTop`/`clientLeft` and `clientHeight`/`clientWidth`),
#   and both rectangles are measured again for each box, because scrolling
#   an inner box moves the element within the outer ones.
#   nearest(s, e, vs, ve): s < vs ? s - vs : e > ve ? min(e - ve, s - vs) : 0
REVEAL_RUNTIME_DEPENDENCY = Script(
    content=r"""
      (()=>{const k=Symbol.for("citry-ui:reveal"),x=globalThis[k];if(x!==void 0){if(x.generation!==1)
      throw new Error("[citry-ui] incompatible reveal runtime; reload the page.");return}
      const n=(s,e,a,b)=>s<a?s-a:e>b?Math.min(e-b,s-a):0,r=(el,c)=>{
      if(!(el instanceof Element)||el===c||!c?.contains(el))return;
      for(let b=el.parentElement;b;b=b===c?null:b.parentElement){const st=getComputedStyle(b),
      i=el.getBoundingClientRect(),o=b.getBoundingClientRect(),t=o.top+b.clientTop,l=o.left+b.clientLeft;
      if(b.scrollHeight>b.clientHeight&&/auto|scroll/.test(st.overflowY))b.scrollTop+=n(i.top,i.bottom,t,t+b.clientHeight);
      if(b.scrollWidth>b.clientWidth&&/auto|scroll/.test(st.overflowX))b.scrollLeft+=n(i.left,i.right,l,l+b.clientWidth)}};
      globalThis[k]={generation:1,reveal:r}})();
    """
)

__all__: list[str] = []
