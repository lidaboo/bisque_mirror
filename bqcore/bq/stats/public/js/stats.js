/*******************************************************************************
  stats.js - data accessor and plotter for Bisque Statistics Service
  <http://www.bioimage.ucsb.edu/downloads/Bisque%20Database>

  @author Dmitry Fedorov  <fedorov@ece.ucsb.edu>   
  
  Copyright (c) 2011 Dmitry Fedorov, Center for Bio-Image Informatics
  
  ver: 1.0 - ExtJS3  
  ver: 2.0 - Update to ExtJS4

Usage:

  The most basic way is by creating a visualizer:
    var visualizer = new BQStatisticsVisualizer( plotter, url, xpath, xmap, xreduce, { 'height':500 } );
  where:
    plotter - dom element or it's id where visualizer will be created
    url - is the url of the Bisque resource you want to summarize
    xpath, xmap and xreduce - are either vectors or just strings of respective statistics service commands.
                              if they are vectors, you will do and receive multiple outputs, 
                              if the vectors are not of equal sizes they will get padded by the last value.
                              Note: see expanation about xpath, xmap and xreduce in the end of this header.
    options - the last dictionary is the options dictionary, available configs are presented in the "options" 
              section to follow
  
  You may want to get data first and visualize it yourself, in this case use:
    var accessor = new BQStatisticsAccessor( url, xpath, xmap, xreduce, 
                                             { 'ondone': callback(this, "onDone"), 'onerror': callback(this, "onError") } );  
    

Options:
  
  title  - optional parameter to define the title
  width  - optional parameter to control the width of the main panel, default is '100%'
  height - optional parameter to control the height of the main panel, default is 500
  
  grid - if set to false then no grid will be displayed, default is true
  plot - if set to false then no plot will be displayed, default is true
  
  width_plot - optional parameter to control the width of the plot panel, default is '65%'
  width_grid - optional parameter to control the width of the grid panel, default is '35%'
  
  plot_margin_top    - optional parameter to control the margin of the plot in teh panel, default is 30
  plot_margin_lelf   - optional parameter to control the margin of the plot in teh panel, default is 60
  plot_margin_bottom - optional parameter to control the margin of the plot in teh panel, default is 30
  plot_margin_righ   - optional parameter to control the margin of the plot in teh panel, default is 30

  args - dictionary of arguments passed directly to the statistics service, ex: args: {numbins: 25}

Statistics service:

 The idea for the statistics service is in the sequence of filter applied to the data
 URL specifies the documents URL, which can be: gobjects, tags or dataset
 1) QUERY: [etree -> vector of objects]
    Elements are extracted from the document into the vector using XPath expression
    at this stage the vector should only comntain:
        a) tags (where values could be either numeric or string), 
        b) primitive gobjects (only graphical elements like poits and polygones...)
        c) numerics as a result of operation in XPath
 2) MAP: [vector of objects -> uniform vector of numbers or strings]
    An operator is applied onto the vector of objects to produce a vector of numbers or strings
    The operator is specified by the user and can take specific elements and produces specific result
    for example: operator "area" could take polygon or rect and produce a number
                 operator "numeric-value" can take a "tag" and return tag's value as a number
                 possible operator functions should be extensible and maintained by the stat service
 3) REDUCE: [uniform vector of numbers or strings -> summary as XML]
    A summarizer function is applied to the vector of objects to produce some summary
    the summary is returned as an XML document
    for example: summary "vector" could simply pass the input vector for output
                 summary "histogram" could bin the values of the input vector and could work on both text and numbers 
                 summary "max" would return max value of the input vector

*******************************************************************************/

Ext.require([
    'Ext.grid.*',
    'Ext.data.*',
    'Ext.util.*',
    'Ext.state.*'
]);

STAT_VECTOR_TAGS = { 'vector':0, 'unique':0, 'set':0, 'histogram':0, 'bin_centroids':0, 'vector-sorted':0, 'unique-sorted':0, 'set-sorted':0 };

//------------------------------------------------------------------------------
// Utils
//------------------------------------------------------------------------------

function showHourGlass(surface, text) {
  surface.style.height = '140px';
  //surface.innerHTML = '<img src="/static/stats/images/progress_128.gif">';
  if (!text) text = 'Fetching data';
  var p = new BQProgressBar( surface, text );
}

function allNumbers(v) {
  for (var i=0; i<v.length; ++i) {
    if (typeof v[i] == 'number' && isFinite(v[i]) ) continue;
    f = parseFloat(v[i]);
    if (typeof f == 'number' && isFinite(f)) continue;
    return false;    
  }
  return true;
}

function splitUrl(u) {
  var r = {}
  var l = u.split('?', 2);
  if (l.length>1) {
    r.path = l[0];
    r.attrs = l[1];
  } else {
    r.attrs = l[0];    
  }
  
  var atts = r.attrs.split('&');
  r.attrs = {};
  for (var i=0; i<atts.length; i++) {
    var a = atts[i].split('=');
    if (a.length<2) continue;
    r.attrs[decodeURIComponent(a[0])] = decodeURIComponent(a[1]);
  }
  
  return r;
}

