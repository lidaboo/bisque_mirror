% Loads ND images from the Bisque system without requiring local storage
%   I = bq.imreadND(url, user, password)
%
% 2.8X faster than using BQLib and more generic returning correct result
% Remember, all the image data is stored within matlab memory, so you can 
% run out of it if loading a very large image!!!
%
% INPUT:
%    url - a url to a Bisque image, may contain authentication inline
%            * Basic Auth - http://user:pass@host/path
%            * Bisque Mex - http://Mex:IIII@host/path
%
% OUTPUT:
%    I   - an ND matrix, with dimensions order: Y X C Z T
%
% EXAMPLES:
%   I = bq.imreadND('http://user:pass@host/imgsrv/XXXXX?slice=,,,2&remap=1');
%     this will fetch a 3D image (all z planes) at time point 2 and only
%     of the first channel
%   
%   AUTHOR:
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 2011-06-27 First implementation
%

function I = imreadND(url, user, password)

    % default to Matlab if it's a local path
    if ~strfind(url, '://'),
        I = imread(url);
        return;
    end

    %% parse the url
    purl = bq.Url(url);
    if purl.hasUser() && purl.hasPassword(),
        user = purl.getUser();
        password = purl.getPassword();        
    end        
    
    %% fetch metadata from image service
    purl.pushQuery('dims');     
    if exist('user', 'var') && exist('password', 'var'),
        doc = bq.get_xml( purl.toString(), user, password );
    else
        doc = bq.get_xml( purl.toString() );
    end 
    
    template = '//image/tag[@name=''%s'']';
    tags = { 'zsize',       'int'; 
             'tsize',       'int';              
             'channels',    'int'; 
             'width',       'int';
             'height',      'int';             
             'depth',       'int';
             'pixelType',   'str';
             'pixelFormat', 'str';
           };
    info = bq.parsetags(doc, tags, template);
    purl.popQuery();    
    

    %% fetch image data stream and reshape it
    purl.pushQuery('format', 'raw');
    if exist('user', 'var') && exist('password', 'var'),
        [I, res] = bq.get(purl.toString(), [], user, password);
    else
        [I, res] = bq.get(purl.toString());
    end  
    if res.status>=300 || isempty(I),
        I = []; return;
    end
    I = typecast(I, info.pixelFormat);
    I = squeeze(reshape(I, info.width, info.height, info.channels, info.zsize, info.tsize)); 
    
    % matlab uses row-major order, opposite to column-major in Bisque
    % we need to transpose all the image planes
    p = 1:length(size(I));
    p(1:2) = [2 1];
    I = permute(I, p);
end

