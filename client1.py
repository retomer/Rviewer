from tkinter import *
import tkinter.font as font
import pickle
from tkinter.filedialog import askopenfilenames
import zipfile
import os
from datetime import datetime
import math
import PIL.Image
import numpy
import cv2
import ctypes
import threading
from pynput.mouse import Listener
from pynput.keyboard import Key
from pynput.keyboard import Listener as Listenerk
from PIL import ImageGrab
import socket
import pyautogui
from tkinter import messagebox

#  Get the size of the user's screen
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
myscreenx, myscreeny = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
"""
#########################################################################################
"""


def get_mouse_cordinates(letshare_socket1):
    """gets from the controller the mouse coordinates and executes them"""
    while True:
        try:
            mdata = letshare_socket1.recv(10).decode('utf-8')

            while mdata[0] == '0':
                mdata = mdata[1:]

            sign = mdata[0]
            mdata = mdata[1:]
            x, y = mdata.split("-")
            x, y = int(x), int(y)

            if sign == 'l':
                pyautogui.tripleClick(x, y)
            else:
                pyautogui.rightClick(x, y)
        except IndexError:
            break
        except ConnectionAbortedError:
            break
        except:
            pass


def close_end2():
    """close the tkinter screen"""
    end_screen2.destroy()
    pass


def end_remote_mode():
    """show a message about the end of the remote modee"""
    messagebox.showinfo("exit", "The Remote Has Ended\n Thank You For Using Rviewer!")


def stop_the_share(boolean=True):
    """stops the screen sharing"""
    print("from stop the share")
    if boolean:
        end_screen2.destroy()
    letshare_socket.close()
    listenerk.stop()
    end_remote_mode()


def sharing_the_screen(letshare_socket2):
    """share the screen to the control user"""
    # get the size of the screen
    user_32 = ctypes.windll.user32
    user_32.SetProcessDPIAware()

    screen_x, screen_y = user_32.GetSystemMetrics(0), user_32.GetSystemMetrics(1)

    img1 = ImageGrab.grab(bbox=(0, 0, screen_x, screen_y))
    photo_to_send1 = img1.tobytes()
    size = len(photo_to_send1)

    letshare_socket2.send(bytes(str(screen_x).zfill(4), 'utf-8'))
    letshare_socket2.send(bytes(str(screen_y).zfill(4), 'utf-8'))
    letshare_socket2.send(bytes(str(size).zfill(10), 'utf-8'))

    while True:
        img = ImageGrab.grab(bbox=(0, 0, screen_x, screen_y))
        photo_to_send = img.tobytes()
        try:
            letshare_socket2.send(photo_to_send)
        except ConnectionAbortedError:
            stop_the_share(False)
            break
        except ConnectionResetError:
            stop_the_share(False)
            break
        except OSError:
            break


def send_mouse_coordinates(mx, my, button):
    """send the mouse coordinates to the controlled user"""
    dodo = [tuple_of_sizes[0], tuple_of_sizes[1], tuple_of_sizes[2], tuple_of_sizes[3]]

    # only when running on one computer two monitors
    dodo[0] += 1920
    mx += 1920
    ##########################

    mx -= dodo[0]
    my -= dodo[1]
    mx = int((mx/myscreenx)*screenx)
    my = int((my/(myscreeny-150))*screeny)
    str1 = button+str(mx) + "-" + str(my)
    control_socket.send(bytes(str1.zfill(10), 'utf-8'))


def on_click(x, y, button, press):
    """listener of the mouse, and checks the coordinates of the click"""
    if math.fabs(tuple_of_sizes[0]) < 1920:
        if x >= tuple_of_sizes[0] and y >= tuple_of_sizes[1]:
            if -1920 < x < 0:
                send_mouse_coordinates(x, y, str(button)[7])


def start_mouse_listener():
    """starts the listener of the mouse"""
    global listener
    with Listener(on_click=on_click) as listener:
        listener.join()


