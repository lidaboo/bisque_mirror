
////////////////////////////////////////////////////////////////////
// ImageCache is a convenience object for handling
// a two dimensional array of image objects
// used for caching prerenderered nodes at given frames for
// time, t and depth, z.
////////////////////////////////////////////////////////////////////

function ImageCache(renderer){
    this.renderer = renderer;
    this.init();
};

ImageCache.prototype.init = function(){
    this.caches = {};
    this.nodeHashes = {};
};

ImageCache.prototype.getCurrentNodeHashes = function(node){

    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;
    var bbox = node.bbox;
    var nHash =
        bbox.min[0] + "," + bbox.min[1] + "," + bbox.min[2] + "," +
        bbox.max[0] + "," + bbox.max[1] + "," + bbox.max[2] + "," +
        z + ',' + t;
    var hashes = [];
    for (var key in this.nodeHashes[nHash]) {
        if (this.nodeHashes[nHash].hasOwnProperty(key)) {
            hashes.push(key);
        }
    }
    return hashes;
}

ImageCache.prototype.getCurrentHash = function(node){
    var scale = this.renderer.stage.scale().x;

    var viewstate = this.renderer.viewer.current_view;
    var dim =       this.renderer.viewer.imagedim;
    var sz = dim.z;
    var st = dim.t;
    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;
    var maxLoc = sz*st;
    var loc = z + t*sz;
    var bbox = node.bbox;

    var proj = viewstate.imagedim.project,
    proj_gob = viewstate.gob_projection;



    var pHash = '';
    if (proj_gob==='all' || proj === 'projectmax' || proj === 'projectmin') {
        pHash = 'all';
    } else if (proj === 'projectmaxz' || proj === 'projectminz' || proj_gob==='Z') {
        pHash = 'Z';
    } else if (proj === 'projectmaxt' || proj === 'projectmint' || proj_gob==='T') {
        pHash = 'T';
    }
    var nHash =
        bbox.min[0] + "," + bbox.min[1] + "," + bbox.min[2] + "," +
        bbox.max[0] + "," + bbox.max[1] + "," + bbox.max[2] + "," +
        z + ',' + t;

    var hash = nHash +','+ pHash + ',' + scale;
    if(!this.nodeHashes[nHash]) this.nodeHashes[nHash] = {};

    this.nodeHashes[nHash][hash] = hash;
    return hash;
}

ImageCache.prototype.createAtFrame = function(i){
    this.caches[i] = new Kinetic.Image({});
};

ImageCache.prototype.deleteAtFrame = function(i){

    if(this.caches[i]) {
        delete this.caches[i];
        this.caches[i] = null;
    }
};

ImageCache.prototype.getCacheAtFrame = function(i){
    return this.caches[i];
};

ImageCache.prototype.setPositionAtFrame = function(i, node){
    var
    cache = this.caches[i],
    scale = this.renderer.stage.scale().x,
    bbox = node.bbox,
    w = bbox.max[0] - bbox.min[0];
    h = bbox.max[1] - bbox.min[1];
    buffer = 0;

    cache.x(bbox.min[0] - buffer/scale);
    cache.y(bbox.min[1] - buffer/scale);
    cache.width(w + 2.0*buffer/scale);
    cache.height(h + 2.0*buffer/scale);
};

ImageCache.prototype.setImageAtFrame = function(i, img){
    this.caches[i].setImage(img);
};

ImageCache.prototype.createAtCurrent = function(node){
    var i = this.getCurrentHash(node);
    this.createAtFrame(i);
};

ImageCache.prototype.deleteAtCurrent = function(node){
    var i = this.getCurrentHash(node);
    this.deleteAtFrame(i);
}

ImageCache.prototype.getCacheAtCurrent = function(node){
    var i = this.getCurrentHash(node);
    return this.getCacheAtFrame(i);
}


ImageCache.prototype.setPositionAtCurrent = function(node){
    var i = this.getCurrentHash(node);
    this.setPositionAtFrame(i,node);
}

ImageCache.prototype.setImageAtCurrent = function(img, node){
    var i = this.getCurrentHash(node);
    this.setImageAtFrame(i,img);
}

ImageCache.prototype.clearAll = function(node){
    if(!node){
        delete this.caches;
        delete this.nodeHashes;
        this.init();
        return;
    }

    var nodeHashes = this.getCurrentNodeHashes(node);
    for(var i = 0; i < nodeHashes.length; i++){
        var hash = nodeHashes[i];
        delete this.caches[hash];
    }
}

function QuadTree(renderer, z, t){
    this.z = z;
    this.t = t;

    this.renderer = renderer;
    this.reset();
    this.maxChildren = 256;
    this.imageCache = new ImageCache(renderer);
};

QuadTree.prototype.reset = function(){
    if(this.nodes){
        var collection = [];
        var collectLeaves = function(node){
            if(node.leaves.length > 0){
                collection = collection.concat(node.leaves);
            }
            return true;
        }
        this.traverseDown(this.nodes[0], collectLeaves);

        collection.forEach(function(e){
            e.inTree = false;
        });
    }
    var view = this.renderer.viewer.imagedim;
    if(!view)
        view = {x:0, y:0, z:0, t: 0};

    this.nodes = [{
        id: 0,
        parent: null,
        children:[],
        leaves: [],
        bbox: {min: [0,0,0,0], max: [view.x,view.y,view.z,view.t]},
        L: 0,
    }];

}

QuadTree.prototype.calcBoxVol = function(bb){
    //given two bounding boxes what is the volume
    var d = [0,0,0,0];
    for(var ii = 0; ii < 2; ii++){
        if(bb.max.length > ii)
            d[ii] = bb.max[ii] - bb.min[ii];
        //minimum distance is one unit
        d[ii] = Math.max(d[ii],1);
    }
    var vol = d[0]*d[1];

    return vol;
};

QuadTree.prototype.compositeBbox  = function(bbi,bbj){
    //given two bounding boxes what is the volume
    var
    min = [999999,999999,999999,999999],
    max = [-999999,-999999,-999999,-9999990];
    if(!bbi) debugger;
    if(!bbj) debugger;
    var N = Math.min(bbi.min.length, bbj.min.length);
    for(var i = 0; i < N; i++){

        min[i] = Math.min(bbi.min[i], bbj.min[i]);
        max[i] = Math.max(bbi.max[i], bbj.max[i]);
        min[i] = min[i] ? min[i] : 0;
        max[i] = max[i] ? max[i] : 0;
    }
    return {min:min, max:max};
};


QuadTree.prototype.calcBbox = function(gobs){
    //given a set of stored objects, find the maximum bounding volume
    var
    min = [9999999,9999999,9999999,9999999],
    max = [-9999999,-9999999,-9999999,-9999999];

    var nodei, nodej, maxVol = 0;

    if(!gobs) debugger;
    for(var i = 0; i < gobs.length; i++){
        var gbb = gobs[i].getBbox();
        var iiN = gbb.min.length;
        for(var ii = 0; ii < iiN; ii++){
            min[ii] = Math.min(min[ii], gbb.min[ii]);
            max[ii] = Math.max(max[ii], gbb.max[ii]);
            min[ii] = min[ii] ? min[ii] : 0;
            max[ii] = max[ii] ? max[ii] : 0;
        }
    }
    return {min: min, max: max};
};

QuadTree.prototype.findMaxVolPairs  = function(gobs){
    //given a set of stored objects, find the maximum bounding volume between pairs in the set
    //return an array of the two indices
    var nodei, nodej, maxVol = 0;
    for(var i = 0; i < gobs.length; i++){
        for(var j = i+1; j < gobs.length; j++){
            //if(i == j) continue;
            var ibb = gobs[i].getBbox();
            var jbb = gobs[j].getBbox();
            var cbb = this.compositeBbox(ibb,jbb);
            var vol = this.calcBoxVol(cbb);
            if(vol > maxVol){
                maxVol = vol;
                nodei = i;
                nodej = j;
            }
        }
    }
    return [gobs[nodei],gobs[nodej]];
};

QuadTree.prototype.hasOverlap  = function(bbox1, bbox2){
    var overlap = true,
    bb1 = bbox1,
    bb2 = bbox2;
    //for each dimension test to see if axis are seperate
    for(var i = 0; i < 4; i++){
        if      (bb1.max[i] <  bb2.min[i]) overlap = false;
        else if (bb1.min[i] >  bb2.max[i]) overlap = false;
    }
    //if(!overlap) debugger;
    return overlap;
};

QuadTree.prototype.calcVolumeChange  = function(obj, node){
    var nodebb = node.bbox;
    var compbb = this.compositeBbox(obj.bbox, nodebb);

    var nodeVol = this.calcBoxVol(nodebb);
    var compVol = this.calcBoxVol(compbb);
    return Math.abs(nodeVol - compVol);
}


QuadTree.prototype.traverseDownBB  = function(node, bb, func){
    var stack = [node];
    while(stack.length > 0){
        var cnode = stack.pop();
        if(!func(cnode)) continue;
        for (var i = 0; i < cnode.children.length; i++){
            var cbb = cnode.children[i].bbox;
            if(this.hasOverlap(bb, cbb))
                stack.push(cnode.children[i]);
        }
    }
};

