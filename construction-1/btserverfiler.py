#!/usr/bin/python

from btserverpeer import *
import sys
from datetime import datetime
import time

PEERNAME = "NAME"   # request a peer's canonical id
LISTPEERS = "LIST"
INSERTPEER = "JOIN"
QUERY = "QUER"
QRESPONSE = "RESP"
FILEGET = "FGET"
PEERQUIT = "QUIT"

REPLY = "REPL"
ERROR = "ERRO"
PING = "PING"

#New types for privacy-preserving settings
REQUEST = "REQU"
ROUTE = "ROUT"
NAIVEINIT = "INI1"
UPLOADDATA = "UPLO"
READDATA = "READ"
LOCATEDATA = "LOCA"
LOCATEDATAFINISH = "LOFI"
EARLYSHUFFLE = "EARL"
EVICTION = "EVIC"
EARLYSHUFFLEFINISH = "EAFI"
EVICTIONFINISH = "EVFI"

NAIVEINIT1 = "IN11"
UPLOADDATA1 = "UPL1"
READDATA1 = "FET1"
INITSTASH = "INST"
UPLOADCIRCUITSEND = "UPCS"
UPLOADSTASHCIRCUITINFO = "UPSC"
UPLOADCIRCUITSTASHINFO = "UCSI"
UPLOADSTASHFINISH = "UPSF"

FETCHPATHPEERINFO = "FEPI"
FETCHCIRCUITPEERINFO = "FECI"
FETCHTOSTASHINFO = "FESI"
FETCHSTASHFINISH = "FESF"
FETCHTOINITINFO = "FEII"
FETCHINITIATORFINISH = "FEIF"

EVICTIONPATHPEERINFO = "EVPI"
EVICTIONCIRCUITPEERINFO = "EVCI"
EVICTIONSTASHFINISH = "EVSF"
EVICTIONPATHPEERFINISH = "EVPF"



# Assumption in this program:
#   peer id's in this application are just "host:port" strings

