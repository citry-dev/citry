(function() {

const anchoredLayerRuntimeCompatible = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime-compatible")
] === true;
const anchoredLayerRuntime = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime")
];

const multiSelectHandoffKey = Symbol.for('citry-ui:multi-select-handoff');
__citryRuntime.registerTypeOptions.bind(null, "CMultiSelect_e37e33", "96e53adacfac375270abbcaa46e456946e5298d01ed9d09f5b2bf4e21555395d")({
  props: {
    value:{}, open:{}, required:{}, disabled:{}, readonly:{}, invalid:{}, loop:{},
    closeOnSelect:{}, placement:{}, matchWidth:{}, variant:{}, size:{},
    onValueChange:{}, onOpenChange:{},
  },
  inject: {
    fieldService:{from:Symbol.for('citry-ui:field'),default:null},
    formService:{from:Symbol.for('citry-ui:form'),default:null},
  },
  onServerRender: ({component}) => {
    if (!anchoredLayerRuntimeCompatible) return;
    const root=component.$refs.root;
    const data=new Proxy(component.serverDefaults,{get(target,key){return key in target?target[key]:component[key];}});
    const props=component.$props;
    const trigger=root.querySelector(':scope > [data-citry-ui-part="control"]');
    const nativeSelect=root.querySelector(':scope > [data-cui-multi-select-native]');
    const readonlyValues=root.querySelector(':scope > [data-cui-multi-select-readonly-values]');
    const popup=root.querySelector(':scope > [data-citry-ui-part="popup"]');
    const listbox=popup?.querySelector(':scope > [data-citry-ui-part="listbox"]');
    const valuesSurface=trigger?.querySelector('[data-citry-ui-part="values"]');
    if (!(trigger instanceof HTMLButtonElement) || !(nativeSelect instanceof HTMLSelectElement)
      || !(readonlyValues instanceof HTMLElement) || !(popup instanceof HTMLElement)
      || !(listbox instanceof HTMLElement) || !(valuesSurface instanceof HTMLElement)) {
      throw new Error('[citry-ui] CMultiSelect settled anatomy is invalid.');
    }
    const field=component.fieldService;
    const form=component.formService;
    const formRuntime=globalThis[Symbol.for('citry-ui:form-control-runtime')];
    if(formRuntime?.generation!==1)throw new Error('[citry-ui] CMultiSelect form-control runtime dependency did not load.');
    const listeners=formRuntime.listeners();
    const nativeForm=nativeSelect.form;
    const coordinator=anchoredLayerRuntime.coordinatorFor(popup);
    const invalidEpisodes=new Set();
    const options=()=>[...listbox.querySelectorAll('[role="option"]')]
      .filter(option=>option.closest('[role="listbox"]')===listbox);
    const enabledOptions=()=>options().filter(option=>!option.hasAttribute('data-disabled'));
    const optionFor=value=>options().find(option=>option.dataset.value===value)??null;
    const canonical=value=>formRuntime.canonical(value);
    const normalize=value=>{
      if(!Array.isArray(value)) return null;
      const result=formRuntime.stringList([],value,canonical);if(result.reason)return null;
      const seen=new Set(result.values), output=[];if(result.values.some(item=>!optionFor(item)))return null;
      options().forEach(option=>{if(seen.has(option.dataset.value))output.push(option.dataset.value);});
      return output;
    };
    const report=(name,value,suffix='')=>{if(invalidEpisodes.has(name))return;invalidEpisodes.add(name);console.error(`[citry-ui] CMultiSelect ${name} received invalid client value${suffix}`,value);};
    const boolean=(name,fallback)=>{const value=props[name];if(value===undefined){invalidEpisodes.delete(name);return fallback;}if(typeof value==='boolean'){invalidEpisodes.delete(name);return value;}report(name,value,'; using the server fallback');return fallback;};
    const choice=(name,fallback,allowed)=>{const value=props[name];if(value===undefined){invalidEpisodes.delete(name);return fallback;}if(typeof value==='string'&&allowed.includes(value)){invalidEpisodes.delete(name);return value;}report(name,value,'; using the server fallback');return fallback;};
    const prior=root[multiSelectHandoffKey];delete root[multiSelectHandoffKey];
    const serverFingerprint=JSON.stringify(data.value);
    let committed=prior?.serverFingerprint===serverFingerprint?[...prior.committed]:[...data.value];
    let current=[...committed];
    // A server re-render hands the previous run's open state to this one, so a popup that was open before the
    // re-render is still open after it. When the server's `open` input changed, the popup follows the server
    // instead. If the re-render disabled the component so this run cannot reopen it, the close is reported
    // once, the same way a disabled component closes within one run.
    const sameServerOpen=Boolean(prior)&&prior.serverOpen===data.open;
    let internalOpen=sameServerOpen?Boolean(prior.internalOpen):data.open;
    let pendingDisabledHandoff=Boolean(prior?.shown);
    let logicalOpen=false, highlightedValue=prior?.highlightedValue??null;
    let controlledValue=false, controlledOpen=false, clientValue, clientOpen;
    let onValueChange=null,onOpenChange=null,nativeInvalid=false,active=true,generation=0;
    let typeBuffer='',typeTimer=null,tabGesture=false,pendingDirection=1,selectionTransaction=false,pendingForced=null;
    let configuration={required:data.required,disabled:data.disabled,readonly:data.readonly,invalid:data.invalid,loop:data.loop,closeOnSelect:data.closeOnSelect,placement:data.placement,matchWidth:data.matchWidth,variant:data.variant,size:data.size};
    const anchorName=data.anchorName;
    if(!anchorName.startsWith('--'))throw new Error('[citry-ui] CMultiSelect could not resolve its anchor.');
    trigger.style.setProperty('anchor-name',anchorName);popup.style.setProperty('position-anchor',anchorName);
    const same=formRuntime.same;
    const effectiveDisabled=()=>configuration.disabled||trigger.matches(':disabled');
    const eligible=()=>!effectiveDisabled()&&!configuration.readonly&&enabledOptions().length>0;
    const syncValue=()=>{
      const selected=new Set(current);root.toggleAttribute('data-empty',!current.length);
      if(!current.length){const placeholder=root.ownerDocument.createElement('span');placeholder.dataset.citryUiPart='placeholder';placeholder.textContent=data.placeholder;valuesSurface.replaceChildren(placeholder);}
      else formRuntime.renderTokens(valuesSurface,current,{className:'cui-multi-select__chip',part:'chip',
        label:value=>data.options.find(option=>option.value===value)?.label??value});
      options().forEach(option=>{const chosen=selected.has(option.dataset.value);option.setAttribute('aria-selected',chosen?'true':'false');option.toggleAttribute('data-selected',chosen);});
      formRuntime.highlight(listbox,'[role="option"]',logicalOpen?highlightedValue:null);
      formRuntime.syncTransport(nativeSelect,readonlyValues,current,{name:data.name,form:data.form,required:configuration.required,
        readonly:configuration.readonly,disabled:effectiveDisabled()});
      if(current.length)nativeInvalid=false;const invalid=configuration.invalid||nativeInvalid;root.toggleAttribute('data-invalid',invalid);formRuntime.relationships([trigger],field,{describedby:data.externalDescribedBy,errormessage:data.externalErrorMessage,required:configuration.required,disabled:effectiveDisabled(),readonly:configuration.readonly},invalid);field?.setNativeInvalid(nativeInvalid);
    };
    const sync=()=>{const disabled=effectiveDisabled();formRuntime.states(root,{open:logicalOpen,required:configuration.required,disabled,readonly:configuration.readonly,'close-on-select':configuration.closeOnSelect,'match-width':configuration.matchWidth});root.dataset.variant=configuration.variant;root.dataset.size=configuration.size;popup.dataset.placement=configuration.placement;trigger.disabled=configuration.disabled;formRuntime.attrs([trigger],{'aria-expanded':logicalOpen?'true':'false','aria-activedescendant':logicalOpen&&highlightedValue?optionFor(highlightedValue)?.id:null});syncValue();};
    const chooseHighlight=direction=>{const enabled=enabledOptions();const selected=direction<0?[...current].reverse():current;const match=selected.map(optionFor).find(option=>option&&!option.hasAttribute('data-disabled'));return match?.dataset.value??(direction<0?enabled.at(-1):enabled[0])?.dataset.value??null;};
    const layer={trigger,surface:popup,isOpen:()=>active&&logicalOpen,isEligible:eligible,requestDismiss:(reason,source)=>{if(!(tabGesture&&reason==='focus-outside'))requestOpen(false,reason,source);},forceClose:(reason,source)=>forceClose(reason==='modal'?'ancestor':reason,source)};
    const notifyOpen=(next,reason,source,forced=false)=>onOpenChange?.(next,{open:next,reason,controlled:controlledOpen,forced,source});
    const applyOpen=(next,{reason=null,source=null,focus=false}={})=>{if(next===logicalOpen){if(next&&!coordinator.register(layer))forceClose('ancestor',popup);
      // The previous run leaves an open popup showing so this run can take it over. When this run starts closed,
      // for example because the server's `open` input changed, nothing else hides it.
      if(!next&&popup.matches(':popover-open')){popup.hidePopover();popup.hidden=true;popup.inert=true;popup.removeAttribute('data-open');sync();}return;}generation+=1;if(next){if(!eligible()||!coordinator.mayOpen(layer)){internalOpen=false;logicalOpen=false;if(popup.matches(':popover-open'))popup.hidePopover();popup.hidden=true;popup.inert=true;sync();return;}highlightedValue=chooseHighlight(pendingDirection);pendingDirection=1;popup.hidden=false;popup.inert=false;try{if(!popup.matches(':popover-open'))popup.showPopover();}catch(error){console.error('[citry-ui] CMultiSelect could not open:',error);popup.hidden=true;popup.inert=true;internalOpen=false;sync();return;}logicalOpen=true;popup.setAttribute('data-open','');if(!coordinator.register(layer)){logicalOpen=false;popup.hidePopover();popup.hidden=true;popup.inert=true;popup.removeAttribute('data-open');sync();return;}sync();if(focus)formRuntime.focus(trigger);optionFor(highlightedValue)?.scrollIntoView({block:'nearest'});return;}logicalOpen=false;highlightedValue=null;popup.inert=true;popup.removeAttribute('data-open');coordinator.unregister(layer);if(popup.matches(':popover-open'))popup.hidePopover();popup.hidden=true;sync();void reason;void source;};
    const requestOpen=(next,reason,source,focus=false,direction=1)=>{if(next===logicalOpen)return;if(next){pendingDirection=direction;coordinator.clearSuppression(layer);}if(controlledOpen){notifyOpen(next,reason,source);return;}internalOpen=next;applyOpen(next,{reason,source,focus});notifyOpen(next,reason,source);};
    const forceClose=(reason,source)=>{if(!logicalOpen){internalOpen=false;return;}internalOpen=false;applyOpen(false,{reason,source});if(selectionTransaction)pendingForced={reason,source};else notifyOpen(false,reason,source,true);};
    const nativeCommit=()=>formRuntime.commit(nativeSelect);
    const requestValue=(next,option,selected,source,event)=>{if(same(next,current))return false;const previous=[...current],detail={value:[...next],previousValue:previous,option,selected,controlled:controlledValue,source,sourceEvent:event};if(!controlledValue){current=[...next];committed=[...next];syncValue();}onValueChange?.([...next],detail);if(!controlledValue)nativeCommit();return true;};
    const toggleOption=(option,event,source)=>{if(!(option instanceof HTMLElement)||option.hasAttribute('data-disabled'))return;const selected=current.includes(option.dataset.value);const wanted=new Set(current);if(selected)wanted.delete(option.dataset.value);else wanted.add(option.dataset.value);const next=options().filter(item=>wanted.has(item.dataset.value)).map(item=>item.dataset.value);selectionTransaction=true;const transaction=generation;requestValue(next,option,!selected,source,event);selectionTransaction=false;if(pendingForced){const notice=pendingForced;pendingForced=null;notifyOpen(false,notice.reason,notice.source,true);return;}if(!active||transaction!==generation||!root.isConnected)return;if(configuration.closeOnSelect)requestOpen(false,'selection',option);};
    const localeLower=value=>{const lang=root.closest('[lang]')?.getAttribute('lang')??root.ownerDocument.documentElement.lang??'';try{return lang?value.toLocaleLowerCase(lang):value.toLocaleLowerCase();}catch{return value.toLowerCase();}};
    const typeahead=event=>{const altGraph=event.getModifierState?.('AltGraph')??false;if(event.isComposing||event.ctrlKey||event.metaKey||(event.altKey&&!altGraph)||event.key.length!==1)return false;const key=localeLower(event.key);typeBuffer=typeBuffer.length===1&&typeBuffer===key?key:typeBuffer+key;if(typeTimer!==null)clearTimeout(typeTimer);typeTimer=setTimeout(()=>{typeBuffer='';typeTimer=null;},500);const enabled=enabledOptions(),index=enabled.findIndex(option=>option.dataset.value===highlightedValue),ordered=[...enabled.slice(index+1),...enabled.slice(0,index+1)],match=ordered.find(option=>localeLower(option.querySelector('[data-citry-ui-part="option-label"]')?.textContent?.trim().replace(/\s+/g,' ')??'').startsWith(typeBuffer));if(!match)return false;highlightedValue=match.dataset.value;sync();match.scrollIntoView({block:'nearest'});return true;};
    const move=direction=>{const enabled=enabledOptions();if(!enabled.length)return;const index=enabled.findIndex(option=>option.dataset.value===highlightedValue),edge=direction>0?enabled[0]:enabled.at(-1),next=index<0?edge:enabled[index+direction]??(configuration.loop?edge:enabled[index]);highlightedValue=next?.dataset.value??null;sync();next?.scrollIntoView({block:'nearest'});};
    const onClick=event=>{const path=event.composedPath();if(path.includes(trigger)){if(eligible())requestOpen(!logicalOpen,'trigger',trigger,true);return;}const option=path.find(node=>node instanceof HTMLElement&&node.getAttribute('role')==='option'&&node.closest('[role="listbox"]')===listbox);if(option)toggleOption(option,event,'pointer');};
    const onPointer=event=>{if(!logicalOpen||(event.pointerType==='pen'&&(event.buttons>0||event.pressure>0)))return;const option=event.composedPath().find(node=>node instanceof HTMLElement&&node.getAttribute('role')==='option'&&node.closest('[role="listbox"]')===listbox);if(!(option instanceof HTMLElement)||option.hasAttribute('data-disabled'))return;highlightedValue=option.dataset.value;sync();};
    const onKey=event=>{if(event.target!==trigger||!eligible())return;if(!logicalOpen){if(['Enter',' ','ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();requestOpen(true,'keyboard',trigger,true,event.key==='ArrowUp'?-1:1);}return;}if(event.key==='ArrowDown'){event.preventDefault();move(1);}else if(event.key==='ArrowUp'){event.preventDefault();move(-1);}else if(event.key==='Home'){event.preventDefault();highlightedValue=enabledOptions()[0]?.dataset.value??null;sync();}else if(event.key==='End'){event.preventDefault();highlightedValue=enabledOptions().at(-1)?.dataset.value??null;sync();}else if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleOption(optionFor(highlightedValue),event,'keyboard');}else if(event.key==='Escape'){event.preventDefault();requestOpen(false,'escape',trigger);}else if(event.key==='Tab'){tabGesture=true;setTimeout(()=>{tabGesture=false;},0);requestOpen(false,'tab',trigger);}else if(typeahead(event))event.preventDefault();};
    const onToggle=event=>{if(event.target!==popup)return;const nativeOpen=popup.matches(':popover-open');if(nativeOpen===logicalOpen)return;if(nativeOpen){if(!coordinator.mayOpen(layer)||controlledOpen){popup.hidePopover();if(controlledOpen)notifyOpen(true,'native',popup);return;}internalOpen=true;logicalOpen=true;popup.hidden=false;popup.inert=false;popup.setAttribute('data-open','');highlightedValue=chooseHighlight(1);coordinator.register(layer);sync();notifyOpen(true,'native',popup);return;}if(controlledOpen&&coordinator.mayOpen(layer)){popup.hidden=false;popup.showPopover();notifyOpen(false,'native',popup);return;}internalOpen=false;logicalOpen=false;popup.inert=true;popup.hidden=true;popup.removeAttribute('data-open');highlightedValue=null;coordinator.unregister(layer);sync();notifyOpen(false,'native',popup);};
    const onInvalid=event=>{nativeInvalid=true;syncValue();event.preventDefault();formRuntime.focus(trigger);};
    const onProxyFocus=()=>{if(root.hasAttribute('data-citry-multi-select-initialized'))formRuntime.focus(trigger);};
    const onReset=event=>{const scheduled=generation;setTimeout(()=>{if(!active||event.defaultPrevented||scheduled!==generation)return;if(!controlledValue&&!same(current,data.value)){const previous=[...current];current=[...data.value];committed=[...data.value];syncValue();onValueChange?.([...current],{value:[...current],previousValue:previous,option:null,selected:false,controlled:false,source:'reset',sourceEvent:event});}else if(controlledValue&&!same(current,data.value))onValueChange?.([...data.value],{value:[...data.value],previousValue:[...current],option:null,selected:false,controlled:true,source:'reset',sourceEvent:event});if(logicalOpen)requestOpen(false,'reset',nativeForm);},0);};
    const reconcile=()=>{if(clientValue===undefined||clientValue===null){invalidEpisodes.delete('value');if(controlledValue)committed=[...current];controlledValue=false;current=[...committed];}else{const normalized=normalize(clientValue);if(normalized===null){report('value',clientValue,'; releasing control from committed selection');if(controlledValue)committed=[...current];controlledValue=false;current=[...committed];}else{invalidEpisodes.delete('value');controlledValue=true;current=normalized;}}const existing=new Set(options().map(option=>option.dataset.value));if(current.some(value=>!existing.has(value))){const previous=[...current];const next=current.filter(value=>existing.has(value));current=next;if(!controlledValue)committed=[...next];queueMicrotask(()=>onValueChange?.([...next],{value:[...next],previousValue:previous,option:null,selected:false,controlled:controlledValue,source:'structure',sourceEvent:null}));}if(clientOpen===undefined||clientOpen===null){invalidEpisodes.delete('open');controlledOpen=false;applyOpen(internalOpen,{reason:'owner',source:trigger});}else if(typeof clientOpen==='boolean'){invalidEpisodes.delete('open');controlledOpen=true;applyOpen(clientOpen,{reason:'owner',source:trigger,focus:clientOpen});}else{report('open',clientOpen,'; releasing control from committed visibility');controlledOpen=false;applyOpen(internalOpen,{reason:'owner',source:trigger});}if((effectiveDisabled()||configuration.readonly)&&logicalOpen)forceClose('ancestor',trigger);if(pendingDisabledHandoff){pendingDisabledHandoff=false;if(!logicalOpen&&effectiveDisabled())notifyOpen(false,'ancestor',trigger,true);}sync();};
    listeners.add(root,'click',onClick,true);listeners.add(root,'pointerover',onPointer,true);listeners.add(trigger,'keydown',onKey,true);listeners.add(popup,'toggle',onToggle);listeners.add(nativeSelect,'invalid',onInvalid);listeners.add(nativeSelect,'focus',onProxyFocus);
    const unregisterReset=formRuntime.registerReset(root,nativeSelect,{invalidate:()=>generation+=1,reset:onReset});
    const stopFieldsets=formRuntime.watchFieldset(root,trigger,reconcile);
    const nativeMode={className:'cui-form-control__native--enhanced'};
    // The stylesheet hides the popup until this mark is present. A server re-render hands an
    // open popup to this run and the effect below reopens it at once, so the mark must already
    // be back or the reopen measures a hidden popup, fails, and closes it without telling the owner.
    root.setAttribute('data-citry-multi-select-initialized','');formRuntime.enhanceNative(nativeSelect,trigger,nativeMode);
    const stop=Citry.vue.watchEffect(()=>{clientValue=props.value;clientOpen=props.open;onValueChange=typeof props.onValueChange==='function'?props.onValueChange:null;onOpenChange=typeof props.onOpenChange==='function'?props.onOpenChange:null;if(props.onValueChange!=null&&onValueChange===null)report('onValueChange',props.onValueChange);else invalidEpisodes.delete('onValueChange');if(props.onOpenChange!=null&&onOpenChange===null)report('onOpenChange',props.onOpenChange);else invalidEpisodes.delete('onOpenChange');configuration={required:field?field.required:boolean('required',data.required),disabled:field?field.disabled:(form?.disabled||boolean('disabled',data.disabled)),readonly:field?field.readonly:(form?.readonly||boolean('readonly',data.readonly)),invalid:field?field.invalid:boolean('invalid',data.invalid),loop:boolean('loop',data.loop),closeOnSelect:boolean('closeOnSelect',data.closeOnSelect),placement:choice('placement',data.placement,['bottom-start','bottom-end','top-start','top-end']),matchWidth:boolean('matchWidth',data.matchWidth),variant:choice('variant',data.variant,['outline','filled','plain']),size:choice('size',data.size,['sm','md','lg'])};reconcile();});
    reconcile();
    return()=>{active=false;generation+=1;if(typeTimer!==null)clearTimeout(typeTimer);root[multiSelectHandoffKey]={serverFingerprint,serverOpen:data.open,shown:logicalOpen,committed:[...committed],internalOpen,highlightedValue};stop?.();stopFieldsets();unregisterReset();listeners.stop();coordinator.unregister(layer,{reason:'ancestor',source:root,cascade:true});field?.setNativeInvalid(false);root.removeAttribute('data-citry-multi-select-initialized');formRuntime.enhanceNative(nativeSelect,trigger,nativeMode,false);};
  },
})

})();