QuadTree.prototype.traverseDown  = function(node, func){
    var stack = [node];
    while(stack.length > 0){
        var cnode = stack.pop();
        if(!func(cnode)) continue;
        for (var i = 0; i < cnode.children.length; i++){
            stack.push(cnode.children[i]);
        }
    }
};


QuadTree.prototype.traverseUp  = function(node, func){
    var stack = [node];
    while(stack.length > 0){
        var cnode = stack.pop();
        if(!func(cnode)) continue;
        if(cnode.parent){
            stack.push(cnode.parent);
        }
    }
};

QuadTree.prototype.splitNode  = function(node, stack){

    var nbb = node.bbox;
    var bbMin = [0,0,0];
    bbMin[0] = Math.ceil(nbb.min[0]);
    bbMin[1] = Math.ceil(nbb.min[1]);
    bbMin[2] = Math.ceil(nbb.min[2]);
    bbMin[3] = Math.ceil(nbb.min[3]);

    var bbw = nbb.max[0] - nbb.min[0];
    var bbh = nbb.max[1] - nbb.min[1];
    var bbz = nbb.max[2] - nbb.min[2];
    var bbt = nbb.max[3] - nbb.min[3];

    var mDim  = 0.5*Math.min(bbw, bbh);
    //var mDimZ = Math.min(bbz, bbt);
    //if(bbz === 1) mDimZ = bbt;
    //if(bbt === 1) mDimZ = bbz;
    var mDimZ = bbz <= 1 ? 1 : 0.5*bbz;
    var mDimT = bbt <= 1 ? 1 : 0.5*bbt;
    if( mDim/mDimZ < 5 ) var mDim = Math.min(mDim, mDimZ);

    //var K = (mDim === bbz || mDim === bbt) ? 1 : 2;
    var nXTiles = Math.max(Math.floor(bbw/mDim),1);
    var nYTiles = Math.max(Math.floor(bbh/mDim),1);
    var nZTiles = Math.max(Math.floor(bbz/mDimZ),1);
    var nTTiles = Math.max(Math.floor(bbt/mDimT),1);

    var tw = bbw/nXTiles; //tile width
    var th = bbh/nYTiles; //tile height
    var tz = bbz/nZTiles; //tile depth
    var tt = bbt/nTTiles; //tile depth

    if(!this.splits) this.splits = [];
    this.splits[node.L + 1] = [nXTiles, nYTiles, nZTiles, nTTiles];

    node.children = [];
    //debugger;
    for(var i = 0; i < nXTiles; i++){
        for(var j = 0; j < nYTiles; j++){
            for(var k = 0; k < nZTiles; k++){
                for(var l = 0; l < nTTiles; l++){

                    var ind = i + j*nXTiles + k*nXTiles*nYTiles + l*nXTiles*nYTiles*nZTiles;
                    var newNode = {
                        parent: node,
                        children:[],
                        leaves:[],
                        bbox: {min:[0,0,0,0], max: [9999,9999,9999,9999]},
                        L: node.L+1
                    }
                    //node.children.push(newNode);
                    var tMinX = bbMin[0] + i*tw;
                    var tMinY = bbMin[1] + j*th;
                    var tMinZ = bbMin[2] + k*tz;
                    var tMinT = bbMin[3] + l*tt;
                    newNode.bbox.min = [tMinX,      tMinY,      tMinZ,      tMinT];
                    newNode.bbox.max = [tMinX + tw, tMinY + th, tMinZ + tz, tMinT + tt ];
                    var id = this.nodes.length;
                    newNode.id = id;
                    this.updateSprite(newNode);

                    node.children.push(newNode);
                    this.nodes.push(newNode);
                }
            }
        }
    }

    for(var i = 0; i < node.leaves.length; i++){
        for(var j = 0; j < node.children.length; j++){
            var leaf = node.leaves[i];
            var cnode = node.children[j];
            if(leaf.hasOverlap(cnode.bbox)){
                var frame = {node: cnode, shape: leaf}
                stack.push(frame);
            }
        }
    }

    node.leaves = [];
};

QuadTree.prototype.insertInNode  = function(gob, node, stack){
    var inSet = false;
    for(var i = 0; i < node.leaves.length; i++){
        if(gob.id() === node.leaves[i].id())
            inSet = true;
    }
    if(!inSet)
        node.leaves.push(gob);

    gob.page = node;
    //node.bbox = this.calcBbox(node.leaves);
    var maxLevel = 6;
    var maxTileLevel = this.renderer.viewer.tiles.pyramid.levels;
    if((node.leaves.length >= this.maxChildren || node.L < maxTileLevel + 2) &&
       node.L < maxLevel){
        this.splitNode(node, stack);
    }
    /*
    //make sure that the leaves are no larger than the client view
    var xc = this.renderer.viewer.tiles.div.clientWidth;
    var yc = this.renderer.viewer.tiles.div.clientHeight;
    var scale = Math.pow(2,node.L);
    var xn = (node.bbox.max[0] - node.bbox.min[0])*scale;
    var yn = (node.bbox.max[1] - node.bbox.min[1])*scale;

    //var fArea = this.calcBoxVol(this.renderer.viewFrustum);
    //var nArea = this.calcBoxVol(node.bbox);
    if(!node.children.length && xn*yn > 1.25*xc*yc){
        this.splitNode(node, stack);
    }
   */
};


QuadTree.prototype.insert = function(shape){
    //I like static integer pointer trees, but a dymanic pointer tree seems appropriate here, so
    // we can pull data on and off the tree without having to do our own
    //return;

    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;

    var view = this.renderer.viewer.imagedim;
    var nudge = 0.01;
    this.nodes[0].bbox = {
        min:[0,0,0,0],
        max: [view.x, view.y, view.z, view.t]
    };
    var stack = [{node: this.nodes[0], shape: shape}];

    //if(shape.id() === 15) debugger;
    //if(shape.page) return;  //if the shapeject has a page then we insert it
    //if(shape.inTree) return;
    shape.inTree = true;
    shape.bbox = shape.calcBbox();

    //if(this.nodes.length > 10) return;
    var k = 0;
    while(stack.length > 0){
        k++;
        //if(l > 18) break;
        var frame = stack.pop();
        var fshape = frame.shape;
        var fnode = frame.node;
        fnode.dirty = true;
        this.imageCache.clearAll(fnode);
        //expand the bounding box of the current node on the stack
        //fnode.bbox = this.compositeBbox(shape.bbox, fnode.bbox);

        if(fnode.children.length === 0){

            if(fnode.leaves.length < this.maxChildren){
                this.insertInNode(fshape,fnode, stack);
            }
        }

        else{
            for(var i = 0; i < fnode.children.length; i++){
                var over = fshape.hasOverlap(fnode.children[i].bbox);
                if(over){

                    stack.push({node: fnode.children[i], shape: fshape});
                }
            }


        }
    }
};


QuadTree.prototype.remove = function(shape){
    var me = this;

    if(!shape.inTree) return;
    shape.inTree = false;
    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;

    //if(shape.id() === 15) debugger;
    var collection = [];
    var collectLeaves = function(node){
        if(node.leaves.length > 0)
            collection.push(node);
        return true;
    }
    this.traverseDownBB(this.nodes[0], shape.bbox, collectLeaves);

    for(var k = 0; k < collection.length; k++){
        var node = collection[k];
        var leaves = node.leaves;
        var pos = -1;
        for(var i= 0; i < leaves.length; i++){
            if(leaves[i].id() === shape.id()) pos = i;
        }
        if(pos > -1)
            leaves.splice(pos,1);
        //node.bbox = this.calcBbox(node.leaves);
        //this.updateSprite(node);
        //node = node.parent;
        while(node){
            //if(node.parent === null) break;
            if(!node.children)       continue;
            this.updateSprite(node);
            node.dirty = true;

            this.imageCache.clearAll(node);
            node = node.parent;
            //
        }
        //shape.page = null;

    }
};


QuadTree.prototype.collectObjectsInRegion = function(frust, node){
    var me = this;
    var collection = [];
    var renderer = this.renderer;
    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;

    var collectSprite = function(node){
        if(node.leaves.length > 0){
            for(var i = 0; i < node.leaves.length; i++){
                var leaf = node.leaves[i];
                if(leaf.collected || !leaf.isVisible(z, t)) continue;
                if(me.hasOverlap(frust, leaf.bbox)){
                    collection.push(leaf);
                    leaf.collected = true;
                }
            }
        }
        return true;
    };
    this.traverseDownBB(node, frust, collectSprite);
    collection.forEach(function(e){
        e.collected = false;
    });
    return collection;
};

QuadTree.prototype.cull = function(frust){
    var me = this;
    var renderer = this.renderer;
    renderer.currentLayer.removeChildren();

    var leaves = this.collectObjectsInRegion(frust, this.nodes[0]);

    leaves.forEach(function(e){
        e.updateStroke();
        renderer.currentLayer.add(e.sprite);
    });
    return leaves;
};


