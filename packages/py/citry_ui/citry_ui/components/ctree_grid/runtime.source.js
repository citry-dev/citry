$component({
  props: {expanded:{}, selected:{}, disabled:{}, onExpandedChange:{}, onSelectionChange:{}, onCellActivate:{}},
  init: ({els,data,props,effect,i18n}) => {
    const root=els[0], table=root?.querySelector(':scope [data-citry-ui-part="table"]'), body=table?.querySelector('[data-citry-ui-part="body"]'), status=root?.querySelector(':scope > [data-citry-ui-part="status"]'), inputs=root?.querySelector(':scope > [data-citry-ui-part="inputs"]');
    if (!(root instanceof HTMLElement)||!(table instanceof HTMLTableElement)||!body||!status||!inputs) throw new Error('[citry-ui] CTreeGrid settled anatomy is invalid.');
    const rows=[...body.querySelectorAll(':scope > [data-citry-tree-grid-row]')], byKey=new Map(rows.map(row=>[row.dataset.rowKey,row]));
    const branches=new Set(rows.filter(row=>row.hasAttribute('aria-expanded')).map(row=>row.dataset.rowKey));
    const unavailable=new Set(rows.filter(row=>row.hasAttribute('data-disabled')).map(row=>row.dataset.rowKey));
    const invalid=new Set(), labelBindings=new Map();
    let acceptedExpanded=[...data.expanded], currentExpanded=[...acceptedExpanded], acceptedSelected=[...data.selected], currentSelected=[...acceptedSelected];
    let expandedControlled=false, selectedControlled=false, disabled=data.disabled, expandedCallback=null, selectionCallback=null, activateCallback=null, active={row:rows[0]?.dataset.rowKey??null,column:0};
    const report=(name,value)=>{if(invalid.has(name))return;invalid.add(name);console.error(`[citry-ui] CTreeGrid ${name} received invalid client value.`,value,root);};
    const cells=row=>[...row.querySelectorAll(':scope > [data-citry-ui-part="cell"]')];
    const parent=row=>row.dataset.parentKey?byKey.get(row.dataset.parentKey)??null:null;
    const children=row=>rows.filter(candidate=>candidate.dataset.parentKey===row.dataset.rowKey);
    const visibleRows=()=>rows.filter(row=>!row.hidden);
    const validVector=(value,allowed)=>Array.isArray(value)&&value.every(key=>typeof key==='string'&&allowed.has(key))&&new Set(value).size===value.length;
    const format=(kind,row)=>{
      if(i18n&&data.catalog[kind])try{return i18n.tr(`citry-ui-tree-grid-${kind}`,{row:row.dataset.label});}catch(error){console.error('[citry-ui] CTreeGrid translation failed.',error,root);}
      return data.labels[kind].replaceAll('{row}',row.dataset.label);
    };
    const bindExpander=row=>{
      const button=row.querySelector(':scope [data-citry-tree-grid-expander]'); if(!button)return;
      const kind=currentExpanded.includes(row.dataset.rowKey)?'collapse':'expand', prior=labelBindings.get(row);
      if(prior?.kind===kind)return; prior?.binding?.dispose();
      if(i18n&&data.catalog[kind]) {
        const binding=i18n.bind({message:`citry-ui-tree-grid-${kind}`,values:()=>({row:row.dataset.label}),onChange:value=>button.setAttribute('aria-label',value)});
        labelBindings.set(row,{kind,binding});
      } else {button.setAttribute('aria-label',format(kind,row));labelBindings.set(row,{kind,binding:null});}
    };
    const visible=row=>{for(let ancestor=parent(row);ancestor;ancestor=parent(ancestor))if(!currentExpanded.includes(ancestor.dataset.rowKey))return false;return true;};
    const focus=(row,column)=>{if(!row||row.hidden)return;const entries=cells(row),cell=entries[Math.max(0,Math.min(entries.length-1,column))];if(!cell)return;active={row:row.dataset.rowKey,column:entries.indexOf(cell)};rows.flatMap(cells).forEach(entry=>entry.tabIndex=entry===cell?0:-1);cell.focus();};
    const syncInputs=()=>{inputs.replaceChildren(...(data.name?currentSelected.map(key=>{const input=document.createElement('input');input.type='hidden';input.name=data.name;input.value=key;input.disabled=disabled;if(data.form)input.setAttribute('form',data.form);return input;}):[]));};
    const sync=()=>{
      root.toggleAttribute('data-disabled',disabled);root.setAttribute('aria-disabled',String(disabled));table.setAttribute('aria-disabled',String(disabled));
      for(const row of rows){const key=row.dataset.rowKey,isVisible=visible(row),expanded=currentExpanded.includes(key),selected=currentSelected.includes(key);row.hidden=!isVisible;row.inert=!isVisible;row.toggleAttribute('data-expanded',expanded);row.toggleAttribute('data-selected',selected);if(branches.has(key))row.setAttribute('aria-expanded',String(expanded));if(data.selection==='none')row.removeAttribute('aria-selected');else row.setAttribute('aria-selected',String(selected));const button=row.querySelector(':scope [data-citry-tree-grid-expander]');if(button){button.disabled=disabled||unavailable.has(key);button.firstElementChild.style.transform=expanded?'rotate(90deg)':'';bindExpander(row);}}
      const activeRow=byKey.get(active.row), visibleNow=visibleRows();if(!activeRow||activeRow.hidden){const fallback=visibleNow.find(row=>currentSelected.includes(row.dataset.rowKey))??visibleNow[0];active={row:fallback?.dataset.rowKey??null,column:active.column};}
      rows.flatMap(cells).forEach(cell=>cell.tabIndex=-1);const row=byKey.get(active.row);if(row&&!disabled){const entry=cells(row)[Math.min(active.column,cells(row).length-1)];if(entry)entry.tabIndex=0;}
      syncInputs();
    };
    const requestExpanded=(row,next,source,event)=>{const key=row.dataset.rowKey;if(disabled||unavailable.has(key)||!branches.has(key))return;const previous=[...currentExpanded], value=next?[...previous.filter(item=>item!==key),key]:previous.filter(item=>item!==key);try{expandedCallback?.([...value],{expanded:[...value],previousExpanded:previous,rowKey:key,rowExpanded:next,controlled:expandedControlled,source,sourceEvent:event});}catch(error){console.error('[citry-ui] CTreeGrid onExpandedChange callback failed.',error,root);}if(!expandedControlled){acceptedExpanded=[...value];currentExpanded=[...value];status.textContent=format(next?'expanded':'collapsed',row);}sync();};
    const requestSelected=(row,source,event)=>{const key=row.dataset.rowKey;if(disabled||unavailable.has(key)||data.selection==='none')return;const previous=[...currentSelected], rowSelected=!previous.includes(key), value=data.selection==='single'?(rowSelected?[key]:[]):(rowSelected?[...previous,key]:previous.filter(item=>item!==key));try{selectionCallback?.([...value],{selected:[...value],previousSelected:previous,rowKey:key,rowSelected,controlled:selectedControlled,source,sourceEvent:event});}catch(error){console.error('[citry-ui] CTreeGrid onSelectionChange callback failed.',error,root);}if(!selectedControlled){acceptedSelected=[...value];currentSelected=[...value];status.textContent=format(rowSelected?'selected':'unselected',row);}sync();};
    const cellFrom=event=>event.composedPath().find(node=>node instanceof HTMLElement&&node.dataset?.citryUiPart==='cell'&&node.closest('[role="treegrid"]')===table);
    const onClick=event=>{const expander=event.target.closest?.('[data-citry-tree-grid-expander]'),cell=cellFrom(event);if(!cell)return;const row=cell.closest('[data-citry-tree-grid-row]');focus(row,cells(row).indexOf(cell));if(expander){requestExpanded(row,row.getAttribute('aria-expanded')!=='true','pointer',event);return;}requestSelected(row,'pointer',event);};
    const onDoubleClick=event=>{const cell=cellFrom(event);if(!cell)return;const row=cell.closest('[data-citry-tree-grid-row]');if(disabled||unavailable.has(row.dataset.rowKey))return;try{activateCallback?.({rowKey:row.dataset.rowKey,columnKey:cell.dataset.columnKey,rowIndex:rows.indexOf(row),columnIndex:cells(row).indexOf(cell),sourceEvent:event});}catch(error){console.error('[citry-ui] CTreeGrid onCellActivate callback failed.',error,root);}};
    const onKeyDown=event=>{const cell=cellFrom(event);if(!cell)return;const row=cell.closest('[data-citry-tree-grid-row]'), rowCells=cells(row), column=rowCells.indexOf(cell), visibleNow=visibleRows(), rowIndex=visibleNow.indexOf(row);let destination=null,destinationColumn=column;
      if(event.shiftKey&&event.key===' '){requestSelected(row,'keyboard',event);event.preventDefault();return;}
      if(event.key==='ArrowDown')destination=visibleNow[rowIndex+1]??row;else if(event.key==='ArrowUp')destination=visibleNow[rowIndex-1]??row;
      else if(event.key==='ArrowRight'){if(column===0&&branches.has(row.dataset.rowKey)&&!currentExpanded.includes(row.dataset.rowKey)){requestExpanded(row,true,'keyboard',event);event.preventDefault();return;}destination=row;destinationColumn=Math.min(rowCells.length-1,column+1);}
      else if(event.key==='ArrowLeft'){if(column===0&&branches.has(row.dataset.rowKey)&&currentExpanded.includes(row.dataset.rowKey)){requestExpanded(row,false,'keyboard',event);event.preventDefault();return;}if(column===0)destination=parent(row)??row;else{destination=row;destinationColumn=column-1;}}
      else if(event.key==='Home'){destination=event.ctrlKey?visibleNow[0]:row;destinationColumn=0;}
      else if(event.key==='End'){destination=event.ctrlKey?visibleNow.at(-1):row;destinationColumn=event.ctrlKey?cells(destination).length-1:rowCells.length-1;}
      else if(event.key==='Enter'){if(column===0&&branches.has(row.dataset.rowKey))requestExpanded(row,!currentExpanded.includes(row.dataset.rowKey),'keyboard',event);else onDoubleClick(event);event.preventDefault();return;}else return;
      event.preventDefault();focus(destination,destinationColumn);
    };
    const onReset=event=>{const form=root.closest('form')??(data.form?document.getElementById(data.form):null);if(event.target!==form)return;queueMicrotask(()=>{if(expandedControlled)expandedCallback?.([...data.expanded],{expanded:[...data.expanded],previousExpanded:[...currentExpanded],rowKey:'',rowExpanded:false,controlled:true,source:'reset',sourceEvent:event});else{acceptedExpanded=[...data.expanded];currentExpanded=[...data.expanded];}if(selectedControlled)selectionCallback?.([...data.selected],{selected:[...data.selected],previousSelected:[...currentSelected],rowKey:'',rowSelected:false,controlled:true,source:'reset',sourceEvent:event});else{acceptedSelected=[...data.selected];currentSelected=[...data.selected];}sync();});};
    body.addEventListener('click',onClick);body.addEventListener('dblclick',onDoubleClick);body.addEventListener('keydown',onKeyDown);document.addEventListener('reset',onReset,true);root.setAttribute('data-citry-tree-grid-initialized','');
    effect(()=>{const nextDisabled=props.disabled;if(nextDisabled!==undefined&&typeof nextDisabled!=='boolean')report('disabled',nextDisabled);else{invalid.delete('disabled');disabled=typeof nextDisabled==='boolean'?nextDisabled:data.disabled;}
      const nextExpanded=props.expanded;expandedControlled=nextExpanded!=null;if(expandedControlled){if(validVector(nextExpanded,branches)){invalid.delete('expanded');currentExpanded=[...nextExpanded];}else{report('expanded',nextExpanded);currentExpanded=[...acceptedExpanded];}}else{invalid.delete('expanded');currentExpanded=[...acceptedExpanded];}
      const selectable=new Set(rows.map(row=>row.dataset.rowKey).filter(key=>!unavailable.has(key)));const nextSelected=props.selected;selectedControlled=nextSelected!=null;if(selectedControlled&&validVector(nextSelected,selectable)&&(data.selection==='multiple'||nextSelected.length<=1)&&(data.selection!=='none'||nextSelected.length===0)){invalid.delete('selected');currentSelected=[...nextSelected];}else if(selectedControlled){report('selected',nextSelected);currentSelected=[...acceptedSelected];}else{invalid.delete('selected');currentSelected=[...acceptedSelected];}
      for(const [name,setter] of [['onExpandedChange',value=>expandedCallback=value],['onSelectionChange',value=>selectionCallback=value],['onCellActivate',value=>activateCallback=value]]){const supplied=props[name];if(supplied==null){setter(null);invalid.delete(name);}else if(typeof supplied==='function'){setter(supplied);invalid.delete(name);}else report(name,supplied);}sync();});
    return()=>{labelBindings.forEach(value=>value.binding?.dispose());document.removeEventListener('reset',onReset,true);body.removeEventListener('click',onClick);body.removeEventListener('dblclick',onDoubleClick);body.removeEventListener('keydown',onKeyDown);root.removeAttribute('data-citry-tree-grid-initialized');};
  },
});
