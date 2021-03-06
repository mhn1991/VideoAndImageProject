#!/usr/bin/python3
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
from numpy import r_
import os
import sys

Q=[
    [8,  8,  6,  6,  4,  4,  2,  2],
    [8,  8,  6,  6,  4,  4,  2,  2],
    [6,  6,  6,  6,  4,  4,  2,  2],
    [6,  6,  6,  6,  4,  4,  2,  2],
    [4,  4,  4,  4,  4,  4,  2,  2],
    [4,  4,  4,  4,  4,  4,  2,  2],
    [2,  2,  2,  2,  2,  2,  2,  2],
    [2,  2,  2,  2,  2,  2,  2,  2]
]

def alpha(u,x):
        if u == 0:
            return np.ones(x)/np.sqrt(x)
        else:
            return np.sqrt(2.0/x)*np.cos((u*np.pi/(2*x))*(np.arange(x)*2+1))


def dct(array):
    shape = array.shape[0]
    cosineMat = np.array([alpha(i,shape) for i in range(shape)])
    tmpMat = np.zeros((shape,shape,shape,shape))
    for i in range(shape):
        for j in range(shape):
            cx,cy = np.meshgrid(cosineMat[i],cosineMat[j])
            tmpMat[i, j] = cx * cy
    final = np.sum(tmpMat.reshape(shape*shape,shape*shape) * array.reshape(shape*shape),axis=1).reshape(shape,shape)
    return final

def idct(array):
    shape = array.shape[0]
    cosineMat = np.array([alpha(i,shape) for i in range(shape)])
    tmpMat = np.zeros((shape,shape,shape,shape))
    for i in range(shape):
        for j in range(shape):
            cx,cy = np.meshgrid(cosineMat[i],cosineMat[j])
            tmpMat[i, j] = cx * cy
    final = np.sum((array.reshape(shape,shape,1)*tmpMat.reshape(shape,shape,shape*shape)).reshape(shape*shape,shape*shape),axis=0).reshape(shape,shape)
    return final


def quantise(block):
    return np.array([[round(a/q) for a,q in zip(a,q)] for a,q in zip(block,Q)])

def dequantise(block):
    return np.array([[a*q for a,q in zip(a,q)] for a,q in zip(block,Q)])

def meanSquareError(orgImg, finalImg):
    return np.square(np.subtract(orgImg,finalImg)).mean()

def SquareNoiseRatio(img,mse):
        return 10*np.log10(np.var(img)/np.sqrt(mse))

def numBits(img):
    return np.sum( img != 0.0 )

def dctThresh(path,thresh = 0.012):
    im = Image.open(path)
    img = np.array(im.copy())
    im.close()
    imsize = img.shape
    arr = np.zeros(imsize)
    for i in r_[:imsize[0]:8]:
        for j in r_[:imsize[1]:8]:
            arr[i:(i+8),j:(j+8)] = dct(img[i:(i+8),j:(j+8)] )
            dct_thresh = arr * (abs(arr) > (thresh*np.max(arr)))
    return dct_thresh


def revDctThresh(img):
    imsize = img.shape
    im_dct = np.zeros(imsize)
    for i in r_[:imsize[0]:8]:
        for j in r_[:imsize[1]:8]:
            im_dct[i:(i+8),j:(j+8)] = idct(img[i:(i+8),j:(j+8)])
    return im_dct

def QuanDct():
    im = Image.open(path)
    img = np.array(im.copy())
    im.close()
    imsize = img.shape
    arr = np.zeros(imsize)
    for i in r_[:imsize[0]:8]:
        for j in r_[:imsize[1]:8]:
            arr[i:(i+8),j:(j+8)] = quantise(dct(img[i:(i+8),j:(j+8)]))
    return arr


def Encode(path,thresh = 0.012):
    im = Image.open(path)
    img = np.array(im.copy())
    im.close()
    imsize = img.shape
    arr = np.zeros(imsize)
    for i in r_[:imsize[0]:8]:
        for j in r_[:imsize[1]:8]:
            arr[i:(i+8),j:(j+8)] = quantise(dct(img[i:(i+8),j:(j+8)]))
            dct_thresh = arr * (abs(arr) > (thresh*np.max(arr)))
    return dct_thresh