QuadTree.prototype.cache = function(frust, onCache){
    var me = this;
    var fArea = this.calcBoxVol(frust);
    var me = this;
    var collection = [];
    var renderer = this.renderer;
    var scale = renderer.stage.scale().x;
    var cache = false;
    //var L = renderer.viewer.tiles.tiled_viewer.zoomLevel;

    this.cachesDestroyed = 0;
    this.cachesRendered = 0;


    var cacheSprite = function(node){
        var nArea = me.calcBoxVol(node.bbox);
        var cache = null;
        //if(L === node.L || node.leaves.length > 0){

        if(nArea <= 0.6*fArea || node.leaves.length > 0) {
            //if(!node.imageCache.getCacheAtCurrent()){

            if(!me.imageCache.getCacheAtCurrent(node)){
                me.cachesDestroyed += 1;
                me.cacheChildSprites(node, onCache);
                cache = true;
                return false;
            }
            return false;
        }
        else return true;
    };
    this.traverseDownBB(this.nodes[0], frust, cacheSprite);
    if(this.cachesDestroyed === 0){
        onCache();
    }
};

QuadTree.prototype.cullCached = function(frust){
    var me = this;
    var fArea = this.calcBoxVol(frust);
    var me = this;
    var collection = [];
    var renderer = this.renderer;
    var scale = renderer.stage.scale().x;
    var cache = false;

    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;
    //var L = renderer.viewer.tiles.tiled_viewer.zoomLevel;

    var collectSprite = function(node){
        var nArea = me.calcBoxVol(node.bbox);
        var cache = null;
        //if(L === node.L || node.leaves.length > 0){
        if(nArea <= 0.6*fArea || node.leaves.length > 0) {
            collection.push(me.imageCache.getCacheAtCurrent(node));
            return false;
        }

        else return true;
    };
    this.traverseDownBB(this.nodes[0], frust, collectSprite);
    renderer.currentLayer.removeChildren();
    collection.forEach(function(e){
        if(e)
            renderer.currentLayer.add(e);
    });
};


QuadTree.prototype.clearCache = function(frust){
    var me = this;
    //var fArea = this.calcBoxVol(frust);
    /*
    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;

    var atSprite = function(node){

        //if(!node.imageCache.getCacheAtCurrent()) return true;
        me.imageCache.clearAll(node);

        return true;
    };
    this.traverseDown(this.nodes[0], atSprite);
    */
    this.imageCache.clearAll();
};

QuadTree.prototype.cacheScene = function(frust){
    var me = this;
    var fArea = this.calcBoxVol(frust);
    var collectSprite = function(node){
        var nArea = me.calcBoxVol(node.bbox);
        if(nArea < fArea) {
            me.cacheChildSprites(node);
            return false;
        }
        else return true;
    };
    this.traverseDownBB(this.nodes[0], frust, collectSprite);
};
/*
QuadTree.prototype.intersectBboxFrustum(bbox){
    var scale = this.renderer.stage.scale().x;

    var viewstate = this.renderer.viewer.current_view;
    var dim =       this.renderer.viewer.imagedim;
    var sz = dim.z;
    var st = dim.t;
    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;
    var maxLoc = sz*st;
    var loc = z + t*sz;

    if(!this.cachesAtScale[scale]) this.cachesAtScale[scale] = [];
    this.caches = this.cachesAtScale[scale];

    var proj = viewstate.imagedim.project,
    proj_gob = viewstate.gob_projection;

    if (proj_gob==='all') {
        return maxLoc;
    } else if (proj === 'projectmaxz' || proj === 'projectminz' || proj_gob==='Z') {
        return maxLoc + t;
    } else if (proj === 'projectmaxt' || proj === 'projectmint' || proj_gob==='T') {
        return maxLoc + st + z;
    } else if (proj === 'projectmax' || proj === 'projectmin') {
        return maxLoc + st + sz;
    } else if (!proj || proj === 'none') {
        return loc;
    }
};
*/

QuadTree.prototype.cacheChildSprites = function(node, onCache){
    //delete cache if it exists

    this.imageCache.deleteAtCurrent(node);

    //initialize a few variables;
    var me = this;
    var renderer = this.renderer;
    var bbox = node.bbox;
    var w = bbox.max[0] - bbox.min[0];
    var h = bbox.max[1] - bbox.min[1];
    var scale = renderer.stage.scale().x;


    var z = this.renderer.viewer.tiles.cur_z;
    var t = this.renderer.viewer.tiles.cur_t;

    var nbbox = {min: [bbox.min[0],bbox.min[1], z, t],
                 max: [bbox.max[0],bbox.max[1], z, t]};

    //console.log(bbox.min[2], bbox.max[2], z);

    node.scale = scale;
    var buffer = renderer.getPointSize();
    buffer = 0;

    //create a new image
    this.imageCache.createAtCurrent(node);

    //create a temp layer to capture the appropriate objects
    var layer = new Kinetic.Layer({
        scaleX: scale,
        scaleY: scale,
        width: w*scale,
        height: h*scale
    });

    //fetch the objects in the tree that are in that node
    var leaves = this.collectObjectsInRegion(nbbox, node);
    leaves.forEach(function(e){
        e.updateLocal();
        layer.add(e.sprite);
    });
    layer.draw();

    //create a new image, in the async callback assign the image to the node's imageCache
    //scale the image region
    var image = layer.toImage({
        callback: function(img){
            //if(!node.dirty) return;

            node.image = img;
            me.imageCache.createAtCurrent(node);
            me.imageCache.setPositionAtCurrent(node);
            me.imageCache.setImageAtCurrent(img, node);

            node.dirty = false;
            me.cachesRendered += 1; //count the caches that have been rerendered since performing a cache call
            //console.log(img.src);
            if(me.cachesRendered >= me.cachesDestroyed && onCache){
                me.cachesRendered = 0;
                me.cachesDestroyed = 0;
                onCache();
            }

        },

        x: bbox.min[0]*scale - buffer,
        y: bbox.min[1]*scale - buffer,
        width: w*scale + 2.0*buffer,
        height: h*scale + 2.0*buffer,
    });

    me.imageCache.setPositionAtCurrent(node);
};

QuadTree.prototype.setDirty = function(node){
    var me = this;
    var dirtFunc = function(node){
        node.dirty = true;
        return true;
    };
    this.traverseUp(node, dirtFunc);
};


QuadTree.prototype.updateSprite = function(node){
    var bbox = node.bbox;
    var w = bbox.max[0] - bbox.min[0];
    var h = bbox.max[1] - bbox.min[1];
    if(!node.sprite)
        node.sprite = new Kinetic.Rect({
            x: bbox.min[0],
            y: bbox.min[1],
            width: w,
            height: h,
            hasFill: false,
            listening: false,
            //fill: "rgba(128,128,128,0.2)",
            stroke: "rgba(128,255,255,0.4)",
            strokeWidth: 1.0,
        });

    node.sprite.x(bbox.min[0]);
    node.sprite.y(bbox.min[1]);
    node.sprite.width(w);
    node.sprite.height(h);
};


QuadTree.prototype.drawBboxes = function(frust){
    var me = this;

    var me = this;
    var collection = [];
    var renderer = this.renderer;
    var node = this.nodes[0];

    var collectSprite = function(node){
        if(node.sprite)
            me.renderer.currentLayer.add(node.sprite);
        return true;
    };

    this.traverseDownBB(node, frust, collectSprite);
};

////////////////////////////////////////////////////////////////
//Controller
////////////////////////////////////////////////////////////////

function CanvasControl(viewer, element) {
    this.viewer = viewer;

    if (typeof element == 'string')
        this.svg_element = document.getElementById(element);
    else
        this.svg_element = element;

    this.viewer.viewer.tiles.tiled_viewer.addViewerZoomedListener(this);
    this.viewer.viewer.tiles.tiled_viewer.addViewerMovedListener(this);
    this.viewer.viewer.tiles.tiled_viewer.addCursorMovedListener(this);
}

CanvasControl.prototype.setFrustum = function(e, scale){
    var dim = this.viewer.viewer.imagedim,
    viewstate = this.viewer.viewer.current_view,
    z = this.viewer.viewer.tiles.cur_z,
    t = this.viewer.viewer.tiles.cur_t,
    sz = dim.z,
    st = dim.t,
    cw = this.viewer.viewer.imagediv.clientWidth/scale.x,
    ch = this.viewer.viewer.imagediv.clientHeight/scale.y,
    x = e.x < 0 ? -e.x/scale.x : 0,
    y = e.y < 0 ? -e.y/scale.y : 0,
    w = e.x < 0 ? dim.x + e.x/scale.x : cw - e.x/scale.x,
    h = e.y < 0 ? dim.y + e.y/scale.y : ch - e.y/scale.y;

    w = Math.min(cw, w);
    w = Math.min(dim.x, w);
    h = Math.min(ch, h);
    h = Math.min(dim.y, h);

    var proj = viewstate.imagedim.project,
    proj_gob = viewstate.gob_projection;
    var z0 = z-0.5;
    var z1 = z+0.5;
    var t0 = t-0.5;
    var t1 = t+0.5;

    if (proj_gob==='all') {
        z0 = 0;
        z1 = sz;
        t0 = 0;
        t1 = st;
    } else if (proj === 'projectmaxz' || proj === 'projectminz' || proj_gob==='Z') {
        z0 = 0;
        z1 = sz;
    } else if (proj === 'projectmaxt' || proj === 'projectmint' || proj_gob==='T') {
        t0 = 0;
        t1 = st;
    } else if (proj === 'projectmax' || proj === 'projectmin') {
        z0 = 0;
        z1 = sz;
        t0 = 0;
        t1 = st;
    }

    this.viewer.setFrustum({
        min: [x,   y,   z0, t0],
        max: [x+w, y+h, z1, t1]
    });
};

