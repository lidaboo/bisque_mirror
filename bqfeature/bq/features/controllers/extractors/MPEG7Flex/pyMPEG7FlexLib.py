from ctypes import CDLL, c_void_p, c_int, c_double, c_char_p, c_bool
from numpy import ctypeslib, asarray, empty
from numpy.ctypeslib import ndpointer
import numpy as np
import sys
import os
import inspect

#Notes
#    add masks to all
#    add documentation
#    add the other features

path=os.path.dirname(__file__) #find current dir of the file#find current dir of the file
#path=path+'/lib'
path = path+'../../../../../src/extractors/MPEG7Flex/lib'
_MPEG7FlexLib = np.ctypeslib.load_library('_MPEG7FlexLib', path)

def extractCSD(im, mask = np.array([]), descSize=64):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    
    if mask.any():
        hasmask = True
        mask = np.asarray(mask)
        mcols , mrows= mask.shape
        
        if mcols!=cols or mrows!=rows:
            raise "TypeError: The column and row vectors must be equal between"
    else:
        hasmask = False
        mask = np.asarray(np.ones([cols,rows]))
        
    _MPEG7FlexLib.computeCSD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),  c_int,\
            c_int, c_int,\
            c_bool, np.ctypeslib.ndpointer(dtype = np.intc ),\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FlexLib.computeCSD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    
    result = np.empty([descSize], dtype=np.double)
    _MPEG7FlexLib.computeCSD(im, descSize, int(rows), int(cols), hasmask , mask, result)
    return result


def extractSCD(im, mask = np.array([]), descSize=64):
    """
    """

    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    
    if mask.any():
        hasmask = True
        mask = np.asarray(mask)
        mcols , mrows= mask.shape
        
        if mcols!=cols or mrows!=rows:
            raise "TypeError: The column and row vectors must be equal between"
    else:
        hasmask = False
        mask = np.asarray(np.zeros([cols,rows]))
        
    _MPEG7FlexLib.computeSCD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),  c_int,\
            c_int, c_int,\
            c_bool, np.ctypeslib.ndpointer(dtype = np.intc ),\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FlexLib.computeSCD.restype = c_void_p

    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    
    result = np.empty([descSize], dtype=np.double)
    
    _MPEG7FlexLib.computeSCD(im, descSize, int(rows), int(cols), hasmask , mask, result)
    return result


def extractCLD(im, mask = np.array([]), numYCoef=64, numCCoef = 28):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    
    if mask.any():
        hasmask = True
        mask = np.asarray(mask)
        mcols , mrows= mask.shape
        
        if mcols!=cols or mrows!=rows:
            raise "TypeError: The column and row vectors must be equal between"
    else:
        hasmask = False
        mask = np.asarray(np.zeros([cols,rows]))
        
    _MPEG7FlexLib.computeCLD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),  c_int, c_int,\
            c_int, c_int,\
            c_bool, np.ctypeslib.ndpointer(dtype = np.intc ),\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FlexLib.computeCLD.restype = c_void_p

    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    
    result = np.empty([(numYCoef+2*numCCoef)], dtype=np.double)
    _MPEG7FlexLib.computeCLD(im, numYCoef, numCCoef, int(rows), int(cols), hasmask, mask, result)
    return result


