/*
 * Research-only Alpine slot-scope adapter.
 *
 * This is not product runtime code. It exists to falsify the old
 * interceptInit-only proposal and to exercise a two-phase alternative:
 *
 * 1. The directive's inline half installs a teleport-like source backlink
 *    before Alpine's inline x-ref handler runs. Native teleport targets keep
 *    their clone-to-template backlinks and extend the chain at the terminal
 *    native source template.
 * 2. The deferred half runs after earlier ancestor x-data handlers, but is
 *    ordered before this fill root's x-id and x-data handlers. It installs a
 *    live source facade rather than copying the physical child's data stack.
 * 3. Direct x-if/x-for templates explicitly propagate the research directive
 *    to their template-content root. Descendants are never inferred from an
 *    inherited source frame.
 *
 * A source is represented in the fixture DOM by:
 *
 *     <!--citry-fill-source:TOKEN-->
 *
 * The comment is durable identity. Its parent Element is the Alpine magic
 * carrier because Alpine's closestRoot traversal expects Element.matches().
 */
(() => {
  const SOURCE_FRAME = Symbol("citry-slot-source-frame");
  const descriptorsByComment = new WeakMap();
  const emptyReference = document.createDocumentFragment();
  let AlpineApi = null;

  function commentToken(node) {
    if (node.nodeType !== Node.COMMENT_NODE) return null;
    const match = /^citry-fill-source:(.+)$/.exec(node.data.trim());
    return match ? match[1] : null;
  }

  function sourceComments(token) {
    const comments = [];
    const walker = document.createTreeWalker(document, NodeFilter.SHOW_COMMENT);
    let node = walker.nextNode();
    while (node) {
      if (commentToken(node) === token) comments.push(node);
      node = walker.nextNode();
    }
    return comments;
  }

  function nearestPrecedingComment(comments, target) {
    let nearest = null;
    for (const comment of comments) {
      const position = comment.compareDocumentPosition(target);
      if (!(position & Node.DOCUMENT_POSITION_FOLLOWING)) continue;
      if (!nearest) {
        nearest = comment;
        continue;
      }
      const nearestToComment = nearest.compareDocumentPosition(comment);
      if (nearestToComment & Node.DOCUMENT_POSITION_FOLLOWING) nearest = comment;
    }
    return nearest;
  }

  function electComment(token, target = null) {
    const comments = sourceComments(token);
    if (comments.length === 0) {
      throw new Error(`No live slot source comment for ${token}`);
    }
    if (comments.length === 1) {
      return { comment: comments[0], strategy: "unique" };
    }
    const nearest = target && nearestPrecedingComment(comments, target);
    if (nearest) return { comment: nearest, strategy: "nearest-preceding" };
    throw new Error(`Slot source ${token} is ambiguous across ${comments.length} live comments`);
  }

  function liveScope(descriptor) {
    descriptor.signal.version;
    if (!descriptor.carrier?.isConnected) return AlpineApi.mergeProxies([]);
    return AlpineApi.mergeProxies(AlpineApi.closestDataStack(descriptor.carrier));
  }

  function makeSourceFrame(descriptor) {
    return new Proxy(
      {},
      {
        ownKeys() {
          return Array.from(new Set([SOURCE_FRAME, ...Reflect.ownKeys(liveScope(descriptor))]));
        },
        has(_target, key) {
          if (key === SOURCE_FRAME) return true;
          return Reflect.has(liveScope(descriptor), key);
        },
        get(_target, key) {
          if (key === SOURCE_FRAME) return descriptor;
          return Reflect.get(liveScope(descriptor), key);
        },
        set(_target, key, value) {
          if (key === SOURCE_FRAME) return false;
          return Reflect.set(liveScope(descriptor), key, value);
        },
        getOwnPropertyDescriptor(_target, key) {
          if (key === SOURCE_FRAME) {
            return { configurable: true, enumerable: false, value: descriptor };
          }
          if (!Reflect.has(liveScope(descriptor), key)) return undefined;
          return {
            configurable: true,
            enumerable: true,
            get: () => Reflect.get(liveScope(descriptor), key),
            set: (value) => Reflect.set(liveScope(descriptor), key, value),
          };
        },
      },
    );
  }

  function descriptorFor(token, target) {
    const elected = electComment(token, target);
    let descriptor = descriptorsByComment.get(elected.comment);
    if (descriptor) return descriptor;
    const carrier = elected.comment.parentElement;
    if (!carrier) throw new Error(`Slot source ${token} has no Element carrier`);
    descriptor = {
      token,
      comment: elected.comment,
      carrier,
      strategy: elected.strategy,
      signal: AlpineApi.reactive({ version: 0 }),
      roots: new Set(),
      frame: null,
    };
    descriptor.frame = makeSourceFrame(descriptor);
    descriptorsByComment.set(elected.comment, descriptor);
    return descriptor;
  }

  function descriptorInStack(el) {
    for (const layer of AlpineApi.closestDataStack(el)) {
      try {
        const descriptor = layer?.[SOURCE_FRAME];
        if (descriptor) return descriptor;
      } catch (_error) {
        // A user proxy is allowed to reject unknown symbols. It is not a
        // Citry source frame, so continue through the stack.
      }
    }
    return null;
  }

  function hasDescriptorInOwnStack(el, descriptor) {
    if (!Object.hasOwn(el, "_x_dataStack")) return false;
    return (el._x_dataStack || []).some((layer) => {
      try {
        return layer?.[SOURCE_FRAME] === descriptor;
      } catch (_error) {
        return false;
      }
    });
  }

  function clearLexicalMagicCaches(root) {
    AlpineApi.walk(root, (el) => {
      delete el._x_refs_proxy;
      delete el._x_id;
    });
  }

  function backlinkOwner(el) {
    let current = el;
    while (true) {
      const origin = current._x_teleportBack;
      if (origin?._x_teleport !== current) return current;
      current = origin;
    }
  }

  function unlinkRoot(el, descriptor) {
    descriptor.roots.delete(el);
    const owner = el._x_citrySlotBacklinkOwner;
    delete el._x_citrySlotBacklinkOwner;
    if (!owner || owner._x_citrySlotBacklink !== descriptor) return;
    const stillUsed = Array.from(descriptor.roots).some(
      (root) => root._x_citrySlotBacklinkOwner === owner,
    );
    if (stillUsed) return;
    delete owner._x_citrySlotBacklink;
    delete owner._x_teleportBack;
  }

  function linkBack(el, descriptor) {
    el._x_citrySlotSource = descriptor;
    const owner = backlinkOwner(el);
    if (owner._x_teleportBack && owner._x_citrySlotBacklink !== descriptor) {
      throw new Error("Cannot replace an existing Alpine teleport backlink");
    }
    owner._x_citrySlotBacklink = descriptor;
    owner._x_teleportBack = descriptor.carrier;
    el._x_citrySlotBacklinkOwner = owner;
    descriptor.roots.add(el);
    AlpineApi.onElRemoved(el, () => unlinkRoot(el, descriptor));
  }

  function refreshDescriptor(descriptor, target = null) {
    const elected = electComment(descriptor.token, target);
    const carrier = elected.comment.parentElement;
    if (!carrier) throw new Error(`Slot source ${descriptor.token} has no Element carrier`);
    if (elected.comment !== descriptor.comment) {
      const occupant = descriptorsByComment.get(elected.comment);
      if (occupant && occupant !== descriptor) {
        throw new Error(`Slot source ${descriptor.token} elected a comment owned by another descriptor`);
      }
      if (descriptorsByComment.get(descriptor.comment) === descriptor) {
        descriptorsByComment.delete(descriptor.comment);
      }
      descriptorsByComment.set(elected.comment, descriptor);
    }
    descriptor.comment = elected.comment;
    descriptor.carrier = carrier;
    descriptor.strategy = elected.strategy;
    for (const root of Array.from(descriptor.roots)) {
      if (!root.isConnected) {
        unlinkRoot(root, descriptor);
        continue;
      }
      const owner = root._x_citrySlotBacklinkOwner;
      if (owner?._x_citrySlotBacklink === descriptor) owner._x_teleportBack = carrier;
      clearLexicalMagicCaches(root);
    }
    descriptor.signal.version += 1;
    return descriptor;
  }

  function install(Alpine) {
    AlpineApi = Alpine;

    const handler = (el, { expression }, { cleanup }) => {
      const descriptor = el._x_citrySlotSource || descriptorFor(expression.trim(), el);
      const undo = hasDescriptorInOwnStack(el, descriptor)
        ? () => {}
        : Alpine.addScopeToNode(el, descriptor.frame, emptyReference);
      cleanup(() => {
        undo();
        unlinkRoot(el, descriptor);
      });
    };

    handler.inline = (el, { expression }) => {
      const descriptor = descriptorFor(expression.trim(), el);
      if (
        el.tagName === "TEMPLATE" &&
        (el.hasAttribute("x-if") || el.hasAttribute("x-for"))
      ) {
        const generatedRoot = el.content.firstElementChild;
        if (!generatedRoot) throw new Error("A structural fill template needs an element root");
        const existing = generatedRoot.getAttribute("x-cfill");
        if (existing && existing.trim() !== expression.trim()) {
          throw new Error("A generated root cannot belong to two slot sources");
        }
        generatedRoot.setAttribute("x-cfill", expression.trim());
      }
      linkBack(el, descriptor);
    };

    // This position is load-bearing. Earlier source ancestors have already
    // queued their x-id/x-data handlers. On the fill root, cfill runs before
    // inline x-ref registration and before deferred x-id/x-data evaluation.
    Alpine.directive("cfill", handler).before("ref");
  }

  function sourceOf(el) {
    return el._x_citrySlotSource || descriptorInStack(el);
  }

  function destructiveRestamp(el) {
    const descriptor = sourceOf(el);
    if (!descriptor) throw new Error("Element has no slot source descriptor");
    AlpineApi.addScopeToNode(el, descriptor.frame, emptyReference);
  }

  document.addEventListener("alpine:init", () => install(globalThis.Alpine));

  globalThis.SlotsScopeSpike = {
    SOURCE_FRAME,
    commentToken,
    descriptorFor,
    destructiveRestamp,
    electComment,
    refreshDescriptor,
    refreshFor(el) {
      const descriptor = sourceOf(el);
      if (!descriptor) throw new Error("Element has no slot source descriptor");
      return refreshDescriptor(descriptor, el);
    },
    sourceComments,
    sourceOf,
  };
})();
