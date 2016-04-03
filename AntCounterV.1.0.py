#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

__author__ = 'Santiago'
import sys
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import math

import queue
import threading

import cv2 as cv
import numpy as np
import pylab


class AppAntCounter(threading.Thread):

    def __init__(self, queue_app, queue_gui):
        threading.Thread.__init__(self)
        self.queue_app = queue_app
        self.queue_gui = queue_gui
        self.videoFileName=''
        self.videoFileNameList=''
        self.duration = 0
        
       
    def run(self):
        """
        This name required by threading.Thread
        """
        while True:
            try:
                info = queue_app.get(timeout=1) 
                # with timeout here can be added some additional logic
                # without will be dead lock till new element came to queue
                
                # info has second element "list", so few vars can be sent
                if info[0] == 'videoFileNameList':
                    # send response to GUI
                    self.queue_gui.put(self.videoFileNameList)
                elif info[0] == 'setFileNameLIst':
                    InputfilesList = info[1][0]
                    self.setFileNameLIst(InputfilesList)
                elif info[0] == 'setDuration':
                    duration = info[1][0]
                    self.setDuration(duration)
                elif info[0] == 'run_app':
                    self.run_app()
            except queue.Empty:
                pass

    def kill_app(self):
        #print('Stop app thread')
        cv.destroyWindow("AntCounter")
        cv.destroyAllWindows()
        sys.exit(0)
        #bug in my opencv module, can't kill it even in this way
        
    def setFileNameLIst(self, fileNameList):
        self.videoFileNameList=fileNameList
        
    def setDuration(self,duration):
        self.duration = duration

    def setFileName(self,filename):
        self.videoFileName = filename

    def graph(self):
        # send current state of app object to GUI thread, it's kind of read-only
        self.queue_gui.put(['graph', [self]])
        
    def showImage(self, window_name, image):
        # use matplot to show image
        # self.queue_gui.put(['showImage', [window_name, image]])
        # or cv
        cv.destroyAllWindows()
        cv.namedWindow(window_name, cv.WINDOW_NORMAL)
        cv.imshow(window_name, image)
        cv.waitKey(0)
        self.kill_app()
        
    def savefile(self,filename ,headline, numpyarray):
        f = open(filename,"w")
        for i in range (len(headline)):
            f.write(headline[i])
            f.write('\t')
        f.write('\n')
        for i in range(len(numpyarray)): # filas
            for j in range(len(numpyarray[0])):# columnas
                f.write (str(numpyarray[i][j]))
                f.write('\t')
            f.write('\n')
        f.close()

    def saveFile(self):

        self.upAdjusted = [1.0754*x for x in self.numberAntsUp]
        self.downAdjusted = [1.0754*x for x in self.numberAntsDown]
        headline=('frame', 'Ants Up', 'Ants up adjusted', 'Ants Down', 'Ants Down Adjusted')
        matrizResponse =(np.array((self.frames, self.numberAntsUp, self.upAdjusted, self.numberAntsDown, self.downAdjusted)).transpose())
        c=np.append(headline,matrizResponse)
        headline=('frame', 'Ants Up', 'Ants up adjusted', 'Ants Down', 'Ants Down Adjusted')
        txtResultFilename = self.getTxtResultFilename(self.videoFileName)
        self.savefile(txtResultFilename,headline,matrizResponse)

    def getTxtResultFilename(self, videoFileName):
        while '/' in videoFileName:
            videoFileName = videoFileName[(videoFileName.index('/'))+1:]
        return videoFileName[:-3]+'txt'

    def calculateDistances(self, previous, actual):
        """
        return a list of indices and the positions of each ant, current and previous are ready with ants
        positions of indices is a list of the index of the previous frame ant
        """

        distances = np.zeros ((len(previous),len(actual)))  # list of the distances between an ant and all the previous frame

        for i in range (len(previous)): # for each previous frame ant row 1
            for j in range (len(actual)): # for each current frame hormone column 2

                x1 = previous[i][0]
                x2 = actual[j][0]
                y1 = previous[i][1]
                y2 = actual[j][1]

                distances[i][j] = math.sqrt(((x2-x1)**2)+((y2-y1)**2))   #the number of distances of the length of the penultimate row


        return distances

    def ants_account(self, antsUp, antsDown, pointsCenterPrevious, pointsCenter, matrizIndices, frameNumber, counted):

        for i in range (len(matrizIndices[frameNumber-1])): #actual
            for j in range (len(matrizIndices[frameNumber-2])): #previous
                if matrizIndices[frameNumber-1][i]== matrizIndices[frameNumber-2][j]:
                    y1 = pointsCenter[i][1]
                    # I think, it not exist only for first frame
                    try:
                        y2 = pointsCenterPrevious[j][1]
                    except:
                        y2 = 0
                    
                    if matrizIndices[frameNumber-1][i] in counted:
                        pass
                    elif 230< y1 < 240 and 250 > y2 >= 240:
                        antsUp +=1
                        counted.append(matrizIndices[frameNumber-1][i])
                    elif  250> y1 > 240 and 230 < y2 <= 240:
                        antsDown +=1
                        counted.append(matrizIndices[frameNumber-1][i])
        return(antsUp, antsDown)

        
    def run_app(self):

        for i in range ((len(self.videoFileNameList))):

            self.setFileName(self.videoFileNameList[i])

            self.capture = cv.VideoCapture(self.videoFileName)

            frameNumber = 1
            self.frames = []
            identifiedAnts = 0
            self.up=0
            self.down=0
            self.numberAntsUp = []
            self.numberAntsDown = []
            pointsCenterPrevious = []
            matrizIndices = []
            maxMovAnt=10
            counted = []

            videoFileNameShort = self.videoFileName
            while '/' in videoFileNameShort:
                videoFileNameShort = videoFileNameShort[(videoFileNameShort.index('/'))+1:]

            
            # Capture first frame to get size
            ret, frame = self.capture.read()
            height, width = frame.shape[:2]
   
            # pixel is scalar
            grey_image = np.zeros((height,width), np.uint8)
            # pixel is array with one scalar element
            #grey_image = np.zeros((height,width,1), np.uint8)
             
            moving_average =  np.zeros((height,width,3), np.float32)
            
            difference = None

            # number of frames of the video
            longvideo = int(self.capture.get(cv.CAP_PROP_FRAME_COUNT))
            if self.duration > longvideo:
                cv.DestroyAllWindows()
                messagebox.showinfo('error','The time in minutes and seconds is longer than the video')

            else:
                # in each frame
                while True:
                    points = []
                    pointsCenter = []
                    
                    cv.namedWindow("AntCounter", cv.WINDOW_NORMAL)

                    # Capture frame from video source
                    ret, color_image = self.capture.read()
                    original_image = color_image.copy()

                    # restrict the zone of tracking between the two lines,
                    # covering the zone upper and  lower the lines with a black rectangle
                    cv.rectangle(color_image,(0,0),(640,140),(0,0,0),cv.FILLED,1)
                    cv.rectangle(color_image,(0,340),(640,480),(0,0,0),cv.FILLED,1)

                    #trace the lines and show tracking zone
                    cv.line(original_image,(0,140),(640,140),(255,255,255),2,8,0)
                    cv.line(original_image,(0,340),(640,340),(255,255,255),2,8,0)

                    #trace counting line
                    cv.line(original_image,(0,240),(640,240),(0,255,0),3,8,0)

                    # Smooth to get rid of false positives
                    # Smooth(src, dst [, smoothtype [, param1 [, param2 [, param3 [, param4]]]]]) -> None
                    # GaussianBlur(src, ksize, sigmaX[, dst[, sigmaY[, borderType]]]) -> dst
                    color_image = cv.GaussianBlur(color_image, (7,7), 21, 1.5)
                    # self.showImage('blur', color_image)

                    if isinstance(difference, type(None)):
                        # Initialize
                        difference = color_image.copy()
                        temp = color_image.copy()
                        # ConvertScale(src, dst [, scale [, shift]]) -> None
                        # convertScaleAbs(src[, dst[, alpha[, beta]]]) -> dst
                        # or try this:
                        # void Mat::copyTo(OutputArray dst);
                        # void UMat::copyTo(OutputArray dst);
                        cv.convertScaleAbs(color_image, moving_average, 1.0, 0.0)
                    else:
                        cv.accumulateWeighted(color_image, moving_average, 0.020, None)

                    # Convert the scale of the moving average.
                    cv.convertScaleAbs(moving_average, temp, 1.0, 50.0)
                    
                    # Minus the current frame from the moving average.
                    cv.absdiff(color_image, temp, difference)
                    # self.showImage("difference", difference)
                    # Convert the image to grayscale.
                    
                    cv.cvtColor(difference, cv.COLOR_RGB2GRAY, grey_image)
                    # Convert the image to black and white.
                    cv.threshold(grey_image, 70, 255, cv.THRESH_BINARY, grey_image)
                    # self.showImage("black and white", grey_image)

                    # Calculate movements
                    contour_image, contours, hierarchy  = cv.findContours(grey_image, cv.RETR_CCOMP, cv.CHAIN_APPROX_NONE)
                    # self.showImage("contour_image", contour_image)
                    
                    # Draw rectangles in each frame
                    for contour in contours:
                        rectangle = cv.boundingRect(contour) # coners of the contour of ants

                        pt1 = (rectangle[0], rectangle[1]) # up left corner
                        pt2 = (rectangle[0] + rectangle[2], rectangle[1] + rectangle[3])  # right down corner

                        pointsCenter.append((int((pt1[0]+pt2[0])/2),int((pt1[1]+pt2[1])/2))) # central point of all ants

                        points.append(pt1)
                        points.append(pt2)

                        cv.rectangle(original_image, pt1,pt2, (0.0, 0.0, 255.0, 0.0), 1)
                        cv.circle(original_image,(int((pt1[0]+pt2[0])/2),int((pt1[1]+pt2[1])/2)),2,(0.0, 255.0, 255.0, 0.0),1)


                    #                cv.PutText(original_image,str('t='),(pointsCenter[-1]),font,(255,0,0))



                    ############################# Tracing

                    if len(pointsCenter) == 0:  #  resizes to the size of array indices center point
                        matrizIndices.append(pointsCenter)

                    elif identifiedAnts == 0 and (len(pointsCenter) > 0): # the first ants
                        indice = np.zeros(len(pointsCenter))
                        for i in range (len(pointsCenter)):
                            identifiedAnts += 1
                            indice[i] = identifiedAnts
                        matrizIndices.append(indice)

                    elif len(pointsCenterPrevious) == 0:
                        indice = np.zeros(len(pointsCenter))
                        for i in range (len(pointsCenter)):
                            identifiedAnts += 1
                            indice[i] = identifiedAnts
                        matrizIndices.append(indice)
                        #
                    else:
                        distancias = self.calculateDistances(pointsCenterPrevious,pointsCenter)
                        matrizIndices.append(np.zeros(len(distancias[0])))

                        #               encuentra el minimo de distancias e identifiva la posicion para cada hormiga
                        for j in range (len(matrizIndices[-1])): # columna
                            minimo = 1000000
                            for i in range (len(distancias)): # fila
                                if distancias[i][j] < minimo:
                                    minimo = distancias[i][j]
                                    columna = j
                                    fila = i
                            if minimo < maxMovAnt:
                                if matrizIndices[frameNumber-2][fila] in matrizIndices[frameNumber-1]:
                                    identifiedAnts +=1
                                    matrizIndices[frameNumber-1][columna] = identifiedAnts
                                else:
                                    (matrizIndices[frameNumber-1][columna]) = matrizIndices[frameNumber-2][fila]

                            else:
                                identifiedAnts +=1
                                matrizIndices[frameNumber-1][columna] = identifiedAnts

                                ############################# Tracing End
                    (self.up,self.down) = self.ants_account(self.up, self.down, pointsCenterPrevious,pointsCenter, matrizIndices, frameNumber, counted)


                    pointsCenterPrevious = pointsCenter
                    
                    font = cv.FONT_HERSHEY_COMPLEX_SMALL
                    
                    # display the number of each ant
                    """
                    if len(pointsCenter)>0:
                        for i in range(len(pointsCenter)):
                            cv.putText(original_image,str(int(matrizIndices[frameNumber-1][i])),(pointsCenter[i]),font,1.0,(255,0,0))
                    """
                    

                    cv.putText(original_image,str('File name:'),(30,20),font,1.0,(255,0,0))
                    cv.putText(original_image,str(videoFileNameShort),(170,20),font,1.0,(255,0,0))

                    cv.putText(original_image,str('t='),(30,40),font,1.0,(255,0,0))
                    cv.putText(original_image,str(int(frameNumber/30)),(120,40),font,1.0,(255,0,0))

                    cv.putText(original_image,str('UP'),(30,190),font,1.0,(255,0,0))
                    cv.putText(original_image,str(self.up),(120,190),font,1.0,(255,0,0))

                    cv.putText(original_image,str('Down'),(30,220),font,1.0,(255,0,0))
                    cv.putText(original_image,str(self.down),(120,220),font,1.0,(255,0,0))

                    # Display frame to user
                    cv.imshow('AntCounter', original_image)
                    self.frames.append(frameNumber)
                    self.numberAntsUp.append(self.up)
                    self.numberAntsDown.append(self.down)
                    
                    # Why this so?
                    if len(self.videoFileNameList) == 1:
                        if frameNumber == self.duration:
                            self.graph()
                            self.saveFile()
                            return self.kill_app()
                    else:
                        if frameNumber == self.duration:
                            self.saveFile()
                            return self.kill_app()

                    # Listen for ESC or ENTER key
                    c = cv.waitKey(7) % 0x100
                    if c == 27 or c == 10:
                        self.graph()
                        self.saveFile()
                        return self.kill_app()
                    frameNumber += 1


                    