function getUrlArg(basename, arg) {
  if (arg instanceof Array) {
    var s='';
    for (var i=0; i<arg.length; i++) {
      var num = i.toString();
      if (i==0) num = '';
      s += '&'+basename+num+'='+escape(arg[i]);
    }
    return s;
  } else {
    return '&'+basename+'='+escape(arg);
  }
}

function getUrlArgs(d) {
  var s='';
  for (k in d)
    s += '&'+k+'='+escape(d[k]);
  return s;
}

//******************************************************************************
// BQStatisticsVisualizer
//******************************************************************************

function BQStatisticsVisualizer( surface, url, xpath, xmap, xreduce, opts ) {
    
  if (typeof surface == 'string')
    this.surface = document.getElementById(surface);
  else
    this.surface = surface;
  this.surface_plot = this.surface;
  this.surface_grid = this.surface;  
  
  this.url     = url;
  this.xpath   = xpath;
  this.xmap    = xmap;
  this.xreduce = xreduce;    
  this.opts    = opts;

  //if (!('title' in this.opts)) this.opts.title = this.xreduce+' of '+this.xmap+' of '+this.xpath;
  if (!('width' in this.opts)) this.opts.width = '100%';
  if (!('height' in this.opts)) this.opts.height = 500;
  if (!('width_plot' in this.opts)) this.opts.width_plot = '65%';
  if (!('width_grid' in this.opts)) this.opts.width_grid = '35%';
  if (!('grid' in this.opts)) this.opts.grid = true;
  if (!('plot' in this.opts)) this.opts.plot = true;

  //showHourGlass(this.surface); // show hour glass here 
  this.surface.style.height = '140px';
  this.progress = new BQProgressBar( this.surface, 'Fetching data' );  
     
  var aopts = { 'ondone': callback(this, "onDone"), 'onerror': callback(this, "onError") };
  if ('args' in opts) aopts.args = opts['args'];
  this.accessor = new BQStatisticsAccessor( this.url, this.xpath, this.xmap, this.xreduce, aopts );
}

BQStatisticsVisualizer.prototype.onDone = function (results) {
  this.surface.style.height = 'auto';  
  //removeAllChildren(this.surface);
  this.progress.stop();
  
  if (this.opts.plot == false) { this.opts.width_grid = '100%'; this.opts.width_plot = 0; }
  if (this.opts.grid == false) { this.opts.width_grid = 0; this.opts.width_plot = '100%'; } 
  var viewport_items = [];
  
  // center plot panel has to exist for the layout to work correctly
  //if (this.opts.plot == true) {
    //this.plotPanel = new Ext.Panel({
    this.plotPanel = Ext.create('Ext.panel.Panel', {
      region:'center',
      split:true,
      //border: false,
      layout: 'fit',
      width: this.opts.width_plot
    });
    viewport_items.push(this.plotPanel);
  //}

  if (this.opts.grid == true) {
    //this.gridPanel = new Ext.Panel({
    this.gridPanel = Ext.create('Ext.panel.Panel', {
      region:'west',
      split:true, 
      collapsible: true,
      //border: false,
      //layout: 'fit',
      layout:'accordion',
      width: this.opts.width_grid
    });
    viewport_items.push(this.gridPanel);
  }
    
  //this.viewport = new Ext.Panel({
  this.viewport = Ext.create('Ext.panel.Panel', {
    renderTo: this.surface,
    layout:'border',
    border: false,
    items:viewport_items,
    width: this.opts.width, height: this.opts.height
  });  
 

  if (this.opts.plot == true) {
    //TODO: find first vector type to be plotted
    if (!('title' in this.opts)) this.opts.title = results[0].xreduce +' of '+ results[0].xmap;    
    this.plotter = BQPlotterFactory.make( this.plotPanel.body.dom, results[0].xreduce, results, this.opts );
  }
  
  // create tables and plots here
  if (this.opts.grid == true) {
    this.grids = [];
    for (var i=0; i<results.length; i++) {
      if (!('titles' in this.opts)) 
        this.opts.title = results[i].xreduce +' of '+ results[i].xmap +' for '+  results[i].xpath;
      else
        this.opts.title = this.opts.titles[i];
      this.grids[i] = BQGridFactory.make( this.gridPanel, results[i].xreduce, results[i], this.opts ); 
    }  
  }

}

BQStatisticsVisualizer.prototype.onError = function (e) {
  this.surface.style.height = 'auto';
  //removeAllChildren(this.surface);
  this.progress.stop();
  this.surface.innerHTML = e.message;  
}

//------------------------------------------------------------------------------
// BQStatisticsAccessor
//------------------------------------------------------------------------------

function BQStatisticsAccessor( url, xpath, xmap, xreduce, opts ) {
  this.url     = url;
  this.xpath   = xpath;
  this.xmap    = xmap;
  this.xreduce = xreduce;   
  this.args    = {}; // additional arguments to pass to statistics service
  if ('args' in opts) this.args = opts['args'];
  
  if (opts['ondone']) this.ondone = opts['ondone'];
  if (opts['onerror']) this.onerror = opts['onerror'];  
 
  this.fetch();
}

