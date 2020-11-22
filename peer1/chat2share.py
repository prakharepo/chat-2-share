# ***chat2share application***
import os
import socket
import sys
from threading import Thread
import time
SPLITOR = "<split>"
BUFFER_SIZE = 4096


# Function responsible for receiving data packets from peers
def GetChatMessage():
    global name
    global broadcastSocket
    while True:
        try:
            recv_message = broadcastSocket.recv(1024)              # receive 1024 bytes from peer
            recv_string_message = str(recv_message.decode('utf-8'))# translating the message into a string
        except:
            break
        if recv_string_message.find(':') != -1:                
        # if the message contains a colon, then we have messages of the form: 'peer name: message'
            if(recv_string_message[:recv_string_message.find(':')] != name):
                # print a message from the peer to the other peers console
                print('\r%s\n' % recv_string_message, end='')      


# Function responsible for sending messages to all peers
def SendChatMessage ():
    global name
    global sendSocket
    sendSocket.setblocking (False)
    while True: # endless loop
        data = input () # input message by peer
        if data == 'Exit()':
        # if someone from the peers wants to exit the program
            sendSocket.close()
            broadcastSocket.close()
            break
        elif data != '' and data != 'Exit()':
        # if the message is not empty and there is no exit message
            send_message = name + ':' + data # form a message in a readable format
            sendSocket.sendto (send_message.encode ('utf-8'), ('255.255.255.255', 8080)) # send message to all peers in the subnet
        else:
        # if the user did not enter a message (i.e. tried to send an empty message)
            print ('Write your message first!')


# Chatting function responsible for connecting to chat room
def chatting ():
    global broadcastSocket
    # socket for receiving messages from peers
    broadcastSocket = socket.socket (socket.AF_INET, socket.SOCK_DGRAM) # initialize a socket to work with IPv4 addresses using UDP protocol
    broadcastSocket.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # SO_REUSEADDR : indicates that several applications can listen to the socket at once
    broadcastSocket.setsockopt (socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # SO_BROADCAST : indicates that the packets will be broadcast
    broadcastSocket.bind (('0.0.0.0', 8080)) # bind to address '0.0.0.0' to listen on all interfaces
    
    global sendSocket
    # socket for sending messages to peers
    sendSocket = socket.socket (socket.AF_INET, socket.SOCK_DGRAM) # initialize the socket to work with IPv4 addresses using the UDP protocol
    sendSocket.setsockopt (socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # SO_BROADCAST : indicates that the packets will be broadcast

    # greeting when client enters into chat room
    print ("***********************************************")
    print ("* Welcome <" +name+ "> to our chat2share! *")
    print ("* To Quit, Enter message: Exit() *")
    print ("* Enjoy Chatting! *")
    print ("***********************************************")

    global recvThread
    recvThread = Thread (target = GetChatMessage) # thread to receive messages from peers

    global sendMsgThread
    sendMsgThread = Thread (target = SendChatMessage) # thread to send messages from peers

    recvThread.start () # start a thread to receive messages from peers
    sendMsgThread.start () # start a thread to send messages to all peers
    
    recvThread.join () # block the thread in which the call is made until recvThread completes
    sendMsgThread.join () # block the thread in which the call is made until sendMsgThread is completed


class ClientThread(Thread):
    def __init__(self,ip,port,sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
    # receiving file using client socket
    def run(self):
        cl_name = self.sock.recv(16).decode()
        print("Sending to",cl_name)
        while True:
            filename = input("Enter filename :")
            # server should know send file not exists and wait for client response
            if not os.path.isfile(filename):
                self.sock.send(('0').encode())
                print("File not exists")
            else:
                self.sock.send(('1').encode())
                # Get file size
                filesize = os.path.getsize(filename)
                # Send name and size of file
                self.sock.send(f"{filename}{SPLITOR}{filesize}".encode())
                # Sending the file
                with open(filename, "rb") as f:
                    while (filesize):
                        bytes_read = f.read(BUFFER_SIZE)
                        if not bytes_read:
                            break
                        self.sock.sendall(bytes_read)
                        filesize -= len(bytes_read)
                f.close()
            # Continue to send more files
            ans = input('\nDo you want to continue(y/n) :') 
            self.sock.send(ans.encode())
            if ans == 'y': 
                continue
            else: 
                break
        # close client socket
        self.sock.close()
    # close server socket


def sending():
    HOST = "127.0.0.1"
    PORT = 5555
    # create the server socket (TCP)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind the socket to address
    s.bind((HOST, PORT))
    # threads = []
    print("Server is Listening on :", PORT)
    cli = int(input("No. of clients: "))
    count = 0
    while True:
        count += 1
        # print(count)
        if(count > cli):
            break
        s.listen(5)
        print ("Waiting for incoming connections...")
        (conn, (ip,port)) = s.accept()
        # print ('Got connection from ', (ip,port))
        newthread = ClientThread(ip,port,conn)
        newthread.start()
        newthread.join()
        # threads.append(newthread)
    # for t in threads:
    #     t.join()
    s.close()    


def receiving():
    HOST = "127.0.0.1"
    PORT = 5555

    # create the client socket
    s = socket.socket()
    print("Connecting to :", PORT)
    try:
        s.connect((HOST, PORT))
        print("Successfully Connected.")
        s.send(name.encode())
        # Get the filename that exists
        try:
            while True:
                exists = s.recv(16).decode()
                if exists != '0':
                    received_filename = s.recv(BUFFER_SIZE).decode()
                    filename, filesize = received_filename.split(SPLITOR)
                    # Extract only filename
                    filename = os.path.basename(filename)
                    # convert filesize to integer
                    filesize = int(filesize)
                    # start receiving the file  
                    with open(filename, "wb") as f:
                        while (filesize):
                            bytes_read = s.recv(BUFFER_SIZE)
                            if not bytes_read:    
                                break
                            f.write(bytes_read)
                            filesize -= len(bytes_read)
                    f.close()
                    print("File stored :",filename)
                ans = s.recv(2).decode()
                if ans == 'y': 
                    continue
                else: 
                    break
            # close the socket
            s.close()
        except:
            print("**Current connection failed**")
            while(1):
                temp = input("Do you wish to connect to other Sender (y/n): ")
                if(temp=='y'):
                    receiving()
                    break
                elif(temp=='n'):
                    break
                else:
                    print("Invalid input")

    except:
        print("**No one is Sending**")


def main():
    global name
    name = '' # username
    while True:
        if not name:
        # if name is empty
            name = input ('Your Name: ')
            if not name:
            # if name is empty
                print ('Please enter a non-empty name!')
            else:
            # if the name is entered, then exit the loop
                break
    print ("***********************************************") # delimiter
    while(True):
        print("Choose your option")
        print("1. Chatting")
        print("2. Sending")
        print("3. Receiving")
        print("4. Exit")
        check = input("Enter Choice: ")
        if(check == '1'):
            chatting()
        elif(check=='2'):
            sending()
        elif(check=='3'):
            receiving()
        elif(check=='4'):
            break
        else:
            print("***Wrong Choice***")
if __name__ == '__main__':
    main()