class Gui():

    def __init__(self, app, queue_app, queue_gui):
        # "app" here only to check if thread is alive
        # direct asses from is pointless,
        # only queues for real interation between threads
        self.app = app
        self.queue_app = queue_app
        self.queue_gui = queue_gui
        self.root = tk.Tk()
        
        #        Menu
        self.root.title('AntCounter')
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        filemenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)

        filemenu.add_command(label="Load Video File", command=self.OpenFileCommand)
        #        filemenu.add_command(label="Seve", command=self.seveFileCommand)
        #        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exitCommand)

        helpmenu = tk.Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=self.helpCommand)

        #          Row 0

        tk.Label(self.root, text='How much time do you want to analyze').grid(row=0,column =0,columnspan=4)
        #          Row 1

        tk.Label(self.root,text='minuts:').grid(row=2,column=0,sticky=tk.E)
        tk.Label(self.root, text="seconds:").grid(row=2,column=2, sticky=tk.W)

        #          Row 2

        self.strMin = tk.StringVar()
        self.strMin.set('1')
        self.minutsEntry = tk.Entry(self.root,text=self.strMin).grid(row=2,column=1,sticky=tk.W+tk.E )

        self.strSeg = tk.StringVar()
        self.strSeg.set('0')
        self.secondsEntry = tk.Entry(self.root,text=self.strSeg).grid(row=2,column=3,sticky=tk.W+tk.E)

        #        Row 3
        self.ButtonOK = tk.Button(self.root, text="OK",command=self.okButtonCommand).grid(row=3,column=3, sticky=tk.E+tk.W)
        
        self.root.after(100, self.checkAppIsAlive)
        self.root.mainloop()
        
    def checkAppIsAlive(self):
        """
        Non-blocking way to check if app thread is alive
        """
        if not self.app.isAlive():
            self.exitCommand()
        else:
            self.root.after(100, self.checkAppIsAlive)
            
    def exitCommand(self):
        #print('Close Gui')
        self.root.quit()
        self.root.destroy()

    def OpenFileCommand(self):

        InputfilesList = filedialog.askopenfilenames(title="Select the source input file(s)", filetypes=[("All files",".*")])
        InputfilesList =  self.root.tk.splitlist(InputfilesList)
        for i in range ((len(InputfilesList))):
            if InputfilesList[i][-3:].lower() in ('mp4','wav','avi','mov','wmv'):
                self.queue_app.put(['setFileNameLIst', [InputfilesList]])
            else:
                messagebox.showinfo('error','choose a mp4, AVI, mov file' )

       
    def helpCommand(self):
        messagebox.showinfo('About Antcounter',"AntCounter V.1.0 2013\nWrite by: Santiago Bustamante\nEmail: santiagobus@gmail.comn\nWeb site: https://sites.google.com/site/antcounter/\n2013"+ u"\u00A9" +"Santiago Bustamante\nAll Rights Reserved")


    def okButtonCommand(self):

        if self.validation():
            self.duration = (int(self.strMin.get())*60*30)+(int(self.strSeg.get())*30)
            self.queue_app.put(['setDuration', [self.duration]])
            self.queue_app.put(['run_app', []])
        else:
            pass

    def validation(self):
        # request info from app
        self.queue_app.put(['videoFileNameList', []])
        # wait till receive response
        videoFileNameList = self.queue_gui.get()
       
        if videoFileNameList == '':
            messagebox.showinfo('error','Load a Video file' )
            return False
        else:
            for i in range ((len(videoFileNameList))):
                if videoFileNameList[i][-3:] in ('mp4','wav','AVI','mov','MOV','wmv'):

                    for s in (self.strMin.get()).split():
                        if (self.strMin.get()).isdigit():
                            pass
                        else:
                            messagebox.showinfo('error','Minuts must be a integer')
                            return False

                    for s in (self.strSeg.get()).split():
                        if (self.strSeg.get()).isdigit():
                            pass
                        else:
                            messagebox.showinfo('error','Seconds must be a integer')
                            return False

                    return True
                else:
                    messagebox.showinfo('error','Load a Video file' )
                    return False

        return False
        
        
        