BQStatisticsAccessor.prototype.fetch = function () {    
  //escape, encodeURI and encodeURIComponent
  var stat_url = '/stats/compute';
  stat_url += '?url='+encodeURIComponent(this.url);
  stat_url += getUrlArg('xpath', this.xpath);
  stat_url += getUrlArg('xmap', this.xmap);
  stat_url += getUrlArg('xreduce', this.xreduce);
  stat_url += getUrlArgs(this.args);
  BQFactory.request( { uri: stat_url, cb: callback(this, "onLoad"), errorcb: callback(this, "onError") } );  
}

BQStatisticsAccessor.prototype.onLoad = function (stats) {
  this.results = [];
  
  // retrieve all the tags available as a result
  for (var c=0; c<stats.children.length; c++) {  
    var resource = stats.children[c];
    if (resource.xmltag != 'resource') continue;
    var tags = resource.tags;
    var result = {};
    result.uri = resource.uri;
    var u = splitUrl(result.uri);
    result.xpath   = u.attrs.xpath;
    result.xmap    = u.attrs.xmap;
    result.xreduce = u.attrs.xreduce;
    
    for (var i=0; i<tags.length; i++) {
        if (tags[i] == null) continue;
        var val_str = tags[i].value;
        if (val_str == null || val_str == '')
          val_str = tags[i].values[0].value;
        result[tags[i].name] = val_str;
    }
    
    // turn all vector tags into arrays
    for (var k in result) {
      if (k in STAT_VECTOR_TAGS) {
        result[k] = result[k].split(',');
        for (var i=0; i<result[k].length; i++)
          result[k][i] = decodeURIComponent(result[k][i]);
      }
    }
    
    this.results.push(result);
  }

  //this.results.stats = stats;  
  if (this.ondone) this.ondone(this.results);
}

BQStatisticsAccessor.prototype.onError = function (str) {
  if (this.onerror) this.onerror(str);
}

//------------------------------------------------------------------------------
// BQPlotterFactory
//------------------------------------------------------------------------------

function BQPlotterFactory (){}
BQPlotterFactory.ctormap = { vector          : BQLinePlotter,
                             'vector-sorted' : BQLinePlotter,
                             unique          : BQLinePlotter,
                             'unique-sorted' : BQLinePlotter,
                             set             : BQLinePlotter,
                             'set-sorted'    : BQLinePlotter,
                             histogram       : BQHistogramPlotter,
};

BQPlotterFactory.make = function(surface, xreduce, results, opts) {
    var ctor = BQPlotter;
    if (xreduce in BQPlotterFactory.ctormap) 
        ctor = BQPlotterFactory.ctormap[xreduce];
    return new ctor(surface, xreduce, results, opts);
}

//------------------------------------------------------------------------------
// BQPlotter
//------------------------------------------------------------------------------

function BQPlotter( surface, xreduce, results, opts ) {
  this.init(surface, xreduce, results, opts);    
}

BQPlotter.prototype.init = function (surface, xreduce, results, opts) {    
  if (!surface) return;
  this.surface = surface;
  this.xreduce = xreduce;    
  this.results = results;
  if (opts) 
    this.opts = opts;
  else  
    this.opts = {};
  
  if (!('plot_margin_top' in this.opts)) this.opts.plot_margin_top=30;
  if (!('plot_margin_lelf' in this.opts)) this.opts.plot_margin_lelf=60;
  if (!('plot_margin_bottom' in this.opts)) this.opts.plot_margin_bottom=30;
  if (!('plot_margin_righ' in this.opts)) this.opts.plot_margin_righ=30;
    
  this.plotter = { x: this.opts.plot_margin_lelf, y: this.opts.plot_margin_top };
  this.plotter.w = this.surface.clientWidth - (this.plotter.x+this.opts.plot_margin_bottom);
  this.plotter.h = this.surface.clientHeight - (this.plotter.y+this.opts.plot_margin_righ);  
  
  this.plot();
}

BQPlotter.prototype.plot = function () {    

}

//------------------------------------------------------------------------------
// BQLinePlotter
//------------------------------------------------------------------------------

function BQLinePlotter( surface, xreduce, results, opts ) {
  this.init(surface, xreduce, results, opts);    
}
BQLinePlotter.prototype = new BQPlotter();
BQLinePlotter.SMALL_PLOT_SIZE = 100;

BQLinePlotter.prototype.plot = function () {    
  removeAllChildren(this.surface);  
  this.draw(this.results);   
}

