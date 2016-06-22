#!/usr/bin/python

"""
Module implementing simple BerryTella GUI for a simple p2p network.
"""


import sys
import threading

#from Tkinter import *
from random import *

from btfiler import *



class BtClient:
    def __init__( self, firstpeer, hops=2, maxpeers=5, serverport=5678, serverhost=None, master=None ):

        self.btpeer = FilerPeer( maxpeers, serverport, serverhost )

        host,port = firstpeer.split(':')
        #self.btpeer.buildpeers( host, int(port), hops=hops )
        #self.updatePeerList()

        t = threading.Thread( target = self.btpeer.mainloop, args = [] )
        t.start()
        #Cancel ping check
        self.btpeer.startstabilizer( self.btpeer.checklivepeers, 3 )
 

    def naiveinit_1(self, peerid):
        #response = self.btpeer.sendtopeer( peerid, NAIVEINIT, self.btpeer.myid )
        print("function naiveinit_1")
        self.btdebug(peerid)
        host,port = peerid.split(':')
        resp = self.btpeer.connectandsend( host, port, NAIVEINIT1, self.btpeer.myid )
        print("self.btpeer.myid", self.btpeer.myid)
        #print peerid + NAIVEINIT + self.btpeer.myid
        #print str(resp)
        if len(resp) > 0:
            data = resp[0][1]
            self.btpeer.bucketdata = self.btpeer.btitpiroram.convertfromstringtopointlist(data)
            #number = self.btpeer.bucketdata[0]
            #del self.btpeer.bucketdata[0]
            #print("bucketdata", str(self.btpeer.bucketdata))

    def uploaddata_1( self, peerid, dataid ):
        host,port = peerid.split(':')
        senddata = dataid
        resp = self.btpeer.connectandsend(host, port, UPLOADDATA1, senddata)
        #data = resp[0][1]
        #self.btdebug( resp)
        data = resp[0][1]
        transactionid, uploadcircuitpeers = str(data).split('<<<')
        self.btpeer.uploadcircuitpeers[transactionid] = uploadcircuitpeers.split(">>>")

        #Generate a block, prepare points
        forcircuitpoints = {}
        for i in self.btpeer.uploadcircuitpeers[transactionid]:
            forcircuitpoints[i] = []

        realpoints = []
        realdatanumber = []
        for i in range(self.btpeer.btitpiroram.pointsnum):
            realdatanumber.append(int(dataid.split("data")[1]))

        #realdatanumber = 1 #mock number for realdata
        #onepoint = btitpiroram.usedcurve.G * datapoint
        #oneblock = btitpiroram.convertfrompointtostring(onepoint)
        for j in range(self.btpeer.btitpiroram.pointsnum):
            onepoint = self.btpeer.btitpiroram.usedcurve.G * realdatanumber[j]
            realpoints.append(onepoint)
            sumpoint = 0
            keys = list(forcircuitpoints.keys())
            for k in forcircuitpoints:
                if k == keys[-1]:
                    sumpoint = (realdatanumber[j] - sumpoint) % self.btpeer.btitpiroram.usedcurve.n
                    forcircuitpoints[k].append(self.btpeer.btitpiroram.usedcurve.G * sumpoint)
                    continue
                apoint = self.btpeer.btitpiroram.generaterandomnumber()
                sumpoint += apoint
                forcircuitpoints[k].append(self.btpeer.btitpiroram.usedcurve.G * apoint)
            
            #onepoint = baserandompoint
            #oneblock = oneblock + "|" + str(self.__generaterandomnumber())
            #oneblock = oneblock + "|" + btitpiroram.convertfrompointtostring(onepoint)
        realpoints = [realpoints]
        realpointsstring = self.btpeer.btitpiroram.convertfrompointlisttostring(realpoints) #real data points
        forcircuitpointsstring = {}
        for i in forcircuitpoints:
            forcircuitpointsstring[i] = self.btpeer.btitpiroram.convertfrompointlisttostring([forcircuitpoints[i]]) #points strings for circuit peers

        for i in forcircuitpointsstring:
            host,port = i.split(':')
            singlecircuitdata = transactionid + "<<<" + forcircuitpointsstring[i]
            resp = self.btpeer.connectandsend(host, port, UPLOADCIRCUITSEND, singlecircuitdata)
        #upload finished
        del self.btpeer.uploadcircuitpeers[transactionid]


    def readdata_1( self, peerid, dataid ):
        host,port = peerid.split(':')
        msg = self.btpeer.myid + "<<<" + dataid
        resp = self.btpeer.connectandsend(host, port, READDATA1, msg)
        self.btdebug("readdata")
        #self.btdebug( resp)
        data = resp[0][1]
        transactionid, circuitpeersstr = data.split("<<<")
        #self.btpeer.fetchcircuitnum[transactionid] = len(circuitpeersstr.split(">>>"))


        
    def naiveinit(self, peerid):
        #response = self.btpeer.sendtopeer( peerid, NAIVEINIT, self.btpeer.myid )
        self.btdebug( peerid)
        host,port = peerid.split(':')
        resp = self.btpeer.connectandsend( host, port, NAIVEINIT, self.btpeer.myid )
        #print peerid + NAIVEINIT + self.btpeer.myid
        #print str(resp)
        if len(resp) > 0:
            data = resp[0][1]
            self.btpeer.bucketdata = str(data).split('>>>')
            number = self.btpeer.bucketdata[0]
            del self.btpeer.bucketdata[0]
            #print(number + " " + str(self.btpeer.bucketdata))

    def uploaddata( self, peerid, dataid, datacontent ):
        host,port = peerid.split(':')
        senddata = dataid + ">>>" + datacontent
        resp = self.btpeer.connectandsend(host, port, UPLOADDATA, senddata)
        #data = resp[0][1]
        self.btdebug( resp)

    def readdata( self, peerid, dataid ):
        host,port = peerid.split(':')
        resp = self.btpeer.connectandsend(host, port, READDATA, dataid)
        self.btdebug("readdata")
        #data = resp[0][1]
        self.btdebug( resp)
        #return data

    def btdebug(self, msg):
        """ Prints a messsage to the screen with the name of the current thread """
        print ("[%s] %s" % ( str(threading.currentThread().getName()), msg ))
def debug (msg):
#--------------------------------------------------------------------------
   """ Print debug information.
   """
   print(msg)

def main():
    if len(sys.argv) < 7:
        debug( "Syntax: %s -c 1 server-host server-port max-peers tracker-ip:port" % sys.argv[0])
        sys.exit(-1)
    if sys.argv[3] != "0":
        serverhost = sys.argv[3]
    else:
        serverhost = None
    serverport = int(sys.argv[4])
    print("serverport", serverport)
    maxpeers = sys.argv[5]
    peerid = sys.argv[6]
    app = BtClient( firstpeer=peerid, maxpeers=maxpeers, serverport=serverport, serverhost=serverhost )
    #app.mainloop()
    #t = threading.Thread( target = app.mainloop(), args = [] )
    #t.start()
    app.naiveinit_1(peerid)

if __name__=='__main__':
    main()
