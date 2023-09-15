import socket
import threading
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import time
try:
    import config as config
except:
    with open("config.py","w") as f:
        f.write("""####################
# FTP CLIENT CONFIG#
####################

############
#NETWORKING#
############
IP: str                     = "127.0.0.1" 
PORT: int                   = 8768
ENCODING: str               = "utf8"
BUFFER_SIZE: int            = 2048
HEADER_SEPARATOR: str       = "#:|:#"


#####
#GUI#
#####
# Window
WINDOW_SIZE_X: int          = 340
WINDOW_SIZE_Y: int          = 340

# Listbox
FILE_LIST_BOX_X: int        = 10
FILE_LIST_BOX_Y: int        = 10
FILE_LIST_BOX_HEIGHT: int   = 17
FILE_LIST_BOX_WIDTH: int    = 30

# Button('s)
REFRESH_BUTTON_X: int       = 35
REFRESH_BUTTON_Y: int       = 300
REFRESH_BUTTON_WIDTH: int   = 15

DOWNLOAD_BUTTON_X: int      = 225
DOWNLOAD_BUTTON_Y: int      = 30
DOWNLOAD_BUTTON_WIDTH: int  = 11

UPLOAD_BUTTON_X: int        = 225
UPLOAD_BUTTON_Y: int        = 80
UPLOAD_BUTTON_WIDTH: int    = 11

DELETE_BUTTON_X: int        = 225
DELETE_BUTTON_Y: int        = 300
DELETE_BUTTON_WIDTH: int    = 11
""")
    import config as config

class File():
    def __init__(self, file_name: str, file_size: int, file_content: bytes) -> None:
        self.file_name: str = file_name
        self.file_size: int = file_size
        self.file_content: bytes = file_content

        self.header = [self.file_name, str(self.file_size)]

    def debug_print(self):
        print(f"File Name: {self.file_name}")
        print(f"File Size: {self.file_size}")
        print(f"File Content: {self.file_content}")