CanvasControl.prototype.viewerMoved = function(e) {
    //this.viewer.stage.setPosition({x: e.x, y: e.y});
    //var canvas = this.viewer.currentLayer.getCanvas()._canvas;
    var scale = this.viewer.stage.scale();
    this.setFrustum(e, scale);

    this.viewer.stage.x(e.x);
    this.viewer.stage.y(e.y);
    var frust = this.viewer.viewFrustum;
    //var w = frust.max[0] - frust.min[0];
    //var h = frust.max[1] - frust.min[1];
    //this.viewer.stage.width(w*scale.x);
    //this.viewer.stage.height(h*scale.y);

    this.viewer.updateVisible();
    var me = this;
    /*
    var draw = function(){
        if(!me.timeout)
            me.viewer.draw();
        me.timeout = null;
    };
    setTimeout(draw, 100);
    */
    this.viewer.draw();
    //this.viewer.stage.content.style.left = e.x + 'px';
    //this.viewer.stage.content.style.top = e.y + 'px';
};

CanvasControl.prototype.viewerZoomed = function(e) {
    //this.viewer.stage.content.style.left = e.x + 'px';
    //this.viewer.stage.content.style.top = e.y + 'px';

    this.viewer.stage.scale({x:e.scale,y:e.scale});
    console.log('zoomed:', e.scale);

    this.setFrustum(e, {x: e.scale, y: e.scale});

    this.viewer.stage.x(e.x);
    this.viewer.stage.y(e.y);
    this.viewer.currentLayer.removeChildren();
    //this.viewer.quadtree.cullCached(this.viewer.viewFrustum);
    this.viewer.updateVisible(); //update visible has draw function
    //this.viewer.draw();

    //this.viewer.draw();
};


CanvasControl.prototype.cursorMoved = function(e) {
    //this.viewer.stage.content.style.left = e.x + 'px';
    //this.viewer.stage.content.style.top = e.y + 'px';
    //console.log(e);
    var
    z = this.viewer.viewer.tiles.cur_z,
    t = this.viewer.viewer.tiles.cur_t;

    var pt = e;
    if(!this.pastPoint)
        this.pastPoint = e;

    var tpt = this.pastPoint;
    var dpt = {x: pt.x - tpt.x, y: pt.y - tpt.y};
    var scale = this.viewer.stage.scale();
    var dl = (dpt.x*dpt.x + dpt.y*dpt.y)*scale.x*scale.x;
    var viewer = this.viewer.viewer;
    var renderer = this.viewer;

    if(this.hoverTimeout) clearTimeout(this.hoverTimeout);
    if(dl < 10 && renderer.mode === 'navigate'){
        this.hoverTimeout = setTimeout(function(){
            var shape = renderer.findNearestShape(tpt.x, tpt.y, z, t);
            if(shape){
                viewer.parameters.onhover(shape.gob, e.event);
                //console.log(shape);
            }

            //me.onhover(e);
        },750);
    }

    this.pastPoint = e;
};

////////////////////////////////////////////////////////////////
//Renderer
////////////////////////////////////////////////////////////////


function CanvasRenderer (viewer,name) {
    var p = viewer.parameters || {};
    //this.default_showOverlay           = p.rotate          || 0;   // values: 0, 270, 90, 180

    this.default_showOverlay   = false;

    this.base = ViewerPlugin;
    this.base (viewer, name);
    this.events  = {};
    this.visit_render = new BQProxyClassVisitor (this);
    //this.visit render

}
CanvasRenderer.prototype = new ViewerPlugin();

CanvasRenderer.prototype.create = function (parent) {
    this.mode = 'navigate';
    this.shapes = {
        'ellipse': CanvasEllipse,
        'circle': CanvasCircle,
        'point': CanvasPoint,
        'polygon': CanvasPolyLine,
        'rectangle': CanvasRectangle,
        'square': CanvasSquare,
        'label': CanvasLabel,
    };

    // dima: kineticjs removes all other elements in the given container, create a wrapper for its sad sole existence
    this.wrapper = document.createElement("div");
    parent.appendChild(this.wrapper);

    this.stage = new Kinetic.Stage({
        container: this.wrapper,
        listening: true,
    });

    this.stage._mousemove = Kinetic.Util._throttle( this.stage._mousemove, 30);
    this.stage.content.style.setProperty('z-index', 15);

    this.initShapeLayer();
    this.initEditLayer();
    this.initSelectLayer();
    this.initPointImageCache();
    this.quadtree = new QuadTree(this);
    this.gobs = [];
    this.visitedFrame = [];
    this.cur_z = 0;
    return parent;
};


CanvasRenderer.prototype.initShapeLayer = function(){
    this.currentLayer = new Kinetic.Layer();
    this.defaultIntersection = this.currentLayer._getIntersection;
    this.noIntersection = function() {return {};};

    this.currentLayer._getIntersection = this.noIntersection;

    this.stage.add(this.currentLayer);
};

CanvasRenderer.prototype.initEditLayer = function(){
    var me = this;
    this.editLayer = new Kinetic.Layer();
    this.editLayer._getIntersection = this.noIntersection;

    this.stage.add(this.editLayer);
    this.editLayer.moveToTop();
    this.initUiShapes();
};

CanvasRenderer.prototype.initSelectLayer = function(){
    var me = this;
    this.selectLayer = new Kinetic.Layer();
    this.selectLayer._getIntersection = this.noIntersection;

    this.stage.add(this.selectLayer);
    this.selectLayer.moveToBottom();

    this.selectedSet = [];
    this.visibleSet = [];

    this.lassoRect = new Kinetic.Rect({
        fill: 'rgba(200,200,200,0.1)',
        stroke: 'grey',
        strokeWidth: 1,
        listening: false,
    });

    this.selectRect = new Kinetic.Rect({
        fill: 'rgba(0,0,0,0.0)',
        strokeWidth: 0,
        width: this.stage.width(),
        height: this.stage.height(),
        listening: true,
    });
    this.selectLayer.add(this.selectRect);

    var
    stage = this.stage,
    lassoRect = this.lassoRect;
    var mousemove = function(e) {
        if(me.mode != 'edit') return;
        var evt = e.evt;
        var scale = stage.scale();

        var stageX = stage.x();
        var stageY = stage.y();
        var x = evt.offsetX==undefined?evt.layerX:evt.offsetX;
        var y = evt.offsetY==undefined?evt.layerY:evt.offsetY;
        x = (x - stageX)/scale.x;
        y = (y - stageY)/scale.y;

        var x0 = lassoRect.x();
        var y0 = lassoRect.y();

        lassoRect.width((x - x0));
        lassoRect.height((y - y0));
        me.editLayer.draw();
    };
    var mousedown = function(e){
        if(me.mode != 'edit') return;
        me.unselect(me.selectedSet);

        var evt = e.evt;
        var scale = stage.scale();

        var stageX = stage.x();
        var stageY = stage.y();
        //var x = (evt.offsetX - stageX)/scale.x;
        //var y = (evt.offsetY - stageY)/scale.y;
        var x = evt.offsetX==undefined?evt.layerX:evt.offsetX;
        var y = evt.offsetY==undefined?evt.layerY:evt.offsetY;
        x = (x - stageX)/scale.x;
        y = (y - stageY)/scale.y;
        //console.log(evt);

        me.currentLayer.draw();
        me.editLayer.draw();
        me.selectedSet = []; //clear out current selection set

        me.editLayer.add(me.lassoRect);
        me.selectLayer.moveToTop();

        lassoRect.width(0);
        lassoRect.height(0);
        lassoRect.x(x);
        lassoRect.y(y);

        me.selectRect.on('mousemove', mousemove);
    }

    var mouseup = function(e) {
        if(me.mode != 'edit') return;
        me.selectRect.off('mousemove');
        me.lassoRect.remove();
        me.selectLayer.moveToBottom();

        var x0t = me.lassoRect.x();
        var y0t = me.lassoRect.y();
        var x1t = me.lassoRect.width() + x0t;
        var y1t = me.lassoRect.height() + y0t;

        var x0 = Math.min(x0t, x1t);
        var y0 = Math.min(y0t, y1t);
        var x1 = Math.max(x0t, x1t);
        var y1 = Math.max(y0t, y1t)
        var dx = x1 - x0;
        var dy = y1 - y0;
        if(dx*dy === 0) return;
        me.lassoSelect(x0,y0,x1,y1);
        me.select(me.selectedSet);
        me.default_select(me.selectedSet);
        me.editLayer.draw();

    } ;

    this.selectRect.on('mousedown', mousedown);
    this.selectRect.on('mouseup', mouseup);

    this.selectLayer.draw();
};

CanvasRenderer.prototype.lassoSelect = function(x0,y0, x1,y1){
    var me = this;
    /*
    var shapes = this.currentLayer.getChildren();
    shapes.forEach(function(e,i,d){
        var x = e.x();
        var y = e.y();
        if(!e.shape) return;
        var bbox = e.shape.getBbox();
        if(!bbox) return;
        if(bbox.min[0] > x0 && bbox.min[1] > y0 &&
           bbox.max[0] < x1 && bbox.max[1] < y1){
            me.addToSelectedSet(e.shape);
        }
    });
    */
    var node0 = this.quadtree.nodes[0];
    var shapes = this.quadtree.collectObjectsInRegion({min:[x0,y0],max:[x1,y1]},node0);
    shapes.forEach(function(e,i,d){
        var x = e.sprite.x();
        var y = e.sprite.y();
        //if(!e.shape) return;
        var bbox = e.getBbox();
        if(!bbox) return;
        if(bbox.min[0] > x0 && bbox.min[1] > y0 &&
           bbox.max[0] < x1 && bbox.max[1] < y1){
            me.addToSelectedSet(e);
        }
    });
}

