function [fg_proj fg_hist FV] = vrl_robPatchHist(I1, Ifg, noBins)
          
%% Multi Scale Patch Histograms

% Filter image with gaussians having different standard deviations
FR1 = imfilter( I1, fspecial('gauss', [21 21], 2), 'same', 'conv'); 
FR2 = imfilter( I1, fspecial('gauss', [21 21], 4), 'same', 'conv');
FR3 = imfilter( I1, fspecial('gauss', [21 21], 6), 'same', 'conv');
FV = [FR1(:) FR2(:) FR3(:)];
roi_pixels = FV( Ifg, :);
% Compute Feature Histograms
fg_hist = vrl_feathist(roi_pixels, noBins);
% BackProject Feature Histograms
fg_proj = -log( vrl_feathistbp(FV, fg_hist) + .05 );