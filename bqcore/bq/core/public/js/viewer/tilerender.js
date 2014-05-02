
PanoJS.MSG_BEYOND_MIN_ZOOM = null;
PanoJS.MSG_BEYOND_MAX_ZOOM = null;
PanoJS.STATIC_BASE_URL = '/panojs3/';
PanoJS.CREATE_INFO_CONTROLS = false;
PanoJS.CREATE_THUMBNAIL_CONTROLS = true;
PanoJS.USE_KEYBOARD = false;

function TilesRenderer (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.events    = {};
    this.tile_size = 512;
    this.template  = 'tile=0,0,0,'+this.tile_size;
    this.myTileProvider = new PanoJS.TileUrlProvider('','','');
};
TilesRenderer.prototype = new ViewerPlugin();

TilesRenderer.prototype.create = function (parent) {
    this.parent = parent;
    this.div  = document.createElementNS(xhtmlns, "div");
    this.div.id =  'tiled_viewer';
    this.div.className = 'viewer';
    this.div.style.width = '100%';
    this.div.style.height = '100%';
    this.parent.appendChild(this.div);
    return this.div;
};

TilesRenderer.prototype.newImage = function () {

};

TilesRenderer.prototype.updateView = function (view) {
    view.addParams ( this.template ); // add a placeholder for tile request, replaced later by the actual tile request
};

TilesRenderer.prototype.updateImage = function (){
    var viewstate = this.viewer.current_view;
    if (this.cur_t && this.cur_z && this.cur_t==viewstate.t && this.cur_z==viewstate.z) return;
    this.cur_t=viewstate.t; this.cur_z=viewstate.z;

    this.base_url = this.viewer.image_url();

    // update tile provider code
    var myPyramid = this.pyramid = new BisqueISPyramid( viewstate.imagedim.x, viewstate.imagedim.y, this.tile_size);
    var myTemplate = this.template;
    var myURL = this.base_url;

    this.myTileProvider.assembleUrl = function(xIndex, yIndex, zoom) {
        return myURL.replace(myTemplate, myPyramid.tile_filename( zoom, xIndex, yIndex ));
    };

    // create tiled viewer
    if (!this.tiled_viewer) {
      this.tiled_viewer = new PanoJS(this.div, {
          tileUrlProvider : this.myTileProvider,
          tileSize        : myPyramid.tilesize,
          maxZoom         : myPyramid.getMaxLevel(),
          imageWidth      : myPyramid.width,
          imageHeight     : myPyramid.height,
          blankTile       : PanoJS.STATIC_BASE_URL + 'images/blank.gif',
          loadingTile     : PanoJS.STATIC_BASE_URL + 'images/progress_' + this.tile_size+ '.gif'
      });

      // this listner will correctly resize and move SVG element
      this.mySvgListener = new SvgControl( this.tiled_viewer, this.viewer.renderer.svgdoc );
      this.myOverListener = new SvgControl( this.tiled_viewer, this.viewer.renderer.overlay );

      // this listner will update viewer if scale has changed in the tiled viewer
      this.myZoomListener = new ZoomListner(this.tiled_viewer, this.viewer);

      //Ext.EventManager.addListener( window, 'resize', callback(this.tiled_viewer, this.tiled_viewer.resize) );
      this.tiled_viewer.init();
      this.viewer.viewer_controls_surface = this.div;
    } else {
      // only update all the tiles in the viewer
      this.tiled_viewer.tileUrlProvider = this.myTileProvider;
      this.tiled_viewer.update();
    }
};

TilesRenderer.prototype.resize = function () {
    if (this.tiled_viewer)
        this.tiled_viewer.resize();
};

TilesRenderer.prototype.ensureVisible = function (gob) {
    if (!this.tiled_viewer || !gob.vertices || gob.vertices.length<1) return;
    var x = gob.vertices[0].x;
    var y = gob.vertices[0].y;
    var v=undefined;
    if (gob.vertices.length>1 && gob.resource_type in {polyline: undefined, polygon: undefined}) {
        for (var i=1; (v=gob.vertices[i]); i++) {
            x += v.x;
            y += v.y;
        }
        x /= gob.vertices.length;
        y /= gob.vertices.length;
    }
    this.tiled_viewer.ensureVisible({x: x, y: y});
};


