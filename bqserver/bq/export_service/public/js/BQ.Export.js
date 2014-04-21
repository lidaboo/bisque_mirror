Ext.define('BQ.Export.Panel', {
    extend : 'Ext.panel.Panel',

    date_pattern: BQ.Date.patterns.ISO8601Long,

    constructor : function() {
        Ext.apply(this, {
            heading : 'Download Images',
            layout : 'fit',
        });

        this.callParent(arguments);
    },

    initComponent : function() {
        this.types_ignore = Ext.clone(BQ.resources.system);
        this.types_ignore.dataset = null; // we'll have a special picker for dataset
        this.types_ignore.image = null; // we'll have a special picker for dataset
        this.dockedItems = [{
            xtype : 'toolbar',
            dock : 'top',
            defaults: {
                scale: 'large'
            },
            allowBlank: false,
            cls: 'tools',
            border: 0,
            layout: {
                overflowHandler: 'Menu'
            },
            items : [{
                xtype : 'tbtext',
                html : '<h2>' + this.heading + ':</h2>'
            }, {
                xtype : 'splitbutton',
                cls: 'x-btn-default-large',
                text : 'Add images',
                iconCls : 'icon-select-images',
                resourceType : 'image',
                handler : this.selectImage,
                scope : this,
                menu : { // dima: requires adding all other resource types
                    plain: true,
                    itemId: 'menu_resources',
                },
            }, {
                text : 'Add dataset',
                cls: 'x-btn-default-large',
                iconCls : 'icon-select-dataset',
                handler : this.selectDataset,
                scope : this,
            }, /*{
                text : 'Add Folder',
                cls: 'x-btn-default-large',
                iconCls : 'icon-select-dataset',
                //handler : this.selectFolder,
                scope : this,
            }*/]
        }, {
            xtype : 'toolbar',
            dock : 'bottom',
            cls: 'footer',
            border: 0,
            defaults: {
                scale: 'large',
                cls: 'x-btn-default-large',
            },
            items : [{
                xtype : 'splitbutton',
                text : 'Download',
                iconCls : 'icon-download',
                arrowAlign : 'right',
                menuAlign : 'bl-tl?',
                compressionType : 'tar',

                handler : this.download,
                scope : this,

                menu : {
                    defaults : {
                        xtype : 'menucheckitem',
                        group : 'downloadGroup',
                        groupCls : Ext.baseCSSClass + 'menu-group-icon',
                        checked : false,
                        scope : this,
                        handler : this.download,
                    },
                    items : [{
                        compressionType : 'tar',
                        text : 'as TARball',
                    }, {
                        compressionType : 'gzip',
                        text : 'as GZip archive',
                        checked : true,
                    }, {
                        compressionType : 'bz2',
                        text : 'as BZip2 archive',
                    }, {
                        compressionType : 'zip',
                        text : 'as (PK)Zip archive',
                    }],
                }
            }/*, {
                text : 'Export to Google Docs',
                disabled : true,
                iconCls : 'icon-gdocs',
            }*/]
        }];

        this.callParent(arguments);
        this.add(this.getResourceGrid());
        this.fetchResourceTypes();
    },

    fetchResourceTypes : function() {
        BQFactory.request ({
            uri : '/data_service/',
            cb : callback(this, this.onResourceTypes),
            errorcb : function(error) {
                BQ.ui.error('Error fetching resource types:<br>'+error.message, 4000);
            },
            cache : false,
        });
    },

    onResourceTypes : function(resource) {
        var types = {};
        BQApp.resourceTypes = [];
        var r=null;
        for (var i=0; (r=resource.children[i]); i++) {
            BQApp.resourceTypes.push({name:r.name, uri:r.uri});
            types[r.name] = '/data_service/' + r.name;
        }

        var items = [];
        var keys = Object.keys(types).sort();
        var name = null;
        for (var i=0; name=keys[i]; ++i) {
            if (name in this.types_ignore) continue;
            items.push({
                resourceType : name,
                text: name,
                scope: this,
                handler : this.selectImage,
            });
        }

        this.queryById('menu_resources').add(items);
    },

    downloadResource : function(resource, compression) {
        if (!( resource instanceof Array))
            resource = [resource];

        for (var i = 0, type, record = []; i < resource.length; i++) {
            type = resource[i].resource_type;

            if (type != 'dataset' || compression === 'none')
                type = 'file';

            record.push(['', '', type, resource[i].ts, '', resource[i].uri, 0]);
        }

        this.resourceStore.loadData(record);
        this.download({
            compressionType : compression
        });
    },

    download : function(btn) {
        if (!this.resourceStore.count()) {
            BQ.ui.notification('Nothing to download! Please add files or datasets first...');
            return;
        }

        function findAllbyType(type) {
            var index = 0, list = [];

            while (( index = this.resourceStore.find('type', type, index)) != -1) {
                // add quotes to make it work in Safari
                list.push(this.resourceStore.getAt(index).get('uri'));
                index++;
            }

            return list;
        }

        Ext.create('Ext.form.Panel', {
            url : '/export/initStream',
            defaultType : 'hiddenfield',
            method : 'GET',
            standardSubmit : true,
            items : [{
                name : 'compressionType',
                value : btn.compressionType,
            }, {
                name : 'files',
                value : findAllbyType.call(this, 'image').concat(findAllbyType.call(this, 'file')),
            }, {
                name : 'datasets',
                value : findAllbyType.call(this, 'dataset'),
            }, {
                name : 'dirs',
                value : findAllbyType.call(this, 'dir'),
            }]
        }).submit();
    },

    exportResponse : function(response) {
    },

    selectImage : function(me) {
        var rbDialog = Ext.create('Bisque.ResourceBrowser.Dialog', {
            width : '85%',
            height : '85%',
            dataset : '/data_service/' + me.resourceType,
            wpublic : 'true',
            listeners : {
                Select : this.addToStore,
                scope : this
            }
        });
    },

    selectDataset : function() {
        var rbDialog = Ext.create('Bisque.DatasetBrowser.Dialog', {
            'height' : '85%',
            'width' : '85%',
            wpublic : 'true',
            listeners : {
                DatasetSelect : this.addToStore,
                scope : this
            }
        });
    },

    addToStore : function(rb, resource) {
        if ( resource instanceof Array) {
            for (var i = 0; i < resource.length; i++)
                this.addToStore(rb, resource[i]);
            return;
        }

        var thumbnail = '';
        var viewPriority = 2;
        if (resource.resource_type === 'image') {
            thumbnail = resource.src;
            viewPriority = 1;
        } else if (resource.resource_type === 'dataset') {
            viewPriority = 0;
        }

        var record = [
            thumbnail,
            resource.name || '',
            resource.resource_type,
            resource.ts,
            resource.permission || '',
            resource.uri,
            viewPriority
        ];
        this.resourceStore.loadData([record], true);
    },

    getResourceGrid : function() {
        var me = this;
        this.resourceGrid = Ext.create('Ext.grid.Panel', {
            store : this.getResourceStore(),
            border : 0,
            listeners : {
                scope : this,
                itemdblclick : function(view, record, item, index) {
                    // delegate resource viewing to ResourceView Dispatcher
                    var newTab = window.open('', "_blank");
                    newTab.location = bq.url('/client_service/view?resource=' + record.get('uri'));
                }
            },

            columns : {
                items : [{
                    width : 80,
                    dataIndex : 'icon',
                    menuDisabled : true,
                    sortable : false,
                    align : 'center',
                    renderer : function(value, cell, record) {
                        if (record.data.type === 'image') {
                            return '<div class="thumbnail '+record.data.type+'" style="background-image: url(\''+value+'?thumbnail=280,280\');"/>';
                        } else {
                            return '<div class="thumbnail '+record.data.type+'" />';
                        }
                    }
                }, {
                    text : 'Name',
                    flex : 0.6,
                    maxWidth : 350,
                    sortable : true,
                    dataIndex : 'name'
                }, {
                    text : 'Type',
                    flex : 0.4,
                    maxWidth : 200,
                    align : 'center',
                    sortable : true,
                    dataIndex : 'type',
                    renderer : function(value, cell, record) {
                        return Ext.String.capitalize(value);
                    }
                }, {
                    text : 'Date created',
                    flex : 0.5,
                    maxWidth : 250,
                    align : 'center',
                    sortable : true,
                    dataIndex : 'ts',
                    renderer : function(value, cell, record) {
                        var date = Ext.Date.parse(value, BQ.Date.patterns.BisqueTimestamp);
                        var pattern = (me ? me.date_pattern : undefined) || BQ.Date.patterns.ISO8601Long;
                        return Ext.Date.format(date, pattern);
                    }
                }, {
                    text : 'Published',
                    flex : 0.4,
                    maxWidth : 200,
                    align : 'center',
                    sortable : true,
                    dataIndex : 'public',
                    renderer : function(value, cell, record) {
                        return (value === 'published') ? '<b>Yes</b>' : 'No';
                    }
                }, {
                    xtype : 'actioncolumn',
                    maxWidth : 80,
                    menuDisabled : true,
                    sortable : false,
                    align : 'center',
                    items : [{
                        icon : bq.url('../export_service/public/images/delete.png'),
                        align : 'center',
                        tooltip : 'Remove',
                        handler : function(grid, rowIndex, colIndex) {
                            var name = grid.store.getAt(rowIndex).get('name');
                            grid.store.removeAt(rowIndex);
                            BQ.ui.message('Export - Remove', 'File ' + name + ' removed!');
                        }
                    }]
                }],
                defaults : {
                    tdCls : 'align'
                }
            }
        });

        return this.resourceGrid;
    },

    getResourceStore : function() {
        this.resourceStore = Ext.create('Ext.data.ArrayStore', {
            fields : ['icon', 'name', 'type', 'ts', 'public', 'uri', 'viewPriority'],
            sorters : [{
                property : 'viewPriority',
                direction : 'ASC'
            }]
        });
        return this.resourceStore;
    }
});
