from btcrypto import *
import itertools
import time
import traceback
import sys

class BtRingORAM:
    
    def __init__( self, realnumber, realpath, dummynumber, dummypath, leavesnumber, evictionrate, blocksize ):
    #--------------------------------------------------------------------------
        """ Initiation of a BtRingORAM for our construction-0 """

        self.debug = 0 #flag for debugging
        self.positionmap = {} # dataid --> tag, level, number
        self.peermap = {} # available peers: o-ram id --> peerid
        self.peermapreverse = {} # reverse peermap: peerid --> o-ram id
        self.peerdata = {} # {peertag:{count:0, rvalid:[], dvalid:[], dataid:[dataid1, dataid2]},...}
        self.stashrealdata = {} #Real data: dataid --> datacontent
        self.stashmap = {} #dataid: --> datatag (new assigned tag)}
        self.tagmap = {} #datatag --> number (maximum is Z)
        self.Z = realnumber
        self.S = dummynumber
        self.A = evictionrate
        self.N = leavesnumber #2**N is number of leaves
        self.key = generateKey(32) #Generate a random key for btringoram
        self.blocksize = blocksize
        self.dummypath = dummypath
        self.realpath = realpath
        self.dummydata = ""

        #initiation
        self.__init_peermap(self.N)
        self.__init_tagmap(self.N)
        self.__initdummydata()
        self.btaes = AESCipher(self.key)
        self.G = 0 #global counter for eviction path
        self.Acount = 0 #global counter for eviction
        self.evictionpaths = self.__initevictionpaths() #eviction paths following reverse lexi order

    # peermap: {peertag:{count:0, rvalid:[], dvalid:[], data:[dataid1, dataid2]},...}
    def __initpeerdata ( self, peertag ):
    #--------------------------------------------------------------------------
        """ Reset peerrdata, and push real data in stash to the new peer
        """
        self.__resetpeerdata(peertag)
        #self.__debug(str(self.peerdata))
        return self.__pushstashtopeer(peertag)


    def __initdummydata ( self ):
    #--------------------------------------------------------------------------
        """ Reset peerrdata, and push real data in stash to the new peer
        """
        #read dummy data
        fd = file(self.dummypath + "/dummy.txt", 'r')
        self.dummydata = ''
        while True:
                filedata = fd.read(2048)
                if not len(filedata):
                        break
                self.dummydata += filedata
        fd.close()

    def join ( self, peerid ):
    #--------------------------------------------------------------------------
        """ A new peer joins the network, returns the data pushed to the peer including real data and dummy data
        """
        print "function join"
        #peerid: IP:port
        peertag = ""
        fullflag = True
        if peerid is None:
            self.__debug('Peerid is None.')
            return None

        for i in self.bitstrings:
            if self.peermap[i] is None:
                peertag = i
                self.peermap[i] = peerid
                self.peermapreverse[peerid] = i
                fullflag = False
                break
                #return True
        if fullflag:
            self.__debug('ORAM tree is full.')
            return None
        #Now join btringoram, dummy blocks will be returned; later real blocks can be returned
        data = [] #data = [data1, data2, ...]
        #data = self.__generatedummy(self.dummypath, self.Z + self.S)
        data = self.__initpeerdata(peertag)
        return data

    def uploaddata (self, dataid, datacontent):
    #--------------------------------------------------------------------------
        """ Upload data with id and content.
        """
        print "function uploaddata"
        if len(datacontent) != self.blocksize:
            self.__debug("Data size is not %s." % self.blocksize)
            return None
        datatag = self.__generaterandomtag()
        self.__updatestashrealdata(dataid, datacontent)
        self.__updatestashmap(dataid, datatag)
        self.__addtagmap(datatag)

        taglist = {} #eviction --> pathtag
        taglist["eviction"] = None
        self.Acount += 1
        pathtag = ""
        if self.Acount >= self.A:
            pathtag = self.evictionpaths[self.G]
            #self.eviction(pathtag, data)
            taglist["eviction"] = pathtag
            self.G += 1
            if self.G >= len(self.evictionpaths):
                self.G = 0
            self.Acount = 0
        #print self.positionmap
        print taglist
        return taglist

    def readdata (self, dataid):
    #--------------------------------------------------------------------------
        """ Read data based on dataid. The return value is a list of pathtag for eviction, peers for earlyshuffle, data in stash,
        or which peer and number should read
        """
        print "function readdata"
        taglist = {} #eviction: peertag, earlyshuffle: [level, ...], stash: dataid, realdatapeer: peerid, peerid: number
        realflag = True
        datatag = ""
        leveltag = ""
        taglist["eviction"] = None
        taglist["realdatapeer"] = None
        taglist["earlyshuffle"] = []
        if dataid in self.stashmap:
            taglist["stash"] = self.stashrealdata[dataid]
            datatag = self.stashmap[dataid]
            #print ("dataid: " + dataid + " datatag: " + datatag)
            newdatatag = self.__generaterandomtag()
            self.__updatestashmap(dataid, newdatatag)
            self.__removetagmap(datatag)
            self.__addtagmap(newdatatag)
            realflag = False
        else:
            taglist["stash"] = None
            datatag = self.positionmap[dataid][0]
            leveltag = self.positionmap[dataid][1]

        for i in range(len(datatag)+1):
            if i == len(datatag):
                level = "R"
            else:
                level = datatag[:i+1]
            if (level == leveltag) and realflag:
                datanumber = self.positionmap[dataid][2]
                taglist[self.peermap[level]] = datanumber
                self.peerdata[level]["rvalid"].remove(datanumber)

                
                self.peerdata[level]["count"] += 1
                if self.peerdata[level]["count"] >= self.S:
                    taglist["earlyshuffle"].append(level)

                self.__removetagmap(self.positionmap[dataid][0])
                ###To do 
                #Waiting for response data to update stashmap, stashrealdata and tagmap
                taglist["realdatapeer"] = self.peermap[level]
                newdatatag = self.__generaterandomtag()
                #self.__updatestashrealdata(dataid, datacontent)
                self.__updatestashmap(dataid, newdatatag)
                self.__addtagmap(newdatatag)
                self.__removepositionmap(dataid)
                #remove positionmap, de-valid peerdata, push to stashrealdata & stashmap
            else:
                #Incomplete tree check
                if self.peermap[level] is not None:
                    randomdummy = random.choice(self.peerdata[level]["dvalid"])
                    self.peerdata[level]["dvalid"].remove(randomdummy)
                    self.peerdata[level]["count"] += 1
                    if self.peerdata[level]["count"] >= self.S:
                        taglist["earlyshuffle"].append(level)
                    taglist[self.peermap[level]] = randomdummy

        self.Acount += 1
        pathtag = ""
        if self.Acount >= self.A:
            pathtag = self.evictionpaths[self.G]
            #self.eviction(pathtag, data)
            taglist["eviction"] = pathtag
            self.G += 1
            if self.G >= len(self.evictionpaths):
                self.G = 0
            self.Acount = 0
        print taglist
        return taglist

    def earlyshuffle ( self, peertag, data ):
    #--------------------------------------------------------------------------
        """ Shuffle data in the peer.
        """
        #read
        print "function earlyshuffle peertag: %s" % peertag
        print "stashmap number before earlyshuffle: %s" % len(self.stashmap.keys())
        print self.peerdata[peertag]
        self.__pullpeertostash(peertag, data)
        #write
        resp = self.__pushstashtopeer(peertag)
        print "stashmap number after earlyshuffle: %s" % len(self.stashmap.keys())
        return resp


    def eviction ( self, pathtag, data ): 
    #--------------------------------------------------------------------------
        """ Eviction for a path based on pathtag with its data.
        """
        #pathtag: "111"
        #data: peertag --> [data1, data2, ...]
        #resp: peertag --> [data1, data2, ...]
        print "function eviction pathtag: %s" % pathtag
        print "stashmap number before eviction: %s" % len(self.stashmap.keys())
        #read
        for i in data:
            peertag = i
            self.__pullpeertostash(peertag, data[i])

        #write
        resp = {}
        for j in range(len(pathtag)):
            peertag = pathtag[:len(pathtag)-j]
            #Incomplete tree check
            if self.peermap[peertag] is not None:
                resp[peertag] = self.__pushstashtopeer(peertag)
        resp["R"] = self.__pushstashtopeer("R")
        print "function eviction pathtag: %s" % pathtag
        print "stashmap number after eviction: %s" % len(self.stashmap.keys())
        print self.stashmap
        return resp

    def __pullpeertostash ( self, peertag, data ):
    #--------------------------------------------------------------------------
        """ Pull data from a peer to stash, preparing for earlyshuffle or eviction.
        """
        #data: [data1, data2, ...]
        #Pull valid real data from peertag to stash
        print "function __pullpeertostash"
        for i in self.peerdata[peertag]["rvalid"]:
            dataid = self.peerdata[peertag]["dataid"][i]
            self.stashrealdata[dataid] = data[i]
            #in stash not in positionmap; but in peerdata
            datatag = self.positionmap[dataid][0]
            #Fixed bug: Only reading real data from stash or peers needs a new datatag, earlyshuffle or eviction does not require a block to change to a new tag
            #newdatatag = self.__generaterandomtag()
            #self.__updatestashmap(dataid, newdatatag)
            self.__updatestashmap(dataid, datatag)
            del self.positionmap[dataid]


    def __pushstashtopeer ( self, peertag ):
    #--------------------------------------------------------------------------
        """ Push real data in stash to a peer (peertag)
        """
        #Find real data in stash fit for peertag
        print "function __pushstashtopeer"
        #print peertag
        count = 0
        tmpdataid = []
        respdata = [] #[data1, data2, ...]
        permutation = []
        for i in range(self.Z+self.S):
            tmpdataid.append("dummy")
        #sorted(self.stashmap)
        for i in self.stashmap:
            #Fixed bug: do not use is, but == 
            if (peertag == "R") or (self.stashmap[i][:len(peertag)] == peertag):
                tmpdataid[count] = i
                #del self.stashmap[i]
                count += 1
                if count >= self.Z:
                    break
        #Permutate real data and dummy data
        permutation = [i for i in range(self.Z+self.S)]
        shuffle(permutation)
        self.__resetpeerdata(peertag)
        respdata = ["" for i in range(self.Z+self.S)]
        #Update peerdata and set respdata based on its permutated order
        print "stashmap"
        print self.stashmap
        for i in range(len(permutation)):
            if tmpdataid[i] == "dummy":
                singledummy = self.__generatedummy(self.dummypath, 1)
                respdata[permutation[i]] = singledummy[0]
                self.peerdata[peertag]["dvalid"].append(permutation[i])
                self.peerdata[peertag]["dataid"][permutation[i]] = "dummy"
            else:
                #Re-encrypt real data not dummy data
                tmpdata = self.btaes.decrypt(self.stashrealdata[tmpdataid[i]])
                respdata[permutation[i]] = self.btaes.encrypt(tmpdata)
                self.peerdata[peertag]["rvalid"].append(permutation[i])
                self.peerdata[peertag]["dataid"][permutation[i]] = tmpdataid[i]

                self.positionmap[tmpdataid[i]] = [self.stashmap[tmpdataid[i]], peertag, permutation[i]]
                del self.stashmap[tmpdataid[i]]
                del self.stashrealdata[tmpdataid[i]]
        
        print "push to peertag: %s. rvalid %s" % (peertag, self.peerdata[peertag]["dataid"])
        return respdata

    def __initevictionpaths ( self ):
    #--------------------------------------------------------------------------
        """ Choose a path for eviction based on reverse-lexi order, e.g., 00, 10, 01, 11
        """
        tags = self.tagmap.keys()
        paths = {}
        for i in range(len(tags)):
            paths[tags[i][::-1]] = tags[i]
        reverselexiorderpaths = [paths[i] for i in sorted(paths)]
        return reverselexiorderpaths

    def __resetpeerdata ( self, peertag ):
    #--------------------------------------------------------------------------
        """ Reset peerdata for a peer.
        """
        self.peerdata[peertag] = {}
        self.peerdata[peertag]["count"] = 0
        self.peerdata[peertag]["rvalid"] = []
        self.peerdata[peertag]["dvalid"] = []
        self.peerdata[peertag]["dataid"] = ["" for i in range(self.Z+self.S)]

    def __removepositionmap (self, dataid):
    #--------------------------------------------------------------------------
        """ Remove the item of dataid in positionmap.
        """
        del self.positionmap[dataid]

    def __updatestashrealdata (self, dataid, datacontent):
    #--------------------------------------------------------------------------
        """ Add real data to stash.
        """
        self.stashrealdata[dataid] = self.btaes.encrypt(datacontent)
        #self.__debug(self.stashrealdata)

    def __removestashrealdata (self, dataid):
    #--------------------------------------------------------------------------
        """ Remove data from stash.
        """
        del self.stashrealdata[dataid]

    def __updatestashmap (self, dataid, datatag):
    #--------------------------------------------------------------------------
        """ Map a datatag to a data
        """
        self.stashmap[dataid] = datatag
        #self.__debug(self.stashmap)

    def __removestashmap (self, dataid):
    #--------------------------------------------------------------------------
        """ Remove a dataid/datatag mapping.
        """
        del self.stashmap[dataid]

    def __addtagmap (self, datatag):
    #--------------------------------------------------------------------------
        """ Increase the used number of a datatag
        """
        self.__debug("tagmap")
        #self.__debug("datatag: " + str(datatag))
        self.tagmap[datatag] += 1
        self.__debug(self.tagmap)

    def __removetagmap (self, datatag):
    #--------------------------------------------------------------------------
        """ Decrease the used number of a datatag
        """
        self.tagmap[datatag] -= 1

    def __debug (self, msg):
    #--------------------------------------------------------------------------
        """ Print debug information.
        """
        if self.debug:
            print msg

    #--------------------------------------------------------------------------
    def __generatebitstrings( self, number ):
    #--------------------------------------------------------------------------
        """ Generate bitstrings for a number: 2 --> 0, 1, 00, 01, 10, 11
        """
        bitstrings = ['R']
        for i in range( 1, number+1 ):
                for j in itertools.product( '01', repeat=i ):
                        bits = [''.join(j)] #j: ('0', '0')
                        bitstrings += bits
        return bitstrings

    def __init_peermap( self, bitstringlength ):
        """ Generate bitstrings as keys for peermap
        """
        #initiation for peermap
        self.bitstrings = self.__generatebitstrings(bitstringlength)
        for bits in self.bitstrings:
                self.peermap[bits] = None

    def __init_tagmap( self, number):
    #--------------------------------------------------------------------------
        """ Generate bits as keys for tagmap
        """
        #initiation for tagmap
        for j in itertools.product( '01', repeat=number ):
            bits = ''.join(j)
            self.tagmap[bits] = 0

    def __generaterandomtag ( self ):
    #--------------------------------------------------------------------------
        """ Generate a random tag for real data not dummy data
        """
        #Generate a random tag for real data not dummy data
        tags = []
        for i in self.tagmap:
            tags.append(i)
        if len(tags) == 0:
            return None
        return generaterandomchoice(tags)

    def __generatedummy( self, dummypath, number ):
    #--------------------------------------------------------------------------
        """ Generate a dummy data list based on number
        """

        data = []
        for i in range(0, number):
            data.append(self.btaes.encrypt(self.dummydata))
        #self.__debug(data)
        return data