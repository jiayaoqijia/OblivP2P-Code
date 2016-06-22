#!/usr/bin/python

# btgui.py by Nadeem Abdul Hamid

"""
Module implementing simple BerryTella GUI for a simple p2p network.
"""


import sys
import threading

from random import *

from btserverfiler import *


class BTGui:
   def __init__( self, firstpeer, hops=2, maxpeers=5, serverport=5678, serverhost=None, master=None ):
      self.btpeer = FilerPeer( maxpeers, serverport, serverhost )
      

      host,port = firstpeer.split(':')
      self.btpeer.buildpeers( host, int(port), hops=hops )
      #self.updatePeerList()

      t = threading.Thread( target = self.btpeer.mainloop, args = [] )
      t.start()
      
      self.btpeer.startstabilizer( self.btpeer.checklivepeers, 3 )


def main():
   if len(sys.argv) < 5:
      print "Syntax: %s server-host server-port max-peers peer-ip:port" % sys.argv[0]
      sys.exit(-1)
   if sys.argv[1] != "0":
      serverhost = sys.argv[1]
   else:
      serverhost = None
   serverport = int(sys.argv[2])
   maxpeers = sys.argv[3]
   peerid = sys.argv[4]
   app = BTGui( firstpeer=peerid, maxpeers=maxpeers, serverport=serverport, serverhost=serverhost )


# setup and run app
if __name__=='__main__':
   main()