BQLinePlotter.prototype.draw = function (results) {
  // prepare data
  var y = [];  
  var N = 0; 
  var mytitles = [];       
  if ('titles' in this.opts) mytitles = this.opts.titles;
  
  for (var i=0; i<results.length; i++) {
    if (!(this.xreduce in results[i])) continue;
    var v = results[i][this.xreduce];
    if (!allNumbers(v)) continue;
  
    y[i] = v;
    N = Math.max(N, v.length);
    if (!('titles' in this.opts)) mytitles[i] = results[i].xpath;      
  }
  if (y.length<=0) return;
  var x = [];
  for (var i=0; i<N; i++) x[i] = i;
   
  // plot   
  var r = Raphael(this.surface, this.surface.clientWidth, this.surface.clientHeight);
  //c.push( "rgb(0,0,"+ (Math.random()*80)+50 +"%)" );   
  
  var title_height = 0;
  if (this.opts.title && this.opts.title!='') {
    r.g.txtattr.font = "18px 'Fontin Sans', Fontin-Sans, sans-serif";    
    r.g.text(this.surface.clientWidth/2, this.plotter.y, this.opts.title).attr({fill: '#003399'});     
    title_height = 25;
  }

  var fin  = function () { 
    r.g.txtattr.font = "11px 'Fontin Sans', Fontin-Sans, sans-serif";  
    this.flag = r.g.popup(this.x, this.y, this.value+'\nfor\n'+this.title).insertBefore(this); 
  };
  var fout = function () { this.flag.animate({opacity: 0}, 300, function () {this.remove();}); };
 
  if (N>BQLinePlotter.SMALL_PLOT_SIZE) {
    // if vector is large
    var opts = { shade: false, axis: "0 0 1 1", nostroke: false, titles: mytitles };    
    r.g.linechart(this.plotter.x, this.plotter.y+title_height, this.plotter.w, this.plotter.h-title_height, x, y, opts ).hover(fin, fout);
  } else {
    // if vector is small, show vertices and hover values
    var opts = { shade: false, axis: "0 0 1 1", nostroke: false, titles: mytitles, symbol: "o", smooth: true };
    var line = r.g.linechart(this.plotter.x, this.plotter.y+title_height, this.plotter.w, this.plotter.h-title_height, x, y, opts).hover(fin, fout);
    line.symbols.attr({r: 3});
  }
}

//------------------------------------------------------------------------------
// BQHistogramPlotter
//------------------------------------------------------------------------------

function BQHistogramPlotter( surface, xreduce, results, opts ) {
  this.init(surface, xreduce, results, opts);    
}
BQHistogramPlotter.prototype = new BQPlotter();

BQHistogramPlotter.prototype.plot = function () {    
  removeAllChildren(this.surface);
  this.draw(this.results);   
}

BQHistogramPlotter.prototype.draw = function (results) {
  // prepare data  
  var x = [];
  var mytitles = []; 
  if ('titles' in this.opts) mytitles = this.opts.titles;  
   
  for (var i=0; i<results.length; i++) {
    if (!(this.xreduce in results[i])) continue;
    var v = results[i][this.xreduce];
    if (!allNumbers(v)) continue;
    x[i] = v;
    
    var titles = [];
    var b = results[i]['bin_centroids'];
    for (var j in v) titles[j] = b[j] +': '+ v[j] +'\nfor\n'+  results[i].xpath;  
      
    if (!('titles' in this.opts)) mytitles[i] = titles;
  }
  if (x.length<=0) return;

  // plot  
  var r = Raphael(this.surface, this.surface.clientWidth, this.surface.clientHeight);
 
  var title_height = 0;
  if (this.opts.title && this.opts.title!='') {
    r.g.txtattr.font = "18px 'Fontin Sans', Fontin-Sans, sans-serif";              
    r.g.text(this.surface.clientWidth/2, this.plotter.y, this.opts.title).attr({fill: '#003399'});     
    title_height = 25;
  }
  
  //, stacked: true  
  var opts = {gutter: "0%", titles: mytitles } ;
  fin  = function () { 
    r.g.txtattr.font = "11px 'Fontin Sans', Fontin-Sans, sans-serif";  
    this.flag = r.g.popup(this.bar.x, this.bar.y, this.bar.title).insertBefore(this); 
  };
  fout = function () { this.flag.animate({opacity: 0}, 300, function () {this.remove();}); };  
  r.g.barchart(this.plotter.x, this.plotter.y+title_height, this.plotter.w, this.plotter.h-title_height, x, opts).hover(fin, fout);
}


//******************************************************************************
// BQGridFactory
//******************************************************************************

function BQGridFactory (){}
BQGridFactory.ctormap = { vector          : BQVectorGrid,
                          'vector-sorted' : BQVectorGrid,
                          unique          : BQVectorGrid,
                          'unique-sorted' : BQVectorGrid,                          
                          set             : BQVectorGrid,
                          'set-sorted'    : BQVectorGrid,                          
                          histogram       : BQHistogramGrid,
};

BQGridFactory.make = function(surface, xreduce, results, opts) {
    var ctor = BQGrid;
    if (xreduce in BQGridFactory.ctormap) 
        ctor = BQGridFactory.ctormap[xreduce];
    return new ctor(surface, xreduce, results, opts);
}

//------------------------------------------------------------------------------
// BQGrid
//------------------------------------------------------------------------------

function BQGrid( surface, xreduce, results, opts ) {
  this.init(surface, xreduce, results, opts);    
}

BQGrid.prototype.init = function (surface, xreduce, results, opts) {    
  this.surface = surface;
  this.xreduce = xreduce;    
  this.results = results;
  this.opts = opts;  
  this.store = this.createStore();
  this.grid = this.createGrid();  
}

BQGrid.prototype.createStore = function () {  
    if (!this.xreduce) return;
    if (!this.xreduce in this.results) return;    
  
    var mydata = [
        [this.xreduce, this.results[this.xreduce]]
    ];

    /*
    // ExtJS3
    this.store = new Ext.data.ArrayStore({
        fields: [
           {name: 'name', title: 'Name'},
           {name: 'value', title: 'Value'}, 
        ]
    });
    this.store.loadData(mydata);
    */
    
    // ExtJS4    
    var myfields = [
           {name: 'name', title: 'Name'},
           {name: 'value', title: 'Value'}, 
        ];
    
    this.store = Ext.create('Ext.data.ArrayStore', {
        fields: myfields,        
        data: mydata
    });
    this.store.bqfields = myfields;    
    
    
    return this.store;
}