CanvasRenderer.prototype.initUiShapes = function(){

    this.bbRect = new Kinetic.Rect({
        fill: 'rgba(255,255,255,0.0)',
        stroke: 'grey',
        strokeWidth: 1,
        listening: false,
    });
    this.bbCorners = []
    for(var i = 0; i < 4; i++){
        this.bbCorners.push(
        new Kinetic.Rect({
            width: 6,
            height: 6,
            fill: 'grey',
            listening: true
        }));
    }
    this.bbCorners.forEach(function(e,i,d){
        e.setDraggable(true);
    });


};

CanvasRenderer.prototype.draw = function (){
    this.stage.draw();
};

CanvasRenderer.prototype.drawEditLayer = function (){
    this.updateBbox(this.selectedSet);
    this.editLayer.draw();
};

CanvasRenderer.prototype.enable_edit = function (enabled) {

    this.viewer.current_view.edit_graphics = enabled?true:false;
    var gobs =  this.viewer.image.gobjects;
    //this.visit_render.visit_array(gobs, [this.viewer.current_view]);

    this.editLayer.moveToTop();
    this.rendered_gobjects = gobs;
};

CanvasRenderer.prototype.findNearestShape = function(x,y, z, t){
    var node = this.quadtree.nodes[0];
    var scale = this.stage.scale().x;
    var w = 4/scale;
    var shapes =
        this.quadtree.collectObjectsInRegion(
            {min: [x-w, y-w, z-0.5, t-0.5],
             max: [x+w, y+w, z+0.5, t+0.5]}, node);

    return shapes[0];
},

CanvasRenderer.prototype.getUserCoord = function (e ){
    var evt = e.evt ? e.evt : e;
    var x = evt.offsetX==undefined?evt.layerX:evt.offsetX;
    var y = evt.offsetY==undefined?evt.layerY:evt.offsetY;
    var scale = this.stage.scale();

    var stageX = this.stage.x();
    var stageY = this.stage.y();
    var x = (x - stageX);
    var y = (y - stageY);

    return {x: x, y: y};
	//return mouser.getUserCoordinate(this.svgimg, e);
    //the old command got the e.x, e.y and applied a transform to localize them to the svg area using a matrix transform.
};

CanvasRenderer.prototype.setMode = function (mode){
    var me = this;
    this.unselectCurrent();

    this.mode = mode;

    me.updateVisible();

    if(mode === 'add' || mode === 'delete' || mode === 'edit') {
        this.currentLayer._getIntersection = this.defaultIntersection;
        this.editLayer._getIntersection = this.defaultIntersection;
        this.selectLayer._getIntersection = this.defaultIntersection;

        this.lassoRect.width(0);
        this.lassoRect.height(0);
        this.selectLayer.moveToBottom();
        this.editLayer.moveToTop();
    }

    if(mode == 'navigate') {
        this.currentLayer._getIntersection = this.noIntersection;
        this.editLayer._getIntersection = this.noIntersection;
        this.selectLayer._getIntersection = this.noIntersection;
        this.lassoRect.width(0);
        this.lassoRect.height(0);
        this.selectLayer.moveToBottom();
        this.editLayer.moveToTop();
        if(this.editableObjects)
            for(var i = 0; i < this.editableObjects.length; i++){
                this.removeSpriteEvents(this.editableObjects[i]);
            }
    }


};

CanvasRenderer.prototype.addHandler = function (ty, cb){
    //console.log ("addHandler " + ty + " func " + cb);
    if (cb) {
        //tremovehis.svgimg.addEventListener (ty, cb, false);
        this.stage.on(ty,cb);
        this.events[ty] = cb;
    }else{
        this.stage.off(ty);
        //this.svgimg.removeEventListener (ty, this.events[ty], false);
    }
};

CanvasRenderer.prototype.setmousedown = function (cb ){
    this.addHandler ("mousedown", cb );
};

CanvasRenderer.prototype.setmouseup = function (cb, doadd ){
    this.addHandler ("mouseup", cb);
};

CanvasRenderer.prototype.setmousemove = function (cb, doadd ){
    var me = this;
    this.addHandler ("mousemove",cb );
};


CanvasRenderer.prototype.setdragstart = function (cb ){
    this.addHandler ("dragstart", cb );
};

CanvasRenderer.prototype.setdragmove = function (cb ){
    this.addHandler ("dragmove", cb );
};

CanvasRenderer.prototype.setdragend = function (cb ){
    this.addHandler ("dragend", cb );
};

CanvasRenderer.prototype.setclick = function (cb, doadd ){
    this.addHandler ("click", cb);
};

CanvasRenderer.prototype.setdblclick = function (cb, doadd ){
    this.addHandler ("dblclick", cb);
};

CanvasRenderer.prototype.setkeyhandler = function (cb, doadd ){
   var ty = 'keydown';
   if (cb) {
        document.documentElement.addEventListener(ty,cb,false);
        this.events[ty] = cb;
   } else {
       document.documentElement.removeEventListener(ty, this.events[ty],false);
   }
};

CanvasRenderer.prototype.newImage = function () {
    var w = this.viewer.imagediv.offsetWidth;
    var h = this.viewer.imagediv.offsetHeight;

    this.rendered_gobjects = [];
    if(!this.viewFrustum) this.initFrustum();

};

CanvasRenderer.prototype.updateView = function (view) {
    if (this.initialized) return;
    this.initialized = true;
//    this.loadPreferences(this.viewer.preferences);
//    if (this.showOverlay !== 'false')
//        this.populate_overlay(this.showOverlay);
};

CanvasRenderer.prototype.appendSvg = function (gob){
    if (gob.shape)
        this.svggobs.appendChild(gob.shape.svgNode);
};

CanvasRenderer.prototype.initFrustum = function(){

    if(!this.viewFrustum){
        var scale = this.stage.scale().x;
        var x = this.viewer.tiles.div.clientWidth/scale;
        var y = this.viewer.tiles.div.clientHeight/scale;
        var z = 1;
        var t = 1;

        this.viewFrustum = {
            min: [0,0,z-0.5,t-0.5],
            max: [x,y,z+0.5,t+0.5]
        };
    }
};

CanvasRenderer.prototype.setFrustum = function(bb){
    if(!this.viewFrustum) this.initFrustum();
    if(!this.cursorRect)
        this.cursorRect = new Kinetic.Rect({
            //x: -20,
            //y: -20,
            width: 0,
            height: 0,
            fill: "rgba(128,255,128,0.2)",
            stroke: 'black',
            strokeWidth: 1,
        });
    //this.editLayer.add(this.cursorRect);
    this.viewFrustum.min[0] = bb.min[0];
    this.viewFrustum.min[1] = bb.min[1];
    this.viewFrustum.min[2] = bb.min[2];
    this.viewFrustum.min[3] = bb.min[3];

    this.viewFrustum.max[0] = bb.max[0];
    this.viewFrustum.max[1] = bb.max[1];
    this.viewFrustum.max[2] = bb.max[2];
    this.viewFrustum.max[3] = bb.max[3];

    this.cursorRect.x(bb.min[0]);
    this.cursorRect.y(bb.min[1]);
    this.cursorRect.width(bb.max[0] - bb.min[0]);
    this.cursorRect.height(bb.max[1] - bb.min[1]);
}

CanvasRenderer.prototype.cacheVisible = function(){
    this.quadtree.cacheScene(this.viewFrustum);
};

CanvasRenderer.prototype.getProjectionRange = function(zrange, trange){
    var viewstate = this.viewer.current_view;
    var dim = this.viewer.imagedim;

    var
    proj = viewstate.imagedim.project,
    proj_gob = viewstate.gob_projection;

    var
    z = dim.z,
    t = dim.t;

    if (proj_gob==='all' || proj === 'projectmax' || proj === 'projectmin') {
        trange[0] = 0;
        trange[1] = t;
        zrange[0] = 0;
        zrange[1] = z;
    } else if (proj === 'projectmaxz' || proj === 'projectminz' || proj_gob==='Z'){
        zrange[0] = 0;
        zrange[1] = z;
    } else if (proj === 'projectmaxt' || proj === 'projectmint' || proj_gob==='T') {
        trange[0] = 0;
        trange[1] = t;
    }
};

CanvasRenderer.prototype.updateVisible = function(){
    var me = this;
    //this.quadtree.cull(this.viewFrustum);
    var z = this.viewer.tiles.cur_z;
    var t = this.viewer.tiles.cur_t;

    var zrange = [z, z+1];
    var trange = [t, t+1];
    this.getProjectionRange(zrange, trange);

    if(this.mode == 'navigate'){
        this.quadtree.cache(this.viewFrustum, function(){
            me.quadtree.cullCached(me.viewFrustum);
            me.draw();
        });

        //this.quadtree.cache(this.viewFrustum);
        //this.quadtree.cullCached(this.viewFrustum);
    }
    else{

        this.editableObjects = this.quadtree.cull(this.viewFrustum);
        for(var i = 0; i < this.editableObjects.length; i++){
            this.addSpriteEvents(this.editableObjects[i]);
        }
        me.draw();
    }
    //this.quadtree.drawBboxes(this.viewFrustum);

};

