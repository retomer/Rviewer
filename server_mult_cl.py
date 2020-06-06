import socket
import sqlite3
import pickle
import multiprocessing
import re


class Users:
    """Users handling the operations with the data base"""

    def __init__(self, clientsocket, tablename="UsersInfo", email_addr="email_addr", username="username", password="password", userId="userId"):
        """ defying the names of the columns of the table and creates one if needed"""
        self.clientsocket = clientsocket
        self.__tablename = tablename
        self.__email_addr = email_addr
        self.__username = username
        self.__password = password
        self.__userId = userId

        conn = sqlite3.connect('rvusers.db')
        conn.execute(f"""CREATE TABLE IF NOT EXISTS {tablename} 
                         ({self.__userId} INTEGER PRIMARY KEY AUTOINCREMENT , 
                          {self.__email_addr} TEXT NOT NULL, 
                          {self.__username} TEXT NOT NULL, 
                          {self.__password} TEXT NOT NULL )""")
        conn.commit()
        conn.close()

    def empty_the_table(self):
        # emptying the table
        conn = sqlite3.connect('rvusers.db')
        conn.execute(f"""DELETE FROM {self.__tablename}""")
        conn.commit()
        conn.close()

    def get_table_name(self):
        # gets the name of the table
        return self.__tablename

    def insert_user(self, email, username, password):
        # insert a user to the table
        conn = sqlite3.connect('rvusers.db')
        str_insert = f"""INSERT INTO {self.__tablename} ({self.__email_addr}, {self.__username}, {self.__password}) VALUES ("{email}", "{username}", "{password}")"""
        conn.execute(str_insert)
        conn.commit()
        conn.close()

    def login(self, email_or_username, password):
        # checking the login information
        conn = sqlite3.connect('rvusers.db')
        by_email = conn.execute(
            f"""SELECT {self.__password} FROM {self.__tablename} WHERE {self.__email_addr} = "{email_or_username}" """)
        by_password = conn.execute(
            f"""SELECT {self.__password} FROM {self.__tablename} WHERE {self.__username} = "{email_or_username}" """)

        by_email = by_email.fetchone()
        by_password = by_password.fetchone()
        msg = ""
        if by_password is None and by_email is None:
            msg = "no such user"
        elif by_email is not None:
            if by_email[0] == password:
                msg = "Welcome in"
            else:
                msg = "wrong password"
        elif by_password is not None:
            if by_password[0] == password:
                msg = "Welcome in"
            else:
                msg = "wrong password"
        try:
            self.clientsocket.send(bytes(msg, 'utf-8'))
        except OSError:
            pass

        user_id = 0
        if msg == "Welcome in":
            if by_email == None:
                user_id = conn.execute(f"""SELECT {self.__userId} FROM {self.__tablename} WHERE {self.__username} = "{email_or_username}" """).fetchone()
            elif by_password == None:
                user_id = conn.execute(
                    f"""SELECT {self.__userId} FROM {self.__tablename} WHERE {self.__email_addr} = "{email_or_username}" """).fetchone()
            user_id = str(user_id).replace("(", "")
            user_id = user_id.replace(")", "")
            user_id = user_id.replace(",", "")
            boole = True
        else:
            boole = False

        return boole, user_id

    def is_details_valid(self, email, username, password, conf_pass):
        # checks if the register details are valid
        conn = sqlite3.connect('rvusers.db')
        # checks if the email is used by another user
        is_email_exist = conn.execute(
            f"""SELECT {self.__userId} FROM {self.__tablename} WHERE {self.__email_addr} = "{email}" """).fetchone()
        # checks if the username is used by another user
        is_username_exist = conn.execute(
            f"""SELECT {self.__userId} FROM {self.__tablename} WHERE {self.__username} = "{username}" """).fetchone()
        # checks if the password is used by another user
        is_password_exist = conn.execute(
            f"""SELECT {self.__userId} FROM {self.__tablename} WHERE {self.__password} = "{password}" """).fetchone()

        conn.commit()
        conn.close()
        str1 = "your"
        str2 = ""
        str3 = ""
        count = 0

        # checks if the email is valid
        regex = "^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
        if not (re.search(regex, str(email))):
            str2 = "your email is not valid"

        if conf_pass != password:
            str3 = "your password confirmation is not valid"

        if is_email_exist is not None and is_username_exist is not None and is_password_exist is not None:
            if is_email_exist is not None:
                str1 += " email"
                count = 1
            if is_username_exist is not None:
                if count == 1:
                    str1 += ", username"
                else:
                    str1 += " username"
                count = 2
            if is_password_exist is not None:
                if count > 0:
                    str1 += ", password"
                else:
                    str1 += " password"
            if count > 1:
                str1 += " are already taken"
            else:
                str1 += " is already taken"

        else:
            str1 = ""
        return str1, str2, str3

    def register(self, email, username, password, conf_pass):
        # checks if the given details are valid and insert the user
        is_not_taken, is_valid, conf = self.is_details_valid(email, username, password, conf_pass)
        self.clientsocket.send(bytes(is_not_taken.zfill(48), 'utf-8'))
        self.clientsocket.send(bytes(is_valid.zfill(23), 'utf-8'))
        self.clientsocket.send(bytes(conf.zfill(39), 'utf-8'))
        while is_not_taken != "" or is_valid != "" or conf != "":
            try:
                break
            except ConnectionResetError:
                break
            except EOFError:
                break
        else:
            self.insert_user(email, username, password)


class Server(object):
    """Server handling the clients"""

    def __init__(self, server_ip, connection_port):
        """defying variables such as ip, port, number of clients and clients array"""
        self.server_ip = server_ip
        self.connection_port = connection_port
        self.count = 0
        self.clients_array = []

    def start(self):
        # starting the tcp server
        try:
            # Create a TCP/IP socket
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serversocket.bind((self.server_ip, self.connection_port))
            serversocket.listen(1)
            while True:
                (clientsocket, client_address) = serversocket.accept()
                self.clients_array.append((clientsocket, client_address[0]))
                self.count += 1
                self.handleclientrequest(self.count)
        except:
            pass

    def handleclientrequest(self, current):
        # start a process per client
        client_handler = multiprocessing.Process(target=self.handle_client_connection, args=(self.clients_array[current - 1][0], self.clients_array[current - 1][1], current,))
        client_handler.start()

    def handle_client_connection(self, ClientSocket, client_adress, current):
        # handling a client
        self.database = Users(ClientSocket)
        data = ""
        while data == "":
            try:
                data = ClientSocket.recv(4096)
            except:
                pass

        else:
            try:
                data = pickle.loads(data)
                while len(data) != 0:
                    if len(data) == 2:
                        is_in, client_id = self.database.login(data[0], data[1])
                        if client_id == 0:
                            self.handle_client_connection(ClientSocket, client_adress, current)
                        else:
                            try:
                                ClientSocket.send(bytes(str(client_id), 'utf-8'))
                                ClientSocket.send(bytes(str(client_adress), 'utf-8'))
                                ClientSocket.close()
                                break
                            except:
                                break
                    else:
                        self.database.register(data[0], data[1], data[2], data[3])
                        data = ClientSocket.recv(4096)
                        data = pickle.loads(data)
                        #  self.handle_client_connection(ClientSocket, current)
            except EOFError:
                pass


# create an instance of Server class and start it
ip = '0.0.0.0'
port = 9999
s = Server(ip, port)
s.start()
