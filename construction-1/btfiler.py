#!/usr/bin/python

from btpeer import *

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
UPLOADSTASHSEND = "UPSS"
UPLOADSTASHCIRCUITINFO = "UPSC"
UPLOADCIRCUITSTASHINFO = "UCSI"
UPLOADSTASHFINISH = "UPSF"

FETCHPATHPEERINFO = "FEPI"
FETCHCIRCUITPEERDATA = "FECP"
FETCHCIRCUITPEERINFO = "FECI"
FETCHTOINITPEER = "FEIP"
FETCHTOSTASHPEER = "FESP"
FETCHTOSTASHINFO = "FESI"
FETCHSTASHFINISH = "FESF"
FETCHTOINITINFO = "FEII"
FETCHINITIATORFINISH = "FEIF"

EVICTIONPATHPEERINFO = "EVPI"
EVICTIONCIRCUITPEERDATA = "EVCP"
EVICTIONCIRCUITPEERINFO = "EVCI"
EVICTIONTOPATHPEER = "EVPP"
EVICTIONSTASHFINISH = "EVSF"
EVICTIONTOSTASHPEER = "EVSP"
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

        self.debug = 0
        
        self.files = {}  # available files: name --> peerid mapping

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
                    LOCATEDATA: self.__handle_locatedata,
                    LOCATEDATAFINISH: self.__handle_locatedatafinish,
                    EARLYSHUFFLE: self.__handle_earlyshuffle,
                    EVICTION: self.__handle_eviction,
                    EARLYSHUFFLEFINISH: self.__handle_earlyshufflefinish,
                    EVICTIONFINISH: self.__handle_evictionfinish,
                    INITSTASH: self.__handle_initstash,
                    UPLOADCIRCUITSEND: self.__handle_uploadcircuitsend,
                    UPLOADSTASHSEND: self.__handle_uploadstashsend,
                    UPLOADSTASHCIRCUITINFO: self.__handle_uploadstashcircuitinfo,
                    UPLOADCIRCUITSTASHINFO: self.__handle_uploadcircuitstashinfo,
                    FETCHPATHPEERINFO: self.__handle_fetchpathpeerinfo,
                    FETCHCIRCUITPEERDATA: self.__handle_fetchcircuitpeerdata,
                    FETCHCIRCUITPEERINFO: self.__handle_fetchcircuitpeerinfo,
                    FETCHTOINITPEER: self.__handle_fetchtoinitpeer,
                    FETCHTOSTASHPEER: self.__handle_fetchtostashpeer,
                    FETCHTOSTASHINFO: self.__handle_fetchtostashinfo,
                    FETCHTOINITINFO: self.__handle_fetchtoinitinfo,
                    EVICTIONPATHPEERINFO: self.__handle_evictionpathpeerinfo,
                    EVICTIONCIRCUITPEERDATA: self.__handle_evictioncircuitpeerdata,
                    EVICTIONCIRCUITPEERINFO: self.__handle_evictioncircuitpeerinfo,
                    EVICTIONTOPATHPEER: self.__handle_evictiontopathpeer,
                    EVICTIONTOSTASHPEER: self.__handle_evictiontostashpeer
                   }
        for mt in handlers:
            self.addhandler(mt, handlers[mt])

    # end FilerPeer constructor







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
    def __debug( self, msg ):
    #--------------------------------------------------------------------------
        if self.debug:
            print("[%s] %s" % ( str(threading.currentThread().getName()), msg ))
    # #--------------------------------------------------------------------------
    # def __debug(self, msg):
    # #--------------------------------------------------------------------------
    #  """ Prints a messsage to the screen with the name of the current thread """
    #     if self.debug:
    #         print("[%s] %s" % ( str(threading.currentThread().getName()), msg ))
    #     #if self.debug:
    #     #    btdebug(msg)


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
    def __handle_naiveinit(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the NAIVEINIT message type. The message data should be in
        the format of a string of peerid.

        """
        dummy = "dummy.txt"
        real = "file.txt"
        peerid = data
        if peerid in self.peermapreverse:
                #read dummy data
                fd = file(dummy, 'r')
                dummydata = ''
                while True:
                        filedata = fd.read(2048)
                        if not len(filedata):
                                break
                        dummydata += filedata
                #print dummydata
                fd.close()

                #read real data
                fd = file(real, 'r')
                realdata = ''
                while True:
                        filedata = fd.read(2048)
                        if not len(filedata):
                                break
                        realdata += filedata
                #print realdata
                fd.close()

                responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
                peerconn.senddata(REPLY, responsedata)
        else:
                peerconn.senddata(ERROR, 'Naive init not successfully: %s'
                                       % peerid)

        
        #peerconn.senddata(REPLY, filedata)

    #--------------------------------------------------------------------------
    def __handle_locatedata(self, peerconn, number):
    #--------------------------------------------------------------------------
        """ Handles the LOCATEDATA message type. The message data should be in
        the format of a string of content.

        """

        #self.__debug("number: " + number)
        resp = ""
        resp = self.bucketdata[int(number)]
        #self.__debug(resp)
        resp += ">>>"
        if len(self.bucketdata) > 0:
        #if 1 > 0:
            #print("data size:")
            #for i in self.bucketdata:
            #    print(len(i))
            #resp = ""
            #for i in range(1024):
            #    resp += "a"
            peerconn.senddata(REPLY, resp)
            self.__debug('Locating data is successful.')
        else:
            peerconn.senddata(ERROR, 'Locating data is not successful.')
            self.__debug('Locating data is not successful.')

    #--------------------------------------------------------------------------
    def __handle_locatedatafinish(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the LOCATEDATAFINISH message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        #self.bucketdata = data.split(">>>")
        #self.__debug(self.bucketdata)

        if len(msg) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'Locating data is successful')
            self.__debug('Locating data is successful')
        else:
            peerconn.senddata(ERROR, 'Locating data is not successful.')
            self.__debug('Locating data is not successful')

    #--------------------------------------------------------------------------
    def __handle_initstash(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the INITSTASH message type. The message data should be in
        the format of a string of content.

        """

        #print("message: " + data)
        self.stashpeerdata = self.btitpiroram.convertfromstringtopointlist(data) #store in stashpeer

        if len(self.stashpeerdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'Initstash is successful')
            self.__debug('Initstash is successful')
        else:
            peerconn.senddata(ERROR, 'Initstash is not successful.')
            self.__debug('Initstash is not successful')

    #--------------------------------------------------------------------------
    def __handle_uploadstashcircuitinfo(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADSTASHCIRCUITINFO message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + data)
        self.trackerid, transactionid, circuitpeers = str(data).split('<<<')
        self.uploadstashcircuitpeers[transactionid] = circuitpeers.split(">>>") #store in stashpeer

        if transactionid not in self.uploadstashshares:
            self.uploadstashshares[transactionid] = {}
            self.uploadstashsharesnum = len(self.uploadstashcircuitpeers[transactionid])

        if len(circuitpeers) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'UPLOADSTASHCIRCUITINFO is successful')
            self.__debug('UPLOADSTASHCIRCUITINFO is successful')
        else:
            peerconn.senddata(ERROR, 'UPLOADSTASHCIRCUITINFO is not successful.')
            self.__debug('UPLOADSTASHCIRCUITINFO is not successful')

    #--------------------------------------------------------------------------
    def __handle_uploadcircuitstashinfo(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADCIRCUITSTASHINFO message type. The message data should be in
        the format of a string of content.

        """
        transactionid, stashpeerid, pointsstring = data.split("<<<")
        #print("message: ", transactionid, stashpeerid)
        self.stashpeerid = stashpeerid
        self.uploadsecretpoints[transactionid] = self.btitpiroram.convertfromstringtopoint(pointsstring)

        if len(pointsstring) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'UPLOADCIRCUITSTASHINFO is successful')
            self.__debug('UPLOADCIRCUITSTASHINFO is successful')
        else:
            peerconn.senddata(ERROR, 'UPLOADCIRCUITSTASHINFO is not successful.')
            self.__debug('UPLOADCIRCUITSTASHINFO is not successful')


    #--------------------------------------------------------------------------
    def __handle_uploadcircuitsend(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADCIRCUITSEND message type. The message data should be in
        the format of a string of content.

        """
        transactionid, circuitreceiveddata = data.split("<<<")
        self.__debug("message: " + data)
        if len(circuitreceiveddata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'UPLOADCIRCUITSEND is successful')
            self.__debug('UPLOADCIRCUITSEND is successful')
        else:
            peerconn.senddata(ERROR, 'UPLOADCIRCUITSEND is not successful.')
            self.__debug('UPLOADCIRCUITSEND is not successful')

        #self.stashpeerdata = self.btitpiroram.convertfromstringtopointlist(data) #store in stashpeer
        self.uploaddatashares[transactionid] = self.btitpiroram.convertfromstringtopointlist(circuitreceiveddata) #circuit peers store data in arrays
            #print(len(circuitdataforupload[i]))
        while transactionid not in self.uploadsecretpoints:
            time.sleep(0.01)

        #if transactionid in self.uploadsecretpoints:
        for j in range(len(self.uploaddatashares[transactionid])):
            for k in range(len(self.uploaddatashares[transactionid][j])):
                self.uploaddatashares[transactionid][j][k] = self.uploaddatashares[transactionid][j][k] + self.uploadsecretpoints[transactionid]
        circuitdatatostashpeer = self.btitpiroram.convertfrompointlisttostring(self.uploaddatashares[transactionid])

        if self.stashpeerid == "":
            print("Stashpeerid is None.")
        else:
            host,port = self.stashpeerid.split(':')
            singlecircuitdata = transactionid + "<<<" + self.myid + "<<<" + circuitdatatostashpeer
            resp = self.connectandsend(host, port, UPLOADSTASHSEND, singlecircuitdata)
            #upload finished
            if resp is not None:
                del self.uploaddatashares[transactionid]
                del self.uploadsecretpoints[transactionid]

    #--------------------------------------------------------------------------
    def __handle_uploadstashsend(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADSTASHSEND message type. The message data should be in
        the format of a string of content.

        """
        transactionid, circuitpeerid, circuitdatatostashpeer = data.split("<<<")
        print("UPLOADSTASHSEND message: ", transactionid, circuitpeerid)
        if transactionid not in self.uploadstashshares:
            self.uploadstashshares[transactionid] = {}
        self.uploadstashshares[transactionid][circuitpeerid] = self.btitpiroram.convertfromstringtopointlist(circuitdatatostashpeer)
        #print("self.uploadstashshares", self.uploadstashshares)
        #print("self.uploadstashsharesnum", self.uploadstashsharesnum)

        if len(circuitdatatostashpeer) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'UPLOADSTASHSEND is successful')
            self.__debug('UPLOADSTASHSEND is successful')
        else:
            peerconn.senddata(ERROR, 'UPLOADSTASHSEND is not successful.')
            self.__debug('UPLOADSTASHSEND is not successful')

        if len(self.uploadstashshares[transactionid]) == self.uploadstashsharesnum:
            tmppoints = [] #stashpeer sums up all the points
            for i in range(1):
                for j in range(self.btitpiroram.pointsnum):
                    sum = self.btitpiroram.usedcurve.G * 0
                    for k in self.uploadstashshares[transactionid]:
                        sum = sum + self.uploadstashshares[transactionid][k][i][j]
                    tmppoints.append(sum)

            self.stashpeerdata.append(tmppoints) #stashpeer appends sum in stashpeerdata
            print("Upload finish.")
            print("Time takes:", time.time() - self.uploadstarttime)
            host,port = self.trackerid.split(':')
            #singlecircuitdata = transactionid + "<<<" + self.myid + "<<<" + circuitdatatostashpeer
            resp = self.connectandsend(host, port, UPLOADSTASHFINISH, transactionid)
            if resp is not None:
                del self.uploadstashshares[transactionid]



    #--------------------------------------------------------------------------
    def __handle_fetchpathpeerinfo(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the FETCHPATHPEERINFO message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + data)
        transactionid, dataseq, circuitpeers = str(data).split('<<<')
        self.fetchcircuitpeers[transactionid] = circuitpeers.split(">>>") 

        if len(circuitpeers) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHPATHPEERINFO is successful')
            self.__debug('FETCHPATHPEERINFO is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHPATHPEERINFO is not successful.')
            self.__debug('FETCHPATHPEERINFO is not successful')
        #print("self.fetchcircuitpeers[transactionid]", self.fetchcircuitpeers[transactionid])

        for i in self.fetchcircuitpeers[transactionid]:
            host,port = i.split(':')
            singlecircuitdata = ""
            if dataseq != "stash":
                singlecircuitdata = transactionid + "<<<" + dataseq + "<<<" + self.btitpiroram.convertfrompointlisttostring(self.bucketdata)
            else:
                singlecircuitdata = transactionid + "<<<" + dataseq + "<<<" + self.btitpiroram.convertfrompointlisttostring(self.stashpeerdata)
            #print("singlecircuitdata", singlecircuitdata)
            resp = self.connectandsend(host, port, FETCHCIRCUITPEERDATA, singlecircuitdata)

        del self.fetchcircuitpeers[transactionid]

    def initpointlist (self, length):
    #initiate point list
        data = []
        for i in range(length):
            tmplist = []
            for j in range(self.btitpiroram.pointsnum): #for one block
                tmplist.append(self.btitpiroram.usedcurve.G * 0)
            data.append(tmplist)
        return data
        
    #--------------------------------------------------------------------------
    def __handle_fetchcircuitpeerdata(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the FETCHCIRCUITPEERDATA message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + data)
        transactionid, dataseq, peerdata = str(data).split('<<<')
        print("error1")
        while transactionid not in self.fetchpathpeernum:
            time.sleep(0.01)
            print("__handle_fetchtostashpeer error2")
        if transactionid not in self.fetchcircuitdata:
            self.fetchcircuitdata[transactionid] = []
            for i in range(self.fetchpathpeernum[transactionid]):
                self.fetchcircuitdata[transactionid].append([])
        #print("self.fetchcircuitdata[transactionid]", self.fetchcircuitdata[transactionid])
        if dataseq != "stash":
            self.fetchcircuitdata[transactionid][int(dataseq)] = self.btitpiroram.convertfromstringtopointlist(peerdata)
        else:
            self.fetchcircuitdata[transactionid][-1] = self.btitpiroram.convertfromstringtopointlist(peerdata)

        #print("self.fetchcircuitdata[transactionid]", self.fetchcircuitdata[transactionid])

        if len(peerdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHCIRCUITPEERDATA is successful')
            self.__debug('FETCHCIRCUITPEERDATA is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHCIRCUITPEERDATA is not successful.')
            self.__debug('FETCHCIRCUITPEERDATA is not successful')

        emptyflag = False
        length = 0
        for i in self.fetchcircuitdata[transactionid]:
            if i == []:
                print("emptyflag", emptyflag)
                emptyflag = True
        if emptyflag == False:
            forstashpeerdatatotal = []#circuitpeers send to the stashpeer
            forinitiatordatatotal = []#circuitpeers send to the initiator
            #forinitiatordata = []
            pathtocircuitdata = []
            # x = btitpiroram.usedcurve.G * 0
            # y = btitpiroram.usedcurve.G * 0
            for i in self.fetchcircuitdata[transactionid]:
                length += len(i)
                pathtocircuitdata.extend(i)

            forinitiatordata = self.initpointlist(length)

            oldpoint = self.fetchcircuitinfo[transactionid][0]
            newpoint = self.fetchcircuitinfo[transactionid][1]
            #forinitiatordata[i] = []
            #forinitiatordata[i].extend(pathtocircuitdata[i])
            # for i1 in range(len(pathpeerinfo) + len(stashpeerdata)):
            #     for i2 in range(btitpiroram.pointsnum):
            forstashpeerdatatotal = [] 
            forinitiatordatatotal = []
            if len(pathtocircuitdata) != len(self.fetchcircuitinfo[transactionid][2]):
                print("error", len(pathtocircuitdata), len(self.fetchcircuitinfo[transactionid][2]))
                #print(len(circuitinfo[i][2]))
                #print("error")
            #print("self.fetchcircuitinfo[transactionid][2]", self.fetchcircuitinfo[transactionid][2])
            #print("forinitiatordata11111", forinitiatordata[i])
            for j in range(len(pathtocircuitdata)):
                num = int(self.fetchcircuitinfo[transactionid][2][j])
                for k in range(self.btitpiroram.pointsnum):
                    # print("before: pathtocircuitdata", pathtocircuitdata[i][j][k])
                    # print("before:", forinitiatordata[i][j][k])
                    forinitiatordata[j][k] = pathtocircuitdata[j][k] * num #Fixed bug: forinitiatordata must be initiated, cannot forinitiatordata[i] = pathtocircuitdata[i]
                    #time.sleep(0.1)
                    # print("after: pathtocircuitdata ", pathtocircuitdata[i][j][k])
                    # print("after:", forinitiatordata[i][j][k])
            for k1 in range(self.btitpiroram.pointsnum):
                pointsum = self.btitpiroram.usedcurve.G * 0
                for k2 in range(len(pathtocircuitdata)):
                    pointsum = pointsum + forinitiatordata[k2][k1]

                #print("pointsum", pointsum)   
                #print("forinitiatordata[i][k2][k1]", forinitiatordata[i][k2][k1])
                forinitiatordatatotal.append(pointsum + oldpoint)
                forstashpeerdatatotal.append(pointsum + oldpoint + newpoint)

            forinitiatordatatotalstring = {} #send to initiator
            forstashpeerdatatotalstring = {} #send to stashpeer

            forinitiatordatatotalstring = self.btitpiroram.convertfrompointlisttostring([forinitiatordatatotal])
                #print(forinitiatordatatotalstring[i])
            forstashpeerdatatotalstring = self.btitpiroram.convertfrompointlisttostring([forstashpeerdatatotal])

            #print("forinitiatordatatotalstring", forinitiatordatatotalstring)
            host,port = self.fetchinitiator[transactionid].split(":")
            toinitpeerdata = transactionid + "<<<" + self.myid + "<<<" + forinitiatordatatotalstring
            initresp = self.connectandsend(host, port, FETCHTOINITPEER, toinitpeerdata)
            #print("toinitpeerdata", toinitpeerdata)


            #print("forstashpeerdatatotalstring", forstashpeerdatatotalstring)
            host,port = self.fetchstashpeerid[transactionid].split(":")
            tostashpeerdata = transactionid + "<<<" + self.myid + "<<<" + forstashpeerdatatotalstring
            stashresp = self.connectandsend(host, port, FETCHTOSTASHPEER, tostashpeerdata)
            #print("tostashpeerdata", toinitpeerdata)

            del self.fetchcircuitdata[transactionid]
            del self.fetchcircuitinfo[transactionid]
            del self.fetchpathpeernum[transactionid]
            del self.fetchinitiator[transactionid]
            del self.fetchstashpeerid[transactionid]

    #--------------------------------------------------------------------------
    def __handle_fetchcircuitpeerinfo(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the FETCHCIRCUITPEERINFO message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        transactionid, initiator, stashpeerid, pathpeernum, circuitinfo = msg.split('<<<')
        self.fetchinitiator[transactionid] = initiator
        self.fetchstashpeerid[transactionid] = stashpeerid
        self.fetchpathpeernum[transactionid] = int(pathpeernum)
        oldpointstr, newpointstr, nummapstr = circuitinfo.split(">>>")
        self.fetchcircuitinfo[transactionid] = [self.btitpiroram.convertfromstringtopoint(oldpointstr), self.btitpiroram.convertfromstringtopoint(newpointstr), nummapstr.split("|")]

        if len(circuitinfo) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHCIRCUITPEERINFO is successful')
            self.__debug('FETCHCIRCUITPEERINFO is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHCIRCUITPEERINFO is not successful.')
            self.__debug('FETCHCIRCUITPEERINFO is not successful')

    #--------------------------------------------------------------------------
    def __handle_fetchtoinitpeer(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the FETCHTOINITPEER message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        transactionid, peerid, forinitiatordatatotalstring = msg.split('<<<')
        if transactionid not in self.fetchinitcircuitdata:
            self.fetchinitcircuitdata[transactionid] = {}
        self.fetchinitcircuitdata[transactionid][peerid] = self.btitpiroram.convertfromstringtopointlist(forinitiatordatatotalstring)
        #print("self.fetchinitcircuitdata[transactionid]", self.fetchinitcircuitdata[transactionid])
        #print("self.fetchcircuitnum", self.fetchcircuitnum)
        # while transactionid not in self.fetchcircuitnum:
        #     time.sleep(0.01)
        #     print("__handle_fetchtoinitpeer error")
        if transactionid not in self.fetchcircuitnum:
            self.fetchcircuitnum[transactionid] = 0

        if len(forinitiatordatatotalstring) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHTOINITPEER is successful')
            self.__debug('FETCHTOINITPEER is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHTOINITPEER is not successful.')
            self.__debug('FETCHTOINITPEER is not successful')

        if len(self.fetchinitcircuitdata[transactionid]) == self.fetchcircuitnum[transactionid]:
            tmppoints = [] #initiator sums up all the points
            for i in range(1):
                for j in range(self.btitpiroram.pointsnum):
                    sum = self.btitpiroram.usedcurve.G * 0
                    for k in self.fetchinitcircuitdata[transactionid]:
                        sum = sum + self.fetchinitcircuitdata[transactionid][k][i][j]
                    tmppoints.append(sum)
            print("Fetch data finished.")
            print("Time takes:", time.time() - self.fetchstarttime)
            self.__debug(tmppoints)
            #print(self.btitpiroram.usedcurve.G * 0)
            del self.fetchcircuitnum[transactionid]
            del self.fetchinitcircuitdata[transactionid]

            host,port = self.trackerid.split(':')
            resp = self.connectandsend(host, port, FETCHINITIATORFINISH, transactionid)



    #--------------------------------------------------------------------------
    def __handle_fetchtostashpeer(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the FETCHTOSTASHPEER message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        transactionid, peerid, forstashpeerdatatotalstring = msg.split('<<<')
        if transactionid not in self.fetchstashcircuitdata:
            self.fetchstashcircuitdata[transactionid] = {}
        self.fetchstashcircuitdata[transactionid][peerid] = self.btitpiroram.convertfromstringtopointlist(forstashpeerdatatotalstring)
        # while transactionid not in self.fetchstashcircuitnum:
        #     time.sleep(0.01)
        #     print("__handle_fetchtostashpeer error")
        if transactionid not in self.fetchstashcircuitnum:
            self.fetchstashcircuitnum[transactionid] = 0

        if len(forstashpeerdatatotalstring) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHTOSTASHPEER is successful')
            self.__debug('FETCHTOSTASHPEER is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHTOSTASHPEER is not successful.')
            self.__debug('FETCHTOSTASHPEER is not successful')

        if len(self.fetchstashcircuitdata[transactionid]) == self.fetchstashcircuitnum[transactionid]:
            tmppoints = [] #initiator sums up all the points
            for i in range(1):
                for j in range(self.btitpiroram.pointsnum):
                    sum = self.btitpiroram.usedcurve.G * 0
                    for k in self.fetchstashcircuitdata[transactionid]:
                        sum = sum + self.fetchstashcircuitdata[transactionid][k][i][j]
                    tmppoints.append(sum)
            self.__debug(tmppoints)
            #print(btitpiroram.usedcurve.G * 0)
            self.stashpeerdata.append(tmppoints)
            #print("Fetch to push stashdata finished.", tmppoints)
            del self.fetchstashcircuitnum[transactionid]
            del self.fetchstashcircuitdata[transactionid]

            host,port = self.trackerid.split(':')
            #singlecircuitdata = transactionid + "<<<" + self.myid + "<<<" + circuitdatatostashpeer
            resp = self.connectandsend(host, port, FETCHSTASHFINISH, transactionid)
            #if resp is not None:
            #    del self.uploadstashshares[transactionid]



    #--------------------------------------------------------------------------
    def __handle_fetchtostashinfo(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the FETCHTOSTASHINFO message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        transactionid, self.trackerid, numstr = msg.split('<<<')
        self.fetchstashcircuitnum[transactionid] = int(numstr)
    
        if len(msg) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHTOSTASHINFO is successful')
            self.__debug('FETCHTOSTASHINFO is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHTOSTASHINFO is not successful.')
            self.__debug('FETCHTOSTASHINFO is not successful')

    #--------------------------------------------------------------------------
    def __handle_fetchtoinitinfo(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the FETCHTOINITINFO message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        transactionid, self.trackerid, numstr = msg.split('<<<')
        self.fetchcircuitnum[transactionid] = int(numstr)
    
        if len(msg) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'FETCHTOINITINFO is successful')
            self.__debug('FETCHTOINITINFO is successful')
        else:
            peerconn.senddata(ERROR, 'FETCHTOINITINFO is not successful.')
            self.__debug('FETCHTOINITINFO is not successful')

    #--------------------------------------------------------------------------
    def __handle_evictionpathpeerinfo(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the EVICTIONPATHPEERINFO message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + data)
        transactionid, dataseq, self.trackerid, circuitpeers = str(data).split('<<<')
        self.evictioncircuitpeers[transactionid] = circuitpeers.split(">>>") 
        self.evictioncircuitpeernum[transactionid] = len(self.evictioncircuitpeers[transactionid])

        if len(circuitpeers) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'EVICTIONPATHPEERINFO is successful')
            self.__debug('EVICTIONPATHPEERINFO is successful')
        else:
            peerconn.senddata(ERROR, 'EVICTIONPATHPEERINFO is not successful.')
            self.__debug('EVICTIONPATHPEERINFO is not successful')

        #print("self.evictioncircuitpeers[transactionid]", self.evictioncircuitpeers[transactionid])
        for i in self.evictioncircuitpeers[transactionid]:
            host,port = i.split(':')
            singlecircuitdata = ""
            if dataseq != "stash":
                singlecircuitdata = transactionid + "<<<" + dataseq + "<<<" + self.btitpiroram.convertfrompointlisttostring(self.bucketdata)
            else:
                singlecircuitdata = transactionid + "<<<" + dataseq + "<<<" + self.btitpiroram.convertfrompointlisttostring(self.stashpeerdata)
            #print("singlecircuitdata", singlecircuitdata)
            resp = self.connectandsend(host, port, EVICTIONCIRCUITPEERDATA, singlecircuitdata)

        del self.evictioncircuitpeers[transactionid]

    #--------------------------------------------------------------------------
    def __handle_evictioncircuitpeerinfo(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the EVICTIONCIRCUITPEERINFO message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        transactionid, pathpeernum, circuitinfo = msg.split('<<<')

        self.evictionpathpeernum[transactionid] = int(pathpeernum)
        self.evictioncircuitinfo[transactionid] = {}

        firstlayer = circuitinfo.split(">>>")
        for i in firstlayer:
            pathpeerid, secondlayer = i.split("==")
            self.evictioncircuitinfo[transactionid][pathpeerid] = []
            numpack = secondlayer.split("++")
            for j in numpack:
                pointstr, numstr = j.split("--")
                num = numstr.split("|")
                self.evictioncircuitinfo[transactionid][pathpeerid].append([self.btitpiroram.convertfromstringtopoint(pointstr), num])

        if len(circuitinfo) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'EVICTIONCIRCUITPEERINFO is successful')
            self.__debug('EVICTIONCIRCUITPEERINFO is successful')
        else:
            peerconn.senddata(ERROR, 'EVICTIONCIRCUITPEERINFO is not successful.')
            self.__debug('EVICTIONCIRCUITPEERINFO is not successful')


    #--------------------------------------------------------------------------
    def __handle_evictioncircuitpeerdata(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the EVICTIONCIRCUITPEERDATA message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + data)
        transactionid, dataseq, peerdata = str(data).split('<<<')
        #print("error1")
        while transactionid not in self.evictionpathpeernum:
            time.sleep(1)
            print("__handle_evictioncircuitpeerdata error2")
        if transactionid not in self.evictioncircuitdata:
            self.evictioncircuitdata[transactionid] = []
            for i in range(self.evictionpathpeernum[transactionid]):
                self.evictioncircuitdata[transactionid].append([])
        #print("self.evictioncircuitdata[transactionid]", self.evictioncircuitdata[transactionid])
        if dataseq != "stash":
            self.evictioncircuitdata[transactionid][int(dataseq)] = self.btitpiroram.convertfromstringtopointlist(peerdata)
        else:
            self.evictioncircuitdata[transactionid][-1] = self.btitpiroram.convertfromstringtopointlist(peerdata)

        #print("self.evictioncircuitdata[transactionid]", self.evictioncircuitdata[transactionid])

        if len(peerdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'EVICTIONCIRCUITPEERDATA is successful')
            self.__debug('EVICTIONCIRCUITPEERDATA is successful')
        else:
            peerconn.senddata(ERROR, 'EVICTIONCIRCUITPEERDATA is not successful.')
            self.__debug('EVICTIONCIRCUITPEERDATA is not successful')

        emptyflag = False
        length = 0
        for i in self.evictioncircuitdata[transactionid]:
            if i == []:
                print("emptyflag", emptyflag)
                emptyflag = True
        if emptyflag == False:
        #To do
            pathtocircuitdata = []#pathpeers + stashpeer send to circuitpeers
            for i in self.evictioncircuitdata[transactionid]:
                length += len(i)
                pathtocircuitdata.extend(i)

            circuitinfo = {}
            a1 = {}

            #key = list(circuitinfototal.keys())
            self.evictioncircuitinfo[transactionid]
            for i in self.evictioncircuitinfo[transactionid]:
                a1[i] = [[] for i in range(len(self.evictioncircuitinfo[transactionid][i]))]

            #for peerid in circuitinfototal:
            for targettag in self.evictioncircuitinfo[transactionid]:
                #a1[targettag] = [{} for i in range(len(circuitinfototal[peerid][targettag]))]
                for targetdata in range(len(self.evictioncircuitinfo[transactionid][targettag])):
                    a1[targettag][targetdata] = self.evictioncircuitinfo[transactionid][targettag][targetdata]

            circuitinfo = a1

            for targettag in circuitinfo:
                topathpeerdata = ""
                for targetdata in range(len(circuitinfo[targettag])):

                    forinitiatordatatotal = {}#circuitpeers send to the initiator
                    forinitiatordata = {}

                    forinitiatordata = self.initpointlist(length)

                    #for i in circuitinfo[targettag][targetdata]:
                    #    print("i", i, targettag, targetdata)
                    oldpoint = circuitinfo[targettag][targetdata][0]

                    forinitiatordatatotal = []
                    if len(pathtocircuitdata) != len(circuitinfo[targettag][targetdata][1]):
                        #print(len(pathtocircuitdata[i]))
                        #print(len(circuitinfo[i][2]))
                        print("error", len(pathtocircuitdata), len(circuitinfo[targettag][targetdata][1]))
                        #break
                    #print("forinitiatordata11111", forinitiatordata[i])
                    for j in range(len(pathtocircuitdata)):
                        num = int(circuitinfo[targettag][targetdata][1][j])
                        for k in range(self.btitpiroram.pointsnum):
                            # print("before: pathtocircuitdata", pathtocircuitdata[i][j][k])
                            # print("before:", forinitiatordata[i][j][k])
                            forinitiatordata[j][k] = pathtocircuitdata[j][k] * num #Fixed bug: forinitiatordata must be initiated, cannot forinitiatordata[i] = pathtocircuitdata[i]
                            # print("after: pathtocircuitdata ", pathtocircuitdata[i][j][k])
                            # print("after:", forinitiatordata[i][j][k])
                            # print("num", num)
                    for k1 in range(self.btitpiroram.pointsnum):
                        pointsum = self.btitpiroram.usedcurve.G * 0
                        for k2 in range(len(pathtocircuitdata)):
                            pointsum = pointsum + forinitiatordata[k2][k1]

                            #print("forinitiatordata[i][k2][k1]", forinitiatordata[i][k2][k1])
                        forinitiatordatatotal.append(pointsum + oldpoint)
                        #forstashpeerdatatotal[i].append(pointsum + oldpoint + newpoint)

                    forinitiatordatatotalstring = {} #send to initiator
                    #forstashpeerdatatotalstring = {} #send to stashpeer
                    #for i in forinitiatordatatotal:
                    forinitiatordatatotalstring = self.btitpiroram.convertfrompointlisttostring([forinitiatordatatotal])
                    topathpeerdata = topathpeerdata + forinitiatordatatotalstring + "++"
                topathpeerdata = topathpeerdata[:-2]
                if targettag[:5] == "stash":
                    host,port = targettag[5:].split(":")
                    tostashpeerdata = transactionid + "<<<" + self.myid +  "<<<" + topathpeerdata
                    tostashpeerresp = self.connectandsend(host, port, EVICTIONTOSTASHPEER, tostashpeerdata)
                else:
                    host,port = targettag.split(":")
                    topathpeerdata = transactionid + "<<<" + self.myid + "<<<" + topathpeerdata
                    topathpeerresp = self.connectandsend(host, port, EVICTIONTOPATHPEER, topathpeerdata)
                        #print(forinitiatordatatotalstring[i])
                        #forstashpeerdatatotalstring[i] = btitpiroram.convertfrompointlisttostring([forstashpeerdatatotal[i]])

            del self.evictioncircuitdata[transactionid]
            del self.evictioncircuitinfo[transactionid]
            del self.evictionpathpeernum[transactionid]
            # del self.fetchinitiator[transactionid]
            # del self.fetchstashpeerid[transactionid]

    #--------------------------------------------------------------------------
    def __handle_evictiontopathpeer(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the EVICTIONTOPATHPEER message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        transactionid, peerid, topathpeerdata = msg.split('<<<')
        pointslist = topathpeerdata.split("++")
        #print("pointslist", pointslist)
        length = len(pointslist)
        if transactionid not in self.evictionpathpeercircuitdata:
            self.evictionpathpeercircuitdata[transactionid] = {}
        self.evictionpathpeercircuitdata[transactionid][peerid] = []
        for i in pointslist:
            points = self.btitpiroram.convertfromstringtopointlist(i)
            self.evictionpathpeercircuitdata[transactionid][peerid].append(points)
        #self.fetchstashcircuitdata[transactionid][peerid] = self.btitpiroram.convertfromstringtopointlist(forstashpeerdatatotalstring)
        # while transactionid not in self.fetchstashcircuitnum:
        #     time.sleep(0.01)
        #     print("__handle_fetchtostashpeer error")
        if transactionid not in self.evictioncircuitpeernum:
            self.evictioncircuitpeernum[transactionid] = 0

        if len(topathpeerdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'EVICTIONTOPATHPEER is successful')
            self.__debug('EVICTIONTOPATHPEER is successful')
        else:
            peerconn.senddata(ERROR, 'EVICTIONTOPATHPEER is not successful.')
            self.__debug('EVICTIONTOPATHPEER is not successful')

        if len(self.evictionpathpeercircuitdata[transactionid]) == self.evictioncircuitpeernum[transactionid]:
            finalpointslist = []
            for l in range(length):
                tmppoints = [] #initiator sums up all the points
                for i in range(1):
                    for j in range(self.btitpiroram.pointsnum):
                        sum = self.btitpiroram.usedcurve.G * 0
                        for k in self.evictionpathpeercircuitdata[transactionid]:
                            sum = sum + self.evictionpathpeercircuitdata[transactionid][k][l][i][j]
                        tmppoints.append(sum)
                self.__debug(tmppoints)
                finalpointslist.append(tmppoints)
            #Bug: stashsize may be the same as bucketsize Fixed
            # if length != len(self.bucketdata):
            #     self.stashpeerdata = []
            #     self.stashpeerdata = finalpointslist
            #     print("Eviction to push stashdata finished.", self.myid, finalpointslist)
            #     host,port = self.trackerid.split(':')
            #     resp = self.connectandsend(host, port, EVICTIONSTASHFINISH, transactionid)
            # else:
            self.bucketdata = []
            self.bucketdata = finalpointslist
            #print("Eviction to push peers finished.", self.myid, finalpointslist)
            host,port = self.trackerid.split(':')
            resp = self.connectandsend(host, port, EVICTIONPATHPEERFINISH, transactionid)

            
            del self.evictionpathpeercircuitdata[transactionid]
            #Bug: try to delete it properly
            #del self.evictioncircuitpeernum[transactionid]


    #--------------------------------------------------------------------------
    def __handle_evictiontostashpeer(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the EVICTIONTOSTASHPEER message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        transactionid, peerid, tostashpeerdata = msg.split('<<<')
        pointslist = tostashpeerdata.split("++")
        #print("pointslist", pointslist)
        length = len(pointslist)
        if transactionid not in self.evictionstashpeercircuitdata:
            self.evictionstashpeercircuitdata[transactionid] = {}
        self.evictionstashpeercircuitdata[transactionid][peerid] = []
        for i in pointslist:
            points = self.btitpiroram.convertfromstringtopointlist(i)
            self.evictionstashpeercircuitdata[transactionid][peerid].append(points)
        #self.fetchstashcircuitdata[transactionid][peerid] = self.btitpiroram.convertfromstringtopointlist(forstashpeerdatatotalstring)
        # while transactionid not in self.fetchstashcircuitnum:
        #     time.sleep(0.01)
        #     print("__handle_fetchtostashpeer error")
        if transactionid not in self.evictioncircuitpeernum:
            self.evictioncircuitpeernum[transactionid] = 0

        if len(tostashpeerdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'EVICTIONTOSTASHPEER is successful')
            self.__debug('EVICTIONTOSTASHPEER is successful')
        else:
            peerconn.senddata(ERROR, 'EVICTIONTOSTASHPEER is not successful.')
            self.__debug('EVICTIONTOSTASHPEER is not successful')

        if len(self.evictionstashpeercircuitdata[transactionid]) == self.evictioncircuitpeernum[transactionid]:
            finalpointslist = []
            for l in range(length):
                tmppoints = [] #initiator sums up all the points
                for i in range(1):
                    for j in range(self.btitpiroram.pointsnum):
                        sum = self.btitpiroram.usedcurve.G * 0
                        for k in self.evictionstashpeercircuitdata[transactionid]:
                            sum = sum + self.evictionstashpeercircuitdata[transactionid][k][l][i][j]
                        tmppoints.append(sum)
                self.__debug(tmppoints)
                finalpointslist.append(tmppoints)
            #Fixed bug: stashsize may be the same as bucketsize
            # if length != len(self.bucketdata):
            self.stashpeerdata = []
            self.stashpeerdata = finalpointslist
            #print("Eviction to push stashdata finished.", self.myid, finalpointslist)
            host,port = self.trackerid.split(':')
            resp = self.connectandsend(host, port, EVICTIONSTASHFINISH, transactionid)
            # else:
            #     self.bucketdata = []
            #     self.bucketdata = finalpointslist
            #     print("Eviction to push peers finished.", self.myid, finalpointslist)

            
            #del self.fetchstashcircuitnum[transactionid]
            del self.evictionstashpeercircuitdata[transactionid]


    #--------------------------------------------------------------------------
    def __handle_earlyshuffle(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the EARLYSHUFFLE message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        resp = ""
        #flag = self.btringoram.uploaddata(dataid, datacontent)
        for i in self.bucketdata:
            if i is self.bucketdata[0]:
                resp += i
            else:
                resp = resp + ">>>" + i
        #resp = self.bucketdata[int(number)]
        #self.__debug(resp)

        if len(self.bucketdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, resp)
            self.__debug('Earlyshuffle is successful')
        else:
            peerconn.senddata(ERROR, 'Earlyshuffle is not successful.')
            self.__debug('Earlyshuffle is not successful')

    #--------------------------------------------------------------------------
    def __handle_earlyshufflefinish(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the EARLYSHUFFLEFINISH message type. The message data should be in
        the format of a string of content.

        """

        #self.__debug("message: " + msg)
        self.bucketdata = data.split(">>>")
        self.__debug(self.bucketdata)

        if len(self.bucketdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'Earlyshufflefinish is successful')
            self.__debug('Earlyshufflefinish is successful')
        else:
            peerconn.senddata(ERROR, 'Earlyshufflefinish is not successful.')
            self.__debug('Earlyshufflefinish is not successful')

    #--------------------------------------------------------------------------
    def __handle_eviction(self, peerconn, msg):
    #--------------------------------------------------------------------------
        """ Handles the EVICTION message type. The message data should be in
        the format of a string of content.

        """

        self.__debug("message: " + msg)
        resp = ""
        #flag = self.btringoram.uploaddata(dataid, datacontent)
        for i in self.bucketdata:
            if i is self.bucketdata[0]:
                resp += i
            else:
                resp = resp + ">>>" + i
        #resp = self.bucketdata[int(number)]
        #self.__debug(resp)

        if len(self.bucketdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, resp)
            self.__debug('Eviction is successful')
        else:
            peerconn.senddata(ERROR, 'Eviction is not successful.')
            self.__debug('Eviction is not successful')

    #--------------------------------------------------------------------------
    def __handle_evictionfinish(self, peerconn, data):
    #--------------------------------------------------------------------------
        """ Handles the EVICTIONFINISH message type. The message data should be in
        the format of a string of content.

        """

        #self.__debug("message: " + msg)
        self.bucketdata = data.split(">>>")
        #self.__debug(self.bucketdata)

        if len(self.bucketdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, 'Evictionfinish is successful')
            self.__debug('Evictionfinish is successful')
        else:
            peerconn.senddata(ERROR, 'Evictionfinish is not successful.')
            self.__debug('Evictionfinish is not successful')

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