CanvasRenderer.prototype.resetTree = function (e) {
    //reset the quadtree and visible node references to tree
    this.visibleSet.forEach(function(e){
        e.page = null;
    });
    this.visibleSet =[]; //cleare the visible set.
    //quadtree reset
    this.quadtree.reset();
};

CanvasRenderer.prototype.updateImage = function (e) {
    var me = this;
    var viewstate = this.viewer.current_view;
    var url = this.viewer.image_url();
    var scale = this.viewer.current_view.scale;
    var x = this.viewer.tiles.tiled_viewer.x;
    var y = this.viewer.tiles.tiled_viewer.y;
    var z = this.viewer.tiles.cur_z;
    var t = this.viewer.tiles.cur_t;
    this.gobsSlice = this.gobs[z];

    this.stage.scale({x: scale, y:scale});
    //this.initDrawer();
    /*
    if(this.selectedSet.length> 0){
        if(this.selectedSet[0].gob.vertices[0]){
            if(this.selectedSet[0].gob.vertices[0].z != z){
            }
        }
    }*/

    this.unselect(this.selectedSet);
    this.selectedSet = [];


    //this.stage.content.style.left = x + 'px';
    //this.stage.content.style.top = y + 'px';

    var width = window.innerWidth;
    var height = window.innerHeight;

    this.stage.setWidth(width);
    this.stage.setHeight(height);

    this.selectRect.width(viewstate.width/scale);
    this.selectRect.height(viewstate.height/scale);

    this.lassoRect.strokeWidth(1.0/scale);

    if(this.cur_z != z){
    }

    this.cur_z = z;

    //dump the currently viewed objects
    //this.currentLayer.removeChildren();

    if(!this.addedListeners){
        this.addedListeners = true;
        this.myCanvasListener = new CanvasControl( this, this.stage );
    }

    //get the gobs and walk the tree to rerender them
    //update visible objects in the tree... next iteration may be 3D.

    this.updateBbox(this.selectedSet);
    this.updateVisible(); //update visible has a draw call
    //this.draw();
};

CanvasRenderer.prototype.editBbox = function(gobs,i, e) {
    //return;
    this.updateManipulators(gobs);
    var scale = this.stage.scale();

    var offx = 8/scale.x;
    var offy = 8/scale.x;

    var me = this;
    //var points = gobs.shape.getAttr('points');

   //ar x0 = shape.x();
    //var y0 = shape.y();
    var px0 = this.bbCorners[0].x() + offx/2;
    var py0 = this.bbCorners[0].y() + offy/2;
    var px1 = this.bbCorners[1].x() + offx/2;
    var py1 = this.bbCorners[1].y() + offy/2;
    var px2 = this.bbCorners[2].x() + offx/2;
    var py2 = this.bbCorners[2].y() + offy/2;
    var px3 = this.bbCorners[3].x() + offx/2;
    var py3 = this.bbCorners[3].y() + offy/2;
    var dx = e.evt.movementX;
    var dy = e.evt.movementY;
    var oCorner;

    if(i == 0){
        this.bbCorners[1].x(px0 - offx/2);
        this.bbCorners[2].y(py0 - offy/2);
        oCorner = [this.bbCorners[3].x() + offx/2,
                   this.bbCorners[3].y() + offy/2];

    }
    if(i == 1){
        this.bbCorners[0].x(px1 - offx/2);
        this.bbCorners[3].y(py1 - offy/2);
        oCorner = [this.bbCorners[2].x() + offx/2,
                   this.bbCorners[2].y() + offy/2];
    }
    if(i == 2){
        this.bbCorners[3].x(px2 - offx/2);
        this.bbCorners[0].y(py2 - offy/2);
        oCorner = [this.bbCorners[1].x() + offx/2,
                   this.bbCorners[1].y() + offy/2];

    }
    if(i == 3){
        this.bbCorners[2].x(px3 - offx/2);
        this.bbCorners[1].y(py3 - offy/2);
        oCorner = [this.bbCorners[0].x() + offx/2,
                   this.bbCorners[0].y() + offy/2];
    }

    var nWidth  = px3-px0;
    var nHeight = py3-py0;
    var sx = nWidth/this.bbRect.width();
    var sy = nHeight/this.bbRect.height();
    //var scale = this.stage.scale();
    //var off = 10/scale.x;

    this.bbRect.x(px0);
    this.bbRect.y(py0);
    this.bbRect.width(px3-px0);
    this.bbRect.height(py3-py0);


    gobs.forEach(function(shape,i,a){
        var sbbox = shape.getBbox();

        var sprite = shape.sprite;
        var x = shape.x();
        var y = shape.y();

        var sdx = x - oCorner[0];
        var sdy = y - oCorner[1];

        var nx = oCorner[0] + sx*sdx;
        var ny = oCorner[1] + sy*sdy;

        //KineticJS's scenegraph stretches shapes and outlines.
        //Manually resizing gobs then updating is simpler and I don't have to
        //worry about transforms

        shape.gob.vertices.forEach(function(v){
            var dx = v.x - x;
            var dy = v.y - y;
            v.x = nx + sx*dx;
            v.y = ny + sy*dy;
        });

        /* here is the code that uses KineticJS transform hierarchy
        sprite.scaleX(sprite.scaleX()*sx);
        sprite.scaleY(sprite.scaleY()*sy);

        sprite.x(oCorner[0] + sx*sdx);
        sprite.y(oCorner[1] + sy*sdy);
        */
        shape.dirty = true;
        shape.update();
        //var mx = 0.5*(px0 + px3);
        //var my = 0.5*(py0 + py3);
    });
};

CanvasRenderer.prototype.updateBbox = function (gobs){

    this.updateManipulators(gobs);

    var scale = this.stage.scale();
    var min = [ 9999999, 9999999];
    var max = [-9999999,-9999999];

    for(var i = 0; i < gobs.length; i++){

        var shape = gobs[i];
        var bb = shape.getBbox();
        if(!bb) continue;
        min[0] = min[0] < bb.min[0] ? min[0] : bb.min[0];
        min[1] = min[1] < bb.min[1] ? min[1] : bb.min[1];

        max[0] = max[0] > bb.max[0] ? max[0] : bb.max[0];
        max[1] = max[1] > bb.max[1] ? max[1] : bb.max[1];
    }
    var pad = 8/scale.x;
    //pad the bbox
    min[0] -=  pad;
    min[1] -=  pad;
    max[0] +=  pad;
    max[1] +=  pad;

    var offx = 8/scale.x;
    var offy = 8/scale.x;

    this.bbRect.x(min[0]);
    this.bbRect.y(min[1]);

    this.bbWidth  = max[0] - min[0];
    this.bbHeight = max[1] - min[1];

    this.bbRect.width(this.bbWidth);
    this.bbRect.height(this.bbHeight);
    this.bbRect.strokeWidth(1.5/scale.x);

    this.bbCorners.forEach(function(e,i,a){
        e.width(offx);
        e.height(offy);
    });

    //offset the bbox vertices
    min[0] -= offx/2;
    min[1] -= offy/2;
    max[0] -= offx/2;
    max[1] -= offy/2;

    //console.log(scale, off);
    this.bbCorners[0].x(min[0]);
    this.bbCorners[0].y(min[1]);

    this.bbCorners[1].x(min[0]);
    this.bbCorners[1].y(max[1]);

    this.bbCorners[2].x(max[0]);
    this.bbCorners[2].y(min[1]);

    this.bbCorners[3].x(max[0]);
    this.bbCorners[3].y(max[1]);
    //this.updateDrawer();
};


CanvasRenderer.prototype.initPointImageCache = function () {
    var me = this;
    var point = new Kinetic.Circle({
            //radius: {x: rx, y: ry},
            x: 4,
            y: 4,
            fill:   'rgba(0,0,0,1.0)',
            stroke: 'rgba(255,255,255,0.5)',
            radius: 3,
            strokeWidth: 2,
        });
    var layer = new Kinetic.Layer({
        width: 8,
        height: 8
    }).add(point);
    layer.draw();

    this.pointImageCache;
    this.pointImageCacheOver;

    layer.toImage({
        callback: function(img){
            me.pointImageCache = img;
        }
    });
    point.fill('rgba(128,128,128,1.0)');
    layer.draw();

    layer.toImage({
        callback: function(img){
            me.pointImageCacheOver = img;
        }
    });
};

CanvasRenderer.prototype.mouseUp = function(){
    var me = this;
    this.endMove(this.selectedSet);
    this.selectedSet.forEach(function(e,i,d){
        me.move_poly(e.gob);
    });
};

CanvasRenderer.prototype.resetShapeCornerFill = function(){
    this.manipulators.forEach(function(e,i,a){
        e.fill('rgba(255,0,0,1)');
    });
};

CanvasRenderer.prototype.updateManipulators = function(shapes){
    if(!shapes) return;

    var me = this;
    var totalPoints = 0;
    var scale = this.stage.scale();

    for(var i = 0; i < shapes.length; i++){
        shapes[i].updateManipulators();
    }
};

