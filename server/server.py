import socket
import threading
import time
import os
import encryption as encryption
try:
    import config as config
except:
    with open("config.py","w") as f:
        f.write("""####################
# FTP SERVER CONFIG#
####################

############
#NETWORKING#
############
IP: str                     = "127.0.0.1"
PORT: int                   = 8768
ENCDOING: str               = "utf8"
BUFFER_SIZE: int            = 2048
BACKLOG: int                = 20
HEADER_SEPARATOR: str       = "#:|:#"

################
#FILE MANAGMENT#
################
FILE_SEPARATOR: str         = "#:|:#"
FILE_INFO_SEPARATOR: str    = "#:-|-:#"
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

class File_Manager():
    def __init__(self) -> None:
        self.Files: list = []

        self.FILE_SEPARATOR = config.FILE_SEPARATOR
        self.FILE_INFO_SEPARATOR = config.FILE_INFO_SEPARATOR

        self.load_file()

    def save_files(self):
        """ DISCLAIMER!!!!
            This encryption method is NOT secure and is only intended to facilitate the saving process """
        File_List = []
        for file in self.Files:
            # Here I encrypt all the file information to eliminate the possibility that any of the information contains any of the separators
            formated_file = [encryption.encrypt_text(file.file_name,encryption.key),encryption.encrypt_text(str(file.file_size),encryption.key),encryption.encrypt_text(file.file_content.decode(),encryption.key)]
            formated_file = self.FILE_INFO_SEPARATOR.join(formated_file)
            File_List.append(formated_file)
            
        File_List = self.FILE_SEPARATOR.join(File_List)

        with open("save.txt","wb") as f:
            f.write(File_List.encode())

    def load_file(self):
        if not os.path.exists("save.txt"): # check if a save file exists
            return

        self.Files = [] # reseting the file list 

        files = ""
        with open("save.txt", "r") as f:
            files = f.read()

        if not files:
            return

        files = files.split(self.FILE_SEPARATOR)
        for file_info_section in files:
            file_info_enc = file_info_section.split(self.FILE_INFO_SEPARATOR)
            file_info_dec = []
            for file_info in file_info_enc:
                file_info_dec.append(encryption.decrypt_text(file_info, encryption.key))
            
            self.Files.append(File(file_info_dec[0],int(file_info_dec[1]),file_info_dec[2].encode()))
            

    def add_file(self, file: File) -> None:
        if type(file) != File:
            return
        
        # check if a file with the same name is already in the list
        # this will prevent confusion when downloading and deleting files 
        for file_ in self.Files:
            if file_.file_name == file.file_name:
                file.file_name = file.file_name + " - Copy"
        
        self.Files.append(file)

        self.save_files()
    
    def remove_file(self, requested_file: File) -> bool:
        removed = False

        for file in self.Files:
            if file == requested_file:
                self.Files.remove(file)
                removed = True

        self.save_files()

        return removed

    def search_for_file_by_name(self, file_name: str) -> list:
        requested_file: File = File("Sample Text", len(b"Sample Bytes"), B"Sample Bytes")
        found = False

        for file in self.Files:
            if file.file_name == file_name:
                requested_file = file
                found = True
                break

        return [found, requested_file]

class main():
    def __init__(self) -> None:
        ############
        #NETWORKING#
        ############
        self.IP = config.IP
        self.PORT = config.PORT
        self.ENCODING = config.ENCDOING
        self.BUFFER_SIZE = config.BUFFER_SIZE
        self.BACKLOG = config.BACKLOG

        self.HEADER_SEPARATOR = config.HEADER_SEPARATOR

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.IP, self.PORT))

        ################
        #FILE MANAGMENT#
        ################
        self.File_Manager: File_Manager = File_Manager() # storing all the files


        acpt_t = threading.Thread(target=self.accept)
        acpt_t.start()

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

    def receiv_commands(self, conn, addr) -> None:
        # try:
        while True:
            command = conn.recv(self.BUFFER_SIZE).decode(self.ENCODING)
            

            # putting the header and the command in separate var's               
            if command == "UPLOAD_FILE":
                file = self.FTP_RECV(conn) # receive the file
                self.File_Manager.add_file(file) # add it to the file manager
                print(f"===== Upload File: {file.file_name} SUCCESS =====") # console info output

            if command == "DOWNLOAD_FILE":
                requested_file_name: str = conn.recv(self.BUFFER_SIZE).decode(self.ENCODING) # get the name
                requested_file: File = File("Sample Name", 1,b"Sample Bytes") # create a var for the requested file
                
                file_requset = self.File_Manager.search_for_file_by_name(requested_file_name) # get the file from the file manager

                if file_requset[0] == False: # check if the file exists
                    conn.send("ERROR".encode(self.ENCODING)) # sennd error code
                    print(f"===== Downloaded File: {requested_file.file_name} FAILURE =====") # console info output
                    continue

                conn.send("NO_ERROR".encode(self.ENCODING)) # send a postive error/status code 

                requested_file = file_requset[1]
                self.FTP_SEND(requested_file,conn)

                print(f"===== Downloaded File: {requested_file.file_name} SUCCESS =====") # console info output


            if command == "REFRESH":
                if len(self.File_Manager.Files) == 0:
                    conn.send("ERROR".encode(self.ENCODING))

                all_files = []
                for file in self.File_Manager.Files:
                    all_files.append(f"{file.file_name} | {round(file.file_size / 1024, 2)} KB") # a "compressed" version of the self.add_to_listbox mehtod (client)

                all_files = self.HEADER_SEPARATOR.join(all_files)

                conn.send(all_files.encode(self.ENCODING))

                print(f"===== Refresh: SUCCESS =====") # console info output

            if command == "DELETE":
                requested_file_name: str = conn.recv(self.BUFFER_SIZE).decode(self.ENCODING)
                requested_file = self.File_Manager.search_for_file_by_name(requested_file_name)
                
                removed = False
                if requested_file[0] == True:
                    self.File_Manager.remove_file(requested_file[1])
                    removed = True

                if removed == False:
                    conn.send("ERROR".encode(self.ENCODING))
                    print(f"===== Delete File: {requested_file[1].file_name} FAILURE =====") # console info output
                    return
                else:
                    conn.send("DONE".encode(self.ENCODING))
                    print(f"===== Delete File: {requested_file[1].file_name} SUCCESS =====") # console info output
                

        # except Exception as e:
        #     print(e)
        #     print("Lost connection")
    
    def accept(self):
        self.server_socket.listen(self.BACKLOG)
        while True:
            conn, addr = self.server_socket.accept()

            receiv_t = threading.Thread(target=self.receiv_commands, args=(conn,addr))
            receiv_t.start()


if __name__ == "__main__":
    main()


#######
#TO DO#
#######

"""

"""
