(function() {
__citryRuntime.registerTypeOptions.bind(null, "SidebarControlled_b83d65", "76496120b520f95e36f37cbd37401911a6f7fe941ffd4c828e82908bf3bb4c00")({data(){return {collapsed:false,last:'No request yet'}},methods:{
      change(next){this.last=`Requested ${next ? 'collapse' : 'expand'}`;this.collapsed=next},
    }})
})();