#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf8')



__author__ = 'Santiago'

import cv2.cv as cv, math
import numpy as np
import pylab
from tkFileDialog   import askopenfilename
import tkMessageBox

def showImage(window_name, image):
        """
        For debug purpose. Using matplot, because my cv.imshow() is broken now.
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
        cv.waitKey(7)
        sys.exit(0)

class AntCounter:

    def __init__(self):
        self.videoFileName=''
        self.videoFileNameList=''
        self.duration = 0

    def setDuration(self,duration):
        self.duration = duration

    def setFileName(self,filename):
        self.videoFileName = filename

    def setFileNameLIst(self, fileNameList):
        self.videoFileNameList=fileNameList

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

    def graficar(self):
        fig = pylab.figure()
        lines = fig.add_subplot(111)

        self.subenAjustado = [1.0754*x for x in self.numeroHormigasSuben]
        self.bajanAjustado = [1.0754*x for x in self.numeroHormigasBajan]
        lines.plot( self.frames, self.numeroHormigasSuben,'b--',
            self.frames, self.subenAjustado,'b-',
            self.frames, self.numeroHormigasBajan, 'r--',
            self.frames, self.bajanAjustado, 'r-',)
        pylab.xlabel("Time in frames(30 frames = 1 Second)")
        pylab.ylabel("Number of ants")
        pylab.leg = lines.legend(('Up', 'Up adjusted','Down','Down adjusted',), 'upper center', shadow=True)
        pylab.show()
        respuesta = 'Up = '+ str( self.numeroHormigasSuben[-1])+ ' Down = '+str(self.numeroHormigasBajan[-1])+'\n'+\
                    'Up adjusted = '+str( int(self.subenAjustado[-1]))+'  Down adjusted = '+str(int(self.bajanAjustado[-1]))+\
                    '\n'+self.videoFileName
        tkMessageBox.showinfo('AntCounter',respuesta )

        return

    def saveFile(self):

        self.subenAjustado = [1.0754*x for x in self.numeroHormigasSuben]
        self.bajanAjustado = [1.0754*x for x in self.numeroHormigasBajan]
        headline=('frame', 'Ants Up', 'Ants up andusted', 'Ants Down', 'Ants Down Adjusted')
        matrizRespuesta =(np.array((self.frames, self.numeroHormigasSuben, self.subenAjustado, self.numeroHormigasBajan, self.bajanAjustado)).transpose())
        c=np.append(headline,matrizRespuesta)
        headline=('frame', 'Ants Up', 'Ants up andusted', 'Ants Down', 'Ants Down Adjusted')
        txtResultFilename = self.getTxtResultFilename(self.videoFileName)
        self.savefile(txtResultFilename,headline,matrizRespuesta)

        cv.DestroyWindow("AntCounter")

    def getTxtResultFilename(self, videoFileName):
        while '/' in videoFileName:
            videoFileName = videoFileName[(videoFileName.index('/'))+1:]
        return videoFileName[:-3]+'txt'

    #retorna una lista con los indices y las pociciones de cada hirmiga, actual y anterir son listas con las pociciones de las hormigas
    # indices es una lista con las el indice de la hormicga en el frame anterior
    def calculaDistancias(self,anterior ,actual):

        distancias = np.zeros ((len(anterior),len(actual)))  # lista de las distancia entre una hormiga y todas las del frame anterior

        for i in range (len(anterior)): # para cada hormiga del frame anterior fila    1
            for j in range (len(actual)): # para cada hormia del frame actual columna  2

                x1 = anterior[i][0]
                x2 = actual[j][0]
                y1 = anterior[i][1]
                y2 = actual[j][1]

                distancias[i][j] = math.sqrt(((x2-x1)**2)+((y2-y1)**2))   # el numero de distancias de el largo de la penultima fila


        return distancias

    def cuentahormigas (self, antsUp, antsDown, peviewFrameCenterPoints, actualFrameCenterPoints, matrizIndices, frameNo, counted):

        for i in range (len(matrizIndices[frameNo-1])): #actual
            for j in range (len(matrizIndices[frameNo-2])): #anterior
                if matrizIndices[frameNo-1][i]== matrizIndices[frameNo-2][j]:
                    y1 = actualFrameCenterPoints[i][1]
                    y2 = peviewFrameCenterPoints[j][1]
                    if matrizIndices[frameNo-1][i] in counted:
                        pass
                    elif 230< y1 < 240 and 250 > y2 >= 240:
                        antsUp +=1
                        counted.append(matrizIndices[frameNo-1][i])
                    elif  250> y1 > 240 and 230 < y2 <= 240:
                        antsDown +=1
                        counted.append(matrizIndices[frameNo-1][i])
        return(antsUp, antsDown)


    def run(self):

        for i in range ((len(self.videoFileNameList))):

            self.setFileName(self.videoFileNameList[i])

            self.capture = cv.CaptureFromFile(self.videoFileName)

            frameNumero = 1
            self.frames = []
            identificaHormigas = 0
            self.suben=0
            self.bajan=0
            self.numeroHormigasSuben = []
            self.numeroHormigasBajan = []
            puntosCentroAnterior = []
            matrizIndices = []
            maxMovAnt=10
            counted = []

            videoFileNameShort = self.videoFileName
            while '/' in videoFileNameShort:
                videoFileNameShort = videoFileNameShort[(videoFileNameShort.index('/'))+1:]

            cv.NamedWindow("AntCounter", 1)
            # Capture first frame to get size
            frame = cv.QueryFrame(self.capture)
            size = cv.GetSize(frame)
            grey_image = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
            
            #show_image(grey_image)
            #sys.exit(0)
            
            #cv.ShowImage("bloor", grey_image)
            #cv.WaitKey(7) % 0x100
            
            #print grey_image
            #print np.asarray(grey_image[:,:])
            #sys.exit(0)
            
            moving_average = cv.CreateImage(size, cv.IPL_DEPTH_32F, 3)
            #print moving_average
            #print np.asarray(moving_average[:,:])
            #sys.exit(0)
            difference = None

            #        number of frames of the video
            longvideo = long(cv.GetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_COUNT))
            if self.duration > longvideo:
                cv.DestroyAllWindows()
                tkMessageBox.showinfo('error','The time in minutes and seconds is longer than the video')

            else:
                # in each frame
                while True:

                    points = []
                    puntosCentro = []

                    # Capture frame from webcam
                    color_image = cv.QueryFrame(self.capture)
                    original_image = cv.CloneImage(color_image)

                    #restrict the zone of tracking between the two lines,
                    # covering the zone upper and  lower the lines with a black rectangle
                    cv.Rectangle(color_image,(0,0),(640,140),(0,0,0),cv.CV_FILLED,1)
                    cv.Rectangle(color_image,(0,340),(640,480),(0,0,0),cv.CV_FILLED,1)

                    #trace the lines and show tracking zone
                    cv.Line(original_image,(0,140),(640,140),(255,255,255),2,8,0)
                    cv.Line(original_image,(0,340),(640,340),(255,255,255),2,8,0)

                    #trace counting line
                    cv.Line(original_image,(0,240),(640,240),(0,255,0),3,8,0)

                    # Smooth to get rid of false positives
                    cv.Smooth(color_image, color_image, cv.CV_GAUSSIAN, 21, 0)
                    #                cv.ShowImage("bloor", color_image)

                    if not difference:
                        # Initialize
                        difference = cv.CloneImage(color_image)
                        temp = cv.CloneImage(color_image)
                        cv.ConvertScale(color_image, moving_average, 1.0, 0.0)
                    else:
                        cv.RunningAvg(color_image, moving_average, 0.020, None)

                    # Convert the scale of the moving average.
                    cv.ConvertScale(moving_average, temp, 1.0, 50.0)

                    # Minus the current frame from the moving average.
                    cv.AbsDiff(color_image, temp, difference)
                    #                cv.ShowImage("difference", difference)
                    # Convert the image to grayscale.
                    #print(difference)
                    #print(grey_image)
                    cv.CvtColor(difference, grey_image, cv.CV_RGB2GRAY)
                    # Convert the image to black and white.
                    cv.Threshold(grey_image, grey_image, 70, 255, cv.CV_THRESH_BINARY)
                    #                cv.ShowImage("blanco y negro", grey_image)

                    # Calculate movements
                    storage = cv.CreateMemStorage(0)
                    contour = cv.FindContours(grey_image, storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_NONE)

                    # Draw rectangles in each frame
                    while contour:
                        rectangle = cv.BoundingRect(list(contour)) # coners of the contour of ants
                        contour = contour.h_next()

                        pt1 = (rectangle[0], rectangle[1]) # up left corner
                        pt2 = (rectangle[0] + rectangle[2], rectangle[1] + rectangle[3])  # right down corner

                        puntosCentro.append((int((pt1[0]+pt2[0])/2),int((pt1[1]+pt2[1])/2))) # punto central de todas las hormigas

                        points.append(pt1)
                        points.append(pt2)

                        cv.Rectangle(original_image, pt1,pt2, cv.CV_RGB(255,0,0), 1)
                        cv.Circle(original_image,(int((pt1[0]+pt2[0])/2),int((pt1[1]+pt2[1])/2)),2,cv.CV_RGB(255,255,0),1)


                    #                cv.PutText(original_image,str('t='),(puntosCentro[-1]),font,(255,0,0))



                    ############################# Seguimiento
                    if len(puntosCentro) == 0:  #  ajusta el tamano de matriz indices al tamano de puntocentro
                        matrizIndices.append(puntosCentro)

                    elif identificaHormigas == 0 and (len(puntosCentro) > 0):# las primeras hormigas
                        indice = np.zeros(len(puntosCentro))
                        for i in range (len(puntosCentro)):
                            identificaHormigas += 1
                            indice[i] = identificaHormigas
                        matrizIndices.append(indice)

                    elif len(puntosCentroAnterior) == 0:
                        indice = np.zeros(len(puntosCentro))
                        for i in range (len(puntosCentro)):
                            identificaHormigas += 1
                            indice[i] = identificaHormigas
                        matrizIndices.append(indice)
                        #
                    else:
                        distancias = self.calculaDistancias(puntosCentroAnterior,puntosCentro)
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
                                if matrizIndices[frameNumero-2][fila] in matrizIndices[frameNumero-1]:
                                    identificaHormigas +=1
                                    matrizIndices[frameNumero-1][columna] = identificaHormigas
                                else:
                                    (matrizIndices[frameNumero-1][columna]) = matrizIndices[frameNumero-2][fila]

                            else:
                                identificaHormigas +=1
                                matrizIndices[frameNumero-1][columna] = identificaHormigas

                                ############################# Seguimiento Fin

                    (self.suben,self.bajan) = self.cuentahormigas(self.suben, self.bajan, puntosCentroAnterior,puntosCentro, matrizIndices, frameNumero, counted)


                    puntosCentroAnterior = puntosCentro

                    # muestra el numero de cada hormiga
                    #            if len(puntosCentro)>0:
                    #                for i in range(len(puntosCentro)):
                    #                    cv.PutText(original_image,str(int(matrizIndices[frameNumero-1][i])),(puntosCentro[i]),font,(255,0,0))

                    font = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX_SMALL, 1, 1, 0, 2, 8) #Creates a font
                    cv.PutText(original_image,str('File name:'),(30,20),font,(255,0,0))
                    cv.PutText(original_image,str(videoFileNameShort),(170,20),font,(255,0,0))

                    font = cv.InitFont(cv.CV_FONT_HERSHEY_COMPLEX_SMALL, 1, 1, 0, 2, 8) #Creates a font
                    cv.PutText(original_image,str('t='),(30,40),font,(255,0,0))
                    cv.PutText(original_image,str(frameNumero/30),(120,40),font,(255,0,0))

                    cv.PutText(original_image,str('UP'),(30,190),font,(255,0,0))
                    cv.PutText(original_image,str(self.suben),(120,190),font,(255,0,0))

                    cv.PutText(original_image,str('Down'),(30,220),font,(255,0,0))
                    cv.PutText(original_image,str(self.bajan),(120,220),font,(255,0,0))

                    # Display frame to user
                    cv.ShowImage("AntCounter", original_image)
                    self.frames.append(frameNumero)
                    self.numeroHormigasSuben.append(self.suben)
                    self.numeroHormigasBajan.append(self.bajan)
                    if len(self.videoFileNameList) == 1:
                        if frameNumero == self.duration:
                            self.graficar()
                            self.saveFile()
                            break
                    else:
                        if frameNumero == self.duration:
                            self.saveFile()
                            break
                    # Listen for ESC or ENTER key
                    c = cv.WaitKey(7) % 0x100
                    if c == 27 or c == 10:
                        self.graficar()
                        break
                    frameNumero += 1

from Tkinter import *
import tkFileDialog

class App:

    def __init__(self, frame):
        self.AntCounter = AntCounter()
        #        Menu
        root.title('AntCounter')
        menu = Menu(root)
        root.config(menu=menu)

        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)

        filemenu.add_command(label="Load Video File", command=self.OpenFileCommand)
        #        filemenu.add_command(label="Seve", command=self.seveFileCommand)
        #        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exitCommand)

        helpmenu = Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=self.helpCommand)

        #          Row 0

        Label(frame,text='How much time do you want to analyze').grid(row=0,column =0,columnspan=4)
        #          Row 1

        Label(frame,text='minuts:').grid(row=2,column=0,sticky=E)
        Label(frame, text="seconds:").grid(row=2,column=2, sticky=W)

        #          Row 2

        self.strMin = StringVar()
        self.strMin.set('1')
        self.minutsEntry = Entry(frame,text=self.strMin).grid(row=2,column=1,sticky=W+E )

        self.strSeg = StringVar()
        self.strSeg.set('0')
        self.secondsEntry = Entry(frame,text=self.strSeg).grid(row=2,column=3,sticky=W+E)

        #        Row 3
        self.ButtonOK = Button(frame, text="OK",command=self.okButtonCommand).grid(row=3,column=3, sticky=E+W)


    def OpenFileCommand(self):

        InputfilesList = tkFileDialog.askopenfilenames(title="Select the source input file(s)", filetypes=[("All files",".*")])
        InputfilesList =  root.tk.splitlist(InputfilesList)
        for i in range ((len(InputfilesList))):
            if InputfilesList[i][-3:] in ('mp4','wav','AVI','mov','MOV','wmv'):
                self.AntCounter.setFileNameLIst(InputfilesList)
            else:
                tkMessageBox.showinfo('error','choose a mp4, AVI, mov file' )

    def exitCommand(self):
        quit()
    def helpCommand(self):
        tkMessageBox.showinfo('About Antcounter',"AntCounter V.1.0 2013\nWrite by: Santiago Bustamante\nEmail: santiagobus@gmail.comn\nWeb site: https://sites.google.com/site/antcounter/\n2013"+ u"\u00A9" +"Santiago Bustamante\nAll Rights Reserved")


    def okButtonCommand(self):

        if self.validation():
            self.duration = (int(self.strMin.get())*60*30)+(int(self.strSeg.get())*30)
            self.AntCounter.setDuration(self.duration)
            self.AntCounter.run()
        else:
            pass

    def validation(self):
        if self.AntCounter.videoFileNameList =='':
            tkMessageBox.showinfo('error','Load a Video file' )
            return False
        else:
            for i in range ((len(self.AntCounter.videoFileNameList))):
                if self.AntCounter.videoFileNameList[i][-3:]in ('mp4','wav','AVI','mov','MOV','wmv'):

                    for s in (self.strMin.get()).split():
                        if (self.strMin.get()).isdigit():
                            pass
                        else:
                            tkMessageBox.showinfo('error','Minuts must be a integer')
                            return False

                    for s in (self.strSeg.get()).split():
                        if (self.strSeg.get()).isdigit():
                            pass
                        else:
                            tkMessageBox.showinfo('error','Seconds must be a integer')
                            return False

                    return True
                else:
                    tkMessageBox.showinfo('error','Load a Video file' )
                    return False

        return False

    def run(self):
        mainloop()


if __name__ == '__main__':
    root = Tk()
    app = App(root)
    app.run()