BQGrid.prototype.createGrid = function () {  
    if (!this.store) return;  
    if (!this.xreduce) return;
    if (!this.xreduce in this.results) return;    
    var store = this.store;
    
    Ext.QuickTips.init();
    Ext.state.Manager.setProvider(Ext.create('Ext.state.CookieProvider'));

    /*
    // ExtJS3
    Ext.state.Manager.setProvider(new Ext.state.CookieProvider());    
    this.grid = new Ext.grid.GridPanel({
        store: store,
        columns: [
            {
                id       : store.fields.items[0].name,
                header   : store.fields.items[0].title, 
                sortable : true, 
                dataIndex: store.fields.items[0].name
            },
            {
                header   : store.fields.items[1].title, 
                sortable : true, 
                dataIndex: store.fields.items[1].name
            },

        ],
        stripeRows: true,
        autoExpandColumn: store.fields.items[0].name,
        title: this.opts.title ? this.opts.title : this.xreduce,
        // config options for stateful behavior
        stateful: true,
        stateId: 'grid'
    });
    */
    
    // ExtJS4 
    var myfields = store.bqfields;
    var mytitle = this.opts.title ? this.opts.title : this.xreduce;
    this.grid = Ext.create('Ext.grid.Panel', {
        store: store,
        columnLines: true,
        title: mytitle,
        viewConfig: { stripeRows: true },    
        
        columns: [
            {
                text     : myfields[0].title,
                sortable : true, 
                dataIndex: myfields[0].name
            },
            {
                text     : myfields[1].title, 
                flex     : 1,                
                sortable : true, 
                dataIndex: myfields[1].name
            },              
            
        ],
    });    
    
    this.surface.insert(this.surface.items.length, this.grid);
    this.surface.doLayout(false);      
    return this.grid;
}


//------------------------------------------------------------------------------
// BQVectorGrid
//------------------------------------------------------------------------------

function BQVectorGrid( surface, xreduce, results, opts ) {
  this.init(surface, xreduce, results, opts);    
}
BQVectorGrid.prototype = new BQGrid();

BQVectorGrid.prototype.createStore = function () {  
    if (!this.xreduce) return;
    if (!this.xreduce in this.results) return;    
  
    var mydata = [];
    for (var i in this.results[this.xreduce]) {
      mydata[i] = [i, this.results[this.xreduce][i]];
    }
    var data_type = 'auto'; // auto string int float boolean date
    if (!isNaN(this.results[this.xreduce][0])) 
      data_type = 'float';
    
    /*
    // ExtJS3
    this.store = new Ext.data.ArrayStore({
        fields: [
           {name: 'index', title: 'Index', type: 'int' },
           {name: 'value', title: 'Value', type: data_type }, 
        ]
    });
    this.store.loadData(mydata);
    */

    // ExtJS4    
    var myfields = [
           {name: 'index', title: 'Index', type: 'int' },
           {name: 'value', title: 'Value', type: data_type }, 
        ];
    
    this.store = Ext.create('Ext.data.ArrayStore', {
        fields: myfields,        
        data: mydata
    });
    this.store.bqfields = myfields;
    
    return this.store;
}

//------------------------------------------------------------------------------
// BQHistogramGrid
//------------------------------------------------------------------------------

function BQHistogramGrid( surface, xreduce, results, opts ) {
  this.init(surface, xreduce, results, opts);    
}
BQHistogramGrid.prototype = new BQGrid();

BQHistogramGrid.prototype.createStore = function () {  
    if (!this.xreduce) return;
    if (!this.xreduce in this.results) return;    
  
    var mydata = [];
    for (var i in this.results[this.xreduce]) {
      mydata[i] = [this.results['bin_centroids'][i], this.results[this.xreduce][i]];
    }
    var data_type = 'auto'; // auto string int float boolean date
    if (!isNaN(this.results['bin_centroids'][0])) 
      data_type = 'float';

    /*
    // ExtJS3
    this.store = new Ext.data.ArrayStore({
        fields: [
           {name: 'centroid', title: 'Centroid', type: data_type},
           {name: 'frequency', title: 'Frequency', type: 'int'}, 
        ]
    });
    this.store.loadData(mydata);
    */
    
    // ExtJS4    
    var myfields = [
           {name: 'centroid', title: 'Centroid', type: data_type},
           {name: 'frequency', title: 'Frequency', type: 'int'}, 
        ];
    
    this.store = Ext.create('Ext.data.ArrayStore', {
        fields: myfields,        
        data: mydata
    });
    this.store.bqfields = myfields;    
    
    return this.store;
}



//******************************************************************************
// BQ.stats.plotter.Factory - ExtJS4 rewrite of BQPlotterFactory
//******************************************************************************

Ext.namespace('BQ.stats.plotter.Factory');