def extractDCD(im, mask = np.array([]), normalize=True, variance=False, spatial=False, bin1=32, bin2=32, bin3=32):
    """still need to impliment spatial
    """
    
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    
    if mask.any():
        hasmask = True
        mask = np.asarray(mask)
        mcols , mrows= mask.shape
        
        if mcols!=cols or mrows!=rows:
            raise "TypeError: The column and row vectors must be equal between"
    else:
        hasmask = False
        mask = np.asarray(np.zeros([cols,rows]))    
    
    _MPEG7FlexLib.computeDCD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ), c_bool ,np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_bool, c_bool, c_bool,\
            c_int, c_int, c_int,\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.intc)]
    _MPEG7FlexLib.computeDCD.restype = c_void_p
    
    _MPEG7FlexLib.returnDCD.argtypes = [ \
            c_void_p , c_bool, c_bool,
            np.ctypeslib.ndpointer(dtype = np.double),
            np.ctypeslib.ndpointer(dtype = np.intc)]
    
    _MPEG7FlexLib.returnDCD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    
    ndc = np.empty([1,1], dtype=np.intc)
    dcd = _MPEG7FlexLib.computeDCD(im, hasmask, mask, normalize, variance, spatial, bin1, bin2, bin3,int(rows), int(cols), ndc)
    

    if variance:
        dcdlength = 7 * ndc[0,0]
    else:
        dcdlength = 4 * ndc[0,0]
    
    results = np.empty([dcdlength], dtype=np.double)
    spatial_output = np.empty([1], dtype=np.intc)
    _MPEG7FlexLib.returnDCD( dcd, variance, spatial, results, spatial_output)
    
    if spatial:
        return results, spatial_output
    else:
        return results

#need to be fix for grayscale input only
#remove mask
def extractHTD(im, layerFlag=True):
    """needs to be a grayscale image
    """
    tmp = np.asarray(im)
    cols, rows = tmp.shape    
    
    mask = np.asarray(np.zeros([cols,rows]))
    hasmask = False
    _MPEG7FlexLib.computeHTD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),  c_bool,\
            c_int, c_int,\
            c_bool, np.ctypeslib.ndpointer(dtype = np.intc ),\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FlexLib.computeHTD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    
    if layerFlag:
        descSize = 62
    else:
        descSize = 32
       
	
    result = np.empty([descSize], dtype=np.double)
    _MPEG7FlexLib.computeHTD(im, layerFlag, int(rows), int(cols), hasmask, mask, result)
    return result

def extractEHD(im,  mask = np.array([]) ):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    
    if mask.any():
        hasmask = True
        mask = np.asarray(mask)
        mcols , mrows= mask.shape
        
        if mcols!=cols or mrows!=rows:
            raise "TypeError: The column and row vectors must be equal between"
    else:
        hasmask = False
        mask = np.asarray(np.zeros([cols,rows]))
        
    _MPEG7FlexLib.computeEHD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            c_bool, np.ctypeslib.ndpointer(dtype = np.intc ),\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FlexLib.computeEHD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    
    result = np.empty([80], dtype=np.double)
    _MPEG7FlexLib.computeEHD(im, int(rows), int(cols), hasmask, mask, result)
    return result

def extractRSD(im, mask):
    """
    """
    tmp = np.asarray(im)
    cols, rows, channel = tmp.shape
    
    mask = np.asarray(mask)
    mcols , mrows= mask.shape
    
    if mcols!=cols or mrows!=rows:
        raise "TypeError: The column and row vectors must be equal between"
        
    _MPEG7FlexLib.computeRSD.argtypes = [ \
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            np.ctypeslib.ndpointer(dtype = np.intc ),\
            c_int, c_int,\
            np.ctypeslib.ndpointer(dtype = np.double)]
    _MPEG7FlexLib.computeRSD.restype = c_void_p
    
    im = tmp.astype(np.intc)
    mask = mask.astype(np.intc)
    result = np.empty([35], dtype=np.double)
    _MPEG7FlexLib.computeRSD(im, mask, int(rows), int(cols), result)
    return result



if __name__=='__main__':
    import cv2
    import time

    im=cv2.imread('test.png',cv2.CV_LOAD_IMAGE_COLOR)
    #im=cv2.imread('test2.jpg',cv2.CV_LOAD_IMAGE_COLOR) #CV_LOAD_IMAGE_GRAYSCALE CV_LOAD_IMAGE_COLOR
    mask=cv2.imread('mask.png',cv2.CV_LOAD_IMAGE_GRAYSCALE)
    start=time.time()
    feature=extractCSD(im)#, mask=mask)
    
    #invert mask
    #mask==0

    print feature
    end=time.time()
    print 'time elapsed: %s'%str(end-start)   


