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
from PIL import Image
import keyboard
from mss import factory, mss
from numba import njit, jit, cuda
from multiprocessing import Queue, Process
from PIL import Image, ImageTk

from pycparser.c_ast import While

def stopRecording():
    global keepRecording, btnStartRecording,btnStopRecording,frame_position,screen_size
    pointer_in = False
    frame_position = [0,0]
    keepRecording = False
    btnStartRecording["state"] = "normal"
    btnStopRecording["state"] = "disabled"

def startRecording(monitor,SCREEN_SIZE):
    global keepRecording, btnStartRecording,btnStopRecording
    btnStartRecording["state"] = "disabled"
    btnStopRecording["state"] = "normal"
    keepRecording = True
    X = fpsSettings.current()
    FPS = float(X*5+10)
    print(FPS)
    window.iconify()
    #_recordScreen(FPS,monitor,keepRecording,SCREEN_SIZE)
    threading.Thread(target=recordScreen,args=[FPS,monitor,SCREEN_SIZE]).start()

def runTimeWindowRenderer(monitor):
    global frame_position
    SCREEN_SIZE = screen_size
    top_padding = frame_position[0]
    left_padding =frame_position[1]
    monitor = {"top":int(top_padding) + 30,"left":int(left_padding) - 30,"width":SCREEN_SIZE[0],"height":SCREEN_SIZE[1]}
    return monitor

def recordScreen(FPS,monitor,SCREEN_SIZE,):
    global keepRecording
    #timeForFrame = 1/FPS
    #img = np.zeros(SCREEN_SIZE)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    output = cv2.VideoWriter("output.avi",fourcc,FPS,(SCREEN_SIZE))
    sct = mss()
    queue = Queue()
    threading.Thread(target=_recordScreen,args=[monitor,sct,queue]).start()
    #Having more than one thread doesn't improve performance
    #threading.Thread(target=_recordScreen,args=[monitor,sct,1,i,queue]).start()
    threading.Thread(target=_writeScreen,args=[output,queue]).start()
    #output.release()


def _recordScreen(monitor,sct,queue):
    i = 0
    start = current = time.time()
    while keepRecording == True:
        monitor = update_monitor()[0]
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
    global floater
    _offsetx = int(screen_size[1]/2)
    _offsety = int(screen_size[0]/2)
    SCREEN_SIZE = screen_size
    top_padding = floater.frame_position[1]
    left_padding =floater.frame_position[0]
    monitor = {"top":top_padding-_offsetx,"left":left_padding-_offsety,"width":SCREEN_SIZE[0],"height":SCREEN_SIZE[1]}
    return monitor,SCREEN_SIZE

class FloatingWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.geometry("%d%s%d" % (screen_size[0],"x",screen_size[1]))
        self.mouseX = pyautogui.position()[0]
        self.mouseY = pyautogui.position()[1]
        self.overrideredirect(True)
        self.wm_attributes("-transparentcolor", "blue")
        self.c = tk.Canvas(self,height=screen_size[0], width=screen_size[1], bg="blue")
        self.c.pack()
        self.filex = PhotoImage(file='t.png')
        point = self.c.create_image(0,0, image=self.filex, anchor=NW)
        self.frame_position = self.winfo_pointerxy()    
        self.c.bind("<B1-Motion>", self.dragwinx)
        self.c.pack(side="left", fill="y")   
        self.c.bind("<Button-1>", self.clickwin)
 
                    
    def dragwinx(self, event):
        x = self.winfo_pointerx() - self._offsetx
        y = self.winfo_pointery() - self._offsety
        y_p = int(self.winfo_rooty()+screen_size[0]/2)
        x_p = int(self.winfo_rootx()+screen_size[0]/2)
        self.frame_position = [x_p,y_p] 
        self.geometry("+%d+%d" % (x, y))

    def clickwin(self, event):
        self._offsetx = event.widget.winfo_rootx() - self.winfo_rootx() + event.x
        self._offsety = event.widget.winfo_rooty() - self.winfo_rooty() + event.y

    def dragwin(self, event):
        self._offsetx = screen_size[0]/2
        self._offsety = screen_size[1]/2
        self.mouseX = pyautogui.position()[0]
        self.mouseY = pyautogui.position()[1]
        self.frame_position = self.winfo_pointerxy()  
        self.geometry("+%d+%d" % (self.mouseX-self._offsetx,self.mouseY-self._offsety))

if __name__ == "__main__":
    global screen_size
    global floater
    keepRecording = False
    screen_size=[500,500]
    #outputVideo(output,converted)
    cv2.destroyAllWindows()
    #output.release()
    window = tk.Tk()
    floater = FloatingWindow(window)
    window.geometry('300x300')
    window.title("Window")
    labelFPSSetting = tk.Label(text = "FPS")
    labelFPSSetting.place(x=90, y=40)
    fpsSettings = tk.ttk.Combobox(window)
    fpsSettings['values'] = (10, 15, 20, 25, 30,35,40, 45,50,55, 60)
    fpsSettings.current(4)
    fpsSettings.place(x=90, y=80,width = 115)
    btnStartRecording = tk.Button(window, text = "Start Recording",command = lambda : startRecording(update_monitor()[0],update_monitor()[1]) )
    btnStartRecording.place(x=90, y=120)
    btnStopRecording = tk.Button(window, text = "Stop Recording", command = stopRecording)
    btnStopRecording.place(x=90,y=160)
    btnStopRecording["state"] = "disabled"
    window.mainloop()
    