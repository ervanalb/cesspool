// Underscore mixins
_.mixin(_.str.exports());
_.mixin({
    obj : function(op){
        return function(obj, fn){
            return _.chain(obj)[op](function(v, k){ return [k, fn(v)] }).object().value();
        };
    }
});

_.mixin({
    objectMap : _.obj("map"),
    objectFilter : _.obj("filter")
});


// Handlebars extras
Handlebars.registerHelper('minutes', function(seconds){
    var hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    var minutes = Math.floor(seconds / 60);
    seconds %= 60;
    seconds = Math.floor(seconds);
    if(hours){
        return hours + ":" + _.lpad(minutes, 2, '0') + ":" + _.lpad(seconds, 2, '0');
    }else{
        return minutes + ":" + _.lpad(seconds, 2, '0');
    }
});

Handlebars.registerHelper('add', function(x, options){
    var v = x + parseInt(options.hash.v);
    if(!v || v < 0){
        return 0;
    }
    return v;
});

Handlebars.registerHelper('percent', function(x, options){
    var of = parseInt(options.hash.of);
    x = parseInt(x);
    if(of && x){
        return Math.floor(x / of * 100);
    }else{
        return 0;
    }
});

Handlebars.registerHelper('if_eq', function(x, options){
    if(options.hash.eq){
        if(x == options.hash.eq){
            return options.fn(this);
        }
        return options.inverse(this);
    }else{
        if(x == options.hash.neq){
            return options.inverse(this);
        }
        return options.fn(this);
    }
});

DOWNLOAD_TEMPLATES = _.objectMap({"torrent": "torrent"}, function(n){
    return Handlebars.compile($("script." + n + "-template").html());
});

var _query_queue = [];
var _runquery_timeout;
//var BASE_URL = "http://localhost:9000/";
var BASE_URL = "/cmd";

function deferQuery(data, cb, err){
    _query_queue.push({"data": data, "cb": cb, "err": err});
}

function forceQuery(data, cb, err){
    deferQuery(data, cb, err);
    runQueries();
}

function runQueries(cb, err){
    window.clearTimeout(_runquery_timeout);
    if(_query_queue.length){
        var cbs = _.pluck(_query_queue, "cb");
        var errs = _.pluck(_query_queue, "cb");
        var datas = _.pluck(_query_queue, "data");
        $.ajax(BASE_URL, {
            data: JSON.stringify(datas),
            dataType: 'json',
            contentType: 'text/json',
            type: 'POST',
            success: function(resp){
                regainConnection();
                if(resp.length != datas.length){ 
                    console.error("Did not recieve correct number of responses from server!");
                    return;
                }
                for(var i = 0; i < resp.length; i++){
                    var r = resp[i];
                    if(!r.success){
                        console.error("Server Error:", r.error);
                        if(errs[i]){
                            errs[i]();
                        }
                    }else if(cbs[i]){
                        cbs[i](r.result);
                    }
                }
                if(cb){
                    cb();
                }
                _runquery_timeout = window.setTimeout(runQueries, 0); // Defer
            },
            error: function(){
                lostConnection();
                _.each(errs, function(x){ if(x){ x(); } });
                _runquery_timeout = window.setTimeout(runQueries, 500); // Connection dropped?
                if(err){
                    err();
                }
            }
        });
    }else{
        _runquery_timeout = window.setTimeout(runQueries, 50);
    }
    _query_queue = [];
}

function regainConnection(){
    $(".disconnect-hide").show();
    $(".disconnect-show").hide();
}

function lostConnection(){
    console.log("Lost connection");
    $(".disconnect-show").show();
    $(".disconnect-hide").hide();
}

function authenticate(cb){
    var doAuth = function(){
        // Auth & get capabilities
        console.log("trying to auth");
        deferQuery({cmd: "pool"}, function(pool){
            cb(pool);
        });
        runQueries(function(){
            //cb(caps);
        }, function(){
            console.log("unable to auth");
            window.setTimeout(doAuth, 2000);
        });
    };
    doAuth();
}

var refreshPool = function(){}; // Don't do anything, until we connect to the backend


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
            deferQuery({cmd: "describe", args: {uid: this.id}}, options.success, options.error);
        }else if(method == "delete"){
            console.log("deleting", model)
            deferQuery({cmd: "rm", uid: this.id});
        }else{
            console.log("ERROR:", "Unable to perform action on download:" + method);
        }
        return this;
    },
    parse: function(resp, options){
        if(resp){
            var attrs = {
                status: resp.status,
                uid: resp.uid,
                url: resp.url,
                torrent_status: resp.torrent_status,
                error: resp.error,
                progress: resp.progress,
                type: resp.type
            }
            return attrs;
        }else{
            return {};
        }
    },
    idAttribute: "uid",
});

var DownloadPool = Backbone.Collection.extend({
    model: Download,
    sync: function(method, model, options){
        if(method != "read"){
            console.error("Can only read the pool");
            return;
        }
        deferQuery({cmd: "pool"}, options.success, options.error);
    },
    parse: function(resp, options){
        return resp;
    }
});

var DownloadView = Backbone.View.extend({
    act_template: Handlebars.compile("{{{ html }}}<a href='#' class='btn rm'>rm</a>"),
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
    updateProgress : function(){
        var $progbar = this.$el.find(".progress-bar");
        if($progbar){
            var progress = this.model.get("progress") || 0.0;
            console.log({width: $progbar.parent().width() * progress + "px"});
            $progbar.animate({width: $progbar.parent().width() * progress + "px"});
        }
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
        deferQuery(
            {cmd: "add", args: {type: "torrent", args: {url: query}}}, 
            function(result){
                console.log("Success adding torrent!", result);
                refreshPool();
            },
            lostConnection
        );
        return false; // Prevent form submitting
    });

    /*
    // This probably will be re-implemented later
    $("#uploadform").submit(function(e){
        var $this = $("#uploadform");
        e.preventDefault();
        var formData = new FormData($this[0]);
        // Clear out the old file by replacing the DOM element.
        // Super hacky, but works cross-browser
        var fparent = $('input.uploadfile').parent();
        fparent.html(fparent.html());
        $this.hide();
        var $progbar = $('div.upload-progress-bar')
        $progbar.css('width', '3%');

        $.ajax({
            url: $this.attr('action'),  //server script to process data
            type: 'POST',
            xhr: function() {  // custom xhr
                var myXhr = $.ajaxSettings.xhr();
                if(myXhr.upload){ // check if upload property exists
                    myXhr.upload.addEventListener('progress',function(pe){
                            if(pe.lengthComputable){
                                var progress = (pe.loaded / pe.total);
                                $progbar.parent().show();
                                $progbar.animate({width: $progbar.parent().width() * progress + 'px'});
                            };
                        }, false); // for handling the progress of the upload
                }
                return myXhr;
            },
            //Ajax events
            //beforeSend: beforeSendHandler,
            success: function(){
                refreshPlaylist();
                $('div.upload-progress').hide();
                $this.show();
            },
            error: function(){
                lostConnection();
                $('div.upload-progress').hide();
                $this.show();
            },
            // Form data
            data: formData,
            //Options to tell JQuery not to process data or worry about content-type
            cache: false,
            contentType: false,
            processData: false
        });
        return false; // Prevent form submitting
    });
    */

    $(".results").delegate("a.push", "click", function(){
        var $this = $(this);
        /*
        $(".addtxt").val($this.attr("content"));
        $(".results").html("");
        $("#queueform").submit();
        */
    });

});