def deCode(img):
    imsize = img.shape
    im_dct = np.zeros(imsize)
    for i in r_[:imsize[0]:8]:
        for j in r_[:imsize[1]:8]:
            im_dct[i:(i+8),j:(j+8)] = idct( dequantise(img[i:(i+8),j:(j+8)]))
    return im_dct
#bpp = (size / (width * hight)) * 8
# 8 because it will change to Byte
def calBpp(size,w,h):
    return (size/(w*h))*8


class Pyramid() :
    def __init__(self) :
        pass
    def setImage(self, image) :
        self.filter = np.array([[1/16.,1/8.,1/16.],[1/8.,1/4.,1/8.],[1/16.,1/8.,1/16.]])
        self.Image = image      
        self.M = image.shape[0]
        self.N = image.shape[1]
    def subsample(self) : 
        self.subSampled = self.Image[::2,::2]       
        return self.subSampled
    def smoothen(self):
        img = np.ones((self.M+2,self.N+2))*128
        img[1:-1,1:-1] = self.Image

        for m in range(self.M) :
            for n in range(self.N) :
                img[m+1,n+1] = sum(sum(img[m:m+3,n:n+3]*self.filter))

        self.smoothened = img[1:-1,1:-1]
        return self.smoothened
    def subtractImage(self) :
        upsampled = self.upsample()
        self.subtractImage = np.subtract(upsampled[0:self.Image.shape[0], :self.Image.shape[1]], self.Image)
        return self.subtractImage
    def upsample(self, image=None) :
        if image is None :
            image = self.subSampled
        m = image.shape[0]
        n = image.shape[1]
        tmp = np.ones((2*m,2*n))
        tmp[::2,::2] = image
        tmp[1::2,1::2] = image
        tmp[::2,1::2] = image
        tmp[1::2,::2] = image
        return tmp
    def ReBuildPic(self,image) :
        self.reconstructed = self.subtractImage + image
        return self.subtractImage + image


# given in lab 1 
def quantise_image(im, bits=8):
    quantised = im[:,:] // ( 2 ** (8 - bits)) 
    output = quantised * ( 2 ** (8 - bits)) 
    return output
"""
input : take image:
 1- construct laplacian pyamid
 2- on each lvl except first lvl quantise the laplacian image
 3- rebuild the picture 
"""        
def EncodeLap(image) :
    img = flag = highP = np.array(image, dtype = float)
    laplacianLevels = []
    for i in range(5) :
        lvlImg = Pyramid()
        lvlImg.setImage(img)
        lvlImg.smoothen()
        flag = lvlImg.subsample()
        highP = lvlImg.subtractImage()
        # according to the note there is no quantisation on first lvl
        if (i != 0):
            highP = quantise_image(highP,i+1)
        img = flag
        laplacianLevels.append(lvlImg)

    for j in range(5,0,-1):
        tmp = laplacianLevels[j-1]
        rebuiltPicture = tmp.ReBuildPic(tmp.upsample())
        img = np.array(rebuiltPicture, dtype = float)
        cv2.imwrite("compressedLap"+str(j)+".jpg",rebuiltPicture)
    return laplacianLevels

def generateLaplacianPyramids(image) :
    img = flag = highP = np.array(image, dtype = float)    
    laplacianLevels = []
    for i in range(5) :
        lvlImg = Pyramid()
        lvlImg.setImage(img)
        lvlImg.smoothen()
        flag = lvlImg.subsample()
        highP = lvlImg.subtractImage()
        cv2.imwrite("lap"+str(i)+".jpg",highP)
        img = flag
        laplacianLevels.append(lvlImg)

"""
input : image
constrct GaussianPyramid
"""            
def  generateGaussianPyramid(image):
    img = flag = np.array(image, dtype = float)
    level=  []
    for i in range(5):
        lvlImg = Pyramid()
        lvlImg.setImage(img)
        lvlImg.smoothen()
        flag = lvlImg.subsample()
        cv2.imwrite("gausImage"+str(i)+".jpg", flag)
        img = flag
        level.append(lvlImg)
    

