#!/usr/bin/python

#(C)2002-2003 Chris Liechti <cliechti@gmx.net>
#redirect data from a TCP/IP connection to a serial port and vice versa
#requires Python 2.2 'cause socket.sendall is used

# Modified to be used as a udoo<->viper bridge
# by Viper Team

"""USAGE: tcp_serial_redirect.py [options]
Simple Serial to Network (TCP/IP) redirector.

Options:
  -p, --port=PORT   serial port, a number, defualt = 0 or a device name
  -b, --baud=BAUD   baudrate, default 9600
  -r, --rtscts      enable RTS/CTS flow control (default off)
  -x, --xonxoff     enable software flow control (default off)
  -P, --localport   TCP/IP port on which to run the server (default 7777)

Note: no security measures are implemeted. Anyone can remotely connect
to this service over the network.
Only one connection at once is supported. If the connection is terminaed
it waits for the next connect.
"""

import sys, os, serial, threading, getopt, socket, time, signal, subprocess

try:
    True
except NameError:
    True = 1
    False = 0

class Redirector:
    def __init__(self, serial, socket):
        self.serial = serial
        self.socket = socket

    def shortcut(self):
        """connect the serial port to the tcp port by copying everything
           from one side to the other"""
        self.alive = True
        self.thread_read = threading.Thread(target=self.reader)
        self.thread_read.setDaemon(1)
        self.thread_read.start()
        self.writer()
    
    def reader(self):
        """loop forever and copy serial->socket"""
        while self.alive:
            try:
                data = self.serial.read(1)              #read one, blocking
                n = self.serial.inWaiting()             #look if there is more
                if n:
                    data = data + self.serial.read(n)   #and get as much as possible
                if data:
                    self.socket.sendall(data)           #send it over TCP
		    #print data
            except socket.error, msg:
                print msg
                #probably got disconnected
                break
        self.alive = False
    
    def writer(self):
        """loop forever and copy socket->serial"""
        while self.alive:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                self.serial.write(data)                 #get a bunch of bytes and send them
		#print(data)
            except socket.error, msg:
                print msg
                #probably got disconnected
                break
        self.alive = False
        self.thread_read.join()

    def stop(self,a,b):
        """Stop copying"""
        if self.alive:
            self.alive = False
            self.thread_read.join()

class Advertiser():
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #create UDP socket
        self.sock.bind(('', 0))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #this is a broadcast socket

    def run(self):
        self.running=True
        print "\nAdvertiser started...\n"
        while self.running:
            data = "udoo_viper"
            self.sock.sendto(data, ('<broadcast>', 7788))
            time.sleep(2)
        print "\nAdvertiser killed...\n"

    def stop(self,a,b):
	global ser
        self.running=False
	try:
	    ser.close()
	except:
	    pass
	sys.exit(1)


if __name__ == '__main__':

    #start advertiser

    print "-"*60
    print "Viper <----> Udoo Serial Bridge"
    print "-"*60


    adv = Advertiser()
    advth = threading.Thread(target=adv.run)
    advth.start()
    signal.signal(signal.SIGINT, adv.stop)


    ser = serial.Serial()
    
    #parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                "hp:b:rxP",
                ["help", "port=", "baud=", "rtscts", "xonxoff", "localport="])
    except getopt.GetoptError:
        # print help information and exit:
        print >>sys.stderr, __doc__
        sys.exit(2)
    
    ser.port    = "/dev/ttymxc3"
    ser.baudrate = 115200
    ser.rtscts  = False
    ser.xonxoff = False
    ser.timeout = 1     #required so that the reader thread can exit
    
    localport = 7777
    for o, a in opts:
        if o in ("-h", "--help"):   #help text
            usage()
            sys.exit()
        elif o in ("-p", "--port"):   #specified port
            try:
                ser.port = int(a)
            except ValueError:
                ser.port = a
        elif o in ("-b", "--baud"):   #specified baudrate
            try:
                ser.baudrate = int(a)
            except ValueError:
                raise ValueError, "Baudrate must be a integer number"
        elif o in ("-r", "--rtscts"):
            ser.rtscts = True
        elif o in ("-x", "--xonxoff"):
            ser.xonxoff = True
        elif o in ("-P", "--localport"):
            try:
                localport = int(a)
            except ValueError:
                raise ValueError, "Local port must be an integer number"

    print "--- TCP/IP to Serial redirector --- type Ctrl-C / BREAK to quit"

    try:
        ser.open()
    except serial.SerialException, e:
        print "Could not open serial port %s: %s" % (ser.portstr, e)
        sys.exit(1)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind( ('', localport) )
    srv.listen(1)
    while 1:
        try:
            print "Waiting for connection..."
            connection, addr = srv.accept()
            print 'Connected by', addr
    	    #reset sam3x
	    subprocess.check_output("./reset.sh",universal_newlines=True,shell=True)
	    #enter console->serial loop
            r = Redirector(ser, connection)
            r.shortcut()
            print 'Disconnected'
            connection.close()
        except socket.error, msg:
            print msg

    print "\n--- exit ---"
