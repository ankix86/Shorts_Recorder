from cv2 import cv2
import numpy as np
from numpy.random import f
import pyautogui
import tkinter as tk
from tkinter import *
from threading import Thread, Event
import threading
import PySimpleGUI as sg
import time
import keyboard
from mss import factory, mss
from numba import njit, jit, cuda
from multiprocessing import Queue, Process
from pycparser.c_ast import While



    
def stopRecording():
    global keepRecording, btnStartRecording,btnStopRecording,screen_size
    keepRecording = False
    btnStartRecording["state"] = "normal"
    btnStopRecording["state"] = "disabled"

def startRecording(monitor,SCREEN_SIZE):
    global keepRecording, btnStartRecording,btnStopRecording,screen_size
    y_p = int(floater.winfo_rooty()+screen_size[0]/2)
    x_p = int(floater.winfo_rootx()+screen_size[0]/2)
    floater.frame_position = [x_p,y_p] 
    update_monitor()
    btnStartRecording["state"] = "disabled"
    btnStopRecording["state"] = "normal"
    keepRecording = True
    X = fpsSettings.current()
    FPS = float(X*5+10)
    print(FPS)
    window.iconify()
    threading.Thread(target=recordScreen,args=[FPS,monitor,SCREEN_SIZE]).start()

def recordScreen(FPS,monitor,SCREEN_SIZE):
    global keepRecording
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    output = cv2.VideoWriter("output.avi",fourcc,FPS,(SCREEN_SIZE))
    sct = mss()
    queue = Queue()
    threading.Thread(target=_recordScreen,args=[monitor,sct,queue]).start()
    threading.Thread(target=_writeScreen,args=[output,queue]).start()

def _recordScreen(monitor,sct,queue):
    i = 0
    start = current = time.time()
    while keepRecording == True:
        #updating monitor 
        monitor = update_monitor()
        queue.put(np.array(sct.grab(monitor)))
        i+=1
        if(current-start>1):
            print(i, " frames in ", current-start, " seconds.")
            start = current
            i=0
        current = time.time()
    queue.put(None)

def _writeScreen(output, queue):
    while keepRecording == True:
        img = queue.get()
        if img is None:
            output.release()
            break
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        output.write(img)
    output.release()

def update_monitor():
    #Calculating Offest X and Y for Make Screen On Center. 
    _offsetx = int(screen_size[1]/2)
    _offsety = int(screen_size[0]/2)

    top_padding = floater.frame_position[1]
    left_padding =floater.frame_position[0]

    #top => offset_x
    #left => offset_y
    monitor = {"top":top_padding-_offsetx,"left":left_padding-_offsety,"width":screen_size[0],"height":screen_size[1]}
    return monitor

class FloatingWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.geometry("%d%s%d" % (screen_size[0],"x",screen_size[1]))
        self.mouseX = pyautogui.position()[0]
        self.mouseY = pyautogui.position()[1]
        self.overrideredirect(True)
        self.wm_attributes("-transparentcolor", "blue")
        self.c = tk.Canvas(self,height=screen_size[0], width=screen_size[1], bg="blue")
        self.c.pack(side="left", fill="y")  

        #Accessing PNG file from Current Directory (You can import direct PNG file path and replace it.)
        self.filex = PhotoImage(file='s_logo.png')
        self.c.create_image(0,0, image=self.filex, anchor=NW)

        #Initializing frame_position with current location of floating window or self.
        self.frame_position = self.winfo_pointerxy()    

        #EVENT
        self.c.bind("<B1-Motion>", self.dragwinx)
        self.c.bind("<Button-1>", self.clickwin)
      
    def dragwinx(self, event):
        #Call when B1-Motion or Drag event on canvas window.
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety

        #Calulating the canvas screen_size with in x & y offsets.
        y_p = int(self.winfo_rooty()+screen_size[0]/2)
        x_p = int(self.winfo_rootx()+screen_size[0]/2)
        self.frame_position = [x_p,y_p] 

        #changeing canvas position
        self.geometry("+%d+%d" % (x, y))

    def clickwin(self, event):
        #Call when Button-1 or Click event on canvas window.
        #Sotring x & y offset values.
        self._offsetx = event.widget.winfo_rootx() - self.winfo_rootx() + event.x
        self._offsety = event.widget.winfo_rooty() - self.winfo_rooty() + event.y

if __name__ == "__main__":
    #Disabling or Setting False Intial Booleans 
    keepRecording = False

    #Static Screen Size (500,500)
    #screen_size Changes [s_logo.png => is 500*500px image with transparent background] 
    #eg. screen_size=[600,600] *requires 600*600 s_logo.png* file inorder to fit with in screen recoder.
    screen_size=[500,500]
    cv2.destroyAllWindows()
    window = tk.Tk()
    window.geometry('300x300')
    window.title("Window")
    labelFPSSetting = tk.Label(text = "FPS")
    labelFPSSetting.place(x=90, y=40)
    fpsSettings = tk.ttk.Combobox(window)
    fpsSettings['values'] = (10, 15, 20, 25, 30,35,40, 45,50,55, 60)
    fpsSettings.current(4)
    fpsSettings.place(x=90, y=80,width = 115)
    
    #Creating FloatingWindow With Canvas 
    floater = FloatingWindow(window)

    btnStartRecording = tk.Button(window, text = "Start Recording",command = lambda : startRecording(update_monitor(),screen_size))
    btnStartRecording.place(x=90, y=120)
    btnStopRecording = tk.Button(window, text = "Stop Recording", command = stopRecording)
    btnStopRecording.place(x=90,y=160)
    btnStopRecording["state"] = "disabled"
    
  
    window.mainloop()
    