// Handlebars extras
Handlebars.registerHelper('round', function(x, options){
    var dp = parseInt(options.hash.dp);
    x = parseFloat(x);
    if(x){
        return x.toFixed(dp);
    }else{
        return 0;
    }
});

DOWNLOAD_TEMPLATES = _.objectMap({"torrent": "torrent"}, function(n){
    return Handlebars.compile($("script." + n + "-template").html());
});

var MODULES = {
    "torrent": {
        commands: ["pause", "resume"],
        parameters: [
            "magnet_url", "state", "error", "torrent_status", "name",
            "progress", "started", "finished", "upload", "download",
            "disk_path", "web_path"
        ],
    },
};
var module_capabilities = _.objectMap(MODULES, function(x){ return x.parameters });

function authenticate(cb){
    var doAuth = function(){
        // Auth & get capabilities
        console.log("Trying to authenticate...");
        pool_endpoint.deferQuery({cmd: "pool"}, function(pool){
            cb(pool);
        });
        pool_endpoint.runQueries(function(){
            //cb(caps);
            console.log("Authenticated!");
        }, function(){
            console.log("Unable to authenticate. Trying again in 2 seconds.");
            window.setTimeout(doAuth, 2000);
        });
    };
    doAuth();
}

var refreshPool = function(){}; // Don't do anything, until we connect to the backend

// Backbone 
Backbone.sync = function(method, model, options){
    // Replace default sync function to raise error unless overridden
    console.error("unsupported sync");
    console.log(method, model, options);
}

var Download = Backbone.Model.extend({
    defaults: function(){
        return {
            type: null,
        };
    },
    initialize: function(params, options, x){

    },
    sync: function(method, model, options){
        if(method == "read"){
            console.error("Cannot read individual download");
            //pool_endpoint.deferQuery({cmd: "describe", args: {uid: this.id}}, options.success, options.error);
        }else if(method == "delete"){
            console.log("deleting", model)
            pool_endpoint.deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success, options.error);
        }else{
            console.log("ERROR:", "Unable to perform action on download:" + method);
        }
        return this;
    },
    parse: function(resp, options){
        if(resp){
            var attrs = {type: resp.type, uid: resp.uid, exists: true};
            _.each(resp.parameters, function(v, k){ attrs[k] = v; });
            if(resp.upload && resp.download && !resp.ratio){
                resp.ratio = resp.upload / resp.download;
            }
            return attrs;
        }else{
            return {};
        }
    },
    idAttribute: "uid",
    comparator: "started",
});

var DownloadPool = Backbone.Collection.extend({
    model: Download,
    sync: function(method, model, options){
        if(method != "read"){
            console.error("Can only read the pool");
            return;
        }
        pool_endpoint.deferQuery({cmd: "pool", args: {parameters: module_capabilities}}, options.success, options.error);
    },
    parse: function(resp, options){
        return resp;
    }
});

var DownloadView = Backbone.View.extend({
    act_template: function(x){ return x.html; }, //Handlebars.compile("{{{ html }}}"),
    events: {
        "click .rm": "remove",
        //"click .cmd": "cmd",
        //"click .action-set": "actionSet",
    },
    initialize: function(){
        var self = this;
        this.listenTo(this.model, "change", this.render);
        this.render();
        return this;
    },
    render: function(ev){
        this.$el.html(this.act_template({
            html: DOWNLOAD_TEMPLATES[this.model.get("type")](this.model.attributes),
            model: this.model
        }));
        return this;
    },
    remove: function(){
        this.model.destroy();
    },
    actionSet : function(ev){
        var $t = $(ev.target);
        var property = $t.attr('data-property');
        var value = $t.attr('data-value');
        var old_val = this.model.get(property);
        if(_.isNumber(old_val)){
            value = parseFloat(value);
        }
        this.model.set(property, value);
    },
});

var DownloadPoolView = Backbone.View.extend({
    subview: DownloadView,
    initialize: function(){
        var self = this;
        this.subviews = {};

        this.listenTo(this.collection, "add", this.addOne);
        this.listenTo(this.collection, "remove", this.removeOne); 
        this.listenTo(this.collection, "all", this.render); //FIXME?
        return this;
    },
    addOne: function(model){
        var $v_el = $("<li class='entry'></li>").attr("data-view-id", model.id);
        var view = new this.subview({model: model, el: $v_el});
        this.subviews[model.id] = view;
        this.render();
    },
    removeOne: function(model){
        this.subviews[model.id].$el.detach();
        delete this.subviews[model.id];
    },
    render: function(event, model, collection, options){
        if(this.no_autorefresh){
            return;
        }
        var self = this;
        if(event != "reset" && event != "sync"){
            self.$el.html($(_.map(this.collection.models, function(model){
                if(self.subviews[model.id]){ //TODO hack
                    return self.subviews[model.id].el;
                }
            })));

            // Delegate events to models now added to the DOM
            _.each(this.subviews, function(view){
                view.delegateEvents();
            });
        }
        return this;
    }
});

var cesspool = {
    download_pool: new DownloadPool(),
};

var authCallback = _.once(function(pool){
    refreshPool = function(){
        cesspool.download_pool.fetch();
    }

    refreshPool();
    // Refresh pool every 3 seconds
    setInterval(refreshPool, 3000);
});

authenticate(authCallback);

$(document).ready(function(){
    cesspool.download_pool_view = new DownloadPoolView({collection: cesspool.download_pool, el: $("ul.pool")});

    $(".torrent-form").submit(function(e){
        e.preventDefault();
        var query = $(".torrent-link").val();
        $(".torrent-link").val("");
        if(!query){
            return false;
        }
        pool_endpoint.deferQuery(
            {cmd: "add", args: {type: "torrent", args: {magnet_url: query}}}, 
            function(result){
                console.log("Success adding torrent!", result);
                refreshPool();
            },
            lostConnection
        );
        return false; // Prevent form submitting
    });
});