CanvasRenderer.prototype.initManipulators = function(shapes){

    var manipMode = shapes.length > 1 ? 'multiple' : 'single';
    manipMode = shapes.length > 5 ? 'many' : manipMode;
    manipMode = this.viewer.parameters.showmanipulators ? 'multiple' : manipMode;

    var me = this;
    this.manipulators = [];

    for(var i = 0; i < shapes.length; i++){
        var manipulators = shapes[i].getManipulators(manipMode);
        manipulators.forEach(function(e){
            me.editLayer.add(e);
        });
        this.manipulators = this.manipulators.concat(manipulators);
    }
};

CanvasRenderer.prototype.resetSelectedSet = function(){
    this.selectedSet = [];
};

CanvasRenderer.prototype.addToSelectedSet = function(shape){
    var inSet = this.inSelectedSet(shape);
    if(!inSet)
        this.selectedSet.push(shape);
};

CanvasRenderer.prototype.inSelectedSet = function(shape){
    var inSet = false;
    for(var i = 0; i < this.selectedSet.length; i++){
        //check _id for now, id() tries to fetch an attribute, which doesn't exist
        if(this.selectedSet[i].sprite._id ===
           shape.sprite._id)
            inSet = true;
    }

    return inSet;
};

CanvasRenderer.prototype.initDrawer = function(){
    var me = this;
    if(!this.guidrawer)
        this.guidrawer = Ext.create('Ext.tip.Tip', {
		    anchor : this.viewer.viewer_controls_surface,
		    cls: 'bq-viewer-menu',

            header: {
                title: ' ',
                tools:[{
                    type: 'close',
                    handler: function(){
                        me.guidrawer.hide();
                    }
                }]},
            layout: {
                type: 'hbox',
                //align: 'stretch',
            },
            /*
              listeners: {
              close : function(){
              debugger;
              },
              show: function(){
              if(renderer.selectedSet.length === 0) this.hide();
              }
              },
            */
	    }).hide();
};

CanvasRenderer.prototype.updateDrawer = function(){
    if(!this.guidrawer) return;
    if(this.guidrawer.isHidden()) return;
    var xy0 = this.bbCorners[2].getAbsolutePosition();
    var xy1 = this.bbCorners[3].getAbsolutePosition();

    this.guidrawer.setWidth(xy1.x - xy0.x);
    this.guidrawer.setHeight(xy1.y - xy0.y);
    this.guidrawer.setX(xy0.x + 10);
    this.guidrawer.setY(xy0.y + 85);
};

CanvasRenderer.prototype.showDrawer = function(){
    if(!this.guidrawer) return;
    this.guidrawer.show();
    this.updateDrawer();
};

CanvasRenderer.prototype.hideDrawer = function(){
    if(!this.guidrawer) return;
    this.guidrawer.removeAll();
    this.guidrawer.hide();
};

CanvasRenderer.prototype.select = function (gobs) {
    var me = this;

    this.editLayer.removeChildren();

    this.initManipulators(gobs);
    this.updateBbox(gobs);

    this.bBoxScale = [1,1];

    gobs.forEach(function(e,i,a){
        e.setLayer(me.editLayer);
        e.sprite.moveToBottom();
    });

    this.editLayer.add(this.bbRect);

    this.bbCorners.forEach(function(e,i,d){
        me.editLayer.add(e); //add corners
        /*
        e.on('mousedown', function(evt) {
        });
        */
        e.on('dragmove', function(evt) {
            //if(this.mode != 'edit') return;
            me.editBbox(gobs,i,evt, e);
            e.moveToTop();
            me.editLayer.batchDraw(); // don't want to use default draw command, as it updates the bounding box
        });

        e.on('mouseup',function(evt){
            e.dirty = true;
            //me.updateDrawer();
            me.selectedSet.forEach(function(e,i,d){
                if(e.dirty)
                    me.move_shape(e.gob);
            });
        });
    });
    //this.showDrawer();
    this.currentLayer.draw();
    this.editLayer.draw();
};

CanvasRenderer.prototype.unselect = function (gobs) {
    //var shape = gobs.shape;
    var me = this;

    gobs.forEach(function(e,i,a){
        e.setLayer(me.currentLayer);
        e.sprite.moveToBottom();
        e.resetManipulators();
    });

    this.bbCorners.forEach(function(e,i,d){
        e.remove(); //remove all current corners
        e.off('mousedown');
        e.off('dragmove');
        e.off('mouseup');
    });
    /*
    if(this.manipulators){
        this.manipulators.forEach(function(e,i,d){
            e.remove(); //remove all current corners

        });
    }
    */
    this.selectedSet.forEach(function(e,i,d){
        if(e.dirty)
            me.move_shape(e.gob);
        me.quadtree.insert(e)
    });
    //this.hideDrawer();
    this.editLayer.removeChildren();
};

CanvasRenderer.prototype.destroy = function (gobs) {
    //var shape = gobs.shape;
    var me = this;

    this.bbCorners.forEach(function(e,i,d){
        e.remove(); //remove all current corners
        e.off('mousedown');
        e.off('dragmove');
        e.off('mouseup');
    });

    if(this.manipulators){
        this.manipulators.forEach(function(e,i,d){
            e.remove(); //remove all current corners
            e.off('mousedown');
            e.off('dragmove'); //kill their callbacks
            e.off('mouseup');
        });
    }
    this.editLayer.removeChildren();

};


CanvasRenderer.prototype.unselectCurrent = function(){
    this.unselect(this.selectedSet);
    this.selectedSet = [];

};

CanvasRenderer.prototype.rerender = function (gobs, params) {
    if (!gobs)
        gobs = this.viewer.image.gobjects;
    if (!params)
        params = [this.viewer.current_view];

    this.visit_render.visit_array(gobs, params);
    this.quadtree.clearCache();

    this.updateVisible();
    this.draw();
};

CanvasRenderer.prototype.visitall = function (gobs, show) {
    params = [this.viewer.current_view, show];
    this.visit_render.visit_array(gobs, params);
};

CanvasRenderer.prototype.is_selected = function (gob){
    if (gob.shape)
        return gob.shape.selected;
    return false;
};


//CanvasRenderer.prototype.set_hover_handler = function (callback){
    //this.select_callback = callback;
//};

CanvasRenderer.prototype.set_select_handler = function (callback){
    this.select_callback = callback;
};

CanvasRenderer.prototype.set_move_handler = function (callback){
    this.callback_move = callback;
};

CanvasRenderer.prototype.default_select = function (gob) {
    if (this.select_callback){
        this.select_callback(gob);
    }
};

CanvasRenderer.prototype.default_move = function (view, gob) {
    if (this.callback_move)
        this.callback_move(view, gob);
};


CanvasRenderer.prototype.toggleWidgets = function(fcn){
    /*
    var scale = this.stage.scale();
    if(fcn === 'hide'){
        this.selectedSet.forEach(function(e){
            e.sprite.strokeWidth(2/scale.x);
        });
    }
    else {
        this.selectedSet.forEach(function(e){
            e.sprite.strokeWidth(1/scale.x);
        });
    }*/

    this.manipulators.forEach(function(e){
        e[fcn]();
    });
    this.updateBbox(this.selectedSet);
    this.bbRect[fcn]();
    this.bbCorners.forEach(function(e,i,a){
        e[fcn]();
    });
    this.editLayer.draw();
    if(fcn === 'hide')
        //this.hideDrawer();
    if(fcn === 'show'){
        //this.showDrawer();
        //this.updateDrawer();
    }
};

CanvasRenderer.prototype.removeSpriteEvents = function(shape){
    var poly = shape.sprite;
    poly.off('mousedown');
    poly.off('dragstart');
    poly.off('dragmove');
    poly.off('dragend');
    poly.off('mouseup');
};

