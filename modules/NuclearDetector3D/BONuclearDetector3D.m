%%  BONucleiDetector3D - 3D nuclei detector
%   
%   REFERENCE:
%       B. Obara and D. Fedorov and C.D. Banna and B.S. Manjunath,
%       Automatic system for detection and validation of cell nuclei in 
%       3D CLS microscopy imagery, SOON :)
%
%   INPUT:
%       imn     - nuclei channel
%       imm     - membrane channel
%       ns      - half of nuclear size[pixels] = 
%                   ns[microns]*[1/resolutionx 1/resolutiony 1/resolutionz]
%       t       - range of lowest intensity bound
%
%   OUTPUT:
%       np      - detected nuclei positions, is a matrix where
%                   np(:,1) -> Y coordinate (starting at 1)
%                   np(:,2) -> X coordinate (starting at 1)
%                   np(:,3) -> Z coordinate (starting at 1)
%                   np(:,4) -> point IDs
%                   np(:,5) -> confidence estimate 
%                   np(:,6) -> average LoG intensity of nuclei volumes
%
%   AUTHOR:
%       Boguslaw Obara, http://boguslawobara.net/
%       Dmitry Fedorov, www.dimin.net
%
%   VERSION:
%       0.1 - 30/06/2009 First implementation
%       0.2 - 04/06/2010 LoG + revision
%       0.3 - 24/09/2010 Speed up
%       0.4 - 2011-06-03 by Dmitry: major rewrite with ~8X speedup, 
%                                   support for image types other than
%                                   double
%%

function np = BONuclearDetector3D(imn, ns, t, session, timetext)
    if ~exist('timetext', 'var'), 
        timetext=''; 
    end
    
    %% Convolve with LoG
    if exist('session', 'var'), session.update([timetext '10% - Blob detection']); end 
    fprintf('Blob detection\n');
    tic;    
    imlog = BOBlobDetector3D(imn, ns);
    toc

    %% Finding seeds
    if exist('session', 'var'), session.update([timetext '40% - Seed search']); end
    fprintf('Seed search\n');    
    t = sort(t);
    np = BOSeedSearch3D(imlog, ns, t);
    clearvars imlog; 
    
    %% removing unchanging point sets towards low thresholds
    dnp = zeros(size(np,1),1);
    for i=1:size(np,1)-1,
        dnp(i) = size(np{i},1) - size(np{i+1},1);
        if max(size(np{i},1), size(np{i+1},1)) < 5000,
            dnp(i) = 0;
        end
    end
    
    % detecting the spike in the number of detections and removing
    % everything towards lower thresholds
    [~,idx] = max(dnp);
    if idx>1,
        idx = min(idx+1, size(np,1));
    end
    np = np(idx:end);
        
    %% Filtering
    if exist('session', 'var'), session.update([timetext '70% - Filtering']); end
    fprintf('Filtering\n');  
    tic;
    for i=1:length(np),
        dt = GetCentroidDescriptors3D(imn, np{i}, ns);
        np{i} = Filter3DPointsByDescriptor(np{i}, dt, ns*1.1);
    end
    toc

    %% Merging    
    if exist('session', 'var'), session.update([timetext '90% - Merging']); end
    fprintf('Merging\n');     
    tic;
    np = MergeThresholds(np);
    dt = GetCentroidDescriptors3D(imn, np, ns);
    toc
    
    %% Producing final list     
    sz = size(np,1);
    counts = np(:,4);
    img_mean = zeros(sz,1);
    for i=1:sz,   
        img_mean(i) = dt{i}.mean;
    end  

    img_mean = scalev(img_mean);
    counts = scalev(counts);

    feature = (5*counts + 5*img_mean)/ 10;
    feature = scalev(feature);

    np(:,5) = feature;

    np = sortrows(np, 5);
end

function v = scalev(v)
    if max(v)<=min(v),
        v = ones(length(v),1);
    else
        v = ( v - min(v) ) / ( max(v) - min(v) );
    end
end