"""
Tkinter is designed to run from the main thread only.
matplotlib use Tkinter for UI, so must be executed from main thread.
http://effbot.org/zone/tkinter-threads.htm
"Just run all UI code in the main thread, and let the writers write to a Queue object."
I know, it's ugly, but plot and tk messagess raising error if calling from threads.
"""
    
def graph(self): # not changed variable name
    """
    It use "freazed" copy of app instance
    """
    fig = pylab.figure()
    lines = fig.add_subplot(111)

    self.upAdjusted = [1.0754*x for x in self.numberAntsUp]
    self.downAdjusted = [1.0754*x for x in self.numberAntsDown]

    lines.plot( self.frames, self.numberAntsUp,'b--',
        self.frames, self.upAdjusted,'b-',
        self.frames, self.numberAntsDown, 'r--',
        self.frames, self.downAdjusted, 'r-',)

    pylab.xlabel("Time in frames(30 frames = 1 Second)")
    pylab.ylabel("Number of ants")
    #pylab.leg = lines.legend(('Up', 'Up adjusted','Down','Down adjusted',),'upper center', shadow=True)
    pylab.show()
    response = 'Up = '+ str( self.numberAntsUp[-1])+ ' Down = '+str(self.numberAntsDown[-1])+'\n'+\
                'Up adjusted = '+str( int(self.upAdjusted[-1]))+'  Down adjusted = '+str(int(self.downAdjusted[-1]))+\
                '\n'+self.videoFileName
    messagebox.showinfo('AntCounter', response)
    
