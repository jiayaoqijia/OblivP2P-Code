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
EARLYSHUFFLE = "EARL"
EVICTION = "EVIC"
EARLYSHUFFLEFINISH = "EAFI"
EVICTIONFINISH = "EVFI"

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
                    EARLYSHUFFLE: self.__handle_earlyshuffle,
                    EVICTION: self.__handle_eviction,
                    EARLYSHUFFLEFINISH: self.__handle_earlyshufflefinish,
                    EVICTIONFINISH: self.__handle_evictionfinish
                   }
        for mt in handlers:
            self.addhandler(mt, handlers[mt])

    # end FilerPeer constructor



    #--------------------------------------------------------------------------
    def __debug(self, msg):
    #--------------------------------------------------------------------------
     """ Prints a messsage to the screen with the name of the current thread """
     print "[%s] %s" % ( str(threading.currentThread().getName()), msg )
        #if self.debug:
        #    btdebug(msg)



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
                print filedata
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
                print dummydata
                fd.close()

                #read real data
                fd = file(real, 'r')
                realdata = ''
                while True:
                        filedata = fd.read(2048)
                        if not len(filedata):
                                break
                        realdata += filedata
                print realdata
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

        self.__debug("number: " + number)
        #flag = self.btringoram.uploaddata(dataid, datacontent)
        resp = self.bucketdata[int(number)]
        #self.__debug(resp)

        if len(self.bucketdata) > 0:
                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            print("data size:")
            for i in self.bucketdata:
                print(len(i))
            peerconn.senddata(REPLY, resp)
            self.__debug('Locating data is successful.')
        else:
            peerconn.senddata(ERROR, 'Locating data is not successful.')
            self.__debug('Locating data is not successful.')

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
        self.__debug(self.bucketdata)

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
                print filedata
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