CanvasRenderer.prototype.addSpriteEvents = function(shape){
    var me = this;
    if(!this.dragCache) this.dragCache = [0,0];
    //poly.setDraggable(true);
    var poly = shape.sprite;
    var gob = shape.gob;
    poly.on('mousedown', function(evt) {
        //select(view, gob);
        if(me.mode === 'delete'){
            //me.quadtree.remove(gob.shape);
            gob.isDestroyed = true;
            me.delete_fun(gob);
            return;
        }

        else if(me.mode != 'edit') return;

        evt.evt.cancelBubble = true;
        poly.shape.clearCache();

        var inSet = me.inSelectedSet(gob.shape);

        if(!inSet){
            me.unselect(me.selectedSet);
            me.resetSelectedSet();
            me.selectedSet[0] = gob.shape;
        }

        poly.setDraggable(true);
        me.editLayer.moveToTop();

        me.mouseselect = true;
        me.select( me.selectedSet);
        me.default_select(me.selectedSet);

        var scale = me.stage.scale();
        me.dragCache[0] = evt.evt.offsetX/scale.x;
        me.dragCache[1] = evt.evt.offsetY/scale.y;

        //me.shapeCache = [];
        for(var j = 0; j < me.selectedSet.length; j++){
            me.selectedSet[j].dragStart();
            me.quadtree.remove(me.selectedSet[j]);
        };

    });

    poly.on('dragstart', function() {
        me.toggleWidgets('hide');
    });

    poly.on('dragmove', function(evt) {
        var scale = me.stage.scale();
        var pos = [evt.evt.offsetX/scale.x,
                   evt.evt.offsetY/scale.y];

        poly.shape.position.x = poly.x();
        poly.shape.position.y = poly.y();
        //console.log(pos, poly.x(), poly.y());
        var bbox, bboxCache, shape, shapeCache, gsprite, fsprite;
        var dxy = [0,0];
        for(var j = 0; j < me.selectedSet.length; j++){

            var f = me.selectedSet[j];


            f.dirty = true;
            dxy[0] = pos[0] - me.dragCache[0];
            dxy[1] = pos[1] - me.dragCache[1];

            gsprite = gob.shape.sprite;
            fsprite = f;

            bbox = f.bbox;
            bboxCache = f.bboxCache;
            shapeCache = f.spriteCache;

            bbox.min[0] = bboxCache.min[0] + dxy[0];
            bbox.max[0] = bboxCache.max[0] + dxy[0];
            bbox.min[1] = bboxCache.min[1] + dxy[1];
            bbox.max[1] = bboxCache.max[1] + dxy[1];

            if(fsprite._id != gsprite._id){
                fsprite.x(shapeCache[0] + dxy[0]);
                fsprite.y(shapeCache[1] + dxy[1]);
            }
        }
        //me.updateBbox(me.selectedSet);
        if(this.shape.selfAnchor)
           this.shape.drag(evt,this);
        //me.currentLayer.draw();
        me.editLayer.draw();
    });

    poly.on('dragend', function() {
        me.toggleWidgets('show');
    });

    poly.on('mouseup', function() {
        poly.setDraggable(false);

        me.selectedSet.forEach(function(e,i,d){
            if(e.dirty)
                me.move_shape(e.gob);

            //me.quadtree.in(f);
            me.quadtree.insert(e)
        });
        ;
        //me.selectedSet.forEach(function(e,i,d){
        //     me.move_shape(e.gob);
        //});
    });

};

CanvasRenderer.prototype.viewShape = function (gob, move, select){
    var me = this;
    var r = this;
    var g = gob;
    if(!gob.shape) return;
    var poly = gob.shape.sprite;
    //this.currentLayer.add(poly);
    var dragMove = false;
    var dragStart = false;
    var dragEnd = false;

    //this.addSpriteEvents(poly, gob);
    //if(gob.shape.text)
    //    this.addSpriteEvents(gob.shape.text, gob);

    /*
    this.appendSvg ( gob );
    gob.shape.init(svgNode);
    gob.shape.update_callback = move;
    gob.shape.select_callback = select;
    gob.shape.callback_data = { view:view, gob:g };
    gob.shape.show(true);
    if (view.edit_graphics === true)
        gob.shape.realize();
    gob.shape.editable(view.edit_graphics);
    */
} ;

CanvasRenderer.prototype.hideShape = function (gob, view) {
    var shape = gob.shape;
    //gob.shape = undefined;


    if (shape) {
        this.destroy(this.selectedSet);
        this.selectedSet = [];
        //shape.sprite.hide();
        shape.destroy();
        delete shape;
    }
    this.draw();
};

CanvasRenderer.prototype.highlight = function (gob, selection) {
    // visitall to enhance on the node and its children

    var me = this;
    if(!selection){
        this.unselect(this.selectedSet);
        this.selectedSet = [];
        return;
    }
    visit_all(gob, function(g, args) {
        if (g.shape)
            me.addToSelectedSet(g.shape);
    }, selection );

    this.select(this.selectedSet);
};

CanvasRenderer.prototype.setcolor = function (gob, color) {
    // visitall to enhance on the node and its children
    visit_all(gob, function(g, args) {
            g.color_override = args[0];
    }, color );
    //this.rerender([this.viewer.current_view, true]);
};

/*
CanvasRenderer.prototype.removeFromLayer = function (gobShape) {

};
*/
//----------------------------------------------------------------------------
// graphical primitives
//----------------------------------------------------------------------------


////////////////////////////////////////////////////////////
CanvasRenderer.prototype.makeShape = function ( gob,  viewstate, shapeDescription, visibility) {
    if(!gob.vertices[0]) return;
    var z = this.viewer.tiles.cur_z;

    visibility = typeof visibility == 'undefined' ? true : visibility;

    if(gob.shape){ //JD:Don't completely understand deleting process, but: for now deferred cleanup
        if(gob.shape.isDestroyed) {
            var shape = gob.shape
            delete shape;
            gob.shape = undefined;
            return;
        }
    }

    if (gob.shape == null ) {
        var poly = new this.shapes[shapeDescription](gob, this);
        gob.shape.viewstate = viewstate;
        gob.shape = poly;

        this.viewShape (gob,
                        callback(this,'move_shape'),
                        callback(this,'select_shape'));

    }

    gob.shape.visibility = visibility;
    gob.shape.update();
    this.quadtree.insert(gob.shape);
    if(gob.dirty)
        this.stage.draw();
};


CanvasRenderer.prototype.move_shape = function ( gob ) {
    gob.shape.move();
    this.default_move(gob);
};

CanvasRenderer.prototype.select_shape = function ( view, gob ) {
    //var gob = state.gob;
    this.default_select(view, gob);
};

////////////////////////////////////////////////////////////
// individual primitives
////////////////////////////////////////////////////////////

CanvasRenderer.prototype.polygon = function (visitor, gob , viewstate, visibility) {
    this.polyline (visitor, gob, viewstate, visibility);
    if(gob.shape)
        gob.shape.closed(true);
};

CanvasRenderer.prototype.polyline = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'polygon', visibility);
};

CanvasRenderer.prototype.line = function (visitor, gob , viewstate, visibility) {
    this.polyline (visitor, gob, viewstate, visibility);
    if(gob.shape)
        gob.shape.closed(false);
};

CanvasRenderer.prototype.ellipse = function ( visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'ellipse', visibility);
};

CanvasRenderer.prototype.circle = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'circle', visibility);
};

CanvasRenderer.prototype.rectangle = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'rectangle', visibility);
};


CanvasRenderer.prototype.square = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'square', visibility);
};

CanvasRenderer.prototype.point = function (visitor, gob,  viewstate, visibility) {
    this.pointSize = 2.5;
    this.makeShape(gob, viewstate, 'point', visibility);
    if(gob.shape)
        gob.shape.setPointSize(this.pointSize);

};

CanvasRenderer.prototype.label = function (visitor, gob,  viewstate, visibility) {
    this.makeShape(gob, viewstate, 'label', visibility);
};

CanvasRenderer.prototype.getPointSize = function () {
    return this.pointSize;
};

CanvasRenderer.prototype.getMergedCanvas = function () {
    this.unselectCurrent();
    return this.currentLayer.canvas._canvas;
};

/*
///////////////////////////////////////
// LABEL is not really implemented .. need to extend 2D.js
// with SVG Text tag

CanvasRenderer.prototype.label = function ( visitor, gob, viewstate, visibility) {

    // Visibility of this gob (create/destroy gob.shape)
    // Create or destroy SVGElement for 2D.js
    // Update SVGElement with current view state ( scaling, etc )

    // viewstate
    // scale  : double (current scaling factor)
    // z, t, ch: current view planes (and channels)
    // svgdoc : the SVG document
    var offset_x  = viewstate.offset_x;
    var offset_y  = viewstate.offset_y;
    var pnt = gob.vertices[0];

    var visible = test_visible(pnt, viewstate);

    if (visibility!=undefined)
    	gob.visible=visibility;
    else if (gob.visible==undefined)
    	gob.visible=true;

    var label_text = gob.value || 'My label';

    if (visible && gob.visible) {
        if (gob.shape == null ) {
            var rect = document.createElementNS(svgns, "text");
            var innertext = document.createTextNode(label_text);
            rect.appendChild(innertext);
            rect.setAttributeNS(null, 'fill-opacity', 0.9);
            rect.setAttributeNS(null, "stroke", "black");
            rect.setAttributeNS(null, 'stroke-width', '0.5px');
            rect.setAttributeNS(null, 'stroke-opacity', 0.0);
            rect.setAttributeNS(null, 'font-size', '18px');
            rect.setAttributeNS(null, 'style', 'text-shadow: 1px 1px 4px #000000;');
            gob.shape = new Label(rect);
        }

		// scale to size
        var p = viewstate.transformPoint (pnt.x, pnt.y);
        var rect = gob.shape.svgNode;
		rect.setAttributeNS(null, "x", p.x);
		rect.setAttributeNS(null, "y", p.y);
        if (gob.color_override)
            rect.setAttributeNS(null, "fill", '#'+gob.color_override);
        else
            rect.setAttributeNS(null, "fill", "white");
        this.viewShape (viewstate, gob,
                        callback(this,"move_label"),
                        callback(this,"select_label"));

    } else {
        this.hideShape (gob, viewstate);
    }
};

CanvasRenderer.prototype.move_label = function (state){
    var gob = state.gob;
    var v   = state.view;
    //gob.shape.refresh();
    var x = gob.shape.svgNode.getAttributeNS(null,"x");
    var y = gob.shape.svgNode.getAttributeNS(null,"y");

    var newpnt = v.inverseTransformPoint (x, y);
    var pnt = gob.vertices[0] ;
    pnt.x = newpnt.x;
    pnt.y = newpnt.y;
    this.default_move(gob);
};

CanvasRenderer.prototype.select_label = function (state){
    var gob = state.gob;
    this.default_select(gob);
};
*/
