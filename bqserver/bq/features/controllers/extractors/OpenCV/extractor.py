# -*- mode: python -*-
""" OpenCV Feature
"""
import cv2
import cv
import logging
import numpy as np
from bq.features.controllers import Feature #import base class
from pylons.controllers.util import abort
log = logging.getLogger("bq.features")
import tables

class BRISK(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'BRISK'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 64
    
    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            x         = tables.Float32Col(pos=3)
            y         = tables.Float32Col(pos=4)
            response  = tables.Float32Col(pos=5)
            size      = tables.Float32Col(pos=6)
            angle     = tables.Float32Col(pos=7)
            octave    = tables.Float32Col(pos=8)
            
        self.Columns = Columns    
        
    @Feature.wrapper        
    def calculate(self, uri):
        """ Append descriptors to BRISK h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        fs = cv2.BRISK().detect(im)                             # keypoints
        
        log.debug('fs: %s' %len(fs))
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("BRISK")
        (kpts, descriptors) = descriptor_extractor.compute(im,fs)

        if descriptors == None: #taking Nonetype into account
            descriptors=[]
        
        x=[]
        y=[]
        response=[]
        size=[]
        angle=[]
        octave=[]
        for k in kpts:
            x.append(k.pt[0])
            y.append(k.pt[1])
            response.append(k.response)
            size.append(k.size)
            angle.append(k.angle)
            octave.append(k.octave)
        
        return descriptors,x,y,response,size,angle,octave
#
class BRISKc(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'BRISKc'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 64
    
    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            x         = tables.Float32Col(pos=3)
            y         = tables.Float32Col(pos=4)
            response  = tables.Float32Col(pos=5)
            size      = tables.Float32Col(pos=6)
            angle     = tables.Float32Col(pos=7)
            octave    = tables.Float32Col(pos=8)
            
        self.Columns = Columns
        
    @Feature.wrapper        
    def calculate(self, uri):
        """ Append descriptors to SIFT h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]/5
        else:
            scale=imagesize[0]/5
            
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)       # keypoints
        
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("BRISK")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])

        if descriptors == None: #taking Nonetype into account
            descriptors=[]
        
        x=[]
        y=[]
        response=[]
        size=[]
        angle=[]
        octave=[]
        for k in kpts:
            x.append(k.pt[0])
            y.append(k.pt[1])
            response.append(k.response)
            size.append(k.size)
            angle.append(k.angle)
            octave.append(k.octave)
        
        return descriptors,x,y,response,size,angle,octave

  
          
class ORB(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'ORB'
    description = """The algorithm uses FAST in pyramids to detect stable keypoints, selects the 
    strongest features using FAST response, finds their orientation using first-order moments and
    computes the descriptors using BRIEF (where the coordinates of random point pairs (or k-tuples)
    are rotated according to the measured orientation).
    This explination was taken from opencv documention on orb and the algorithm iself was taken from
    the opencv library"""
    length = 32
    contents = 'several points are described in an image, each will have a position: X Y Scale'

    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            x         = tables.Float32Col(pos=3)
            y         = tables.Float32Col(pos=4)
            response  = tables.Float32Col(pos=5)
            size      = tables.Float32Col(pos=6)
            angle     = tables.Float32Col(pos=7)
            octave    = tables.Float32Col(pos=8)
            
        self.Columns = Columns

    @Feature.wrapper        
    def calculate(self, uri):
        """ Append descriptors to ORB h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im      
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        fs = cv2.ORB().detect (im)                             # keypoints
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("ORB")
        (kpts, descriptors) = descriptor_extractor.compute(im,fs)
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            
        x=[]
        y=[]
        response=[]
        size=[]
        angle=[]
        octave=[]
        for k in kpts:
            x.append(k.pt[0])
            y.append(k.pt[1])
            response.append(k.response)
            size.append(k.size)
            angle.append(k.angle)
            octave.append(k.octave)
        
        return descriptors,x,y,response,size,angle,octave

class ORBc(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'ORBc'
    description = """The algorithm uses FAST in pyramids to detect stable keypoints, selects the 
    strongest features using FAST response, finds their orientation using first-order moments and
    computes the descriptors using BRIEF (where the coordinates of random point pairs (or k-tuples)
    are rotated according to the measured orientation).
    This explination was taken from opencv documention on orb and the algorithm iself was taken from
    the opencv library"""
    length = 32
    contents = 'several points are described in an image, each will have a position: X Y Scale'


    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            x         = tables.Float32Col(pos=3)
            y         = tables.Float32Col(pos=4)
            response  = tables.Float32Col(pos=5)
            size      = tables.Float32Col(pos=6)
            angle     = tables.Float32Col(pos=7)
            octave    = tables.Float32Col(pos=8)
            
        self.Columns = Columns

    @Feature.wrapper        
    def calculate(self, uri):
        """ Append descriptors to ORB h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im      
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]
        else:
            scale=imagesize[0]
            
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)       # keypoints
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("ORB")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            
        x=[]
        y=[]
        response=[]
        size=[]
        angle=[]
        octave=[]
        for k in kpts:
            x.append(k.pt[0])
            y.append(k.pt[1])
            response.append(k.response)
            size.append(k.size)
            angle.append(k.angle)
            octave.append(k.octave)
        
        return descriptors,x,y,response,size,angle,octave


