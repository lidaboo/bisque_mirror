/*

Examples:

    BQ.ui.message('Attention', 'I have news', 1000); 
    
    BQ.ui.error('Something happened...'); 
    BQ.ui.warning('You are not logged in! You need to log-in to run any analysis...'); 
    BQ.ui.notification('Seed detection done! Verify results...');

    BQ.ui.tip( 'my_id', 'Verify results...', {color: 'green', timeout: 10000} );
*/


Ext.namespace('BQ.ui');

function showTip( element, text, opts ) {
  opts = opts || {};
  if (!('color' in opts)) opts.color = 'red';
  if (!('timeout' in opts)) opts.timeout = 5000;  
  opts.anchor = opts.anchor || 'top';    
  
  var tip = new Ext.ToolTip({
      target: element,
      anchor: opts.anchor,
      bodyStyle: 'font-size: 160%; color: '+opts.color+';',        
      html: text
  });
  tip.show();
  setTimeout( function () { tip.destroy(); }, opts.timeout );
}

BQ.ui = function(){
    var msgCt;

    function createBox(t, s, c){
       return '<div class="msg '+c+'"><img src="/images/cancel.png" /><h3>' + t + '</h3><p>' + s + '</p></div>';
    }
    return {
        message: function(title, format, delay, css) {
            if (!msgCt) {
                msgCt = Ext.core.DomHelper.insertFirst(document.body, {id:'messagepopup'}, true);
            }
            if (delay == undefined) delay = 3000;
            if (css == undefined) css = '';            
            var s = Ext.String.format.apply(String, Array.prototype.slice.call(arguments, 1));
            var m = Ext.core.DomHelper.append(msgCt, createBox(title, s, css), true);
            m.hide();
            m.on('click', function(){ 
                    this.stopAnimation();
                    //this.fadeOut( {remove: true} );
                    this.destroy(); 
                }, m, { 
                single: true, 
                stopEvent : true, 
            });
            m.slideIn('t').ghost("t", { delay: delay, remove: true});
        },

        popup: function(type, text, delay) {
            var t = BQ.ui.types[type] || BQ.ui.types['notification'];
            BQ.ui.message( t.title, text, delay || t.delay, t.cls );
        },

        notification: function(text, delay) {
            BQ.ui.popup('notification', text, delay );
        },

        attention: function(text, delay) {
            BQ.ui.popup('attention', text, delay );
        },
        
        warning: function(text, delay) {
            BQ.ui.popup('warning', text, delay );            
        },        

        error: function(text, delay) {
            BQ.ui.popup('error', text, delay );
        },
  
        tip: function( element, text, opts ) {
            opts = opts || {};
            if (!('color' in opts)) opts.color = 'red';
            if (!('timeout' in opts)) opts.timeout = 5000;  
            opts.anchor = opts.anchor || 'top';               
            var tip = new Ext.ToolTip({
              target: element,
              anchor: opts.anchor,
              bodyStyle: 'font-size: 160%; color: '+opts.color+';',        
              html: text
            });
            tip.show();
            setTimeout( function () { tip.destroy(); }, opts.timeout );
        },

        highlight: function( element, text, opts ) {
            opts = opts || {};
            opts.timeout = opts.timeout || 5000;  
            opts.anchor = opts.anchor || 'top';    
            
            var w = Ext.create('Ext.ToolTip', Ext.apply({
              target: element,
              anchor: opts.anchor,
              cls: 'highlight',
              html: text,
              autoHide: false,
              shadow: false,
            }, opts));
            w.show();
            w.getEl().fadeOut({ delay: opts.timeout, remove: true});
        },

    };
}();

BQ.ui.types = {
    'notification': { delay: 5000,  title: '',        cls: 'notification' },
    'attention':    { delay: 10000, title: '',        cls: 'warning' },
    'warning':      { delay: 10000, title: 'Warning', cls: 'warning' },
    'error':        { delay: 50000, title: 'Error',   cls: 'error' },            
};