#==============================================================================
class FilerPeer(BTPeer):
#==============================================================================
    """ Implements a file-sharing peer-to-peer entity based on the generic
    BerryTella P2P framework.

    """

    #--------------------------------------------------------------------------
    def __init__(self, maxpeers, serverport, serverhost = None):
    #--------------------------------------------------------------------------
        """ Initializes the peer to support connections up to maxpeers number
        of peers, with its server listening on the specified port. Also sets
        the dictionary of local files to empty and adds handlers to the 
        BTPeer framework.

        """
        BTPeer.__init__(self, maxpeers, serverport, None, serverhost)
        
        self.files = {}  # available files: name --> peerid mapping
        self.debug = 0

        self.addrouter(self.__router)

        handlers = {LISTPEERS : self.__handle_listpeers,
                    INSERTPEER : self.__handle_insertpeer,
                    PING : self.__handle_ping,
                    PEERNAME: self.__handle_peername,
                    QUERY: self.__handle_query,
                    QRESPONSE: self.__handle_qresponse,
                    FILEGET: self.__handle_fileget,
                    PEERQUIT: self.__handle_quit,
                    REQUEST: self.__handle_request,
                    ROUTE: self.__handle_route,
                    NAIVEINIT: self.__handle_naiveinit,
                    UPLOADDATA: self.__handle_uploaddata,
                    READDATA: self.__handle_readdata,
                    NAIVEINIT1: self.__handle_naiveinit_1,
                    UPLOADDATA1: self.__handle_uploaddata_1,
                    READDATA1: self.__handle_readdata_1,
                    UPLOADSTASHFINISH: self.__handle_uploadstashfinish,
                    FETCHSTASHFINISH: self.__handle_fetchstashfinish,
                    FETCHINITIATORFINISH: self.__handle_fetchinitiatorfinish,
                    EVICTIONSTASHFINISH: self.__handle_evictionstashfinish,
                    EVICTIONPATHPEERFINISH: self.__handle_evictionpathpeerfinish
                   }
        for mt in handlers:
            self.addhandler(mt, handlers[mt])

    # end FilerPeer constructor


    #--------------------------------------------------------------------------
    def __debug( self, msg ):
    #--------------------------------------------------------------------------
        if self.debug:
            print("[%s] %s" % ( str(threading.currentThread().getName()), msg ))
    # #--------------------------------------------------------------------------
    # def __debug(self, msg):
    # #--------------------------------------------------------------------------
    #  """ Prints a messsage to the screen with the name of the current thread """
    #     if self.debug:
    #         print ("[%s] %s" % ( str(threading.currentThread().getName()), msg ))
    #     #if self.debug:
    #     #    btdebug(msg)



    #--------------------------------------------------------------------------
    def __router(self, peerid):
    #--------------------------------------------------------------------------
        if peerid not in self.getpeerids():
            return (None, None, None)
        else:
            rt = [peerid]
            rt.extend(self.peers[peerid])
            return rt



    #--------------------------------------------------------------------------
    def __handle_insertpeer(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the INSERTPEER (join) message type. The message data
        should be a string of the form, "peerid  host  port", where peer-id
        is the canonical name of the peer that desires to be added to this
        peer's list of peers, host and port are the necessary data to connect
        to the peer.

        """
        self.peerlock.acquire()
        try:
            try:
                peerid,host,port = data.split()

                if self.maxpeersreached():
                    self.__debug('maxpeers %d reached: connection terminating' 
                                  % self.maxpeers)
                    peerconn.senddata(ERROR, 'Join: too many peers')
                    return

                # peerid = '%s:%s' % (host,port)
                if peerid not in self.getpeerids() and peerid != self.myid:
                    self.addpeer(peerid, host, port)
                    self.__debug('added peer: %s' % peerid)
                    peerconn.senddata(REPLY, 'Join: peer added: %s' % peerid)
                else:
                    peerconn.senddata(ERROR, 'Join: peer already inserted %s'
                                       % peerid)
            except:
                self.__debug('invalid insert %s: %s' % (str(peerconn), data))
                peerconn.senddata(ERROR, 'Join: incorrect arguments')
        finally:
            self.peerlock.release()

    # end handle_insertpeer method



    #--------------------------------------------------------------------------
    def __handle_listpeers(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the LISTPEERS message type. Message data is not used. """
        self.peerlock.acquire()
        try:
            self.__debug('Listing peers %d' % self.numberofpeers())
            peerconn.senddata(REPLY, '%d' % self.numberofpeers())
            for pid in self.getpeerids():
                host,port = self.getpeer(pid)
                peerconn.senddata(REPLY, '%s %s %d' % (pid, host, port))
        finally:
            self.peerlock.release()



    #--------------------------------------------------------------------------
    def __handle_peername(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the NAME message type. Message data is not used. """
        peerconn.senddata(REPLY, self.myid)

    #--------------------------------------------------------------------------
    def __handle_ping(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the PING message type. Message data is not used. """
        peerconn.senddata(REPLY, self.myid)


    # QUERY arguments: "return-peerid key ttl"
    #--------------------------------------------------------------------------
    def __handle_query(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the QUERY message type. The message data should be in the
        format of a string, "return-peer-id  key  ttl", where return-peer-id
        is the name of the peer that initiated the query, key is the (portion
        of the) file name being searched for, and ttl is how many further 
        levels of peers this query should be propagated on.

        """
        # self.peerlock.acquire()
        try:
            peerid, key, ttl = data.split()
            peerconn.senddata(REPLY, 'Query ACK: %s' % key)
        except:
            self.__debug('invalid query %s: %s' % (str(peerconn), data))
            peerconn.senddata(ERROR, 'Query: incorrect arguments')
        # self.peerlock.release()

        t = threading.Thread(target=self.__processquery, 
                              args=[peerid, key, int(ttl)])
        t.start()



    # 
    #--------------------------------------------------------------------------
    def __processquery(self, peerid, key, ttl):
    #--------------------------------------------------------------------------
        """ Handles the processing of a query message after it has been 
        received and acknowledged, by either replying with a QRESPONSE message
        if the file is found in the local list of files, or propagating the
        message onto all immediate neighbors.

        """
        #print self.files.keys()
        for fname in self.files.keys():
            if key in fname:
                fpeerid = self.files[fname]
                if not fpeerid:   # local files mapped to None
                    fpeerid = self.myid
                host,port = peerid.split(':')
                # can't use sendtopeer here because peerid is not necessarily
                # an immediate neighbor
                self.connectandsend(host, int(port), QRESPONSE, 
                                     '%s %s' % (fname, fpeerid),
                                     pid=peerid)
                return
        # will only reach here if key not found... in which case
        # propagate query to neighbors
        if ttl > 0:
            msgdata = '%s %s %d' % (peerid, key, ttl - 1)
            for nextpid in self.getpeerids():
                self.sendtopeer(nextpid, QUERY, msgdata)

# QUERY arguments: "return-peerid key ttl"
    #--------------------------------------------------------------------------
    def __handle_request(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the QUERY message type. The message data should be in the
        format of a string, "return-peer-id  key  ttl", where return-peer-id
        is the name of the peer that initiated the query, key is the (portion
        of the) file name being searched for, and ttl is how many further 
        levels of peers this query should be propagated on.

        """
        # self.peerlock.acquire()
        try:
            peerid, key, ttl = data.split()
            peerconn.senddata(REPLY, 'Query ACK: %s' % key)
        except:
            self.__debug('invalid query %s: %s' % (str(peerconn), data))
            peerconn.senddata(ERROR, 'Query: incorrect arguments')
        # self.peerlock.release()

        t = threading.Thread(target=self.__processquery, 
                              args=[peerid, key, int(ttl)])
        t.start()



    # 
    #--------------------------------------------------------------------------
    def __processrequest(self, peerid, key, ttl):
    #--------------------------------------------------------------------------
        """ Handles the processing of a query message after it has been 
        received and acknowledged, by either replying with a QRESPONSE message
        if the file is found in the local list of files, or propagating the
        message onto all immediate neighbors.

        """
        #print self.files.keys()
        for fname in self.files.keys():
            if key in fname:
                fpeerid = self.files[fname]
                if not fpeerid:   # local files mapped to None
                    fpeerid = self.myid
                host,port = peerid.split(':')
                # can't use sendtopeer here because peerid is not necessarily
                # an immediate neighbor
                self.connectandsend(host, int(port), QRESPONSE, 
                                     '%s %s' % (fname, fpeerid),
                                     pid=peerid)
                return
        # will only reach here if key not found... in which case
        # propagate query to neighbors
        if ttl > 0:
            msgdata = '%s %s %d' % (peerid, key, ttl - 1)
            for nextpid in self.getpeerids():
                self.sendtopeer(nextpid, QUERY, msgdata)

        #--------------------------------------------------------------------------
    def __handle_route(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the FILEGET message type. The message data should be in
        the format of a string, "file-name", where file-name is the name
        of the file to be fetched.

        """
        fname = data
        if fname not in self.files:
            self.__debug('File not found %s' % fname)
            peerconn.senddata(ERROR, 'File not found')
            return
        try:
            fd = file(fname, 'r')
            filedata = ''
            while True:
                data = fd.read(2048)
                if not len(data):
                    break;
                filedata += data
                #print filedata
            fd.close()
        except:
            self.__debug('Error reading file %s' % fname)
            peerconn.senddata(ERROR, 'Error reading file')
            return
        
        peerconn.senddata(REPLY, filedata)

    #--------------------------------------------------------------------------
    def __handle_naiveinit_1(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the NAIVEINIT message type. The message data should be in
        the format of a string of peerid.

        """
        peerid = data
        self.__debug("peermap: " + str(self.btitpiroram.peermap))
        receiveddata = self.btitpiroram.join(peerid)
        #for i in self.bitstrings:
        #    if self.peermap[i] is None:
        #            self.peermap[i] = peerid
        #            self.peermapreverse[peerid] = i
        #            break
        #if i is self.bitstrings[-1]:
        #    return False
        self.__debug("peermap " + str(self.btitpiroram.peermap))

        # dummy = "dummy.txt"
        # real = "file.txt"
        # print str(self.peermapreverse.keys()) + " " + data
        if peerid in self.btitpiroram.peermapreverse:
        #     #read dummy data
        #     fd = file(dummy, 'r')
        #     dummydata = ''
        #     while True:
        #             filedata = fd.read(2048)
        #             if not len(filedata):
        #                     break
        #             dummydata += filedata
        #     #print dummydata
        #     fd.close()

        #     #read real data
        #     fd = file(real, 'r')
        #     realdata = ''
        #     while True:
        #             filedata = fd.read(2048)
        #             if not len(filedata):
        #                     break
        #             realdata += filedata
        #     #print realdata
        #     fd.close()
            respdata = self.btitpiroram.convertfrompointliststringtostring(receiveddata)
            #print("respdata", respdata)
            #print(receiveddata)
            #respdata += str(len(receiveddata))
            #for i in receiveddata:
            #    respdata = respdata + ">>>" + bytes.decode(i)

                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, respdata)
        else:
            peerconn.senddata(ERROR, 'Naive init not successfully: %s'
                                       % peerid)
        #peerconn.senddata(REPLY, filedata)

    #--------------------------------------------------------------------------
    def __handle_uploaddata_1(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADDATA message type. The message data should be in
        the format of a string of content.

        """
        #self.uploadfinish = False 
        self.__debug("self.evictionon: %s" % self.evictionon)
        #upload time
        self.uploadstarttime = time.time()
        # if  self.evictionon:
        #     time.sleep(0.2)
        #     self.__debug("Eviction sleep.")
        #     self.__handle_uploaddata_1(peerconn, data)
        while self.evictionon is True:
            time.sleep(1)
            self.__debug("Eviction sleep for uploading data.")
       
        dataid = data
        self.__debug("Upload data %s time: %s." % (dataid, datetime.now()))
        #self.__debug("dataid: " + dataid)
        #flag = self.btringoram.uploaddata(dataid, datacontent)

        # net = open(self.rxpath, "r")
        # self.uploadstartrx = int(net.read().split("\n")[0])
        # net.close()
        # net = open(self.txpath, "r")
        # self.uploadstarttx = int(net.read().split("\n")[0])
        # net.close()

        circuitinfo = {}
        circuitdataforupload = {}
        data = self.btitpiroram.uploaddata(dataid)
        #print("uploaddata", data)
        transactionid = str(time.time())
        #print("transactionid", transactionid)
        self.transactions[transactionid] = "upload " + dataid
        #print("transactions", self.transactions)

        if data["pushstash"] is not None:
            stashpeerid = data["stashpeer"] #store in tracker
            tmp = ">>>".join(data["pushstash"]) #send to stashpeer
            #stashpeerdata = self.btitpiroram.convertfromstringtopointlist(tmp) #store in stashpeer
            host,port = self.btitpiroram.peermap[self.btitpiroram.stashpeer].split(":")
            print("INITSTASH", host, port, tmp)
            stashresp = self.connectandsend(host, port, INITSTASH, tmp)
            #print("INITSTASH", stashresp)

        
        uploadcircuitpeers = ">>>".join(data["uploadpeerinfo"])
        respdata = transactionid + "<<<" + uploadcircuitpeers
        peerconn.senddata(REPLY, respdata)
        #self.__debug('Uploading data is successfully')

        host,port = self.btitpiroram.peermap[self.btitpiroram.stashpeer].split(":")
        stashpeerresp = self.connectandsend(host, port, UPLOADSTASHCIRCUITINFO, self.myid + "<<<" + respdata)
        #print("self.myid", self.myid)

        circuitinfo = data["circuitinfo"] #send to circuit peers
        for i in circuitinfo:
            circuitpeerid = i
            host,port = circuitpeerid.split(":")
            respdata = transactionid + "<<<" + self.btitpiroram.peermap[self.btitpiroram.stashpeer] + "<<<" + circuitinfo[i]
            stashpeerresp = self.connectandsend(host, port, UPLOADCIRCUITSTASHINFO, respdata)

        if data["eviction"] is not None:
            #Bug: should use lock
            #if self.uploadfinish is False:
            #    time.sleep(1)
            #self.uploadfinish = True
            self.evictionon = True
            self.evictionpath = data["eviction"]
            self.evictionfinishnum = len(data["eviction"]) + 2
                
            

    #--------------------------------------------------------------------------
    def __handle_uploadstashfinish(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADSTASHFINISH message type. The message data should be in
        the format of a string of content.

        """

        #self.__debug("message: " + msg)
        if data != "":
            transactionid = data
            print("self.transactions", self.transactions)
            del self.transactions[transactionid]

        # dataid = "data0"
        # onepoint = self.btitpiroram.usedcurve.G * int(dataid.split("data")[1])
        # print("dataid", dataid, onepoint + self.btitpiroram.secretmap[dataid])

        if len(data) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'UPLOADSTASHFINISH is successful')
            self.__debug('UPLOADSTASHFINISH is successful')
        else:
            peerconn.senddata(ERROR, 'UPLOADSTASHFINISH is not successful.')
            self.__debug('UPLOADSTASHFINISH is not successful')

        print("Upload finished")
        print("upload time takes ", time.time()-self.uploadstarttime)

        if self.evictionpath != "":
            print("eviction:", self.evictionpath)
            self.eviction(self.evictionpath)


    #--------------------------------------------------------------------------
    def __handle_readdata_1(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the READDATA1 message type. The message data should be in
        the format of a string of content.

        """
        #To do: store data in DB or filesystem; paralell communication with peers, reuse the connection for earlyshuflle and eviction
        initiator, dataid = msg.split("<<<")
        self.__debug("self.evictionon: %s" % self.evictionon)
        # if  self.evictionon:
        #     time.sleep(0.5)
        #     self.__debug("Eviction sleep.")
        #     self.__handle_readdata_1(peerconn, msg)
        while self.evictionon is True:
            time.sleep(0.01)
            self.__debug("Eviction sleep.")
        # else:           

        # net = open(self.rxpath, "r")
        # self.fetchstartrx = int(net.read().split("\n")[0])
        # net.close()
        # net = open(self.txpath, "r")
        # self.fetchstarttx = int(net.read().split("\n")[0])
        # net.close()


        #dataid = data
        self.__debug("Fetch data %s time: %s." % (dataid, datetime.now()))
        #self.__debug("dataid: " + dataid)
        #flag = self.btringoram.uploaddata(dataid, datacontent)

        data = self.btitpiroram.fetch(dataid)
        #print("fetch: ", data)
        
        pathpeerinfo = data["pathpeerinfo"]
        circuitinfo = data["circuitinfo"]
        circuitpeers = list(circuitinfo.keys())
        transactionid = str(time.time())
        #print("transactionid", transactionid)
        #self.initiator[transactionid] = initiator
        self.transactions[transactionid] = "fetch " + dataid
        self.fetchfinishnum[transactionid] = 2
        print("transactions", self.transactions)
        fetchcircuitpeers = ">>>".join(circuitpeers)
        respdata = transactionid + "<<<" + fetchcircuitpeers
        peerconn.senddata(REPLY, respdata)

        respdata = transactionid + "<<<" + self.myid + "<<<" + str(len(circuitpeers))
        host,port = initiator.split(":")
        toinitinfo = self.connectandsend(host, port, FETCHTOINITINFO, respdata)


        #uploadcircuitpeers = ">>>".join(data["uploadpeerinfo"])
        tostashinfo = transactionid + "<<<" + self.myid + "<<<" + str(len(circuitpeers))
        host,port = self.btitpiroram.peermap[self.btitpiroram.stashpeer].split(":")
        tostashpeerresp = self.connectandsend(host, port, FETCHTOSTASHINFO, tostashinfo)

        totalpathdata = len(pathpeerinfo) + 1
        for i in circuitpeers:
            nummap = "|".join(circuitinfo[i][2])
            circuitstr = circuitinfo[i][0] + ">>>" + circuitinfo[i][1] + ">>>" + nummap
            fetchcircuitdata = transactionid + "<<<" + initiator + "<<<" + self.btitpiroram.peermap[self.btitpiroram.stashpeer] + "<<<" + str(totalpathdata) + "<<<" + circuitstr
            host, port = i.split(":")
            stashpeerresp = self.connectandsend(host, port, FETCHCIRCUITPEERINFO, fetchcircuitdata)

        print("data[eviction]", data["eviction"])
        if data["eviction"] is not None:
            #Bug: should use lock
            #if self.uploadfinish is False:
            #    time.sleep(1)
            #self.uploadfinish = True
            print("eviction", data["eviction"])
            self.evictionon = True
            self.evictionpath = data["eviction"]
            self.evictionfinishnum = len(data["eviction"]) + 2

        for i in range(len(pathpeerinfo)):
            fetchpathpeerdata = transactionid + "<<<" + str(i) + "<<<" + fetchcircuitpeers
            host, port = pathpeerinfo[i].split(":")
            stashpeerresp = self.connectandsend(host, port, FETCHPATHPEERINFO, fetchpathpeerdata)

        fetchpathpeerdata = transactionid + "<<<" + "stash" + "<<<" + fetchcircuitpeers
        host, port = self.btitpiroram.peermap[self.btitpiroram.stashpeer].split(":")
        stashpeerresp = self.connectandsend(host, port, FETCHPATHPEERINFO, fetchpathpeerdata)

        print("positionmap", self.btitpiroram.positionmap)
        print("stashmap", self.btitpiroram.stashmap)

        # if data["eviction"] is not None:
        #     print("eviction:", data["eviction"])
        #     self.eviction(data["eviction"])




    #--------------------------------------------------------------------------
    def __handle_fetchstashfinish(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the FETCHSTASHFINISH message type. The message data should be in
        the format of a string of content.

        """

        #self.__debug("message: " + msg)
        if data != "":
            transactionid = data
            print("self.transactions", self.transactions)
            self.fetchfinishnum[transactionid] -= 1
            if self.fetchfinishnum[transactionid] == 0:
                print("fetch --> eviction:", self.evictionpath)
                #fetch finished
                if self.evictionpath != "":
                    print("fetch --> eviction:", self.evictionpath)
                    self.eviction(self.evictionpath)
                del self.fetchfinishnum[transactionid]
                del self.transactions[transactionid]


                # net = open(self.rxpath, "r")
                # print("fetch rx: ", (int(net.read().split("\n")[0]) - self.fetchstartrx) / 1024)
                # net.close()
                # net = open(self.txpath, "r")
                # print("fetch tx: ", (int(net.read().split("\n")[0]) - self.fetchstarttx) / 1024)
                # net.close()
                # uploadN = 8
                # for i in range(uploadN):
                #     dataid = "data"+str(i)
                #     onepoint = self.btitpiroram.usedcurve.G * int(dataid.split("data")[1])
                #     print("dataid", dataid, onepoint, onepoint + self.btitpiroram.secretmap[dataid])

        if len(data) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHSTASHFINISH is successful')
            self.__debug('FETCHSTASHFINISH is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHSTASHFINISH is not successful.')
            self.__debug('FETCHSTASHFINISH is not successful')



    #--------------------------------------------------------------------------
    def __handle_fetchinitiatorfinish(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the FETCHINITIATORFINISH message type. The message data should be in
        the format of a string of content.

        """

        #self.__debug("message: " + msg)
        if data != "":
            transactionid = data
            print("self.transactions", self.transactions)
            self.fetchfinishnum[transactionid] -= 1
            if self.fetchfinishnum[transactionid] == 0:
                #fetch finished
                print("fetch --> eviction:", self.evictionpath)
                if self.evictionpath != "":
                    print("fetch --> eviction:", self.evictionpath)
                    self.eviction(self.evictionpath)
                del self.fetchfinishnum[transactionid]
                del self.transactions[transactionid]


                # net = open(self.rxpath, "r")
                # print("fetch rx: ", (int(net.read().split("\n")[0]) - self.fetchstartrx) / 1024)
                # net.close()
                # net = open(self.txpath, "r")
                # print("fetch tx: ", (int(net.read().split("\n")[0]) - self.fetchstarttx) / 1024)
                # net.close()
                # uploadN = 8
                # for i in range(uploadN):
                #     dataid = "data"+str(i)
                #     onepoint = self.btitpiroram.usedcurve.G * int(dataid.split("data")[1])
                #     print("dataid", dataid, onepoint, onepoint + self.btitpiroram.secretmap[dataid])
        # dataid = "data0"
        # onepoint = self.btitpiroram.usedcurve.G * int(dataid.split("data")[1])
        # print("dataid", dataid, onepoint + self.btitpiroram.secretmap[dataid])

        if len(data) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHINITIATORFINISH is successful')
            self.__debug('FETCHINITIATORFINISH is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHINITIATORFINISH is not successful.')
            self.__debug('FETCHINITIATORFINISH is not successful')

        # if self.evictionpath != "":
        #     print("eviction:", self.evictionpath)
        #     self.eviction(self.evictionpath)

    #--------------------------------------------------------------------------
    def __handle_evictionstashfinish(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the EVICTIONSTASHFINISH message type. The message data should be in
        the format of a string of content.

        """

        #self.__debug("message: " + msg)
        if data != "":
            transactionid = data
            print("self.transactions", self.transactions)
            self.evictionfinishnum -= 1
            if self.evictionfinishnum == 0:
                #eviction finished
                print("Eviction finish.", self.evictionpath)
                print("eviction time takes ", time.time()-self.evictionstarttime)
                self.evictionpath = ""
                self.evictionon = False
                del self.transactions[transactionid]



                # net = open(self.rxpath, "r")
                # print("eviction rx: ", (int(net.read().split("\n")[0]) - self.evictionstartrx) / 1024)
                # net.close()
                # net = open(self.txpath, "r")
                # print("eviction tx: ", (int(net.read().split("\n")[0]) - self.evictionstarttx) / 1024)
                # net.close()
        # for i in range(3):
        #     dataid = "data" + str(i)
        #     onepoint = self.btitpiroram.usedcurve.G * int(dataid.split("data")[1])
        #     print("dataid", dataid, onepoint + self.btitpiroram.secretmap[dataid])
        print("positionmap", self.btitpiroram.positionmap)
        print("stashmap", self.btitpiroram.stashmap)
        self.__debug("peermap %s" % self.btitpiroram.peermap)
        self.__debug("peerdata %s" % self.btitpiroram.peerdata)
        #self.evictionon = True

        if len(data) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'EVICTIONSTASHFINISH is successful')
            self.__debug('EVICTIONSTASHFINISH is successful')
        else:
            peerconn.senddata(ERROR, 'EVICTIONSTASHFINISH is not successful.')
            self.__debug('EVICTIONSTASHFINISH is not successful')
        

    #--------------------------------------------------------------------------
    def __handle_evictionpathpeerfinish(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the EVICTIONPATHPEERFINISH message type. The message data should be in
        the format of a string of content.

        """

        #self.__debug("message: " + msg)
        if data != "":
            transactionid = data
            print("self.transactions", self.transactions)
            self.evictionfinishnum -= 1
            if self.evictionfinishnum == 0:
                #eviction finished
                print("Eviction finish.", self.evictionpath)
                print("Time takes", time.time()-self.evictionstarttime)
                self.evictionpath = ""
                self.evictionon = False
                del self.transactions[transactionid]

                # net = open(self.rxpath, "r")
                # print("eviction rx: ", (int(net.read().split("\n")[0]) - self.evictionstartrx) / 1024)
                # net.close()
                # net = open(self.txpath, "r")
                # print("eviction tx: ", (int(net.read().split("\n")[0]) - self.evictionstarttx) / 1024)
                # net.close()

        # for i in range(3):
        #     dataid = "data" + str(i)
        #     onepoint = self.btitpiroram.usedcurve.G * int(dataid.split("data")[1])
        #     print("dataid", dataid, onepoint + self.btitpiroram.secretmap[dataid])
        # print("positionmap", self.btitpiroram.positionmap)
        # print("stashmap", self.btitpiroram.stashmap)
        # print("peermap", self.btitpiroram.peermap)
        # print("peerdata", self.btitpiroram.peerdata)

        if len(data) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'EVICTIONPATHPEERFINISH is successful')
            self.__debug('EVICTIONPATHPEERFINISH is successful')
        else:
            peerconn.senddata(ERROR, 'EVICTIONPATHPEERFINISH is not successful.')
            self.__debug('EVICTIONPATHPEERFINISH is not successful')
        #eviction finished
        #self.evictionpath = ""

    #--------------------------------------------------------------------------
    def eviction ( self, datapathtag ):
    #--------------------------------------------------------------------------
        """ Handles the EVICTION1 message type. The message data should be in
        the format of a string of content.

        """
        #datapathtag = "00"
        #global stashpeerdata
        #global peertagdata
        #global uploadN

        # net = open(self.rxpath, "r")
        # self.evictionstartrx = int(net.read().split("\n")[0])
        # net.close()
        # net = open(self.txpath, "r")
        # self.evictionstarttx = int(net.read().split("\n")[0])
        # net.close()
        
        self.__debug("Eviction time: %s." % datetime.now())
        data = self.btitpiroram.eviction(datapathtag)
        #eviction time
        self.evictionstarttime = time.time()
        pathpeerinfo = data["pathpeerinfo"]
        circuitinfototal = data["circuitinfo"]
        circuitpeers = list(circuitinfototal.keys())

        transactionid = str(time.time())
        #print("transactionid", transactionid)
        #self.initiator[transactionid] = initiator
        self.transactions[transactionid] = "eviction " + datapathtag
        print("transactions", self.transactions)
        

        totalpathdata = len(pathpeerinfo) + 1
        for i in circuitinfototal:
            strj = ""
            for j in circuitinfototal[i]:
                strk = ""
                for k in circuitinfototal[i][j]:
                    #print("circuitinfototal[i][j][k]", circuitinfototal[i][j][k])
                    #strk = strk + circuitinfototal[i][j][k][0] + "--" + "|".join(circuitinfototal[i][j][k][1]) + "++"
                    strk = strk + k[0] + "--" + "|".join(k[1]) + "++"

                strk = strk[:-2]
                if j != "stashpeer":
                    pathpeerid = self.btitpiroram.peermap[j]
                else:
                    pathpeerid = "stash" + self.btitpiroram.peermap[self.btitpiroram.stashpeer]
                strj = strj + pathpeerid + "==" + strk + ">>>"
            circuitpeerdata = strj[:-3]

            evictioncircuitdata = transactionid + "<<<" + str(totalpathdata) + "<<<" + circuitpeerdata
            host, port = i.split(":")
            stashpeerresp = self.connectandsend(host, port, EVICTIONCIRCUITPEERINFO, evictioncircuitdata)

        evictioncircuitpeers = ">>>".join(circuitpeers)
        for i in range(len(pathpeerinfo)):
            evictionpathpeerdata = transactionid + "<<<" + str(i) + "<<<" + self.myid + "<<<" + evictioncircuitpeers
            host, port = pathpeerinfo[i].split(":")
            peerresp = self.connectandsend(host, port, EVICTIONPATHPEERINFO, evictionpathpeerdata)

        evictionpathpeerdata = transactionid + "<<<" + "stash" + "<<<" + self.myid + "<<<" + evictioncircuitpeers
        host, port = self.btitpiroram.peermap[self.btitpiroram.stashpeer].split(":")
        peerresp = self.connectandsend(host, port, EVICTIONPATHPEERINFO, evictionpathpeerdata)

        # for i in range(uploadN):
        #     point = btitpiroram.usedcurve.G * i
        #     point = point + btitpiroram.secretmap["data"+str(i)]
        #     print("data"+str(i))
        #     print(point)
        print("positionmap", self.btitpiroram.positionmap)
        print("stashmap", self.btitpiroram.stashmap)
        self.__debug("peermap " + str(self.btitpiroram.peermap))
        self.__debug("peerdata " + str(self.btitpiroram.peerdata))



    #--------------------------------------------------------------------------
    def __handle_naiveinit(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the NAIVEINIT message type. The message data should be in
        the format of a string of peerid.

        """
        peerid = data
        self.__debug("peermap: " + str(self.btringoram.peermap))
        receiveddata = self.btringoram.join(peerid)
        #for i in self.bitstrings:
        #    if self.peermap[i] is None:
        #            self.peermap[i] = peerid
        #            self.peermapreverse[peerid] = i
        #            break
        #if i is self.bitstrings[-1]:
        #    return False
        self.__debug("peermap " + str(self.btringoram.peermap))

        # dummy = "dummy.txt"
        # real = "file.txt"
        # print str(self.peermapreverse.keys()) + " " + data
        if peerid in self.btringoram.peermapreverse:
        #     #read dummy data
        #     fd = file(dummy, 'r')
        #     dummydata = ''
        #     while True:
        #             filedata = fd.read(2048)
        #             if not len(filedata):
        #                     break
        #             dummydata += filedata
        #     #print dummydata
        #     fd.close()

        #     #read real data
        #     fd = file(real, 'r')
        #     realdata = ''
        #     while True:
        #             filedata = fd.read(2048)
        #             if not len(filedata):
        #                     break
        #             realdata += filedata
        #     #print realdata
        #     fd.close()
            respdata = ""
            #print(receiveddata)
            respdata += str(len(receiveddata))
            for i in receiveddata:
                respdata = respdata + ">>>" + bytes.decode(i)

                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, respdata)
        else:
            peerconn.senddata(ERROR, 'Naive init not successfully: %s'
                                       % peerid)
        #peerconn.senddata(REPLY, filedata)

    #--------------------------------------------------------------------------
    def __handle_uploaddata(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADDATA message type. The message data should be in
        the format of a string of content.

        """
        
        
        self.__debug("self.earlyshuffleon: %s self.evictionon: %s" % (self.earlyshuffleon, self.evictionon))
        if self.earlyshuffleon or self.evictionon:
            time.sleep(1)
            self.__debug("Eviction sleep.")
            self.__handle_uploaddata(peerconn, data)
        else:           
            dataid, datacontent = data.split(">>>")
            self.__debug("Upload data %s time: %s." % (dataid, datetime.now()))
            self.__debug("dataid: " + dataid)
            #flag = self.btringoram.uploaddata(dataid, datacontent)
            tag = {}
            tag = self.btringoram.uploaddata(dataid, datacontent)
            self.__debug(self.btringoram.stashmap)
            #self.btringoram.updatestashrealdata(dataid, datacontent)
            self.__debug(self.btringoram.stashrealdata.keys())

            if  tag is not None:
                    #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
                peerconn.senddata(REPLY, 'Uploading data is successfully.')
                self.__debug('Uploading data is successfully')
            else:
                peerconn.senddata(ERROR, 'Uploading data is not successfully.')
                self.__debug('Uploading data is not successfully')

            if  (tag is not None) and (tag["eviction"] is not None):
                self.evictionon = True
                evictionpeer = {}
                #evictionpeer["R"] = peertagdata["R"]
                self.__debug("eviction %s" % tag["eviction"])
                host,port = self.btringoram.peermap["R"].split(":")
                resp = self.connectandsend(host, port, EVICTION, "eviction")
                self.__debug("eviction resp: %s" % resp)
                tmpdata = resp[0][1]
                evictionpeer["R"] = tmpdata.split(">>>")
                pathtag = tag["eviction"]
                for i in range(len(pathtag)):
                    peertag = pathtag[:i+1]
                    #Incomplete tree check
                    if self.btringoram.peermap[peertag] is not None:
                        #evictionpeer[pathtag[:i+1]] = peertagdata[pathtag[:i+1]]
                        host,port = self.btringoram.peermap[peertag].split(":")
                        resp = self.connectandsend(host, port, EVICTION, "eviction")
                        self.__debug("eviction resp: %s" % resp)
                        tmpdata = resp[0][1]
                        evictionpeer[peertag] = tmpdata.split(">>>")
                        #self.__debug("eviction peertag: %s" % peertag)
                #print "evictionpeer"
                #print evictionpeer
                evictiondata = self.btringoram.eviction(pathtag, evictionpeer)
                #self.__debug("peertagdata")
                self.__debug("evictiondata keys: %s" % evictiondata.keys())
                for i in evictiondata:
                    #peertagdata[i] = evictiondata[i]
                    host,port = self.btringoram.peermap[i].split(":")
                    finishdata = ""
                    for j in evictiondata[i]:
                        if j is evictiondata[i][0]:
                            #self.__debug("evictiondata: %s" % evictiondata)
                            finishdata = bytes.decode(j)
                        else:
                            finishdata = finishdata + ">>>" + bytes.decode(j)
                    evictionresp = self.connectandsend(host, port, EVICTIONFINISH, finishdata)
                    self.__debug("Evictionresp resp: %s" % evictionresp)
                    self.__debug("Eviction time: %s." % str(datetime.now()))
                self.__debug("positionmap %s. \n dataid %s. \n number %s" % (self.btringoram.positionmap, self.btringoram.positionmap.keys(), len(self.btringoram.positionmap.keys())))
                self.__debug("stashmap %s. \n dataid %s. \n number %s" % (self.btringoram.stashmap, self.btringoram.stashmap.keys(), len(self.btringoram.stashmap.keys())))
                #self.__debug("positionmap %s." % self.btringoram.positionmap)
                self.__debug("Eviction finish time: %s." % str(datetime.now()))
                self.evictionon = False

    #--------------------------------------------------------------------------
    def __handle_readdata(self, peerconn, dataid):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADDATA message type. The message data should be in
        the format of a string of content.

        """
        #To do: store data in DB or filesystem; paralell communication with peers, reuse the connection for earlyshuflle and eviction
        self.__debug("Read data %s time: %s." % (dataid, datetime.now()))
        if self.earlyshuffleon or self.evictionon:
            time.sleep(1)
            self.__debug("Eviction sleep.")
            self.__handle_readdata(peerconn, dataid)
        else:
            respdata = ""
            self.__debug("readdata dataid: " + dataid)
            data = self.btringoram.readdata(dataid)

            #self.__debug(data)
            peerlist = dict(data)
            del peerlist["eviction"]
            del peerlist["stash"]
            del peerlist["earlyshuffle"]
            del peerlist["realdatapeer"]
            #self.__debug(peerlist)
            #eviction: peertag, earlyshuffle: [level, ...], stash: dataid, realdatapeer: peerid, peerid: number
            for i in peerlist:
                host,port = i.split(':')
                number = peerlist[i]
                self.__debug("Read data from %s" % i)
                resp = self.connectandsend(host, port, LOCATEDATA, str(number))
                print("readdata: tmpdata ")
                #print(resp)
                #tmpdata = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                tmpdata = resp[0][1].split(">>>")[0]
                #= resp[0][1]
                #self.__debug(tmpdata)
                #self.__debug(data)
                #locateresp = self.connectandsend(host, port, LOCATEDATAFINISH, "LOCATEDATA finish.")

                if data["realdatapeer"] is not None:
                    if i is data["realdatapeer"]:
                        respdata = tmpdata
            #self.__debug(respdata)
            if  data["stash"] is not None:
                self.__debug("Read from stash.")
                respdata = data["stash"]
                #self.btringoram.stashrealdata[data["stash"]]
                #print(respdata)
                try:
                    respdata = self.btringoram.btaes.decrypt(respdata)
                except Exception as e:
                    print("Couldn't do it: %s" % e)
                #print("")
            #respdata = "hahahah"
            #peerconn.senddata(REPLY, respdata)    
            if  data["realdatapeer"] is not None:
                self.__debug("Read real data from peer: %s." % data["realdatapeer"])
                #tmppeerid = data["realdatapeer"]
                #tmppeertag = btringoram.peermapreverse[tmppeerid]
                #tmprealdata = peertagdata[tmppeertag][data[tmppeerid]]
                #Update stashrealdata and positionmap
                #print tmprealdata
                #print peertagdata
                self.btringoram.stashrealdata[dataid] = respdata
                respdata = self.btringoram.btaes.decrypt(respdata.encode())
            #self.__debug(respdata)
            if  len(respdata) > 0:
                #print("REPLY")
                #print(respdata)
                peerconn.senddata(REPLY, respdata.decode())
            else:
                peerconn.senddata(ERROR, 'Read data is not successful.')

            if  len(data["earlyshuffle"]) > 0:
                self.earlyshuffleon = True
                shuffletags = [] #shuffletags is a list, for loop directly lists its content not index
                #shuffledata = {}
                shuffletags = data["earlyshuffle"]
                self.__debug("earlyshuffle")
                #print shuffletags
                for j in shuffletags:
                    host,port = self.btringoram.peermap[j].split(":")
                    resp = self.connectandsend(host, port, EARLYSHUFFLE, "earlyshuffle")
                    tmpdata = resp[0][1]
                    tmpdata = tmpdata.split(">>>")
                    shuffledata = self.btringoram.earlyshuffle(j, tmpdata)
                    #self.__debug("earlyshuffle %s" % tmpdata)
                    finishdata = ""
                    for k in shuffledata:
                        if k is shuffledata[0]:
                            finishdata += bytes.decode(k)
                        else:
                            finishdata = finishdata + ">>>" + bytes.decode(k)
                    shuffleresp = self.connectandsend(host, port, EARLYSHUFFLEFINISH, finishdata)
                self.earlyshuffleon = False

            if data["eviction"] is not None:
                self.evictionon = True
                evictionpeer = {}
                #evictionpeer["R"] = peertagdata["R"]
                self.__debug("eviction %s" % data["eviction"])
                host,port = self.btringoram.peermap["R"].split(":")
                resp = self.connectandsend(host, port, EVICTION, "eviction")
                self.__debug("eviction resp: %s" % resp)
                tmpdata = resp[0][1]
                evictionpeer["R"] = tmpdata.split(">>>")
                pathtag = data["eviction"]
                for i in range(len(pathtag)):
                    peertag = pathtag[:i+1]
                    #Incomplete tree check
                    if self.btringoram.peermap[peertag] is not None:
                        #evictionpeer[pathtag[:i+1]] = peertagdata[pathtag[:i+1]]
                        host,port = self.btringoram.peermap[peertag].split(":")
                        resp = self.connectandsend(host, port, EVICTION, "eviction")
                        self.__debug("eviction resp: %s" % resp)
                        tmpdata = resp[0][1]
                        evictionpeer[peertag] = tmpdata.split(">>>")
                        #self.__debug("eviction peertag: %s" % peertag)
                #print "evictionpeer"
                #print evictionpeer
                evictiondata = self.btringoram.eviction(pathtag, evictionpeer)
                #self.__debug("peertagdata")
                self.__debug("evictiondata keys: %s" % evictiondata.keys())
                for i in evictiondata:
                    #peertagdata[i] = evictiondata[i]
                    host,port = self.btringoram.peermap[i].split(":")
                    finishdata = ""
                    for j in evictiondata[i]:
                        if j is evictiondata[i][0]:
                            #self.__debug("evictiondata: %s" % evictiondata)
                            finishdata = bytes.decode(j)
                        else:
                            finishdata = finishdata + ">>>" + bytes.decode(j)
                    evictionresp = self.connectandsend(host, port, EVICTIONFINISH, finishdata)
                    self.__debug("evictionresp resp: %s" % evictionresp)
                    self.__debug("Eviction time: %s." % str(datetime.now()))
                self.__debug("positionmap %s. \n dataid %s. \n number %s" % (self.btringoram.positionmap, self.btringoram.positionmap.keys(), len(self.btringoram.positionmap.keys())))
                self.__debug("stashmap %s. \n dataid %s. \n number %s" % (self.btringoram.stashmap, self.btringoram.stashmap.keys(), len(self.btringoram.stashmap.keys())))
                #self.__debug("positionmap %s." % self.btringoram.positionmap)
                self.__debug("Eviction finish time: %s." % str(datetime.now()))
                self.evictionon = False

    #--------------------------------------------------------------------------
    def __handle_qresponse(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the QRESPONSE message type. The message data should be
        in the format of a string, "file-name  peer-id", where file-name is
        the file that was queried about and peer-id is the name of the peer
        that has a copy of the file.

        """
        try:
            fname, fpeerid = data.split()
            if fname in self.files:
                self.__debug('Can\'t add duplicate file %s %s' % 
                              (fname, fpeerid))
            else:
                self.files[fname] = fpeerid
        except:
            #if self.debug:
                traceback.print_exc()


    #--------------------------------------------------------------------------
    def __handle_fileget(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the FILEGET message type. The message data should be in
        the format of a string, "file-name", where file-name is the name
        of the file to be fetched.

        """
        fname = data
        if fname not in self.files:
            self.__debug('File not found %s' % fname)
            peerconn.senddata(ERROR, 'File not found')
            return
        try:
            fd = file(fname, 'r')
            filedata = ''
            while True:
                data = fd.read(2048)
                if not len(data):
                    break;
                filedata += data
                #print filedata
            fd.close()
        except:
            self.__debug('Error reading file %s' % fname)
            peerconn.senddata(ERROR, 'Error reading file')
            return
        
        peerconn.senddata(REPLY, filedata)



    #--------------------------------------------------------------------------
    def __handle_quit(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the QUIT message type. The message data should be in the
        format of a string, "peer-id", where peer-id is the canonical
        name of the peer that wishes to be unregistered from this
        peer's directory.

        """
        self.peerlock.acquire()
        try:
            peerid = data.lstrip().rstrip()
            if peerid in self.getpeerids():
                msg = 'Quit: peer removed: %s' % peerid 
                self.__debug(msg)
                peerconn.senddata(REPLY, msg)
                self.removepeer(peerid)
            else:
                msg = 'Quit: peer not found: %s' % peerid 
                self.__debug(msg)
                peerconn.senddata(ERROR, msg)
        finally:
            self.peerlock.release()



    # precondition: may be a good idea to hold the lock before going
    #               into this function
    #--------------------------------------------------------------------------
    def buildpeers(self, host, port, hops=1):
    #--------------------------------------------------------------------------
        """ buildpeers(host, port, hops) 

        Attempt to build the local peer list up to the limit stored by
        self.maxpeers, using a simple depth-first search given an
        initial host and port as starting point. The depth of the
        search is limited by the hops parameter.

        """
        if self.maxpeersreached() or not hops:
            return

        peerid = None

        self.__debug("Building peers from (%s,%s)" % (host,port))

        try:
            _, peerid = self.connectandsend(host, port, PEERNAME, '')[0]

            self.__debug("contacted " + peerid)
            resp = self.connectandsend(host, port, INSERTPEER, 
                                        '%s %s %d' % (self.myid, 
                                                      self.serverhost, 
                                                      self.serverport))[0]
            self.__debug(str(resp))
            if (resp[0] != REPLY) or (peerid in self.getpeerids()):
                return

            self.addpeer(peerid, host, port)

            # do recursive depth first search to add more peers
            resp = self.connectandsend(host, port, LISTPEERS, '',
                                        pid=peerid)
            if len(resp) > 1:
                resp.reverse()
                resp.pop()    # get rid of header count reply
                while len(resp):
                    nextpid,host,port = resp.pop()[1].split()
                    if nextpid != self.myid:
                        self.buildpeers(host, port, hops - 1)
        except:
            if self.debug:
                traceback.print_exc()
            self.removepeer(peerid)



    #--------------------------------------------------------------------------
    def addlocalfile(self, filename):
    #--------------------------------------------------------------------------
        """ Registers a locally-stored file with the peer. """
        self.files[filename] = None
        self.__debug("Added local file %s" % filename)