BQ.stats.plotter.Factory.ctormap = { vector          : 'BQ.stats.plotter.Line',
                                     'vector-sorted' : 'BQ.stats.plotter.Line',
                                     unique          : 'BQ.stats.plotter.Line',
                                     'unique-sorted' : 'BQ.stats.plotter.Line',                          
                                     set             : 'BQ.stats.plotter.Line',
                                     'set-sorted'    : 'BQ.stats.plotter.Line',                          
                                     histogram       : 'BQ.stats.plotter.Histogram',
};

BQ.stats.plotter.Factory.make = function(xreduce, results, opts) {
    var ctor = 'BQ.stats.plotter.Plotter';
    if (xreduce in BQ.stats.plotter.Factory.ctormap) 
        ctor = BQ.stats.plotter.Factory.ctormap[xreduce];
    
    return Ext.create(ctor, { 
        xreduce: xreduce, 
        results: results, 
        opts: opts,
        flex: 1,
    });
}

//------------------------------------------------------------------------------
// BQ.stats.plotter.Plotter
//------------------------------------------------------------------------------

Ext.define('BQ.stats.plotter.Plotter', {
    alias: 'widget.statsplotter',    
    extend: 'Ext.panel.Panel', // extend: 'Ext.container.Container', // dima - apparently requires Panel
    //requires: ['Ext.grid.Panel'],    
    
    // required inputs
    xreduce : undefined,
    results : undefined,
    opts    : undefined,

    // configs
    layout: 'fit',
    
    initComponent : function() {
        this.opts = this.opts || {};      
        this.callParent();
        this.createStore();
    },      
    
    afterRender : function() {
        this.plot();
    },    
    
    createStore: function () {
        if (!this.xreduce) return;
        if (!this.xreduce in this.results) return;    
        
        var mydata = [
            [this.xreduce, this.results[this.xreduce]]
        ];
        
        var myfields = [
               {name: 'name', title: 'Name'},
               {name: 'value', title: 'Value'}, 
            ];
        
        this.store = Ext.create('Ext.data.ArrayStore', {
            fields: myfields,        
            data: mydata
        });
        this.store.bqfields = myfields;    
    },

    plot: function () {

    },    

});



//------------------------------------------------------------------------------
// BQLinePlotter
//------------------------------------------------------------------------------

/*
BQLinePlotter.SMALL_PLOT_SIZE = 100;

BQLinePlotter.prototype.draw = function (results) {
  // prepare data
  var y = [];  
  var N = 0; 
  var mytitles = [];       
  if ('titles' in this.opts) mytitles = this.opts.titles;
  
  for (var i=0; i<results.length; i++) {
    if (!(this.xreduce in results[i])) continue;
    var v = results[i][this.xreduce];
    if (!allNumbers(v)) continue;
  
    y[i] = v;
    N = Math.max(N, v.length);
    if (!('titles' in this.opts)) mytitles[i] = results[i].xpath;      
  }
  if (y.length<=0) return;
  var x = [];
  for (var i=0; i<N; i++) x[i] = i;
   
  // plot   
  var r = Raphael(this.surface, this.surface.clientWidth, this.surface.clientHeight);
  //c.push( "rgb(0,0,"+ (Math.random()*80)+50 +"%)" );   
  
  var title_height = 0;
  if (this.opts.title && this.opts.title!='') {
    r.g.txtattr.font = "18px 'Fontin Sans', Fontin-Sans, sans-serif";    
    r.g.text(this.surface.clientWidth/2, this.plotter.y, this.opts.title).attr({fill: '#003399'});     
    title_height = 25;
  }

  var fin  = function () { 
    r.g.txtattr.font = "11px 'Fontin Sans', Fontin-Sans, sans-serif";  
    this.flag = r.g.popup(this.x, this.y, this.value+'\nfor\n'+this.title).insertBefore(this); 
  };
  var fout = function () { this.flag.animate({opacity: 0}, 300, function () {this.remove();}); };
 
  if (N>BQLinePlotter.SMALL_PLOT_SIZE) {
    // if vector is large
    var opts = { shade: false, axis: "0 0 1 1", nostroke: false, titles: mytitles };    
    r.g.linechart(this.plotter.x, this.plotter.y+title_height, this.plotter.w, this.plotter.h-title_height, x, y, opts ).hover(fin, fout);
  } else {
    // if vector is small, show vertices and hover values
    var opts = { shade: false, axis: "0 0 1 1", nostroke: false, titles: mytitles, symbol: "o", smooth: true };
    var line = r.g.linechart(this.plotter.x, this.plotter.y+title_height, this.plotter.w, this.plotter.h-title_height, x, y, opts).hover(fin, fout);
    line.symbols.attr({r: 3});
  }
}

//------------------------------------------------------------------------------
// BQHistogramPlotter
//------------------------------------------------------------------------------

BQHistogramPlotter.prototype.draw = function (results) {
  // prepare data  
  var x = [];
  var mytitles = []; 
  if ('titles' in this.opts) mytitles = this.opts.titles;  
   
  for (var i=0; i<results.length; i++) {
    if (!(this.xreduce in results[i])) continue;
    var v = results[i][this.xreduce];
    if (!allNumbers(v)) continue;
    x[i] = v;
    
    var titles = [];
    var b = results[i]['bin_centroids'];
    for (var j in v) titles[j] = b[j] +': '+ v[j] +'\nfor\n'+  results[i].xpath;  
      
    if (!('titles' in this.opts)) mytitles[i] = titles;
  }
  if (x.length<=0) return;

  // plot  
  var r = Raphael(this.surface, this.surface.clientWidth, this.surface.clientHeight);
 
  var title_height = 0;
  if (this.opts.title && this.opts.title!='') {
    r.g.txtattr.font = "18px 'Fontin Sans', Fontin-Sans, sans-serif";              
    r.g.text(this.surface.clientWidth/2, this.plotter.y, this.opts.title).attr({fill: '#003399'});     
    title_height = 25;
  }
  
  //, stacked: true  
  var opts = {gutter: "0%", titles: mytitles } ;
  fin  = function () { 
    r.g.txtattr.font = "11px 'Fontin Sans', Fontin-Sans, sans-serif";  
    this.flag = r.g.popup(this.bar.x, this.bar.y, this.bar.title).insertBefore(this); 
  };
  fout = function () { this.flag.animate({opacity: 0}, 300, function () {this.remove();}); };  
  r.g.barchart(this.plotter.x, this.plotter.y+title_height, this.plotter.w, this.plotter.h-title_height, x, opts).hover(fin, fout);
}


*/





