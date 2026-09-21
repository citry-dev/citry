
      const buttonRuntime = globalThis[Symbol.for("citry-ui:button-runtime")];
      const menuRuntime = globalThis[Symbol.for("citry-ui:menu-root-runtime")];
      const submitRuntime = globalThis[Symbol.for("citry-ui:split-button-submit-runtime")];
      if (buttonRuntime?.generation !== 1) {
        throw new Error("[citry-ui] CSplitButton Button runtime dependency did not load.");
      }
      if (menuRuntime?.generation !== 1) {
        throw new Error("[citry-ui] CSplitButton Menu runtime dependency did not load.");
      }
      if (submitRuntime?.generation !== 1) {
        throw new Error("[citry-ui] CSplitButton submit runtime dependency did not load.");
      }

      $component({
        props: {
          open: {},
          disabled: {},
          primaryDisabled: {},
          menuDisabled: {},
          loading: {},
          variant: {},
          intent: {},
          size: {},
          block: {},
          loadingPosition: {},
          loop: {},
          placement: {},
          matchWidth: {},
          closeOnSelect: {},
          onOpenChange: {},
          onAction: {},
        },
        inject: {formService: {from: Symbol.for("citry-ui:form"), default: null}},
        setup() {
          const service = Citry.vue.markRaw(menuRuntime.helpers.createMenuService());
          Citry.vue.onUnmounted(() => service.dispose());
          return {menuService: service};
        },
        provide() { return {[Symbol.for("citry-ui:menu")]: this.menuService}; },
        onServerRender: ({component}) => {
          const root = component.$el;
          const data = {
            rootId: component.rootId, primaryId: component.primaryId,
            triggerId: component.triggerId, surfaceId: component.surfaceId,
            anchorName: component.anchorName, label: component.label,
            menuLabel: component.menuLabel, primaryType: component.primaryType,
            ...component.serverDefaults,
          };
          const props = component.$props;
          const effect = Citry.vue.watchEffect;
          let submitRegistration = null;
          let controller = null;
          const anatomy = menuRuntime.helpers.createCompoundAnatomy(root, data, () => {
            applyCompoundConfiguration(configuration);
            controller?.repairOwned();
            controller?.refreshRootScope();
            submitRegistration?.refresh();
          });
          const { primary, trigger, surface, indicator } = anatomy;
          const formContext = component.formService;
          const allowed = {
            variant: ["solid", "outline", "ghost"],
            intent: ["primary", "neutral", "success", "warn", "danger"],
            size: ["sm", "md", "lg"],
            loadingPosition: ["start", "center", "end"],
          };
          const resolver = buttonRuntime.helpers.createResolver(
            "CSplitButton", root, data, props, allowed,
          );
          let configuration = {
            disabled: data.disabled,
            primaryDisabled: data.primaryDisabled,
            menuDisabled: data.menuDisabled,
            loading: data.loading,
            variant: data.variant,
            intent: data.intent,
            size: data.size,
            block: data.block,
            loadingPosition: data.loadingPosition,
          };

          const effectiveFormDisabled = () => Boolean(formContext?.disabled);
          const applyCompoundConfiguration = (next) => {
            configuration = next;
            buttonRuntime.helpers.applyCompoundConfiguration(
              root, primary, trigger, indicator, effectiveFormDisabled(), next,
            );
          };
          const menuData = {
            open: data.open,
            disabled: data.disabled || data.menuDisabled,
            loop: data.loop,
            placement: data.placement,
            matchWidth: data.matchWidth,
            closeOnSelect: data.closeOnSelect,
            size: data.size,
          };
          const menuProps = {};
          Object.defineProperties(menuProps, {
            open: { get: () => props.open },
            disabled: {
              get: () => (
                resolver.boolean("disabled")
                || resolver.boolean("menuDisabled")
                || effectiveFormDisabled()
              ),
            },
            loop: { get: () => resolver.boolean("loop") },
            placement: { get: () => props.placement },
            matchWidth: { get: () => resolver.boolean("matchWidth") },
            closeOnSelect: { get: () => resolver.boolean("closeOnSelect") },
            size: { get: () => props.size },
            onOpenChange: { get: () => props.onOpenChange },
            onAction: { get: () => props.onAction },
          });
          controller = menuRuntime.factory({
            host: root, data: menuData, props: menuProps,
            effect, service: component.menuService,
          }, {
            anchor: root,
            committedOpen: (open) => root.toggleAttribute("data-open", open),
            componentName: "CSplitButton",
            compound: true,
            controller: true,
            disabledChanged: () => applyCompoundConfiguration(configuration),
            disabledFocusTarget: () => (
              primary.isConnected
              && !primary.matches(":disabled")
              && primary.getClientRects().length > 0
                ? primary
                : null
            ),
            host: root,
            ignoreFocusOutside: (source) => (
              submitRegistration?.consumeInvalidFocus(source) ?? false
            ),
            insideElements: [root],
            ownsTriggerDisabled: true,
            readyChanged: (ready) => {
              root.toggleAttribute("data-citry-split-button-initialized", ready);
            },
            surface,
            trigger,
          });

          const onPrimaryClick = (event) => {
            controller.refreshRootScope();
            submitRegistration?.refresh();
            if (!anatomy.refresh()) {
              event.preventDefault();
              event.stopImmediatePropagation();
              return;
            }
            if (!buttonRuntime.helpers.guardActivation(primary, configuration, event)) {
              return;
            }
            controller.beginPrimaryAction(primary, event);
          };
          primary.addEventListener("click", onPrimaryClick, true);
          if (data.primaryType === "submit") {
            submitRegistration = submitRuntime.register(primary, {
              available: (event) => (
                anatomy.valid()
                && buttonRuntime.helpers.guardActivation(primary, configuration, event)
              ),
              hasAcceptedClick: () => controller.hasPrimaryClickToken(primary),
              observe: (event) => controller.observePrimarySubmit(event),
            });
          }

          effect(() => {
            applyCompoundConfiguration({
              disabled: resolver.boolean("disabled"),
              primaryDisabled: resolver.boolean("primaryDisabled"),
              menuDisabled: resolver.boolean("menuDisabled"),
              loading: resolver.boolean("loading"),
              variant: resolver.choice("variant"),
              intent: resolver.choice("intent"),
              size: resolver.choice("size"),
              block: resolver.boolean("block"),
              loadingPosition: resolver.choice("loadingPosition"),
            });
          });
          return () => {
            root.removeAttribute("data-citry-split-button-initialized");
            primary.removeEventListener("click", onPrimaryClick, true);
            anatomy.cleanup();
            submitRegistration?.cleanup();
            controller.cleanup();
          };
        },
      });
    