def getting_screen_share(control_socket2):
    """getting the screen share"""
    global screenx, screeny
    screenx = int(control_socket2.recv(4).decode('utf-8'))
    screeny = int(control_socket2.recv(4).decode('utf-8'))
    size = int(control_socket2.recv(10).decode('utf-8'))

    try:
        while True:
            chunks = []
            rc_data = 0
            while rc_data < size:
                chunk = control_socket2.recv(size - rc_data)
                chunks.append(chunk)
                rc_data += len(chunk)

            img_to_save = PIL.Image.frombytes("RGB", (screenx, screeny), b''.join(chunks))
            img_np = numpy.array(img_to_save)
            imS = cv2.resize(img_np, (myscreenx, myscreeny-150))

            img_np = cv2.cvtColor(imS, cv2.COLOR_BGR2RGB)
            cv2.namedWindow('frame')
            cv2.imshow('frame', img_np)
            global tuple_of_sizes
            tuple_of_sizes = cv2.getWindowImageRect('frame')

            key = cv2.waitKey(1)
            if key == 27:
                break
    except ConnectionResetError:
        pass

    print("from here")
    listener.stop()
    control_socket.close()
    cv2.destroyAllWindows()
    end_remote_mode()


def control_and_see_another_computer(hi):
    """open a connection with the second user in order to perform screen share"""
    global control_socket

    try:
        control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_socket.connect((ip, int(port)))
        global tr1, tr2
        tr1 = threading.Thread(target=getting_screen_share, args=(control_socket,))
        tr2 = threading.Thread(target=start_mouse_listener)
        tr2.start()
        tr1.start()
        hi.close_ctrl()
    except:
        hi.ctrl_screen.destroy()
        hi.control("oops!\nsomething went wrong\n make sure that the code is correct\n"
                   " and that your fellow pressed his button")


def dont_stop_me_now():
    """close the end remote window"""
    end_screen2.destroy()


def on_key_release(key):
    """open the end remote window when the user press f4"""
    print('{0} release'.format(key))
    if key == key.f4:
        global end_screen2
        end_screen2 = Tk()
        end_screen2.title('exit remote mode')
        end_screen2.geometry('460x250')
        Label(end_screen2, text="").pack()
        Label(end_screen2, text="are you sure you want \nto stop the remote mode?", font=("Helvetica", 20), fg='#003F87').pack()
        global yesb
        yesb = Button(end_screen2, text="Yes", font=("Helvetica", 16), bg="#948771", command=stop_the_share)
        yesb.pack()
        Label(end_screen2, text="").pack()
        Button(end_screen2, text="NO", font=("Helvetica", 16), bg="#948771", command=dont_stop_me_now).pack()
        end_screen2.protocol('WM_DELETE_WINDOW', close_end2)
        end_screen2.mainloop()


def listen_to_keyboard():
    """listen to keyboards pressses"""
    global listenerk
    with Listenerk(on_release=on_key_release) as listenerk:
        listenerk.join()


def let_other_computer_control(hi2):
    """open a connection with the second user in order to perform screen share"""
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('0.0.0.0', PORT))
    serversocket.listen(1)
    # declare the socket as a global var
    global letshare_socket
    (letshare_socket, client_address) = serversocket.accept()

    global t1, t2
    t1 = threading.Thread(target=sharing_the_screen, args=(letshare_socket,))
    t2 = threading.Thread(target=get_mouse_cordinates, args=(letshare_socket,))
    t3 = threading.Thread(target=listen_to_keyboard)
    t3.start()
    t2.start()
    t1.start()
    hi2.close_share()


def send_file(client_socket2):
    """sending a file to another user"""
    if len(fl_arr) > 1:
        zipping = zipfile.ZipFile('filestosend.zip', 'w')
        for i in fl_arr:
            zipping.write(i, compress_type=zipfile.ZIP_DEFLATED)
        zipping.close()
        f1 = "filestosend.zip"

    else:
        f1 = fl_arr[0]

    size = str(os.path.getsize(f1))
    if "\\" in f1:
        name = (f1.split("\\")[-1]).split('.')[-1]
    else:
        name = f1.split('.')[-1]
    client_socket2.send(bytes(name.zfill(5), 'utf-8'))
    client_socket2.send(bytes(size.zfill(10), 'utf-8'))

    with open(f1, 'rb') as f:
        bytestosend = f.read(1024)
        while len(bytestosend) != 0:
            client_socket2.send(bytestosend)
            bytestosend = f.read(1024)


    if name == 'zip':
        os.remove(f1)


