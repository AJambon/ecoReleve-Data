define(['marionette', 'lyt-rootview', 'router', 'controller'],
function(Marionette, Lyt_rootview, Router, Controller) {


	var app = {}, JST = window.JST = window.JST || {};

	Backbone.Marionette.Renderer.render = function(template, data){
		if (!JST[template]) throw "Template '" + template + "' not found!";
		return JST[template](data);
	};

	app = new Marionette.Application();

	app.on('start', function() {
		app.rootView = new Lyt_rootview();
		app.rootView.render();
		app.controller = new Controller({app : app});
		app.router = new Router({controller: app.controller});
		Backbone.history.start();
	});

	return app;
});