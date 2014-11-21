/*******************************************************************************
  ImgInfoBar - creates text about an image

  GSV 3.0 : PanoJS3
  @author Dmitry Fedorov  <fedorov@ece.ucsb.edu>

  Copyright (c) 2010 Dmitry Fedorov, Center for Bio-Image Informatics

  using: isClientTouch() and isClientPhone() from utils.js

*******************************************************************************/

function ImgInfoBar (viewer,name){
    this.base = ViewerPlugin;
    this.base (viewer, name);
}

ImgInfoBar.prototype = new ViewerPlugin();
ImgInfoBar.prototype.create = function (parent) {
    this.parentdiv = parent;
    this.infobar = null;
    this.namebar = null;
    this.mobile_cls = '';
    if (isClientTouch())
        this.mobile_cls = 'tablet';
    if (isClientPhone())
        this.mobile_cls = 'phone';
    return parent;
};

ImgInfoBar.prototype.newImage = function () {

};

ImgInfoBar.prototype.updateImage = function () {
    // update inforamtion string
    var viewer = this.viewer;
    var view = viewer.current_view;
    var dim = view.imagedim;
    var imgphys = viewer.imagephys;

    // create info bar
    if (!this.infobar) {
      var surf = viewer.viewer_controls_surface ? viewer.viewer_controls_surface : this.parentdiv;
      this.infobar = document.createElement('span');
      this.infobar.className = 'info '+this.mobile_cls;
      surf.appendChild(this.infobar);
    }

    // create name bar
    if (!this.namebar && !(viewer.parameters && viewer.parameters.hide_file_name_osd) ) {
      var surf = this.parentdiv;
      if (viewer.viewer_controls_surface) surf = viewer.viewer_controls_surface;
      this.namebar = document.createElement('a');
      this.namebar.className = 'info name '+this.mobile_cls;
      surf.appendChild(this.namebar);
    }

    // create position bar
    if (!this.posbar) {
      var surf = this.parentdiv;
      if (viewer.viewer_controls_surface) surf = viewer.viewer_controls_surface;
      this.posbar = document.createElement('a');
      this.posbar.className = 'info position '+this.mobile_cls;
      //this.posbar.innerText = '[AAAxAAAA]';
      surf.appendChild(this.posbar);
    }

    if (this.infobar) {
      var s = 'Image: '+dim.x+'x'+dim.y;
      if (dim.z>1) s += ' Z:'+dim.z;
      if (dim.t>1) s += ' T:'+dim.t;
      s += ' ch: '+ dim.ch;
      if (imgphys && imgphys.pixel_depth) s += '/'+ imgphys.pixel_depth +'bits';
      s += ' Scale: '+ view.scale*100 +'%';
      this.infobar.innerHTML = s;
    }

    if (this.namebar) {
      this.namebar.innerHTML = viewer.image.name;
      this.namebar.href = '/client_service/view?resource='+viewer.image.uri;
    }
};