def get_file(client_socket3):
    """getting a file from another user"""
    ending = client_socket3.recv(5).decode('utf-8').replace('0', '')
    size = int(client_socket3.recv(10).decode('utf-8'))
    now = datetime.now()
    current_time = str(now.strftime("%Y-%m-%d--%H-%M"))
    fl_name = "Rviewer-" + current_time + "." + ending
    with open(fl_name, 'wb') as fl:
        while size >= 0:
            indata = client_socket3.recv(1024)
            size -= 1024
            fl.write(indata)
    fl.close()


def combine(ip2, port2):
    """encryption of the ip and port"""
    arr = ip2.split('.')
    for i in range(len(arr)):
        arr[i] = int(arr[i])

    for i in range(len(arr)):
        arr[i] = arr[i] << 2

    for i in range(len(arr)):
        count = 0
        while not 65 < arr[i] < 90:
            if arr[i] > 90:
                arr[i] -= 24
                count += 1
            if arr[i] < 65:
                arr[i] += 24
                count -= 1

        arr[i] = [count, arr[i]]

    str_arr = ["", "", "", ""]

    for i in range(len(str_arr)):
        if arr[i][0] < 0:
            arr[i][0] *= -1
            arr[i][1] = chr(arr[i][1]).lower()
            str_arr[i] = f"""{arr[i][0]}{arr[i][1]}"""
        elif arr[i][0] == 0:
            str_arr[i] = f"""{chr(arr[i][1])}"""
        elif arr[i][0] > 0:
            str_arr[i] = f"""{arr[i][0]}{chr(arr[i][1])}"""

    return f"""{str_arr[0]}-{str_arr[1]}-{str_arr[2]}-{str_arr[3]}-{port2 << 1}"""


def decombine(code):
    """decryption of the ip and port"""
    str_arr = code.split("-")
    port3 = int(str_arr[-1]) >> 1
    del str_arr[-1]
    for i in range(len(str_arr)):
        if str_arr[i].isalpha():
            str_arr[i] = (str_arr[i])
        if str_arr[i][0:2].isnumeric():
            str_arr[i] = (str_arr[i][0:2], str_arr[i][2:])
        else:
            str_arr[i] = (str_arr[i][0], str_arr[i][1:])

    for i in range(len(str_arr)):
        if str_arr[i][1].islower():
            str_arr[i] = ord(str_arr[i][1].upper()) - int(str_arr[i][0]) * 24
        else:
            try:
                str_arr[i] = ord(str_arr[i][1]) + int(str_arr[i][0]) * 24
            except TypeError:
                str_arr[i] = ord(str_arr[i][0])

    for i in range(len(str_arr)):
        str_arr[i] = str_arr[i] >> 2

    return f"""{str_arr[0]}.{str_arr[1]}.{str_arr[2]}.{str_arr[3]}:{port3}"""


def sending_the_files(hi3):
    """open a connection with the second user in order to perform files share"""
    serversocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket2.bind(('0.0.0.0', PORT))
    serversocket2.listen(1)
    clientsocket, clientaddress = serversocket2.accept()
    send_file(clientsocket)
    hi3.close_sndfl()


def recv_the_files(hi4):
    """open a connection with the second user in order to perform files share"""
    try:
        clientsocket4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket4.settimeout(2.0)
        clientsocket4.connect((ip, int(port)))
        get_file(clientsocket4)
        hi4.close_getfiles()
    except:
        hi4.get_fl.destroy()
        hi4.get_files("oops!\nsomething went wrong\n make sure that the code is correct\n and that your fellow pressed his button")


