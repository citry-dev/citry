$component({
  props: {
    sort: {}, selected: {}, disabled: {}, overscan: {},
    onSortChange: {}, onSelectionChange: {}, onRangeChange: {}, onCellActivate: {},
    onCellEditStart: {}, onCellEditCommit: {}, onCellEditCancel: {},
  },
  init: ({els, data, props, effect, i18n}) => {
    const root = els[0];
    const viewport = root?.querySelector(':scope > [data-citry-ui-part="viewport"]');
    const table = viewport?.querySelector(':scope > [data-citry-ui-part="table"]');
    const status = root?.querySelector(':scope > [data-citry-ui-part="status"]');
    if (!(root instanceof HTMLElement) || !(viewport instanceof HTMLElement)
        || !(table instanceof HTMLTableElement) || !(status instanceof HTMLElement)) {
      throw new Error('[citry-ui] CDataGrid settled anatomy is invalid.');
    }
    const headers = [...table.querySelectorAll('[data-citry-ui-part="header-cell"]')];
    let rows = [...table.querySelectorAll('[data-citry-ui-part="row"]')];
    let cells = [...table.querySelectorAll('[data-citry-ui-part="cell"]')];
    if (headers.length !== Number(table.getAttribute('aria-colcount'))
        || cells.length !== rows.length * headers.length) {
      throw new Error('[citry-ui] CDataGrid settled row and column anatomy is invalid.');
    }
    if ([...headers, ...cells].some(cell => cell.querySelector(
      'a[href],button,input,select,textarea,[contenteditable="true"],[tabindex]:not([tabindex="-1"])',
    ))) {
      throw new Error('[citry-ui] CDataGrid header and cell slots cannot contain focusable descendants.');
    }
    const byRow = new Map(rows.map(row => [row.dataset.rowKey, row]));
    let knownRows = rows.map(row => row.dataset.rowKey);
    const knownColumns = headers.map(header => header.dataset.columnKey);
    const editorKey = (rowKey, columnKey) => `${rowKey}\u0000${columnKey}`;
    const editors = new Map(data.editors.map(item => [editorKey(item.rowKey, item.columnKey), item]));
    const serverRowOrder = new Map(knownRows.map((key, index) => [key, index]));
    const completeCollection = data.start_index === 0 && data.total_count === rows.length;
    const invalid = new Set();
    let active = cells.find(cell => cell.tabIndex === 0) ?? headers[0] ?? null;
    let currentSort = data.sort.map(item => ({...item}));
    let currentSelected = [...data.selected];
    let controlledSelection = false;
    let selectionAnchor = currentSelected.at(-1) ?? null;
    let disabled = data.disabled;
    let overscan = data.overscan;
    let onSortChange = null;
    let onSelectionChange = null;
    let onRangeChange = null;
    let onCellActivate = null;
    let onCellEditStart = null;
    let onCellEditCommit = null;
    let onCellEditCancel = null;
    let activeEditor = null;
    let rangeFrame = 0;
    let requestId = 0;
    let pendingSort = null;
    let locallySorted = false;
    let pendingSelection = null;
    let sortInitialized = false;
    let pointerSelection = null;
    let suppressClick = false;
    let suppressClickTimer = 0;
    let alive = true;
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CDataGrid ${name} received invalid client value.`, value, root);
    };
    const sameArray = (left, right) => left.length === right.length
      && left.every((item, index) => item === right[index]);
    const sameSort = (left, right) => left.length === right.length
      && left.every((item, index) => item.key === right[index].key && item.direction === right[index].direction);
    const validSort = value => Array.isArray(value)
      && new Set(value.map(item => item?.key)).size === value.length
      && value.every(item => item && typeof item === 'object' && knownColumns.includes(item.key)
        && ['asc', 'desc'].includes(item.direction)
        && headers.find(header => header.dataset.columnKey === item.key)?.hasAttribute('data-sortable'));
    const validSelected = value => Array.isArray(value)
      && value.every(item => typeof item === 'string' && knownRows.includes(item))
      && new Set(value).size === value.length
      && (data.selection !== 'none' || value.length === 0)
      && (data.selection !== 'single' || value.length <= 1);
    const format = (pattern, values) => Object.entries(values).reduce(
      (result, [name, value]) => result.replaceAll(`{${name}}`, String(value)), pattern,
    );
    const translateSort = (direction, column) => {
      try {
        if (i18n && direction === 'asc' && data.catalog.sort_ascending) {
          return i18n.tr('citry-ui-data-grid-sort-ascending', {column});
        }
        if (i18n && direction === 'desc' && data.catalog.sort_descending) {
          return i18n.tr('citry-ui-data-grid-sort-descending', {column});
        }
        if (i18n && direction === null && data.catalog.sort_cleared) {
          return i18n.tr('citry-ui-data-grid-sort-cleared', {column});
        }
      } catch (error) { console.error('[citry-ui] CDataGrid translation failed.', error, root); }
      return format(data.labels[direction === 'asc' ? 'sort_ascending'
        : direction === 'desc' ? 'sort_descending' : 'sort_cleared'], {column});
    };
    const translateEdit = (kind, column) => {
      try {
        if (i18n && data.catalog[kind]) {
          return i18n.tr(`citry-ui-data-grid-${kind.replaceAll('_', '-')}`, {column});
        }
      } catch (error) { console.error('[citry-ui] CDataGrid translation failed.', error, root); }
      return format(data.labels[kind], {column});
    };
    const announceSelection = count => {
      try {
        if (i18n && count === 1 && data.catalog.selected_one) {
          status.textContent = i18n.tr('citry-ui-data-grid-selected-one');
          return;
        }
        if (i18n && count !== 1 && data.catalog.selected) {
          status.textContent = i18n.tr('citry-ui-data-grid-selected', {count: String(count)});
          return;
        }
      } catch (error) { console.error('[citry-ui] CDataGrid translation failed.', error, root); }
      status.textContent = count === 1 ? data.labels.selected_one : format(data.labels.selected, {count});
    };
    const announceSort = (key, direction) => {
      const column = data.column_labels[key];
      if (typeof column === 'string') status.textContent = translateSort(direction, column);
    };
    const rowSortValue = (row, key) => {
      const cell = [...row.cells].find(candidate => candidate.dataset.columnKey === key);
      return cell?.textContent?.trim().replace(/\s+/g, ' ') ?? '';
    };
    const reorderCompleteRows = sort => {
      if (!completeCollection) return;
      locallySorted = true;
      const locale = i18n?.context.locale || root.ownerDocument.documentElement.lang || undefined;
      const collator = new Intl.Collator(locale, {numeric: true, sensitivity: 'base'});
      const ordered = [...rows].sort((left, right) => {
        for (const item of sort) {
          const result = collator.compare(rowSortValue(left, item.key), rowSortValue(right, item.key));
          if (result) return item.direction === 'desc' ? -result : result;
        }
        return (serverRowOrder.get(left.dataset.rowKey) ?? 0) - (serverRowOrder.get(right.dataset.rowKey) ?? 0);
      });
      const body = table.tBodies[0];
      for (const row of ordered) body.append(row);
      rows = ordered;
      knownRows = rows.map(row => row.dataset.rowKey);
      rows.forEach((row, rowIndex) => {
        row.dataset.rowIndex = String(rowIndex);
        row.setAttribute('aria-rowindex', String(rowIndex + 2));
        for (const cell of row.cells) cell.dataset.rowIndex = String(rowIndex);
      });
      cells = rows.flatMap(row => [...row.querySelectorAll('[data-citry-ui-part="cell"]')]);
    };
    const applySort = next => {
      currentSort = next.map(item => ({...item}));
      headers.forEach(header => {
        const index = currentSort.findIndex(item => item.key === header.dataset.columnKey);
        const direction = index < 0 ? null : currentSort[index].direction;
        header.toggleAttribute('data-sort', direction !== null);
        if (direction) header.dataset.sort = direction;
        else header.removeAttribute('data-sort');
        if (index >= 0) header.dataset.sortPriority = String(index + 1);
        else header.removeAttribute('data-sort-priority');
        if (direction) header.setAttribute('aria-sort', direction === 'asc' ? 'ascending' : 'descending');
        else header.removeAttribute('aria-sort');
        const indicator = header.querySelector('[data-citry-ui-part="sort-indicator"]');
        if (indicator) indicator.textContent = direction === 'asc' ? '↑' : direction === 'desc' ? '↓' : '';
      });
    };
    const applySelected = next => {
      currentSelected = [...next];
      const selected = new Set(currentSelected);
      rows.forEach(row => {
        const value = selected.has(row.dataset.rowKey);
        row.toggleAttribute('data-selected', value);
        if (data.selection !== 'none') row.setAttribute('aria-selected', String(value));
      });
    };
    const focusCell = (cell, preventScroll = false) => {
      if (!cell) return;
      [...headers, ...cells].forEach(item => { item.tabIndex = item === cell ? 0 : -1; });
      active = cell;
      cell.focus({preventScroll});
      if (!preventScroll) cell.scrollIntoView({block: 'nearest', inline: 'nearest'});
    };
    const locate = (rowIndex, columnIndex) => {
      if (rowIndex < 0) return headers[columnIndex] ?? null;
      return cells.find(cell => Number(cell.dataset.rowIndex) === rowIndex
        && Number(cell.dataset.columnIndex) === columnIndex) ?? null;
    };
    const visibleRange = () => {
      const headerSize = table.tHead?.getBoundingClientRect().height ?? 0;
      const offset = Math.max(0, viewport.scrollTop - headerSize);
      const start = Math.max(0, Math.min(data.total_count, Math.floor(offset / data.row_height)));
      const count = Math.max(1, Math.ceil(viewport.clientHeight / data.row_height));
      return {start, end: Math.min(data.total_count, start + count)};
    };
    const scheduleRange = (reason, sourceEvent = null) => {
      cancelAnimationFrame(rangeFrame);
      rangeFrame = requestAnimationFrame(() => {
        rangeFrame = 0;
        if (!alive || data.total_count === 0) return;
        const visible = visibleRange();
        const startIndex = Math.max(0, visible.start - overscan);
        const endIndex = Math.min(data.total_count, visible.end + overscan);
        const suppliedEnd = data.start_index + rows.length;
        const covered = startIndex >= data.start_index && endIndex <= suppliedEnd;
        root.toggleAttribute('data-pending', !covered);
        if (covered) table.removeAttribute('aria-busy');
        else table.setAttribute('aria-busy', 'true');
        if (!covered && onRangeChange) {
          const detail = {
            startIndex, endIndex, visibleStartIndex: visible.start, visibleEndIndex: visible.end,
            requestId: ++requestId, reason, sourceEvent,
          };
          try { onRangeChange(detail); }
          catch (error) { console.error('[citry-ui] CDataGrid onRangeChange callback failed.', error, root); }
        }
      });
    };
    const requestSort = (header, event, source) => {
      if (disabled || !header.hasAttribute('data-sortable')) return;
      const key = header.dataset.columnKey;
      const existing = currentSort.find(item => item.key === key);
      const direction = !existing ? 'asc' : existing.direction === 'asc' ? 'desc' : null;
      let next = event.shiftKey && data.multi_sort ? currentSort.filter(item => item.key !== key) : [];
      if (direction) next = [...next, {key, direction}];
      if (sameSort(next, currentSort)) return;
      pendingSort = {next: next.map(item => ({...item})), key, direction};
      if (onSortChange) {
        try {
          onSortChange(next.map(item => ({...item})), {
            sort: next.map(item => ({...item})), previousSort: currentSort.map(item => ({...item})),
            columnKey: key, direction, source, sourceEvent: event,
          });
        } catch (error) { console.error('[citry-ui] CDataGrid onSortChange callback failed.', error, root); }
      }
    };
    const selectionRequest = (next, changed, rowKey, selectedRow, event, source) => {
      if (sameArray(next, currentSelected)) return;
      const previous = [...currentSelected];
      if (controlledSelection) pendingSelection = [...next];
      else { applySelected(next); announceSelection(next.length); }
      if (onSelectionChange) {
        try {
          onSelectionChange([...next], {
            selected: [...next], previousSelected: previous, changed: [...changed], rowKey, selectedRow,
            controlled: controlledSelection, source, sourceEvent: event,
          });
        } catch (error) {
          console.error('[citry-ui] CDataGrid onSelectionChange callback failed.', error, root);
        }
      }
    };
    const selectRow = (row, event, source) => {
      if (disabled || data.selection === 'none' || row.hasAttribute('data-disabled')) return;
      const key = row.dataset.rowKey;
      const current = new Set(currentSelected);
      let next;
      if (data.selection === 'single') next = current.has(key) ? [] : [key];
      else if (event.shiftKey && source !== 'keyboard' && selectionAnchor && knownRows.includes(selectionAnchor)) {
        const start = knownRows.indexOf(selectionAnchor);
        const end = knownRows.indexOf(key);
        const range = knownRows.slice(Math.min(start, end), Math.max(start, end) + 1)
          .filter(value => !byRow.get(value).hasAttribute('data-disabled'));
        next = [...new Set([...currentSelected, ...range])];
      } else if (event.ctrlKey || event.metaKey || source === 'keyboard') {
        if (current.has(key)) current.delete(key); else current.add(key);
        next = knownRows.filter(value => current.has(value));
      } else next = [key];
      selectionAnchor = key;
      const before = new Set(currentSelected);
      const after = new Set(next);
      const changed = knownRows.filter(value => before.has(value) !== after.has(value));
      selectionRequest(next, changed, key, after.has(key), event, source);
    };
    const editDetail = (session, event, reason) => ({
      rowKey: session.descriptor.rowKey,
      columnKey: session.descriptor.columnKey,
      rowIndex: session.descriptor.rowIndex,
      columnIndex: session.descriptor.columnIndex,
      editor: session.descriptor.editor,
      previousValue: session.descriptor.value,
      source: session.source,
      reason,
      sourceEvent: event,
    });
    const restoreEditor = (session, {focus = true} = {}) => {
      session.control.remove();
      session.cell.append(...session.content);
      session.cell.removeAttribute('data-editing');
      root.removeAttribute('data-editing');
      activeEditor = null;
      if (focus) focusCell(session.cell, true);
    };
    const cancelEdit = (event, reason = 'escape', {notify = true, focus = true} = {}) => {
      const session = activeEditor;
      if (!session) return;
      restoreEditor(session, {focus});
      if (notify && onCellEditCancel) {
        try { onCellEditCancel(editDetail(session, event, reason)); }
        catch (error) { console.error('[citry-ui] CDataGrid onCellEditCancel callback failed.', error, root); }
      }
      if (notify) status.textContent = translateEdit('edit_cancelled', session.descriptor.columnLabel);
    };
    const commitEdit = (event, reason = 'enter', {focus = true} = {}) => {
      const session = activeEditor;
      if (!session) return true;
      const {control, descriptor} = session;
      let value;
      if (descriptor.editor === 'checkbox') value = control.checked;
      else if (descriptor.editor === 'number') {
        value = control.value === '' ? Number.NaN : control.valueAsNumber;
        if (!control.validity.valid || !Number.isFinite(value)) {
          control.setAttribute('aria-invalid', 'true');
          status.textContent = translateEdit('edit_invalid', descriptor.columnLabel);
          return false;
        }
      } else value = control.value;
      if (descriptor.editor === 'select' && !descriptor.options.some(option => option.value === value && !option.disabled)) {
        control.setAttribute('aria-invalid', 'true');
        status.textContent = translateEdit('edit_invalid', descriptor.columnLabel);
        return false;
      }
      if (onCellEditCommit && value !== descriptor.value) {
        try {
          if (onCellEditCommit(value, editDetail(session, event, reason)) === false) {
            control.setAttribute('aria-invalid', 'true');
            status.textContent = translateEdit('edit_invalid', descriptor.columnLabel);
            return false;
          }
        } catch (error) {
          console.error('[citry-ui] CDataGrid onCellEditCommit callback failed.', error, root);
          control.setAttribute('aria-invalid', 'true');
          status.textContent = translateEdit('edit_invalid', descriptor.columnLabel);
          return false;
        }
      }
      restoreEditor(session, {focus});
      status.textContent = translateEdit('edit_submitted', descriptor.columnLabel);
      return true;
    };
    const startEdit = (cell, event, source, seed = null) => {
      const row = cell.closest('[data-citry-ui-part="row"]');
      const descriptor = editors.get(editorKey(row?.dataset.rowKey, cell.dataset.columnKey));
      if (!row || !descriptor || disabled || row.hasAttribute('data-disabled')) return false;
      if (activeEditor?.cell === cell) return true;
      if (activeEditor && !commitEdit(event, 'next-cell', {focus: false})) return false;
      const control = descriptor.editor === 'select'
        ? root.ownerDocument.createElement('select') : root.ownerDocument.createElement('input');
      if (descriptor.editor !== 'select') control.type = descriptor.editor;
      control.setAttribute('data-citry-ui-part', 'editor');
      control.setAttribute('aria-label', translateEdit('edit', descriptor.columnLabel));
      for (const [name, value] of Object.entries(descriptor.attrs)) {
        if (typeof value === 'boolean') control.toggleAttribute(name, value);
        else control.setAttribute(name, String(value));
      }
      if (descriptor.editor === 'select') {
        for (const option of descriptor.options) {
          const element = root.ownerDocument.createElement('option');
          element.value = option.value;
          element.textContent = option.label;
          element.disabled = option.disabled;
          control.append(element);
        }
        control.value = descriptor.value;
      } else if (descriptor.editor === 'checkbox') control.checked = descriptor.value;
      else control.value = seed === null ? String(descriptor.value) : seed;
      const content = [...cell.childNodes];
      cell.replaceChildren(control);
      cell.setAttribute('data-editing', '');
      root.setAttribute('data-editing', '');
      activeEditor = {cell, control, content, descriptor, source};
      if (onCellEditStart) {
        try { onCellEditStart(editDetail(activeEditor, event, seed === null ? event.type : 'printable')); }
        catch (error) { console.error('[citry-ui] CDataGrid onCellEditStart callback failed.', error, root); }
      }
      status.textContent = translateEdit('editing', descriptor.columnLabel);
      control.focus();
      if (control instanceof HTMLInputElement && control.type !== 'checkbox') {
        if (seed === null) control.select();
        else control.setSelectionRange(control.value.length, control.value.length);
      }
      return true;
    };
    const activate = (cell, event, source) => {
      const row = cell.closest('[data-citry-ui-part="row"]');
      if (!row || disabled || row.hasAttribute('data-disabled') || !onCellActivate) return;
      try {
        onCellActivate({
          rowKey: row.dataset.rowKey, columnKey: cell.dataset.columnKey,
          rowIndex: Number(cell.dataset.rowIndex), columnIndex: Number(cell.dataset.columnIndex),
          source, sourceEvent: event,
        });
      } catch (error) { console.error('[citry-ui] CDataGrid onCellActivate callback failed.', error, root); }
    };
    const onKeydown = event => {
      const cell = event.target.closest('[data-citry-ui-part="header-cell"],[data-citry-ui-part="cell"]');
      if (!cell || !table.contains(cell) || disabled || !data.is_ready) return;
      if (activeEditor && event.target === activeEditor.control) {
        if (event.key === 'Escape') {
          event.preventDefault();
          cancelEdit(event);
        } else if (event.key === 'Enter' || event.key === 'F2') {
          event.preventDefault();
          commitEdit(event, event.key.toLowerCase());
        } else if (event.key === 'Tab') {
          event.preventDefault();
          const currentIndex = cells.indexOf(activeEditor.cell);
          const target = cells[Math.max(0, Math.min(cells.length - 1, currentIndex + (event.shiftKey ? -1 : 1)))];
          if (commitEdit(event, event.shiftKey ? 'shift-tab' : 'tab', {focus: false})) focusCell(target, true);
        }
        return;
      }
      const header = cell.matches('[data-citry-ui-part="header-cell"]');
      const rowIndex = header ? -1 : Number(cell.dataset.rowIndex);
      const columnIndex = Number(cell.dataset.columnIndex);
      if (event.key === 'Enter') {
        event.preventDefault();
        if (header) requestSort(cell, event, 'keyboard');
        else if (!startEdit(cell, event, 'keyboard')) activate(cell, event, 'keyboard');
        return;
      }
      if (!header && event.key === 'F2') {
        event.preventDefault();
        startEdit(cell, event, 'keyboard');
        return;
      }
      if (!header && !event.ctrlKey && !event.metaKey && !event.altKey
          && (event.key.length === 1 || event.key === 'Backspace' || event.key === 'Delete')) {
        const descriptor = editors.get(editorKey(cell.dataset.rowKey, cell.dataset.columnKey));
        if (descriptor && ['text', 'number'].includes(descriptor.editor)) {
          event.preventDefault();
          startEdit(cell, event, 'keyboard', event.key.length === 1 ? event.key : '');
          return;
        }
      }
      if (event.key === ' ' && event.shiftKey && !header) {
        event.preventDefault();
        selectRow(cell.closest('[data-citry-ui-part="row"]'), event, 'keyboard');
        return;
      }
      let target = null;
      const rtl = getComputedStyle(table).direction === 'rtl';
      if (event.key === 'ArrowLeft') target = locate(rowIndex, Math.max(0,
        Math.min(headers.length - 1, columnIndex + (rtl ? 1 : -1))));
      else if (event.key === 'ArrowRight') target = locate(rowIndex, Math.max(0,
        Math.min(headers.length - 1, columnIndex + (rtl ? -1 : 1))));
      else if (event.key === 'ArrowUp') target = locate(rowIndex <= 0 ? -1 : rowIndex - 1, columnIndex);
      else if (event.key === 'ArrowDown') {
        target = locate(rowIndex < 0 ? data.start_index : rowIndex + 1, columnIndex);
      }
      else if (event.key === 'Home') target = event.ctrlKey || event.metaKey
        ? headers[0] : locate(rowIndex, 0);
      else if (event.key === 'End') target = event.ctrlKey || event.metaKey
        ? cells.at(-1) ?? headers.at(-1) : locate(rowIndex, headers.length - 1);
      else if (event.key === 'PageUp' || event.key === 'PageDown') {
        const delta = Math.max(1, Math.floor(viewport.clientHeight / data.row_height));
        target = locate(Math.max(data.start_index, Math.min(data.start_index + rows.length - 1,
          rowIndex + (event.key === 'PageDown' ? delta : -delta))), columnIndex);
        scheduleRange('navigation', event);
      }
      if ((event.ctrlKey || event.metaKey) && event.key === 'Home' && data.start_index > 0) {
        viewport.scrollTop = 0;
        scheduleRange('navigation', event);
      } else if ((event.ctrlKey || event.metaKey) && event.key === 'End'
          && data.start_index + rows.length < data.total_count) {
        viewport.scrollTop = data.total_count * data.row_height;
        scheduleRange('navigation', event);
      }
      if (target) { event.preventDefault(); focusCell(target); }
      else if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End'].includes(event.key)) {
        scheduleRange('navigation', event);
      }
    };
    const onClick = event => {
      if (activeEditor && activeEditor.control.contains(event.target)) return;
      if (suppressClick) {
        suppressClick = false;
        clearTimeout(suppressClickTimer);
        event.preventDefault();
        return;
      }
      if (disabled || !data.is_ready) return;
      const header = event.target.closest('[data-citry-ui-part="header-cell"]');
      if (header && table.contains(header)) {
        if (activeEditor && !commitEdit(event, 'outside', {focus: false})) return;
        focusCell(header, true);
        requestSort(header, event, 'pointer');
        return;
      }
      const cell = event.target.closest('[data-citry-ui-part="cell"]');
      if (!cell || !table.contains(cell)) return;
      focusCell(cell, true);
      selectRow(cell.closest('[data-citry-ui-part="row"]'), event, 'pointer');
    };
    const finishPointerSelection = (event, cancelled = false) => {
      const session = pointerSelection;
      if (!session || event.pointerId !== session.pointerId) return;
      pointerSelection = null;
      root.removeAttribute('data-selecting');
      if (table.hasPointerCapture?.(event.pointerId)) table.releasePointerCapture(event.pointerId);
      if (!cancelled && !session.moved) {
        const row = byRow.get(session.startKey);
        if (row) selectRow(row, event, 'pointer');
      }
      selectionAnchor = session.startKey;
      suppressClick = !cancelled;
      clearTimeout(suppressClickTimer);
      suppressClickTimer = setTimeout(() => { suppressClick = false; }, 0);
    };
    const onPointerDown = event => {
      if (activeEditor && activeEditor.control.contains(event.target)) return;
      if (event.pointerType !== 'mouse' || !event.isPrimary || event.button !== 0
          || disabled || !data.is_ready || data.selection !== 'multiple') return;
      const cell = event.target.closest('[data-citry-ui-part="cell"]');
      const row = cell?.closest('[data-citry-ui-part="row"]');
      if (!cell || !row || !table.contains(row) || row.hasAttribute('data-disabled')) return;
      event.preventDefault();
      focusCell(cell, true);
      const startKey = row.dataset.rowKey;
      pointerSelection = {
        pointerId: event.pointerId,
        startKey,
        lastKey: startKey,
        base: new Set(currentSelected),
        selected: !currentSelected.includes(startKey),
        moved: false,
      };
      root.setAttribute('data-selecting', '');
      table.setPointerCapture?.(event.pointerId);
    };
    const onPointerMove = event => {
      const session = pointerSelection;
      if (!session || event.pointerId !== session.pointerId || !(event.buttons & 1)) return;
      const hovered = root.ownerDocument.elementFromPoint(event.clientX, event.clientY);
      const row = hovered?.closest?.('[data-citry-ui-part="row"]');
      if (!row || !table.contains(row)) return;
      const endKey = row.dataset.rowKey;
      if (!knownRows.includes(endKey) || endKey === session.lastKey) return;
      session.lastKey = endKey;
      session.moved = true;
      const start = knownRows.indexOf(session.startKey);
      const end = knownRows.indexOf(endKey);
      const range = knownRows.slice(Math.min(start, end), Math.max(start, end) + 1)
        .filter(value => !byRow.get(value).hasAttribute('data-disabled'));
      const nextSet = new Set(session.base);
      for (const value of range) {
        if (session.selected) nextSet.add(value);
        else nextSet.delete(value);
      }
      const next = knownRows.filter(value => nextSet.has(value));
      const before = new Set(currentSelected);
      const changed = knownRows.filter(value => before.has(value) !== nextSet.has(value));
      selectionRequest(next, changed, endKey, session.selected, event, 'pointer');
    };
    const onPointerUp = event => finishPointerSelection(event);
    const onPointerCancel = event => finishPointerSelection(event, true);
    const onDoubleClick = event => {
      if (disabled || !data.is_ready) return;
      const cell = event.target.closest('[data-citry-ui-part="cell"]');
      if (cell && table.contains(cell) && !startEdit(cell, event, 'pointer')) activate(cell, event, 'pointer');
    };
    const onDocumentPointerDown = event => {
      if (activeEditor && !activeEditor.cell.contains(event.target)
          && !commitEdit(event, 'outside', {focus: false})) {
        event.preventDefault();
        event.stopPropagation();
        activeEditor.control.focus();
      }
    };
    const onFocusIn = event => {
      if (activeEditor && event.target === activeEditor.control) return;
      const cell = event.target.closest('[data-citry-ui-part="header-cell"],[data-citry-ui-part="cell"]');
      if (cell && table.contains(cell)) focusCell(cell, true);
    };
    const onViewportFocus = event => {
      if (event.target === viewport && active && data.is_ready) {
        viewport.tabIndex = -1;
        focusCell(active, true);
      }
    };
    const onScroll = event => scheduleRange('scroll', event);
    table.addEventListener('keydown', onKeydown);
    table.addEventListener('click', onClick);
    table.addEventListener('dblclick', onDoubleClick);
    table.addEventListener('focusin', onFocusIn);
    table.addEventListener('pointerdown', onPointerDown);
    table.addEventListener('pointermove', onPointerMove);
    table.addEventListener('pointerup', onPointerUp);
    table.addEventListener('pointercancel', onPointerCancel);
    root.ownerDocument.addEventListener('pointerdown', onDocumentPointerDown, true);
    viewport.addEventListener('focus', onViewportFocus);
    viewport.addEventListener('scroll', onScroll, {passive: true});
    const observer = typeof ResizeObserver === 'function'
      ? new ResizeObserver(() => scheduleRange('resize')) : null;
    observer?.observe(viewport);
    const stopI18n = i18n?.subscribe(() => {
      if (locallySorted) reorderCompleteRows(currentSort);
    });
    applySort(currentSort);
    applySelected(currentSelected);
    viewport.scrollTop = data.initial_index * data.row_height;
    root.setAttribute('data-citry-data-grid-initialized', '');
    scheduleRange('initial');
    effect(() => {
      for (const name of [
        'onSortChange', 'onSelectionChange', 'onRangeChange', 'onCellActivate',
        'onCellEditStart', 'onCellEditCommit', 'onCellEditCancel',
      ]) {
        const value = props[name];
        if (value !== undefined && value !== null && typeof value !== 'function') report(name, value);
        else invalid.delete(name);
      }
      onSortChange = typeof props.onSortChange === 'function' ? props.onSortChange : null;
      onSelectionChange = typeof props.onSelectionChange === 'function' ? props.onSelectionChange : null;
      onRangeChange = typeof props.onRangeChange === 'function' ? props.onRangeChange : null;
      onCellActivate = typeof props.onCellActivate === 'function' ? props.onCellActivate : null;
      onCellEditStart = typeof props.onCellEditStart === 'function' ? props.onCellEditStart : null;
      onCellEditCommit = typeof props.onCellEditCommit === 'function' ? props.onCellEditCommit : null;
      onCellEditCancel = typeof props.onCellEditCancel === 'function' ? props.onCellEditCancel : null;
      if (props.disabled !== undefined && typeof props.disabled !== 'boolean') {
        report('disabled', props.disabled);
      }
      else invalid.delete('disabled');
      disabled = typeof props.disabled === 'boolean' ? props.disabled : data.disabled;
      if (disabled && activeEditor) cancelEdit(new Event('disabled'), 'disabled');
      root.toggleAttribute('data-disabled', disabled);
      root.setAttribute('aria-disabled', String(disabled));
      table.setAttribute('aria-disabled', String(disabled || !data.is_ready));
      const nextOverscan = props.overscan;
      if (nextOverscan === undefined) overscan = data.overscan;
      else if (Number.isInteger(nextOverscan) && nextOverscan >= 0 && nextOverscan <= 100) {
        overscan = nextOverscan; invalid.delete('overscan');
      } else report('overscan', nextOverscan);
      const nextSort = props.sort;
      const acceptedSort = nextSort === undefined || nextSort === null ? data.sort : nextSort;
      if (validSort(acceptedSort)) {
        invalid.delete('sort');
        if (!sameSort(acceptedSort, currentSort)) {
          const previous = currentSort.map(item => ({...item}));
          const acceptedPending = pendingSort && sameSort(acceptedSort, pendingSort.next);
          applySort(acceptedSort);
          if (acceptedPending) reorderCompleteRows(acceptedSort);
          if (sortInitialized) {
            if (acceptedPending) announceSort(pendingSort.key, pendingSort.direction);
            else {
              const changed = acceptedSort.find(item => !previous.some(
                prior => prior.key === item.key && prior.direction === item.direction,
              ));
              const removed = previous.find(item => !acceptedSort.some(prior => prior.key === item.key));
              if (changed) announceSort(changed.key, changed.direction);
              else if (removed) announceSort(removed.key, null);
            }
          }
        }
        if (pendingSort && sameSort(acceptedSort, pendingSort.next)) pendingSort = null;
      } else report('sort', nextSort);
      sortInitialized = true;
      const nextSelected = props.selected;
      if (nextSelected === undefined || nextSelected === null) controlledSelection = false;
      else if (validSelected(nextSelected)) {
        invalid.delete('selected');
        controlledSelection = true;
        if (!sameArray(nextSelected, currentSelected)) {
          applySelected(nextSelected);
          if (pendingSelection && sameArray(nextSelected, pendingSelection)) {
            announceSelection(nextSelected.length);
          }
          pendingSelection = null;
        }
      } else report('selected', nextSelected);
      scheduleRange('configuration');
    });
    return () => {
      alive = false;
      cancelAnimationFrame(rangeFrame);
      observer?.disconnect();
      stopI18n?.();
      if (activeEditor) cancelEdit(new Event('cleanup'), 'cleanup', {notify: false, focus: false});
      table.removeEventListener('keydown', onKeydown);
      table.removeEventListener('click', onClick);
      table.removeEventListener('dblclick', onDoubleClick);
      table.removeEventListener('focusin', onFocusIn);
      table.removeEventListener('pointerdown', onPointerDown);
      table.removeEventListener('pointermove', onPointerMove);
      table.removeEventListener('pointerup', onPointerUp);
      table.removeEventListener('pointercancel', onPointerCancel);
      root.ownerDocument.removeEventListener('pointerdown', onDocumentPointerDown, true);
      viewport.removeEventListener('focus', onViewportFocus);
      viewport.removeEventListener('scroll', onScroll);
      root.removeAttribute('data-citry-data-grid-initialized');
      root.removeAttribute('data-pending');
      root.removeAttribute('data-selecting');
      clearTimeout(suppressClickTimer);
    };
  },
});