class SIFT(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'SIFT'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 128
    feature_format = "int32"
    
    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            x         = tables.Float32Col(pos=3)
            y         = tables.Float32Col(pos=4)
            response  = tables.Float32Col(pos=5)
            size      = tables.Float32Col(pos=6)
            angle     = tables.Float32Col(pos=7)
            octave    = tables.Float32Col(pos=8)
            
        self.Columns = Columns
    
    @Feature.wrapper
    def calculate(self, uri):
        """ Append descriptors to SIFT h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        fs = cv2.SIFT().detect(im)                             # keypoints
        
        #log.debug('fs: %s' %len(fs))
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("SIFT")
        (kpts, descriptors) = descriptor_extractor.compute(im,fs)

        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            
        x=[]
        y=[]
        response=[]
        size=[]
        angle=[]
        octave=[]
        for k in kpts:
            x.append(k.pt[0])
            y.append(k.pt[1])
            response.append(k.response)
            size.append(k.size)
            angle.append(k.angle)
            octave.append(k.octave)
        
        return descriptors,x,y,response,size,angle,octave


class SIFTc(SIFT):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'SIFTc'
    description = """Scale-invariant feature transform also know as SIFT """
     
    @Feature.wrapper        
    def calculate(self, uri):
        """ Append descriptors to SIFT h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]/3
        else:
            scale=imagesize[0]/3
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)   # keypoints
        
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("SIFT")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            
        x=[]
        y=[]
        response=[]
        size=[]
        angle=[]
        octave=[]
        for k in kpts:
            x.append(k.pt[0])
            y.append(k.pt[1])
            response.append(k.response)
            size.append(k.size)
            angle.append(k.angle)
            octave.append(k.octave)
        
        return descriptors,x,y,response,size,angle,octave
    

#class SIFTg(SIFT):
#    """
#        Initalizes table and calculates the ORB descriptor to be
#        placed into the HDF5 table.
#    """
#    
#    #parameters
#    file = 'features_siftg.h5'
#    name = 'SIFTg'
#    description = """Scale-invariant feature transform also know as SIFT """
#        
#        
#    def appendTable(self, uri, idnumber):
#        """ Append descriptors to SIFT h5 table """
#        
#        Session = BQSession().init_local('admin','admin',bisque_root='')
#        data = Session.fetchxml(uri+'?view=deep,clean') #needs to be changed only for prototyping purposes
#        vertices=data.xpath('point/vertex')
#        log.debug('vertices: %s' % vertices)
#        resource_uniq = data.attrib['resource_uniq']
#        Im = Feature.ImageImport(image_service/images/'+resource_uniq) #importing image from image service
#        image_path = Im.returnpath()
#        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
#        del Im     
#        im=np.asarray(im)
#        if not im.any():
#            abort(415, 'Format was not supported')
#        
#        imagesize=im.shape
#        fs=[]
#        for vertex in vertices:
#            fs.append(cv2.KeyPoint(float(vertex.attrib['x']),float(vertex.attrib['y']),50))  # keypoints
#        
#        # extract the feature keypoints and descriptor
#        descriptor_extractor = cv2.DescriptorExtractor_create("SIFT")
#        (kpts, descriptors) = descriptor_extractor.compute(im,fs)
#        
#        if descriptors == None: #taking Nonetype into account
#            descriptors=[]
#            self.setRow(uri, idnumber, [None], [None])
#        
#        #initalizing rows for the table
#        else:
#            for i in range(0,len(descriptors)):
#                parameter=[kpts[i].pt[0],kpts[i].pt[1],kpts[i].response,kpts[i].size,kpts[i].angle,kpts[i].octave]
#                self.setRow(uri, idnumber, descriptors[i], parameter)

                
class SURF(Feature.Feature):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'SURF'
    description = """Speeded Up Robust Features also know as SURF"""
    length = 64 

    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            x         = tables.Float32Col(pos=3)
            y         = tables.Float32Col(pos=4)
            laplacian = tables.Float32Col(pos=5)
            size      = tables.Float32Col(pos=6)
            direction = tables.Float32Col(pos=7)
            hessian   = tables.Float32Col(pos=8)
            
        self.Columns = Columns
        
    @Feature.wrapper        
    def calculate(self, uri):
        """ Append descriptors to SURF h5 table """
        #initalizing
        extended = 0
        HessianThresh = 400
        nOctaves = 3
        nOctaveLayers = 4

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        (kpts,descriptors)=cv.ExtractSURF(cv.fromarray(im), None, cv.CreateMemStorage(), (extended, HessianThresh, nOctaves, nOctaveLayers)) #calculating descriptor
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            
        x=[]
        y=[]
        laplacian=[]
        size=[]
        direction=[]
        hessian=[]
        for k in kpts:
            x.append(k[0][0])
            y.append(k[0][1])
            laplacian.append(k[1])
            size.append(k[2])
            direction.append(k[3])
            hessian.append(k[4])
        
        return descriptors,x,y,laplacian,size,direction,hessian

    