class RviwerUserInterface:
    """RviwerUserInterface implements the graphic user interface and the login and register """
    def __init__(self):
        """
        defying variables such as open, register and login screens.
        also defying arrays of information ans labels that may be changed.
        """
        self.open_screen = Tk()
        self.login_screen = None
        self.register_screen = None

        self.login_arr = []
        self.register_arr = []
        self.combi_array = []

        self.text_label1 = Label()
        self.text_label2 = Label()

        self.combi = ""

        self.open_screen.geometry('422x600')
        self.open_screen.title('r -> viewer')
        photo = PhotoImage(file="logo2.png")
        label1 = Label(self.open_screen, image=photo)
        label1.pack()

        Button(self.open_screen, text="Login", width='14', height='3', font=("Helvetica", 20), bg='#948771', command=self.login_interface).place(x=90, y=250)
        Button(self.open_screen, text="Register", width="14", height='3', font=("Helvetica", 20), bg='#948771', command=self.register_interface).place(x=90, y=400)
        self.open_screen.mainloop()

    def exe_screen(self):
        # trying to decrypt the code
        self.combi = f"""{self.combi_array[0].get()}-{self.combi_array[1].get()}-{self.combi_array[2].get()}-{self.combi_array[3].get()}-{self.combi_array[4].get()}"""
        self.combi_array = []
        try:
            self.combi = decombine(self.combi)
            global ip, port
            ip, port = self.combi.split(":")
            control_and_see_another_computer(self)
        except:
            self.ctrl_screen.destroy()
            self.control("your code is not valid, please check it")

    def close_share(self):
        # close the window
        self.screensh.destroy()

    def after_share(self):
        # activate the screen share
        let_other_computer_control(self)

    def share(self):
        # open the window before the screen share
        self.screensh = Tk()
        self.screensh.geometry('400x300')
        self.screensh.title('screen share')
        Label(self.screensh, text="").pack()
        Label(self.screensh, text="in order to start the sharing,\npress the botton,\n and give your fellow the code:\n ", font=("Helvetica", 16), fg='#003F87').pack()
        combi = combine(ADRESS, PORT)
        Label(self.screensh, text=combi, font=("Helvetica", 16), fg='#003F87').pack()
        Button(self.screensh, text="press me", font=("Helvetica", 16), bg="#948771", command=self.after_share).pack()
        Label(self.screensh, text="you can end the remote anytime\n by pressing the f4 key".title(), font=("Helvetica", 18), fg='red').pack()

        self.screensh.protocol('WM_DELETE_WINDOW', self.close_share)

        self.screensh.mainloop()

    def close_ctrl(self):
        # close the window
        self.ctrl_screen.destroy()
        self.combi_array = [None, None, None, None, None]

    def control(self, msg=""):
        # open the screen before the controling
        self.ctrl_screen = Tk()
        self.ctrl_screen.geometry('400x360')
        self.ctrl_screen.title('controlling')
        self.combi_array = [None, None, None, None, None]

        Label(self.ctrl_screen, text="Please enter the code", font=("Helvetica", 16), fg="#003F87").pack()
        Label(self.ctrl_screen, text="Pay Attention! \nyou can exit the remote mode \n only by pressing ESC", font=("Helvetica", 16), fg="red").pack()

        self.combi_array[0] = (Entry(self.ctrl_screen, font=("Helvetica", 13), width=5))
        self.combi_array[0].place(x=50, y=140)

        Label(self.ctrl_screen, text="-").place(x=100, y=140)

        self.combi_array[1] = (Entry(self.ctrl_screen, font=("Helvetica", 13), width=5))
        self.combi_array[1].place(x=110, y=140)

        Label(self.ctrl_screen, text="-").place(x=160, y=140)

        self.combi_array[2] = (Entry(self.ctrl_screen, font=("Helvetica", 13), width=5))
        self.combi_array[2].place(x=170, y=140)

        Label(self.ctrl_screen, text="-").place(x=220, y=140)

        self.combi_array[3] = (Entry(self.ctrl_screen, font=("Helvetica", 13), width=5))
        self.combi_array[3].place(x=230, y=140)

        Label(self.ctrl_screen, text="-").place(x=280, y=140)

        self.combi_array[4] = (Entry(self.ctrl_screen, font=("Helvetica", 13), width=5))
        self.combi_array[4].place(x=290, y=140)

        Label(self.ctrl_screen, text="").pack()

        Button(self.ctrl_screen, text="enter", font=("Helvetica", 16), bg="#948771", command=self.exe_screen).place(x=160, y=180)

        self.mes_ctrl_label = Label(self.ctrl_screen, text=msg, font=("Helvetica", 16), fg="#003F87")
        self.mes_ctrl_label.place(x=15, y=220)

        self.ctrl_screen.protocol('WM_DELETE_WINDOW', self.close_ctrl)

        self.ctrl_screen.mainloop()

    def close_sndfl(self):
        # close the window
        self.snd_fl.destroy()

    def send_fl(self):
        # activate the file sending
        sending_the_files(self)

    def after_selecting(self, files_array):
        # shows to code to the user in order to send the files
        self.snd_fl.destroy()
        self.snd_fl = Tk()
        self.snd_fl.title('send files')
        self.snd_fl.geometry('400x400')
        Label(self.snd_fl, text="").pack()
        Label(self.snd_fl, text="in order to start the sharing,\npress the botton,\n and give your fellow the code:\n ", font=("Helvetica", 16), fg='#003F87').pack()
        combi = combine(ADRESS, PORT)
        Label(self.snd_fl, text=combi, font=("Helvetica", 16), fg='#003F87').pack()
        Button(self.snd_fl, text="press me", font=("Helvetica", 16), bg="#948771", command=self.send_fl).pack()
        self.snd_fl.protocol('WM_DELETE_WINDOW', self.close_sndfl)
        self.snd_fl.mainloop()

    def open_fl_slct(self):
        # open files selection - show an "Open" dialog box and return the path to the selected file
        root = Tk().withdraw()
        filenames = askopenfilenames()
        global fl_arr
        fl_arr = filenames
        if len(fl_arr) == 0:
            self.files_label["text"] = "you must choose at least \none file"
            self.files_label.pack()
            self.open_fl_slct()

        self.after_selecting(fl_arr)

    def send_files(self):
        # open before file selection window
        self.snd_fl = Tk()
        self.snd_fl.title('send files')
        self.snd_fl.geometry('400x400')
        Label(self.snd_fl, text="choose the files that you want \nand let me know when you are \nready to send", font=("Helvetica", 18), fg="#003F87").pack()
        Button(self.snd_fl, text="choose files", font=("Helvetica", 18), command=self.open_fl_slct, bg='#948771').pack()
        self.files_label = Label(self.snd_fl, text="", font=("Helvetica", 18), fg="#003F87")
        self.files_label.pack()

        self.snd_fl.mainloop()

    def exe_files(self):
        # trying to decrypt the code in order to send files
        self.combi = f"""{self.combi_array[0].get()}-{self.combi_array[1].get()}-{self.combi_array[2].get()}-{self.combi_array[3].get()}-{self.combi_array[4].get()}"""
        self.combi_array = []
        try:
            self.combi = decombine(self.combi)
            global ip, port
            ip, port = self.combi.split(":")
            recv_the_files(self)
        except:
            self.get_fl.destroy()
            self.get_files("your code is not valid, please check it")

    def close_getfiles(self):
        # close window and nullify the combination array
        self.get_fl.destroy()
        self.combi_array = [None, None, None, None, None]

    def get_files(self, msg=""):
        # open the "get files" window and waits for the code
        self.get_fl = Tk()
        self.get_fl.geometry('400x400')
        self.get_fl.title('get files')
        self.combi_array = [None, None, None, None, None]
        Label(self.get_fl, text="Please enter the code", font=("Helvetica", 16), fg="#003F87").pack()
        Label(self.get_fl, text="").pack()

        self.combi_array[0] = (Entry(self.get_fl, font=("Helvetica", 13), width=5))
        self.combi_array[0].place(x=50, y=70)

        Label(self.get_fl, text="-").place(x=100, y=70)

        self.combi_array[1] = (Entry(self.get_fl, font=("Helvetica", 13), width=5))
        self.combi_array[1].place(x=110, y=70)

        Label(self.get_fl, text="-").place(x=160, y=70)

        self.combi_array[2] = (Entry(self.get_fl, font=("Helvetica", 13), width=5))
        self.combi_array[2].place(x=170, y=70)

        Label(self.get_fl, text="-").place(x=220, y=70)

        self.combi_array[3] = (Entry(self.get_fl, font=("Helvetica", 13), width=5))
        self.combi_array[3].place(x=230, y=70)

        Label(self.get_fl, text="-").place(x=280, y=70)

        self.combi_array[4] = (Entry(self.get_fl, font=("Helvetica", 13), width=5))
        self.combi_array[4].place(x=290, y=70)

        Label(self.get_fl, text="").pack()

        Button(self.get_fl, text="enter", font=("Helvetica", 16), bg="#948771", command=self.exe_files).place(x=160, y=150)

        self.mes2_ctrl_label = Label(self.get_fl, text=msg, font=("Helvetica", 16), fg="#003F87")
        self.mes2_ctrl_label.place(x=15, y=200)

        self.get_fl.protocol('WM_DELETE_WINDOW', self.close_getfiles)

        self.get_fl.mainloop()

    def close_rv(self):
        # close the window
        self.rv_screen.destroy()

    def using_the_rviwer(self):
        # open the main screen
        self.rv_screen = Tk()
        myfont = font.Font(family='Helvetica', size=17)
        self.rv_screen.geometry('422x650')
        self.rv_screen.title('r -> viewer')
        photo = PhotoImage(file="logo2.png")
        label1 = Label(self.rv_screen, image=photo)
        label1.pack()
        Label(self.rv_screen, text="").pack()
        Label(self.rv_screen, text="").pack()
        Button(self.rv_screen, text="Share my Screen", font=myfont, width='20', height='2', bg='#948771', command=self.share).pack()
        Label(self.rv_screen, text="").pack()
        Button(self.rv_screen, text="Control a Computer", font=myfont, width="20", height='2', bg='#948771', command=self.control).pack()
        Label(self.rv_screen, text="").pack()
        Button(self.rv_screen, text="Send Files", font=myfont, width="20", height='2', bg='#948771', command=self.send_files).pack()
        Label(self.rv_screen, text="").pack()
        Button(self.rv_screen, text="Get Files", font=myfont, width="20", height='2', bg='#948771', command=self.get_files).pack()
        self.rv_screen.protocol('WM_DELETE_WINDOW', self.close_rv)
        self.rv_screen.mainloop()

    def send_login_server(self):
        # send login details to the server and waits for reply
        self.text_label2["text"] = ""
        self.text_label2.pack()
        login_info = ["", ""]
        for i in range(len(self.login_arr)):
            login_info[i] = self.login_arr[i].get()

        msg = pickle.dumps(login_info)
        client_socket.send(msg)
        info_msg = client_socket.recv(30).decode('utf-8')
        self.text_label2["text"] = info_msg
        self.text_label2.pack()
        if info_msg == "Welcome in":
            if self.register_screen is not None:
                self.register_screen.destroy()

            self.login_screen.destroy()
            self.open_screen.destroy()
            global ID,ADRESS, PORT
            ID = client_socket.recv(1).decode('utf-8')
            ADRESS = client_socket.recv(15).decode('utf-8')
            PORT = 50 + int(ID)
            client_socket.close()
            self.using_the_rviwer()

    def send_register_server(self):
        # send register details to the server and waits for reply
        self.text_label1["text"] = ""
        self.text_label1.pack()
        register_info = ["", "", "", ""]
        for i in range(len(self.register_arr)):
            register_info[i] = self.register_arr[i].get()

        msg = pickle.dumps(register_info)
        client_socket.send(msg)
        info_msg1 = client_socket.recv(48).decode('utf-8')
        info_msg2 = client_socket.recv(23).decode('utf-8')
        info_msg3 = client_socket.recv(39).decode('utf-8')
        if '0' in info_msg1:
            info_msg1 = ""
        if '0' in info_msg2:
            info_msg2 = ""
        if '0' in info_msg3:
            info_msg3 = ""

        if info_msg1 == "" and info_msg3 == "" and info_msg2 == "":
            self.text_label1["text"] = "registered successfully"
            self.text_label1.pack()
        else:
            self.text_label1["text"] = info_msg1+"\n"+info_msg2+"\n"+info_msg3
            self.text_label1.pack()

    def close_register(self):
        # close the window and nullify the register array
        self.register_screen.destroy()
        self.register_arr = []

    def register_interface(self):
        # open register window
        self.register_arr = []
        self.register_screen = Toplevel(self.open_screen)
        self.register_screen.title("Register")
        self.register_screen.geometry("450x500")
        Label(self.register_screen, text="Rviewer Registration", font=("Helvetica", 16), fg='#003F87').pack()

        Label(self.register_screen, text="please enter your details below".title(), font=("Helvetica", 16)).pack()

        Label(self.register_screen, text="\nEmail Address", font=("Helvetica", 13)).pack()
        self.register_arr.append(Entry(self.register_screen, font=("Helvetica", 13)))
        self.register_arr[0].pack()

        Label(self.register_screen, text="\nUsername", font=("Helvetica", 13)).pack()
        self.register_arr.append(Entry(self.register_screen, font=("Helvetica", 13)))
        self.register_arr[1].pack()

        Label(self.register_screen, text="\nPassword ", font=("Helvetica", 13)).pack()
        self.register_arr.append(Entry(self.register_screen, font=("Helvetica", 13)))
        self.register_arr[2].pack()

        Label(self.register_screen, text="\nConfirm Password ", font=("Helvetica", 13)).pack()
        self.register_arr.append(Entry(self.register_screen, font=("Helvetica", 13)))
        self.register_arr[3].pack()

        Label(self.register_screen, text="").pack()
        Button(self.register_screen, text="Register", fg='#003F87', font=("Helvetica", 13), width=10, height=1, command=self.send_register_server).pack()
        self.text_label1 = Label(self.register_screen, text="", font=("Helvetica", 15), fg="green")
        self.text_label1.pack()

        self.register_screen.protocol('WM_DELETE_WINDOW', self.close_register)
        self.register_screen.mainloop()

    def close_login(self):
        # close window and nullify the login array
        self.login_screen.destroy()
        self.login_arr = []

    def login_interface(self):
        # open login window
        self.login_arr = []
        self.login_screen = Toplevel(self.open_screen)
        self.login_screen.title("Login")
        self.login_screen.geometry("422x410")
        Label(self.login_screen, text="Rviewer Login", font=("Helvetica", 16), fg='#003F87').pack()

        Label(self.login_screen, text="please enter your details below".title(), font=("Helvetica", 16)).pack()

        Label(self.login_screen, text="\nEmail Address or Username", font=("Helvetica", 13)).pack()

        self.login_arr.append(Entry(self.login_screen, font=("Helvetica", 13)))
        self.login_arr[0].pack()

        Label(self.login_screen, text="\nPassword", font=("Helvetica", 13)).pack()
        self.login_arr.append(Entry(self.login_screen, font=("Helvetica", 13)))
        self.login_arr[1].pack()

        Label(self.login_screen, text="").pack()
        Button(self.login_screen, text="Login", fg='#003F87', font=("Helvetica", 13), width=10, height=1, command=self.send_login_server).pack()
        self.text_label2 = Label(self.login_screen, text="", font=("Helvetica", 15), fg="green")
        self.text_label2.pack()

        self.login_screen.protocol('WM_DELETE_WINDOW', self.close_login)
        self.login_screen.mainloop()


def main():
    # connect to the server
    global client_socket, hi
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 9999))
    # start the rviewer
    hi = RviwerUserInterface()


if __name__ == "__main__":
    main()
