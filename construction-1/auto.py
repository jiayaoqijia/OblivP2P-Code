import subprocess
import socket
import struct
import threading
import time
import traceback
import sys

def debug (msg):
#--------------------------------------------------------------------------
   """ Print debug information.
   """
   print(msg)

def subprocess_cmd(command):
    process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    debug( proc_stdout)

def obtain_host():
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.connect( ( "www.google.com", 80 ) )
    serverhost = s.getsockname()[0]
    debug( "server host: %s" % serverhost)
    #print "server host: %s" % serverhost
    s.close()
    return serverhost

cmd = ""
N = int(sys.argv[1])
M = 2**(N+1) - 2
#serverhost = obtain_host()
serverhost = "127.0.0.1"
trackerid = "127.0.0.1:7090"
for i in range(0, M):
    cmd = cmd + " sleep 0.01; python3 btclient0.py -c 1 " + serverhost + " "+ str(10000+i) +  " 0 " + trackerid + "& "

debug( cmd)
subprocess_cmd(cmd)
