#!/usr/bin/python

import sys
import threading

from random import *

from btfiler import *



class BtClient:
    def __init__( self, firstpeer, hops=2, maxpeers=5, serverport=5678, serverhost=None, master=None ):
        self.btpeer = FilerPeer( maxpeers, serverport, serverhost )
        
        #self.bind( "<Destroy>", self.__onDestroy )

        host,port = firstpeer.split(':')

        t = threading.Thread( target = self.btpeer.mainloop, args = [] )
        t.start()
        self.btpeer.startstabilizer( self.btpeer.checklivepeers, 3 )

        
    def naiveinit(self, peerid):
        #response = self.btpeer.sendtopeer( peerid, NAIVEINIT, self.btpeer.myid )
        print peerid
        host,port = peerid.split(':')
        resp = self.btpeer.connectandsend( host, port, NAIVEINIT, self.btpeer.myid )
        #print peerid + NAIVEINIT + self.btpeer.myid
        #print str(resp)
        if len(resp) > 0:
            data = resp[0][1]
            self.btpeer.bucketdata = str(data).split('>>>')
            number = self.btpeer.bucketdata[0]
            del self.btpeer.bucketdata[0]
            #print number + " " + str(self.btpeer.bucketdata)

    def uploaddata( self, peerid, dataid, datacontent ):
        host,port = peerid.split(':')
        senddata = dataid + ">>>" + datacontent
        resp = self.btpeer.connectandsend(host, port, UPLOADDATA, senddata)
        #data = resp[0][1]
        print resp

    def readdata( self, peerid, dataid ):
        host,port = peerid.split(':')
        resp = self.btpeer.connectandsend(host, port, READDATA, dataid)
        print "readdata"
        #data = resp[0][1]
        print resp

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


# setup and run app
if __name__=='__main__':
    main()