//******************************************************************************
// BQ.stats.grid.Factory - ExtJS4 rewrite of BQGridFactory
//******************************************************************************

Ext.namespace('BQ.stats.grid.Factory');

BQ.stats.grid.Factory.ctormap = { vector          : 'BQ.stats.grid.Vector',
                                  'vector-sorted' : 'BQ.stats.grid.Vector',
                                  unique          : 'BQ.stats.grid.Vector',
                                  'unique-sorted' : 'BQ.stats.grid.Vector',                          
                                  set             : 'BQ.stats.grid.Vector',
                                  'set-sorted'    : 'BQ.stats.grid.Vector',                          
                                  histogram       : 'BQ.stats.grid.Histogram',
};

BQ.stats.grid.Factory.make = function(xreduce, results, opts) {
    var ctor = 'BQ.stats.grid.Grid';
    if (xreduce in BQ.stats.grid.Factory.ctormap) 
        ctor = BQ.stats.grid.Factory.ctormap[xreduce];
    
    return Ext.create(ctor, { 
        xreduce: xreduce, 
        results: results, 
        opts: opts,
        flex: 1,
    });
}

//------------------------------------------------------------------------------
// BQ.stats.grid.Grid
//------------------------------------------------------------------------------

Ext.define('BQ.stats.grid.Grid', {
    alias: 'widget.statsgrid',    
    extend: 'Ext.panel.Panel', // extend: 'Ext.container.Container', // dima - apparently requires Panel
    requires: ['Ext.grid.Panel'],    
    
    // required inputs
    xreduce : undefined,
    results : undefined,
    opts    : undefined,

    // configs
    layout: 'fit',
    
    initComponent : function() {
        this.callParent();
        this.createStore();
    },    
    
    afterRender : function() {
        this.createGrid();
    },    
    
    createStore: function () {
        if (!this.xreduce) return;
        if (!this.xreduce in this.results) return;    
        
        var mydata = [
            [this.xreduce, this.results[this.xreduce]]
        ];
        
        var myfields = [
               {name: 'name', title: 'Name'},
               {name: 'value', title: 'Value'}, 
            ];
        
        this.store = Ext.create('Ext.data.ArrayStore', {
            fields: myfields,        
            data: mydata
        });
        this.store.bqfields = myfields;    
    },    

    createGrid: function () {
        if (!this.store) return;  
        if (!this.xreduce) return;
        if (!this.xreduce in this.results) return;    
        var store = this.store;

        var mytitle = this.opts.title ? this.opts.title : this.xreduce;
        this.setTitle(mytitle);
        
        Ext.QuickTips.init();
        Ext.state.Manager.setProvider(Ext.create('Ext.state.CookieProvider'));
    
        var myfields = store.bqfields;
        this.grid = Ext.create('Ext.grid.Panel', {
            store: store,
            columnLines: true,
            border: 0,
            //title: mytitle,
            viewConfig: { stripeRows: true },    
            
            columns: [
                {
                    text     : myfields[0].title,
                    sortable : true, 
                    dataIndex: myfields[0].name
                },
                {
                    text     : myfields[1].title, 
                    flex     : 1,                
                    sortable : true, 
                    dataIndex: myfields[1].name
                },              
                
            ],
        });    
        this.add(this.grid);
    },

});

//------------------------------------------------------------------------------
// BQ.stats.grid.Vector
//------------------------------------------------------------------------------

Ext.define('BQ.stats.grid.Vector', {
    alias: 'widget.statsgridvector',    
    extend: 'BQ.stats.grid.Grid',
 
    createStore: function () {
        if (!this.xreduce) return;
        if (!this.xreduce in this.results) return;    
      
        var mydata = [];
        for (var i in this.results[this.xreduce]) {
          mydata[i] = [i, this.results[this.xreduce][i]];
        }
        var data_type = 'auto'; // auto string int float boolean date
        if (!isNaN(this.results[this.xreduce][0])) 
          data_type = 'float';
        
        var myfields = [
               {name: 'index', title: 'Index', type: 'int' },
               {name: 'value', title: 'Value', type: data_type }, 
            ];
        
        this.store = Ext.create('Ext.data.ArrayStore', {
            fields: myfields,        
            data: mydata
        });
        this.store.bqfields = myfields;
    },    

});