def Q1():
    for i in range(10,20):
        #generate ixi matric that elements ranged between 0 - 255
        tmp = np.random.randint(255, size=(i, i))
        dctMat = dct(tmp)
        revDct = idct(dctMat)
        print("test case: "+str(i-9)+" Mean Square Error : %s and isEqual: %s "  %  (str(meanSquareError(tmp,revDct)),np.allclose(tmp,revDct)))


def Q2():
    files = {'barbara.jpg','zelda.jpg','airplane.jpg'}
    for file in files:
        im = Image.open(file)
        img = np.array(im.copy())
        im.close()
        cp = dctThresh(path=file)
        im_dct = revDctThresh(cp)
        print("picture %s Signal To Noise is : %s " % (file,str(np.round(SquareNoiseRatio(img,meanSquareError(img,im_dct)), 2))))
        print("picture %s TOTAL NUMBER OF bits: %s" % (file,str(numBits(im_dct))))

def Q3():
    files = {'barbara.jpg','zelda.jpg','airplane.jpg'}
    for file in files:
        thresh = 0.04
        snr = []
        bpp = []
        for i in range (1,20):
            cp = Encode(file,thresh = thresh - 0.002*i)
            im_dct = deCode(cp)
            cv2.imwrite('comp-'+file, im_dct)
            size = os.path.getsize('comp-'+file)
            im = Image.open('comp-'+file)
            img = np.array(im.copy())
            im.close()
            snr.append(np.round(SquareNoiseRatio(img,meanSquareError(img,im_dct)), 2))
            bpp.append(calBpp(size,im_dct.shape[0],im_dct.shape[1]))

        plt.plot(bpp,snr,'r')
        plt.title("Rate-Distortion curve"+file)
        plt.xlabel("bpp")
        plt.ylabel("Signal to Noise Ratio (dB)")
        plt.savefig(file+"plot.png")
        plt.close()



            
def Q4():
    im = Image.open('./zelda.jpg')
    img = np.array(im.copy())
    im.close()
    generateGaussianPyramid(img)
    generateLaplacianPyramids(img)

def Q5():
    im = Image.open('./zelda.jpg')
    img = np.array(im.copy())
    im.close()
    EncodeLap(img)

"""
to produce the distortion-ratio curve we should calculate the Bpp and SNR 
bacuse Gaussian pyramid is lossless we can assume it as a original image 
and use laplacian reconstruction pramid as a compressed one
with this assumption we can calculate rate-distortion curve 
"""
def Q6():        
    Q4()
    Q5()
    file = './zelda.jpg'
    snr = []
    bpp = []
    for i in range (4): 
        sizeOrg = os.path.getsize("gausImage"+str(i)+".jpg")
        imG = Image.open("gausImage"+str(i)+".jpg")
        imgG = np.array(imG.copy())
        imG.close()
        sizeRec = os.path.getsize("compressedLap"+str(i+2)+".jpg")
        imRec = Image.open("compressedLap"+str(i+2)+".jpg")
        imgRec = np.array(imRec.copy())
        imRec.close()
        snr.append(np.round(SquareNoiseRatio(imgG,meanSquareError(imgG,imgRec)), 2))
        bpp.append(calBpp(sizeRec,imgRec.shape[0],imgRec.shape[1]))

    plt.plot(bpp,snr,'r')
    plt.title("DoG Rate-Distortion curve"+file)
    plt.xlabel("bpp")
    plt.ylabel("Signal to Noise Ratio (dB)")
    plt.savefig(file+"Dog-plot.png")
    plt.close()


def test(arg):
        if (arg == '1'):
                Q1()
        if (arg == '2'):
                Q2()
        if (arg == '3'):
                Q3()
        if (arg == '4'):
                Q4()
        if (arg == '5'):
                Q5()
        if (arg == '6'):
                Q6()
        if (arg == '7'):
                Q1()
                Q2()
                Q3()
                Q4()
                Q5()
                Q6()

                
if __name__== "__main__":
    argList =  sys.argv
    if (len(argList) > 1):
            test(argList[1])
    else:
            print("you should write : ./dct.py <question number>")
            print("number 7 will run all questions")
