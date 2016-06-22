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
                    NAIVEINIT: self.__handle_naiveinit,
                    UPLOADDATA: self.__handle_uploaddata,
                    READDATA: self.__handle_readdata
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
            respdata += str(len(receiveddata))
            #print "respdata: " + respdata
            for i in receiveddata:
                respdata = respdata + ">>>" + i

                #responsedata = str(self.N) + ">>>" + dummydata + ">>>" + realdata
            peerconn.senddata(REPLY, respdata)
            del respdata
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
        
        
        print "self.earlyshuffleon: %s self.evictionon: %s" % (self.earlyshuffleon, self.evictionon)
        # if self.earlyshuffleon or self.evictionon:
        #     time.sleep(0.5)
        #     self.__debug("Eviction sleep.")
        #     self.__handle_uploaddata(peerconn, data)
        while self.earlyshuffleon or self.evictionon:
            time.sleep(1)
            self.__debug("Eviction sleep.")
            #self.__handle_uploaddata(peerconn, data)
        #else:           
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
            self.evictionstarttime = time.time()
            self.evictionon = True
            evictionpeer = {}
            #evictionpeer["R"] = peertagdata["R"]
            self.__debug("eviction %s" % tag["eviction"])
            host,port = self.btringoram.peermap["R"].split(":")
            resp = self.connectandsend(host, port, EVICTION, "eviction")
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
                    #self.__debug("eviction resp: %s" % resp)
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
                        finishdata = j
                    else:
                        finishdata = finishdata + ">>>" + j
                evictionresp = self.connectandsend(host, port, EVICTIONFINISH, finishdata)
                self.__debug("Evictionresp resp: %s" % evictionresp)
                self.__debug("Eviction time: %s." % str(datetime.now()))
            self.__debug("positionmap %s. \n dataid %s. \n number %s" % (self.btringoram.positionmap, self.btringoram.positionmap.keys(), len(self.btringoram.positionmap.keys())))
            self.__debug("stashmap %s. \n dataid %s. \n number %s" % (self.btringoram.stashmap, self.btringoram.stashmap.keys(), len(self.btringoram.stashmap.keys())))
            #self.__debug("positionmap %s." % self.btringoram.positionmap)
            self.__debug("Eviction finish time: %s." % str(datetime.now()))
            print "eviction finished."
            print "Time takes " + str(time.time() - self.evictionstarttime) 
            self.evictionon = False

    #--------------------------------------------------------------------------
    def __handle_readdata(self, peerconn, dataid):
    #--------------------------------------------------------------------------
        """ Handles the UPLOADDATA message type. The message data should be in
        the format of a string of content.

        """
        #To do: store data in DB or filesystem; paralell communication with peers, reuse the connection for earlyshuflle and eviction
        self.__debug("Read data %s time: %s." % (dataid, datetime.now()))
        # if self.earlyshuffleon or self.evictionon:
        #     time.sleep(2)
        #     self.__debug("Eviction sleep.")
        #     self.__handle_readdata(peerconn, dataid)
        while self.earlyshuffleon or self.evictionon:
            time.sleep(1)
            self.__debug("Eviction sleep.")
            #self.__handle_readdata(peerconn, dataid)
        #else:
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
            tmpdata = resp[0][1]
            #self.__debug(tmpdata)
            #self.__debug(data)
            if data["realdatapeer"] is not None:
                if i is data["realdatapeer"]:
                    respdata = tmpdata
        #self.__debug(respdata)
        if  data["stash"] is not None:
            self.__debug("Read from stash.")
            respdata = data["stash"]
            #self.btringoram.stashrealdata[data["stash"]]
            respdata = self.btringoram.btaes.decrypt(respdata)
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
            respdata = self.btringoram.btaes.decrypt(respdata)
        #self.__debug(respdata)
        if  len(respdata) > 0:
            peerconn.senddata(REPLY, respdata)
        else:
            peerconn.senddata(ERROR, 'Read data is not successful.')

        if  len(data["earlyshuffle"]) > 0:
            self.earlyshufflestarttime = time.time()
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
                        finishdata += k
                    else:
                        finishdata = finishdata + ">>>" + k
                shuffleresp = self.connectandsend(host, port, EARLYSHUFFLEFINISH, finishdata)
            self.earlyshuffleon = False
            print "earlyshuffle finished."
            print "Time takes " + str(time.time() - self.earlyshufflestarttime)

        if data["eviction"] is not None:
            self.evictionstarttime = time.time()
            self.evictionon = True
            evictionpeer = {}
            #evictionpeer["R"] = peertagdata["R"]
            self.__debug("eviction %s" % data["eviction"])
            host,port = self.btringoram.peermap["R"].split(":")
            resp = self.connectandsend(host, port, EVICTION, "eviction")
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
                    #self.__debug("eviction resp: %s" % resp)
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
                        finishdata = j
                    else:
                        finishdata = finishdata + ">>>" + j
                evictionresp = self.connectandsend(host, port, EVICTIONFINISH, finishdata)
                self.__debug("evictionresp resp: %s" % evictionresp)
                self.__debug("Eviction time: %s." % str(datetime.now()))
            self.__debug("positionmap %s. \n dataid %s. \n number %s" % (self.btringoram.positionmap, self.btringoram.positionmap.keys(), len(self.btringoram.positionmap.keys())))
            self.__debug("stashmap %s. \n dataid %s. \n number %s" % (self.btringoram.stashmap, self.btringoram.stashmap.keys(), len(self.btringoram.stashmap.keys())))
            #self.__debug("positionmap %s." % self.btringoram.positionmap)
            self.__debug("Eviction finish time: %s." % str(datetime.now()))
            print "eviction finished."
            print "Time takes " + str(time.time() - self.evictionstarttime) 
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