//------------------------------------------------------------------------------
// BQ.stats.grid.Histogram
//------------------------------------------------------------------------------

Ext.define('BQ.stats.grid.Histogram', {
    alias: 'widget.statsgridvector',    
    extend: 'BQ.stats.grid.Grid',
 
    createStore: function () {
        if (!this.xreduce) return;
        if (!this.xreduce in this.results) return;    
      
        var mydata = [];
        for (var i in this.results[this.xreduce]) {
          mydata[i] = [this.results['bin_centroids'][i], this.results[this.xreduce][i]];
        }
        var data_type = 'auto'; // auto string int float boolean date
        if (!isNaN(this.results['bin_centroids'][0])) 
          data_type = 'float';

        var myfields = [
               {name: 'centroid', title: 'Centroid', type: data_type},
               {name: 'frequency', title: 'Frequency', type: 'int'}, 
            ];
        
        this.store = Ext.create('Ext.data.ArrayStore', {
            fields: myfields,        
            data: mydata
        });
        this.store.bqfields = myfields;    
    },    

});

//******************************************************************************
// BQ.stats.Visualizer - ExtJS4 rewrite of BQStatisticsVisualizer
//******************************************************************************

Ext.define('BQ.stats.Visualizer', {
    alias: 'widget.statsvisualizer',    
    extend: 'Ext.panel.Panel', // extend: 'Ext.container.Container',
    //requires: ['BQ.viewer.Image'],    
    
    // required inputs
    url     : undefined,
    xpath   : undefined,
    xmap    : undefined,
    xreduce : undefined,
    opts    : undefined,
    
    // configs    
    //cls: 'selector',
    border: 0,
    layout: 'border',
    defaults: {
        collapsible: true,
        split: true,
        //border: false,
    },
    
    //defaults: { border: 0, xtype: 'container', },
    /*
    constructor: function(config) {
        this.addEvents({
            'changed'   : true,
        });
        this.callParent(arguments);
        return this;
    },*/

    initComponent : function() {
        this.opts = this.opts || {};      
        if (!('grid' in this.opts)) this.opts.grid = true;
        if (!('plot' in this.opts)) this.opts.plot = true; 
        
        this.items = [];
        if (this.opts.grid == true) {
            this.gridPanel = Ext.create('Ext.panel.Panel', {
                region: 'west',
                width: '35%',          
                layout: 'accordion',
                defaults: { border: 0, },
            });
            this.items.push(this.gridPanel);
        }        
        
        // center plot panel has to exist for the layout to work correctly
        this.plotPanel = Ext.create('Ext.panel.Panel', {
            collapsible: false,
            region: 'center',
            flex: 1,
            //layout: 'fit',
        });
        this.items.push(this.plotPanel);        
        
        this.callParent();
    },
    
    afterRender : function() {
        //this.callParent();
        this.setLoading('Fetching data');
        var opts = { 'ondone': callback(this, 'ondone'), 'onerror': callback(this, 'onerror') };
        if ('args' in opts) opts.args = this.opts.args;
        this.accessor = new BQStatisticsAccessor( this.url, this.xpath, this.xmap, this.xreduce, opts );        
    },    
    
    onerror: function (e) {
        this.setLoading(false);
        BQ.ui.error(e.message);  
    },    

    ondone: function (results) {
        this.setLoading(false);
        
        if (this.opts.plot == true) {
            //TODO: find first vector type to be plotted
            if (!('title' in this.opts)) this.opts.title = results[0].xreduce +' of '+ results[0].xmap;    
            this.plotter = BQPlotterFactory.make( this.plotPanel.el.dom, results[0].xreduce, results, this.opts );
        }        
        
        // create tables and plots here
        if (this.opts.grid == true) {
            this.grids = [];
            for (var i=0; i<results.length; i++) {
                this.opts.title = this.opts.titles ? this.opts.titles[i] :
                    results[i].xreduce +' of '+ results[i].xmap +' for '+  results[i].xpath;
                
                this.grids[i] = BQ.stats.grid.Factory.make(results[i].xreduce, results[i], this.opts);
                this.gridPanel.add(this.grids[i]);
            }  
        }
    },

});

//--------------------------------------------------------------------------------------
// BQ.upload.Dialog
// Instantiates upload panel in a modal window
//-------------------------------------------------------------------------------------- 

Ext.define('BQ.stats.Dialog', {
    extend : 'Ext.window.Window',
    alias: 'widget.statsdialog',        
    requires: ['BQ.stats.Visualizer'],
    
    layout : 'fit',
    modal : true,
    border : false,
    width : '85%',
    height : '85%',
    
    constructor : function(config) {

        var conf = { 
            border: 0, 
            //flex: 1, 
        };

        // move the config options that belong to the uploader
        for (var c in config)
            //if (c in BQ.upload.DEFAULTS)
                 conf[c] = config[c];
    
        this.my_panel = Ext.create('BQ.stats.Visualizer', conf);         
        this.items = [this.my_panel];
        
        this.callParent(arguments);
       
        this.show();
        return this;
    },
    
});