class main():
    def __init__(self) -> None:
        # self.debug_init()
        # return

        # client networking settings
        self.IP: str = config.IP
        self.PORT: int = config.PORT
        self.ENCODING: str = config.ENCODING
        self.BUFFER_SIZE: int = config.BUFFER_SIZE
        self.HEADER_SEPARATOR: str = config.HEADER_SEPARATOR

        self.WINDOW_SIZE_X: int = config.WINDOW_SIZE_X
        self.WINDOW_SIZE_Y: int = config.WINDOW_SIZE_Y

        # creating the socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server() # calling custom connect function

        GUI_t = threading.Thread(target=self.GUI) # creating window
        GUI_t.start() # calling window


    def debug_init(self) -> None:
        # its used to skip the actual innitiation and therefor dont get a socket error
        # (testing)
        self.WINDOW_SIZE_X: int = config.WINDOW_SIZE_X
        self.WINDOW_SIZE_Y: int = config.WINDOW_SIZE_Y

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.HEADER_SEPARATOR: str = config.HEADER_SEPARATOR

        self.ENCODING: str = config.ENCODING
        self.BUFFER_SIZE: int = config.BUFFER_SIZE

        self.GUI()

    def add_file_to_listbox(self, file: File) -> None:
        file_size_kb = round(file.file_size / 1024, 2)
        self.FILE_LIST_BOX.insert(tk.END, f"{file.file_name} | {file_size_kb} KB")
    
    def add_text_to_listbox(self, text: str):
        self.FILE_LIST_BOX.insert(tk.END, text)

    def on_resize(self,event) -> None:
        width = event.width
        height = event.height
        print("Window size:", width, "x", height)

    def connect_to_server(self) -> bool:
        try:
            self.client_socket.connect((self.IP, self.PORT))
            return True
        except TimeoutError:
            return False

    def refresh(self):
        self.client_socket.send("REFRESH".encode(self.ENCODING))
        all_files = self.client_socket.recv(self.BUFFER_SIZE).decode(self.ENCODING)
        if all_files == "ERROR":
            return
        all_files = all_files.split(self.HEADER_SEPARATOR)
        
        # Clearing the listbox
        self.FILE_LIST_BOX.delete(0, tk.END)

        for file in all_files:
            self.add_text_to_listbox(file)

        return # finish
    
    def download_file(self) -> None:
        try:
            index: int = self.FILE_LIST_BOX.curselection() # getting the curretn selected item in the listbox
            file_name: str = self.FILE_LIST_BOX.get(index)
        except:
            return
        
        file_name = file_name.split(" | ")[0] # this is to get rid of the | ..KB

        self.client_socket.send("DOWNLOAD_FILE".encode(self.ENCODING))
        self.client_socket.send(file_name.encode(self.ENCODING))
        error_msg = self.client_socket.recv(self.BUFFER_SIZE).decode(self.ENCODING)
        
        if error_msg != "NO_ERROR":
            tk.messagebox.showerror("Error", "There Was A Server-Side Error, Please Try Again")
            return
        
        file = self.FTP_RECV(self.client_socket) # receving the requested file
        
        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
 
        file_path = filedialog.askdirectory(initialdir=desktop_path)

        if (not file_path): # check if a file was selected
            return
        
        with open(os.path.join(file_path, file.file_name), "wb") as f:
            f.write(file.file_content)
        
        return # Finish
    
    def upload_file(self) -> None:
        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
 
        file_path = filedialog.askopenfile(initialdir=desktop_path)
        file_path = file_path.name

        if (not file_path): # check if a file was selected
            return

        file_name = file_path.split("/")[-1] # the last element of the path is the filename

        file_content = b""
        with open(file_path, "rb") as f: # gathering the file content
            file_content = f.read()

        file_size = len(file_content) # gathering the file size


        file = File(file_name, file_size, file_content) # creating a file object

        self.client_socket.send("UPLOAD_FILE".encode(self.ENCODING)) # sending the comand
        self.FTP_SEND(file, self.client_socket) # and than the file

        self.refresh()

        return # Finish

    def delete_file(self) -> None:
        try:
            index: int = self.FILE_LIST_BOX.curselection() # getting the curretn selected item in the listbox
            old_file_name: str = self.FILE_LIST_BOX.get(index)
        except:
            return
        
        file_name = old_file_name.split(" | ")[0] # this is to get rid of the | ..KB

        self.client_socket.send("DELETE".encode(self.ENCODING)) # send the command
        self.client_socket.send(file_name.encode(self.ENCODING)) # send the file name
        error_msg = self.client_socket.recv(self.BUFFER_SIZE).decode(self.ENCODING) # checking if the file got deleted
        
        if error_msg == "ERROR":
            tk.messagebox.showerror("Error", "There Was A Server-Side Error, Please Try Again")
            return    
    
        index = self.FILE_LIST_BOX.get(0, tk.END).index(old_file_name)  # Find the index of the item with that value
        self.FILE_LIST_BOX.delete(index)  # Remove the item at that index


    def FTP_RECV(self, socket: socket.socket) -> File:
        header = socket.recv(self.BUFFER_SIZE).decode(self.ENCODING)
        header = header.split(config.HEADER_SEPARATOR)

        file_content = socket.recv(int(header[1]))

        file = File(header[0], int(header[1]), file_content)
        
        return file
        
    def FTP_SEND(self, file: File, socket: socket.socket) -> None:
        header = file.header
        header = self.HEADER_SEPARATOR.join(header)

        socket.send(header.encode(self.ENCODING))
        time.sleep(1) # we need to wait because the server needs to procses the header
        socket.send(file.file_content)

    def GUI(self) -> None:
        # setting up the main window
        self.window = tk.Tk()
        self.window.title(f"FTP SERVER - Client")
        self.window.geometry(f"{self.WINDOW_SIZE_X}x{self.WINDOW_SIZE_Y}")

        # defining
        self.FILE_LIST_BOX = tk.Listbox(master=self.window,height=config.FILE_LIST_BOX_HEIGHT,width=config.FILE_LIST_BOX_WIDTH)
        self.REFRESH_BUTTON = tk.Button(master=self.window, text="Refresh", command= self.refresh,width=config.REFRESH_BUTTON_WIDTH)
        self.DOWNLOAD_BUTTON = tk.Button(master=self.window,text="Download",command=self.download_file,width=config.DOWNLOAD_BUTTON_WIDTH)
        self.UPLOAD_BUTTON = tk.Button(master=self.window,text="Upload",command=self.upload_file,width=config.UPLOAD_BUTTON_WIDTH)
        self.DELETE_BUTTON = tk.Button(master=self.window,text="Delete",command=self.delete_file,width=config.DELETE_BUTTON_WIDTH)

        # placing
        self.REFRESH_BUTTON.place(x=config.REFRESH_BUTTON_X,y=config.REFRESH_BUTTON_Y)
        self.FILE_LIST_BOX.place(x=config.FILE_LIST_BOX_X,y=config.FILE_LIST_BOX_Y)
        self.DOWNLOAD_BUTTON.place(x=config.DOWNLOAD_BUTTON_X,y=config.DOWNLOAD_BUTTON_Y)
        self.UPLOAD_BUTTON.place(x=config.UPLOAD_BUTTON_X,y=config.UPLOAD_BUTTON_Y)
        self.DELETE_BUTTON.place(x=config.DELETE_BUTTON_X,y=config.DELETE_BUTTON_Y)


        # adding all the current uploaded files to the listbox
        self.refresh()

        # self.window.bind("<Configure>", self.on_resize)
        self.window.mainloop()
    

if __name__ == "__main__":
    main()


#######
#TO DO#
#######

"""

"""
