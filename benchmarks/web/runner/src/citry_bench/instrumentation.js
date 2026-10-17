(() => {
  performance.setResourceTimingBufferSize(10000);
  const marks = [];
  const faults = [];
  const pendingMarks = [];
  const pendingValidation = new WeakMap();
  let armed = null;
  let started = null;
  let pendingReady = null;
  const identitySnapshot = () => {
    const board = document.querySelector('#board');
    return board ? {
      revision: Number(board.dataset.revision),
      session: board.dataset.session,
      operation: board.dataset.operation,
    } : null;
  };
  const required = (selector, root = document) => {
    const element = root.querySelector(selector);
    if (!element) throw new Error(`Missing semantic marker: ${selector}`);
    return element;
  };
  const text = (selector, root = document) => required(selector, root).textContent.trim();
  const bool = value => value === 'true';
  const controlValue = element => 'value' in element ? element.value : element.textContent.trim();
  const deepEqual = (left, right) => {
    if (Object.is(left, right)) return true;
    if (Array.isArray(left) || Array.isArray(right)) {
      return Array.isArray(left) && Array.isArray(right) && left.length === right.length &&
        left.every((value, index) => deepEqual(value, right[index]));
    }
    if (!left || !right || typeof left !== 'object' || typeof right !== 'object') return false;
    const leftKeys = Object.keys(left).sort();
    const rightKeys = Object.keys(right).sort();
    return leftKeys.length === rightKeys.length && leftKeys.every((key, index) =>
      key === rightKeys[index] && deepEqual(left[key], right[key]));
  };
  const semanticSnapshot = () => {
    const board = required('#board');
    required('#project-navbar', board);
    required('#project-sidebar', board);
    const tabs = Array.from(required('#project-tabs', board).querySelectorAll('[data-tab-target]'));
    const tabIds = ['project-info', 'notes-1', 'notes-2', 'notes-3', 'outputs'];
    if (tabs.length !== tabIds.length || tabs.some((tab, index) => tab.dataset.tabTarget !== tabIds[index])) {
      throw new Error('Project tabs do not match the canonical order');
    }
    tabIds.forEach(id => {
      const panel = required(`#${id}`, board);
      if (panel.dataset.tabPanel !== id) throw new Error(`Panel ${id} has the wrong data-tab-panel value`);
    });
    const outputPanel = required('#outputs', board);
    if (outputPanel.hidden || getComputedStyle(outputPanel).display === 'none') {
      throw new Error('The outputs panel is not active at readiness');
    }
    const phaseGroups = Array.from(outputPanel.querySelectorAll('[data-phase-id]'), phase => {
      if (phase.dataset.phaseExpanded !== 'true') throw new Error('Canonical phase group is not open');
      const outputs = Array.from(phase.querySelectorAll('[data-row-id]'), row => {
        if (row.dataset.outputExpanded !== 'true') throw new Error('Canonical output is not open');
        const sourceId = row.getAttribute('data-source-id');
        const status = text('.row-status', row);
        if (required('[data-output-badge]', row).dataset.outputBadge !== status) {
          throw new Error('Output badge differs from displayed status');
        }
        if (!row.querySelector(`[data-bench-action="select-${row.dataset.rowId}"]`)) {
          throw new Error('Output select action is missing');
        }
        const attachments = Array.from(row.querySelectorAll('[data-attachment-id]'), attachment => {
          const link = attachment.matches('a') ? attachment : attachment.querySelector('a');
          const name = text('.attachment-name', attachment);
          if (attachment.dataset.attachmentName !== name) throw new Error('Attachment name marker differs from text');
          return {
            id: Number(attachment.dataset.attachmentId),
            name,
            url: link?.getAttribute('href') || '',
            tags: Array.from(attachment.querySelectorAll('[data-attachment-tag]'), tag => tag.dataset.attachmentTag),
          };
        });
        const dependencies = Array.from(row.querySelectorAll('[data-dependency-id]'), dependency => {
          const title = text('.dependency-title', dependency);
          if (dependency.dataset.dependencyTitle !== title) throw new Error('Dependency title marker differs from text');
          return {
            id: Number(dependency.dataset.dependencyId),
            title,
            completed: bool(dependency.dataset.dependencyCompleted),
          };
        });
        return {
          id: Number(row.dataset.rowId),
          source_id: sourceId === null ? null : Number(sourceId),
          title: text('.row-title', row),
          status,
          completed: required('[data-output-completed]', row).checked,
          description: controlValue(required('[data-output-description]', row)),
          phase_id: Number(phase.dataset.phaseId),
          attachments,
          dependencies,
          selected: bool(row.dataset.selected),
        };
      });
      return {id: Number(phase.dataset.phaseId), title: text('.phase-title', phase), outputs};
    });
    const noteTabs = ['notes-1', 'notes-2', 'notes-3'].map(id => {
      const panel = required(`#${id}`, board);
      return {
        id,
        title: tabs.find(tab => tab.dataset.tabTarget === id).textContent.trim(),
        notes: Array.from(panel.querySelectorAll('[data-note-id]'), note => ({
          id: Number(note.dataset.noteId),
          text: text('.note-text', note),
          comments: Array.from(note.querySelectorAll('[data-comment-id]'), comment => ({
            id: Number(comment.dataset.commentId),
            text: text('.comment-text', comment),
            author: text('.comment-author', comment),
          })),
        })),
      };
    });
    const projectInfo = required('#project-info', board);
    const rows = phaseGroups.flatMap(phase => phase.outputs);
    return {
      rows,
      phase_groups: phaseGroups,
      project: {
        id: Number(board.dataset.projectId),
        name: text('#board-title', board),
        status: text('#project-status', board),
        start_date: text('#project-start-date', board),
        end_date: text('#project-end-date', board),
        organization: text('#project-organization', board),
      },
      note_tabs: noteTabs,
      roles: Array.from(projectInfo.querySelectorAll('[data-role-id]'), role => ({
        id: Number(role.dataset.roleId), name: text('.role-name', role), user_name: text('.user-name', role),
      })),
      bookmarks: Array.from(board.querySelectorAll('[data-bookmark-id]'), bookmark => {
        const name = text('.bookmark-name', bookmark);
        if (bookmark.dataset.bookmarkName !== name) throw new Error('Bookmark name marker differs from text');
        return {id: Number(bookmark.dataset.bookmarkId), text: name, url: bookmark.getAttribute('href') || ''};
      }),
      contacts: Array.from(required('[data-project-contacts]', board).querySelectorAll('[data-contact-id]')),
      status_updates: Array.from(
        required('[data-project-status-updates]', board).querySelectorAll('[data-status-update-id]')
      ),
      project_tags: Array.from(required('[data-project-tags]', board).querySelectorAll('[data-project-tag-id]')),
      title: text('#board-title', board),
      title_input: required('#title-input', board).value,
      query: required('#query', board).value,
      error: text('#form-error', board),
      notice: text('#form-notice', board),
      visible_count: Number(board.dataset.visibleCount),
      total_count: Number(board.dataset.totalCount),
    };
  };
  const sockets = [];
  const socketState = new WeakMap();
  const NativeWebSocket = window.WebSocket;
  // Count browser-visible messages before framework handlers. Payload bytes are
  // collected through CDP afterward; this observer never parses application data.
  window.WebSocket = class extends NativeWebSocket {
    constructor(...args) {
      super(...args);
      const state = {index: sockets.length, url: this.url, sent: [], received: [], closed: null};
      sockets.push(state);
      socketState.set(this, state);
      this.addEventListener('message', () => state.received.push(performance.now()));
      this.addEventListener('close', event => {
        state.closed = {at: performance.now(), code: event.code};
      });
    }
    send(data) {
      const at = performance.now();
      super.send(data);
      socketState.get(this).sent.push(at);
    }
  };
  const transportSnapshot = () => sockets.map(socket => ({
    index: socket.index, url: socket.url,
    sent: socket.sent.length, received: socket.received.length,
    closed: socket.closed,
  }));
  // Paint timing. The browser stamps every paint entry with its own time since
  // performance.timeOrigin, which is navigation start of this document and the
  // same zero as the initial readiness interval (`start: 0` below). The runner
  // only reads the entries later, so driver delay never enters these values.
  const paint = {
    supported: {}, errors: [], fcp: null, lcp: null, lcp_candidates: 0,
    first_input: null, finalized_ms: null,
  };
  const paintObservers = [];
  const describe = element => element ? {
    tag: element.tagName.toLowerCase(), id: element.id || null,
    connected: element.isConnected,
  } : null;
  const observePaint = (type, handle) => {
    const supported = typeof PerformanceObserver === 'function' &&
      (PerformanceObserver.supportedEntryTypes || []).includes(type);
    paint.supported[type] = supported;
    if (!supported) return;
    // `buffered` also delivers entries recorded before the observer existed,
    // so the result does not depend on when this script runs.
    try {
      const observer = new PerformanceObserver(list => list.getEntries().forEach(handle));
      observer.observe({type, buffered: true});
      paintObservers.push({observer, handle});
    } catch (error) {
      paint.errors.push(`${type}: ${error}`);
    }
  };
  observePaint('paint', entry => {
    if (entry.name === 'first-contentful-paint' && paint.fcp === null) paint.fcp = entry.startTime;
  });
  observePaint('largest-contentful-paint', entry => {
    // Chromium emits a new entry only when a larger element paints, so the
    // last entry received is the current largest contentful paint.
    paint.lcp_candidates += 1;
    paint.lcp = {start_ms: entry.startTime, render_ms: entry.renderTime, load_ms: entry.loadTime,
      size: entry.size, element: describe(entry.element)};
  });
  // Chromium stops reporting LCP candidates after the first click, tap or key
  // press (or a user scroll, which the runner never performs). The runner
  // finalizes before its first click; this records an earlier input so a
  // truncated LCP is reported instead of trusted silently. A performance
  // observer is used rather than DOM listeners so the page's event-listener
  // count, which the memory report shows, stays unchanged.
  observePaint('first-input', entry => {
    if (paint.first_input === null) paint.first_input = {type: entry.name, at: entry.startTime};
  });
  const paintSnapshot = () => ({
    time_origin: 'navigation-start',
    supported: {...paint.supported}, errors: [...paint.errors],
    fcp_ms: paint.fcp, lcp: paint.lcp, lcp_candidates: paint.lcp_candidates,
    first_input: paint.first_input, finalized_ms: paint.finalized_ms,
    request_start_ms: performance.getEntriesByType('navigation')[0]?.requestStart ?? null,
  });
  window.__citryBench = {
    marks, faults, pendingMarks,
    connections: () => sockets,
    paintTimings() {
      if (paint.finalized_ms !== null) return Promise.resolve(paintSnapshot());
      // A paint entry reaches observers only after the frame is presented.
      // Waiting two frames and one task gives entries for frames already drawn
      // time to arrive; takeRecords then drains anything still queued. Disconnecting
      // freezes the values, so later actions cannot change the initial load.
      return new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(() => {
        for (const {observer, handle} of paintObservers) {
          observer.takeRecords().forEach(handle);
          observer.disconnect();
        }
        paint.finalized_ms = performance.now();
        resolve(paintSnapshot());
      }, 0))));
    },
    arm(value) {
      if (armed || pendingReady) throw new Error('Previous operation has not completed');
      armed = {...value, previousRevision: identitySnapshot()?.revision};
      started = null;
      // Adapters send the operation id in the submitting form's normal request
      // or event payload, so only that form needs it. Setting `.value` on a
      // hidden input also rewrites its `value` attribute, and a framework that
      // patches the page leaves that attribute in place, so writing every form
      // would put the id into each repeated row and inflate the final HTML.
      const control = document.querySelector(`[data-bench-action="${CSS.escape(String(value.action))}"]`);
      const form = control?.form || control?.closest('form');
      const own = form ? Array.from(form.elements).filter(element => element.name === 'operation') : [];
      // With no operation field in the control's form, write every operation
      // input, because an adapter such as Unicorn reads the id from a field
      // outside the submitting form.
      const targets = own.length ? own : document.querySelectorAll('input[name="operation"]');
      targets.forEach(input => {
        input.value = value.operation;
      });
    },
    expect(value) {
      window.__citryBenchExpected = value;
    },
    semanticSnapshot,
    ready(value) {
      // Reserve the original readiness boundary before waiting for a common
      // browser rendering opportunity. This is not a physical-paint signal.
      const end = performance.now();
      const state = identitySnapshot();
      const isInitial = value.phase === 'initial';
      if (pendingReady) {
        faults.push({message: 'Readiness arrived while a prior layout mark was pending', value, state, end,
          pending: pendingReady});
        return;
      }
      const armedAtReady = armed ? {...armed} : null;
      const startedAtReady = started ? {...started} : null;
      // The expected state is replaced, not mutated, by the runner; retaining
      // this reference avoids cloning O(rows) benchmark data into the interval.
      const expectedAtReady = window.__citryBenchExpected;
      const operation = isInitial ? 'initial' : armedAtReady?.operation;
      const navigation = performance.getEntriesByType('navigation')[0];
      const reservation = {
        ...value,
        state,
        end,
        start: isInitial ? 0 : startedAtReady?.start,
        requestStart: isInitial ? navigation?.requestStart : null,
        event: isInitial ? null : startedAtReady,
        transport: transportSnapshot(),
      };
      pendingValidation.set(reservation, {
        armed: armedAtReady,
        started: startedAtReady,
        expected: expectedAtReady,
      });
      pendingReady = reservation;
      pendingMarks.push(reservation);
      const releaseReservation = () => {
        const index = pendingMarks.indexOf(reservation);
        if (index >= 0) pendingMarks.splice(index, 1);
        if (pendingReady === reservation) pendingReady = null;
      };
      const fail = (message, details = {}) => {
        faults.push({message, ...reservation, ...details});
        releaseReservation();
      };
      const rect = element => {
        const box = element.getBoundingClientRect();
        const result = {
          x: box.x, y: box.y, top: box.top, right: box.right,
          bottom: box.bottom, left: box.left, width: box.width, height: box.height,
        };
        if (Object.values(result).some(number => !Number.isFinite(number)) || box.width <= 0 || box.height <= 0) {
          throw new Error('Layout geometry is missing or has nonpositive dimensions');
        }
        return result;
      };
      try {
        requestAnimationFrame(() => {
          let geometry;
          try {
            const board = document.querySelector('#board');
            if (!board) throw new Error('Missing layout marker: #board');
            const rows = board.querySelectorAll('[data-row-id]');
            const lastRow = rows.item(rows.length - 1);
            if (!lastRow) throw new Error('Missing layout marker: last [data-row-id]');
            // These fixed reads flush and record the same board/last-row geometry
            // in every framework arm before the second-frame endpoint.
            geometry = {
              row_count: rows.length,
              last_row_id: lastRow.dataset.rowId,
              board: rect(board),
              last_row: rect(lastRow),
            };
          } catch (error) {
            fail('Layout geometry capture failed', {layout_error: String(error)});
            return;
          }
          requestAnimationFrame(() => {
            // Preserve this timestamp before semantic assertions or report work.
            const layoutEnd = performance.now();
            reservation.layout_end = layoutEnd;
            reservation.layout_geometry = geometry;
            const semanticStart = performance.now();
            reservation.semantic_start = semanticStart;
            const validation = pendingValidation.get(reservation);
            let semantic = null;
            let semanticError = null;
            try {
              semantic = window.__citryBench.semanticSnapshot();
              if (!validation.expected || !deepEqual(semantic, validation.expected)) {
                semanticError = 'Semantic snapshot differs from expected state';
              }
            } catch (error) {
              semanticError = String(error);
            }
            const semanticObserverMs = performance.now() - semanticStart;
            const error = !state || !Number.isSafeInteger(state.revision) || state.revision < 0 ||
              !["initial", "update"].includes(reservation.phase) || reservation.pending !== 0 ||
              state.revision !== Number(reservation.revision) ||
              state.session !== reservation.session ||
              state.operation !== reservation.operation ||
              reservation.operation !== operation ||
              (!isInitial && (!validation.started || !validation.armed ||
                state.revision <= validation.armed.previousRevision)) ||
              (isInitial && marks.some(mark => mark.phase === 'initial')) || semanticError;
            if (error) {
              fail('Invalid or premature readiness', {
                semantic, semanticError, semanticObserverMs, semantic_start: semanticStart,
                layout_end: layoutEnd, layout_extra_ms: layoutEnd - end,
                layout_geometry: geometry, armed: validation.armed, started: validation.started,
              });
              return;
            }
            marks.push({
              ...reservation,
              semantic,
              semantic_observer_ms: semanticObserverMs,
              semantic_start: semanticStart,
              layout_end: layoutEnd,
              layout_extra_ms: layoutEnd - end,
              layout_geometry: geometry,
            });
            releaseReservation();
            armed = null;
            started = null;
          });
        });
      } catch (error) {
        fail('Unable to schedule layout opportunity', {layout_error: String(error)});
      }
    },
  };
  for (const type of ['click', 'input', 'change', 'submit']) {
    window.addEventListener(type, event => {
      if (!armed || started || type !== armed.event) return;
      const target = event.target.closest('[data-bench-action]');
      if (!target || target.dataset.benchAction !== armed.action) return;
      started = {
        start: performance.now(), timeStamp: event.timeStamp,
        type, trusted: event.isTrusted, action: target.dataset.benchAction,
      };
      if (!event.isTrusted) faults.push({message: 'Untrusted measured event', started});
    }, {capture: true});
  }
})();