def showImage(window_name, image):
        """
        For debug purpose.
        """
        # test first pixel, if image gray convert to BGR (openCV color order)
        if  isinstance(image[0][0], np.uint8) or \
                isinstance(image[0][0], np.ndarray) and len(image[0][0]) == 1:
            image = cv.cvtColor(image, cv.COLOR_GRAY2BGR)
        
        # now convert to RGB, suitable for matplotlib
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        
        # hide axis
        ax = pylab.gca()
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)

        pylab.title(window_name)
        pylab.imshow(image)
        pylab.show()
        
        

if __name__ == '__main__':

    queue_app = queue.Queue()
    queue_gui = queue.Queue()
    
    #Thread
    app = AppAntCounter(queue_app, queue_gui)
    # simple way to kill it on GUI close
    app.daemon = True
    # another way is to use queue and send command to die,
    # add "queue.get()" in run_app() frame handling loop with little timeout,
    # but this can create performance lose anyway
    app.start()
   

    gui = Gui(app, queue_app, queue_gui)

    # show some info after death of App and Gui
    while True:
        try:
            info = queue_gui.get(timeout=1)
            if info[0] == 'graph':
                graph(info[1][0])
            elif info[0] == 'showImage':
                showImage(*info[1]) #unpack vars
        except queue.Empty:
            break