class SURFc(SURF):
    """
        Initalizes table and calculates the SURF descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'SURFc'
    description = """Speeded Up Robust Features also know as SURF"""
        
    @Feature.wrapper        
    def calculate(self, uri):
        """ Append descriptors to SURF h5 table """
        #initalizing
        extended = 0
        HessianThresh = 400
        nOctaves = 3
        nOctaveLayers = 4

        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]
        else:
            scale=imagesize[0]
        
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)       # keypoints
        descriptor_extractor = cv2.DescriptorExtractor_create("SURF")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            
        x=[]
        y=[]
        response=[]
        size=[]
        angle=[]
        octave=[]
        for k in kpts:
            x.append(k.pt[0])
            y.append(k.pt[1])
            response.append(k.response)
            size.append(k.size)
            angle.append(k.angle)
            octave.append(k.octave)
        
        return descriptors,x,y,response,size,angle,octave

class FREAKc(Feature.Feature):
    """
        Initalizes table and calculates the ORB descriptor to be
        placed into the HDF5 table.
    """
    
    #parameters
    name = 'FREAKc'
    description = """Scale-invariant feature transform also know as SIFT """
    length = 64
    
    def columns(self):
        """
            creates Columns to be initalized by the create table
        """
        featureAtom = tables.Atom.from_type(self.feature_format, shape=(self.length ))
        class Columns(tables.IsDescription):
            idnumber  = tables.StringCol(32,pos=1)
            feature   = tables.Col.from_atom(featureAtom, pos=2)
            x         = tables.Float32Col(pos=3)
            y         = tables.Float32Col(pos=4)
            response  = tables.Float32Col(pos=5)
            size      = tables.Float32Col(pos=6)
            angle     = tables.Float32Col(pos=7)
            octave    = tables.Float32Col(pos=8)
        
    @Feature.wrapper        
    def calculate(self, uri):
        """ Append descriptors to SIFT h5 table """
        
        Im = Feature.ImageImport(uri) #importing image from image service
        image_path = Im.returnpath()
        im=cv2.imread(image_path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
        del Im     
        im=np.asarray(im)
        if not im.any():
            abort(415, 'Format was not supported')
        
        imagesize=im.shape
        if imagesize[0]>imagesize[1]:
            scale=imagesize[1]/10
        else:
            scale=imagesize[0]/10
            
        fs = cv2.KeyPoint(imagesize[0]/2,imagesize[1]/2,scale)       # keypoints
        
        
        # extract the feature keypoints and descriptor
        descriptor_extractor = cv2.DescriptorExtractor_create("FREAK")
        (kpts, descriptors) = descriptor_extractor.compute(im,[fs])
        
        if descriptors == None: #taking Nonetype into account
            descriptors=[]
            
        x=[]
        y=[]
        response=[]
        size=[]
        angle=[]
        octave=[]
        for k in kpts:
            x.append(k.pt[0])
            y.append(k.pt[1])
            response.append(k.response)
            size.append(k.size)
            angle.append(k.angle)
            octave.append(k.octave)
        
        return descriptors,x,y,response,size,angle,octave
            