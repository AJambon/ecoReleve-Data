
define(['jquery', 'marionette', 'backbone', 'config', 'sweetAlert', 'controller'],
  function($, Marionette, Backbone, config,Swal) {

  'use strict';
  return Marionette.AppRouter.extend({
    history: [],
    appRoutes: {
      'export(/)': 'export',

      'importFile(/)': 'importFile',

      'individuals/new(/)': 'newIndividual',
      'individuals/:id(/)': 'individual',
      'individuals(/)': 'individuals',

      'monitoredSites/new(/)': 'newMonitoredSite',
      'monitoredSites/:id(/)': 'monitoredSite',
      'monitoredSites(/)': 'monitoredSites',

      'sensors/new/:type(/)': 'newSensor',
      'sensors/:id(/)': 'sensor',
      'sensors(/)': 'sensors',

      'stations/new/:from(/)': 'newStation',
      'stations/new(/)': 'newStation',
      'stations/:id(/)': 'station',
      'stations(/)': 'stations',

      //'stations/:id/release(/)': 'stationRelease',
      'release/:id(/)': 'releaseIndividuals',
      'release(/)': 'release',

      'validate/:type(/)': 'validateType',
      'validate(/)': 'validate',


      '*route(/:page)': 'home',
    },

    initialize: function(opt) {
      this.collection = new Backbone.Collection([
      {label: 'Manual import', href: 'importFile', icon: 'reneco-import'},
      {label: 'New', href: 'stations/new', icon: 'reneco-entrykey'},
      {label: 'Release', href: 'release', icon: 'reneco-to_release'},
      {label: 'Validate', href: 'validate', icon: 'reneco-validate'},
      {label: 'Stations', href: 'stations', icon: 'reneco-stations'},
      {label: 'Observations', href: 'observations', icon: 'reneco-stations'},
      {label: 'Individuals', href: 'individuals', icon: 'reneco-individuals'},
      {label: 'Sensors', href: 'sensors', icon: 'reneco-sensors'},
      {label: 'Monitored Sites', href: 'monitoredSites', icon: 'reneco-sensors'},
      {label: 'Export', href: 'export', icon: 'reneco-export'},
      ]);
    },

    execute: function(callback, args, route) {
      // get current route
      this.history.push(Backbone.history.fragment);
      var _this= this;
      window.checkExitForm(function(){
        _this.continueNav(callback, args);
      },function(){
        _this.previous();
      });
    },
    onRoute: function(url, patern, params) {
      patern = patern.replace(/\(/g, '');
      patern = patern.replace(/\)/g, '');
      patern = patern.replace(/\:/g, '');
      patern = patern.split('/');

      if (patern[0] == '*route') {
        $('#arial').html('');
        $('#arialSub').html('');
      }else {
        this.setNav(patern);
      }

      this.checkResestCurrentDatas(patern[0], params);
    },

    checkResestCurrentDatas: function(type, params) {   
      if(params.length > 1){
        if(this.currentId && this.currentId != params[0]){
          window.app.currentData = null;
        }
        this.currentId = params[0];
      } else {
        this.currentId = null;
      }
      if(window.app.currentData){
        if((window.app.currentData.type != type)){
          window.app.currentData = null;
        }
      }
    },

    previous: function() {
        var href = this.history[this.history.length-2];
        var url = '#'+ href;
        Backbone.history.navigate(url,{trigger:false, replace: false});
        this.history.pop();
        var patern;
        var patern =   href.split('/');
        this.setNav(patern);
    },
    continueNav : function(callback, args){
        $.ajax({
          context: this,
          url: config.coreUrl + 'security/has_access'
        }).done(function() {
          $.xhrPool.abortAll();
          callback.apply(this, args);
        }).fail(function(msg) {
          if (msg.status === 403) {
            document.location.href = config.portalUrl;
          }
        });
    },
    unique : function(list) {
        var result = [];
        $.each(list, function(i, e) {
            if ($.inArray(e, result) == -1) result.push(e);
        });
        return result;
    },
    setNav : function(patern){
        var md = this.collection.findWhere({href: patern[0]});
        $('#arial').html('<a href="#' + md.get('href') + '">| &nbsp; ' + md.get('label') + '</a>');
        if (patern[1] && patern[1] != 'id' && patern[1] != 'type') {
          $('#arialSub').html('<a href="#' + patern[0] + '/' + patern[1] + '">| &nbsp;' + patern[1] + '</a>');
        }else {
          $('#arialSub').html('');
        }
     }
  });
});
