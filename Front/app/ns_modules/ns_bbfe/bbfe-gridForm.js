define([
  'jquery',
  'underscore',
  'backbone',
  'marionette',
  'ns_ruler/ruler',
  'backbone-forms',
  'ns_grid/grid.view',

  ], function ($, _, Backbone, Marionette,Ruler, Form, GridView, tpl) {

  'use strict';
  return Form.editors.GridFormEditor = Form.editors.Base.extend({
    events: {
        'click .js-btn-add' : 'addRow',
        'click .js-btn-delete' : 'deleteRows',
        'click .js-cloneLast' : 'cloneLast',
    },

    template: '\
        <div class="js-rg-grid-subform col-xs-12 no-padding" style="height: 300px">\
        </div>\
        <button type="button" class="js-btn-add btn btn-success btn-sm hide"><span class="reneco reneco-add"></span></button>\
        <button type="button" class="js-btn-delete btn btn-danger btn-sm pull-right hide"><span class="reneco reneco-trash"></span> Delete selected rows</button>\
    ',

    
    addRow: function(){
      this.gridView.gridOptions.api.addItems([{}]);
    },

    deleteRows: function() {
      this.gridView.deleteSelectedRows();
    },

    initialize: function(options) {
      var _this = this; 

      this.editable = options.schema.editable;

      options.schema.fieldClass = 'col-xs-12';
      this.formatColumns(options.schema);

      this.templateSettings = {
          hidden: false,
          hiddenClone: false,
      };
      
      this.regionManager = new Marionette.RegionManager();
      _.bindAll(this, 'render', 'afterRender'); 
      this.render = _.wrap(this.render, function(render) {
          render();    
          setTimeout(function(){
              _this.afterRender(options);
          }, 0);
          return _this;
      });
    },

    render: function(){
        this.template = _.template(this.template, this.templateSettings);
        this.$el.html(this.template);
        if(this.editable){
          this.$el.find('.js-btn-add').removeClass('hide');
          this.$el.find('.js-btn-delete').removeClass('hide');
        }
        return this;
    },

    afterRender: function(options){
      var rowData = options.model.get(options.key) || [];
      this.regionManager.addRegions({
        rgGrid: '.js-rg-grid-subform'
      });

      var url = 'stations/' + this.model.get('FK_Station') + '/observations'; 

      this.regionManager.get('rgGrid');
      this.regionManager.get('rgGrid').show(this.gridView = new GridView({
        columns: this.formatColumns(options.schema),
        clientSide: true,
        url: url,
        gridOptions: {
          rowData: rowData,
          rowSelection: (this.editable)? 'multiple' : '',
        },
        onFocusedRowChange: function(row){

        }
      }));

    },

    formatColumns: function(schema){
      var odrFields = schema.fieldsets[0].fields;
                        
      var columnsDefs = [];

      for (var i = odrFields.length - 1; i >= 0; i--) {
          var field = schema.subschema[odrFields[i]];

          var colDef = {
              editable: this.editable,
              field: field.name,
              headerName: field.title,
              type: field.type,
              options: field.options
          };
          
          columnsDefs.push(colDef)
      }

      return columnsDefs;             
    },



    getValue: function() {
      var rowData = [];
      this.gridView.gridOptions.api.forEachNode( function(node) {
          rowData.push(node.data);
      });
      return rowData;
    },

    initRules:function(form) {
      var _this = this;
      this.ruler = new Ruler({
            form: form
          });
      var globalError = {};
      var errorMsg = 'error on field(s): \n';

      _.each(form.schema,function(curSchema){
        if (curSchema.rule){
          var curRule = curSchema.rule;
          var target = curSchema.name;
          var curResult = _this.ruler.addRule(target,curRule.operator,curRule.source,curRule.value);
          if (curResult) {
            globalError[target] = curResult;
            errorMsg +=  curResult.object + ':  '+curResult.message+'\n' ;
          }
        }
      });

      if (!$.isEmptyObject(globalError) && this.displayMode == 'edit'){
        this.swal({
          title : 'Rule error',
          text : errorMsg,
          type:'error',
          showCancelButton: false,
          confirmButtonColor:'#DD6B55',
          confirmButtonText:'Ok'});
      }
    },

  });
});