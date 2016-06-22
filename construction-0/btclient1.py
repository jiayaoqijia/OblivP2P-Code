#!/usr/bin/python


import sys
import threading
import random
import time

from btfiler import *



class BtClient:
     def __init__( self, firstpeer, hops=2, maxpeers=5, serverport=5678, serverhost=None, master=None ):

            self.btpeer = FilerPeer( maxpeers, serverport, serverhost )
            host,port = firstpeer.split(':')

            t = threading.Thread( target = self.btpeer.mainloop, args = [] )
            t.start()
            self.btpeer.startstabilizer( self.btpeer.checklivepeers, 3 )

            
     def naiveinit(self, peerid):
            print peerid
            host,port = peerid.split(':')
            resp = self.btpeer.connectandsend( host, port, NAIVEINIT, self.btpeer.myid )

            if len(resp) > 0:
                data = resp[0][1]
                self.btpeer.bucketdata = str(data).split('>>>')
                number = self.btpeer.bucketdata[0]
                del self.btpeer.bucketdata[0]
            print number + " " + str(self.btpeer.bucketdata)

     def uploaddata( self, peerid, dataid, datacontent ):
            self.btpeer.uploadstarttime = time.time()
            host,port = peerid.split(':')
            senddata = dataid + ">>>" + datacontent
            resp = self.btpeer.connectandsend(host, port, UPLOADDATA, senddata)
            data = resp[0][1]
            print "uploaddata finished."
            print "Time takes " + str(time.time() - self.btpeer.uploadstarttime) 
            print "first 20 bytes"
            print data[:20]

     def readdata( self, peerid, dataid ):
            self.btpeer.readstarttime = time.time()
            host,port = peerid.split(':')
            resp = self.btpeer.connectandsend(host, port, READDATA, dataid)
            print "readdata finished."
            print "Time takes " + str(time.time() - self.btpeer.readstarttime) 
            data = resp[0][1]
            print "first 20 bytes"
            print data[:20]
            #return data

     def btdebug(self, msg):
        """ Prints a messsage to the screen with the name of the current thread """
        print "[%s] %s" % ( str(threading.currentThread().getName()), msg )


def main():
    if len(sys.argv) < 7:
        print "Syntax: %s -c 1 server-host server-port max-peers tracker-ip:port" % sys.argv[0]
        sys.exit(-1)
    if sys.argv[3] != "0":
        serverhost = sys.argv[3]
    else:
        serverhost = None
    serverport = int(sys.argv[4])
    maxpeers = sys.argv[5]
    peerid = sys.argv[6]
    app = BtClient( firstpeer=peerid, maxpeers=maxpeers, serverport=serverport, serverhost=serverhost )
    #app.mainloop()
    #t = threading.Thread( target = app.mainloop(), args = [] )
    #t.start()
    app.naiveinit(peerid)

    N = 3
    dummypath = "."
    uploadN = 3
    accessN = 2**N

    fd = file(dummypath + "/dummy.txt", 'r')
    dummydata = ''
    while True:
        filedata = fd.read(2048)
        if not len(filedata):
            break
        dummydata += filedata
    #print dummydata
    fd.close()
    realdata = dummydata

    for i in range(uploadN):
        if i < 10:
            app.uploaddata(peerid, "data"+str(i), realdata.replace("rese", "res"+str(i)))
        elif i < 100:
            app.uploaddata(peerid, "data"+str(i), realdata.replace("rese", "re"+str(i)))
        elif i< 1000:
            app.uploaddata(peerid, "data"+str(i), realdata.replace("rese", "r"+str(i)))
        else:
            app.uploaddata(peerid, "data"+str(i), realdata.replace("rese", str(i)))

    mockreadsequence = []
    for i in range(accessN):
        n = random.randint(0, uploadN-1)
        mockreadsequence.append("data"+str(n))

    for i in mockreadsequence:
        #if the first 20 bytes contains the requested dataid, e.g., "res2minate" contains 2, then the result is correct
        print "Read data: %s" % i
        app.readdata(peerid, i)

# setup and run app
if __name__=='__main__':
     main()
