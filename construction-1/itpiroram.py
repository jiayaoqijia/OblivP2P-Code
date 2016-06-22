import itertools
import time
import traceback
import sys
from btcrypto import *

import math
import random

from ecc import AffineCurvePoint, ShortWeierstrassCurve, getcurvebyname
from ecc import ECPrivateKey

class BtITPIRORAM:
    
    def __init__( self, realnumber, realpath, dummypath, leavesnumber, evictionrate, circuitlength, blocksize, prerandompointsnum ):
    #--------------------------------------------------------------------------
        """ Initiation of a BtITPIRORAM for our construction-1 """

        self.debug = 0 #flag for debugging
        self.positionmap = {} # dataid --> tag, level, number
        self.peermap = {} # available peers: o-ram id --> peerid
        self.peermapreverse = {} # reverse peermap: peerid --> o-ram id
        self.peerdata = {} # {peertag:{count:0, rvalid:[], dvalid:[], dataid:[dataid1, dataid2]},...}
        #self.stashrealdata = {} #Real data: dataid --> datacontent
        self.stashmap = {} #dataid: --> datatag (new assigned tag)}
        self.stashpeermap = [] #dataid stored on stashpeer in sequence
        self.tagmap = {} #datatag --> number (maximum is Z)
        self.secretmap = {} #dataid --> ecc random point: we use randomnum represent it, which can be calculated by usedcurve.G * randomnum
        self.usedcurve = getcurvebyname("NIST P-256") #The ecc curve we use
        #self.usedcurve = getcurvebyname("brainpoolP160t1")#brainpoolP160t1
        self.pointsnum = int(blocksize / 512 * 8)  #The number of points for one block
        self.stashpeer = "" #the peertag chosen to store stashdata
        self.Z = realnumber
        self.C = circuitlength #circuit length
        #self.S = dummynumber
        self.A = evictionrate
        self.N = leavesnumber #2**N is number of leaves
        #self.key = generateKey(16) #Generate a random key for btringoram
        self.blocksize = blocksize
        self.dummypath = dummypath
        self.realpath = realpath
        self.neutralpoint = self.usedcurve.G * 0

        #initiation
        self.__init_peermap(self.N)
        self.__init_tagmap(self.N)
        #self.btaes = AESCipher(self.key)
        self.G = 0 #global counter for evictionpath
        self.Acount = 0 #global counter for eviction
        self.evictionpaths = self.__initevictionpaths() #eviction paths following reverse lexi order

        self.prerandompointsnum = prerandompointsnum
        #self.prerandompointsnum = 2**self.N
        self.randompoints = self.__init_randompoints(self.prerandompointsnum) #pre generate random points

    # peermap: {peertag:{count:0, rvalid:[], dvalid:[], data:[dataid1, dataid2]},...}
    def __initpeerdata ( self, peertag ):
    #--------------------------------------------------------------------------
        """ Reset peerrdata, and push real data in stash to the new peer
        """

        return self.__pushdummytopeer(peertag)

    def join ( self, peerid ):
    #--------------------------------------------------------------------------
        """ A new peer joins the network, returns the data pushed to the peer including real data and dummy data.
        return ["rand11, rand12, ...", "rand21, rand22, ...", ..self.]
        """
        print ("function join")
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

    def uploaddata (self, dataid):
    #--------------------------------------------------------------------------
        """ Upload data with id and content.
        """
        #datalist = {"pushstash": data, }
        print ("function uploaddata")
        datalist = {}
        datalist["pushstash"] = None 
        if self.stashpeer == "":
            self.stashpeer = "R"
            #self.stashpeer = self.__generaterandompeertag()
            datalist["pushstash"] = self.__pushstashtostashpeer(self.stashpeer)
            #Fixed bug: should use id not data
            for i in range(len(datalist["pushstash"])):
                self.stashpeermap.append("dummy")
            #self.stashpeermap.extend(datalist["pushstash"])

        circuitpeers = [] #peers for a circuit
        points = [] #points for each circuit peer, use number instead
        datalist["circuitinfo"] = {}
        pointsum = self.usedcurve.G * 0
        circuittags = self.__generaterandompeertags(self.C)
        for i in range(self.C):
            circuitpeers.append(self.peermap[circuittags[i]])
            #pointnum = self.usedcurve.G * self.__generaterandomnumber()
            pointnum = self.__generaterandompoint()
            pointsum += pointnum
            pointstr = self.convertfrompointtostring(pointnum)
            points.append(pointstr)
            datalist["circuitinfo"][circuitpeers[i]] = points[i]
        #self.secretmap[dataid] = self.convertfrompointtostring(pointsum)
        print("original secretmap", self.secretmap)
        self.secretmap[dataid] = pointsum
        #print("dataid and pointsum", dataid, pointsum)
        datalist["stashpeer"] = self.peermap[self.stashpeer]
        datalist["uploadpeerinfo"] = circuitpeers
        #if len(datacontent) != self.blocksize:
        #    self.__debug("Data size is not %s." % self.blocksize)
        #    return None
        datatag = self.__generaterandomtag()
        #self.__updatestashrealdata(dataid, datacontent)
        self.__updatestashmap(dataid, datatag) #map a tag to data in stash
        self.__updatestashpeermap(dataid) #add dataid in stashpeer
        self.__addtagmap(datatag)

        #taglist = {} #eviction --> pathtag
        datalist["eviction"] = None
        self.Acount += 1
        pathtag = ""
        if self.Acount >= self.A:
            pathtag = self.evictionpaths[self.G]
            #self.eviction(pathtag, data)
            datalist["eviction"] = pathtag
            self.G += 1
            if self.G >= len(self.evictionpaths):
                self.G = 0
            self.Acount = 0
        #print self.positionmap
        #print (datalist)
        # for i in self.secretmap:
        #     #print("secretmap", i)
        #     print("secretmap before:", i, self.usedcurve.G * int(i.split("data")[1]))
        #     print("secretmap after:", i, (self.usedcurve.G * int(i.split("data")[1]) + self.secretmap[i]))
        #     print("secretmap data:", i, self.secretmap[i])
        return datalist


    def __pushstashtostashpeer ( self, peertag ):
    #--------------------------------------------------------------------------
        """ Push stash to stashpeer
        """
        blocknum = self.Z * (self.N + 1)
        dummyblocks = self.__generatedummy(blocknum)
        return dummyblocks

    def fetch (self, dataid):
    #--------------------------------------------------------------------------
        """ Read data based on dataid. The return value is a list of pathtag for eviction, data in stash,
        or which peer and number should read
        """
        print ("function fetch")
        datalist = {} #eviction: peertag, earlyshuffle: [level, ...], stash: dataid, realdatapeer: peerid, peerid: number
        #realflag = True
        location = 0
        datatag = ""
        leveltag = ""
        
        #taglist["realdatapeer"] = None
        #taglist["earlyshuffle"] = []
        if dataid in self.stashmap:
            #taglist["stash"] = self.stashrealdata[dataid]
            datatag = self.stashmap[dataid]
            location = self.Z #for R
            for i in range(len(datatag)):
                level = datatag[:i+1]
                if self.peermap[level] is not None:
                    location += self.Z
            location = location + len(self.stashpeermap) - 1 - self.stashpeermap[::-1].index(dataid) #from the rightmost data
            #print ("dataid: " + dataid + " datatag: " + datatag)
            newdatatag = self.__generaterandomtag()
            self.__updatestashmap(dataid, newdatatag)
            self.__removetagmap(datatag)
            self.__addtagmap(newdatatag)
            #realflag = False
        else:
            #taglist["stash"] = None
            datatag = self.positionmap[dataid][0]
            leveltag = self.positionmap[dataid][1]
            if leveltag == "R":
                location = self.positionmap[dataid][2]
            else:
                location = len(leveltag) * self.Z + self.positionmap[dataid][2]

            self.__removetagmap(self.positionmap[dataid][0])
            ###To do 
            #Waiting for response data to update stashmap, stashrealdata and tagmap
            #taglist["realdatapeer"] = self.peermap[level]
            newdatatag = self.__generaterandomtag()
            #self.__updatestashrealdata(dataid, datacontent)
            self.__updatestashmap(dataid, newdatatag)
            self.__addtagmap(newdatatag)
            self.__removepositionmap(dataid) #remove positionmap

        datalist["pathpeerinfo"] = []
        datalist["pathpeerinfo"].append(self.peermap["R"])
        for i in range(len(datatag)):
            datalist["pathpeerinfo"].append(self.peermap[datatag[:i+1]])
        #remember to add stashpeer
        circuitpeers = [] #peers for a circuit
        oldpoints = [] #points for each circuit peer, use number instead
        newpoints = [] #points for each circuit peer, use number instead
        datalist["circuitinfo"] = {}
        newpointsum = self.usedcurve.G * 0
        oldpointsum = self.usedcurve.G * 0
        totalsize = (self.N + 1) * self.Z + len(self.stashpeermap)
        circuittags = self.__generaterandompeertags(self.C)
        xmapsum = [0 for k in range(totalsize)]
        print("location: ", location)
        for i in range(self.C):
            circuitpeers.append(self.peermap[circuittags[i]])
            #oldpointnum = self.usedcurve.G *  self.__generaterandomnumber()
            newpointnum = self.__generaterandompoint()
            oldpointnum = self.__generaterandompoint()
            #newpointnum = self.usedcurve.G * 1
            oldpointsum += oldpointnum
            newpointsum += newpointnum
            oldpointstr = self.convertfrompointtostring(oldpointnum)
            newpointstr = self.convertfrompointtostring(newpointnum)
            oldpoints.append(oldpointstr)
            newpoints.append(newpointstr)
            xmap = []   
            if i != (self.C-1):
                for j in range(totalsize):
                    xnum = self.__generaterandomnumber()
                    #xnum = 1
                    xmap.append(str(xnum))
                    xmapsum[j] += xnum
                    #print("xnum", xnum)
            else:
                for j in range(totalsize):
                    if j != location:
                        xnum = (-xmapsum[j]) % self.usedcurve.n
                        xmap.append(str(xnum))
                    else:
                        xnum = (1 - xmapsum[j]) % self.usedcurve.n
                        xmap.append(str(xnum))
                    #print("xnum", xnum)
            datalist["circuitinfo"][circuitpeers[i]] = [oldpoints[i], newpoints[i], xmap]
        oldsecret = self.secretmap[dataid]

        comparepoint = self.convertfromstringtopoint(oldpoints[-1])
        # print("comparepoint", comparepoint)

        if  self.convertfrompointtostring(comparepoint) != self.convertfrompointtostring(self.neutralpoint):
            tmpnum = (-comparepoint) + oldpointsum 
        else:
            tmpnum = (comparepoint) + oldpointsum 
        #tmpnum = (-tmpnum - oldsecret) % self.usedcurve.n
        print(oldsecret)

        if  self.convertfrompointtostring(tmpnum) == self.convertfrompointtostring(self.neutralpoint):
            tmpnum = tmpnum
        else:
            tmpnum = (-tmpnum)

        if  self.convertfrompointtostring(oldsecret) == self.convertfrompointtostring(self.neutralpoint):
            oldsecret = oldsecret
        else:
            oldsecet = (-oldsecret)
        tmpnum = tmpnum + oldsecret
        datalist["circuitinfo"][circuitpeers[-1]][0] = self.convertfrompointtostring(tmpnum)
        self.secretmap[dataid] = newpointsum #update secretmap
        self.__updatestashpeermap(dataid)
        datalist["eviction"] = None
        self.Acount += 1
        pathtag = ""
        if self.Acount >= self.A:
            pathtag = self.evictionpaths[self.G]
            #self.eviction(pathtag, data)
            datalist["eviction"] = pathtag
            self.G += 1
            if self.G >= len(self.evictionpaths):
                self.G = 0
            self.Acount = 0

        return datalist

    def eviction ( self, pathtag ): 
    #--------------------------------------------------------------------------
        """ Eviction for a path based on pathtag with its data.
        """
        #pathtag: "111"
        #data: peertag --> [data1, data2, ...]
        #resp: peertag --> [data1, data2, ...]
        self.__debug("function eviction pathtag: %s" % pathtag)
        self.__debug("stashmap number before eviction: %s" % len(self.stashmap.keys()))
        #read
        datalist = {}
        oldposition = {} #dataid --> location
        newposition = {} #peertag ---> [dataid, dataid, ...]
        totalsize = (self.N + 1) * self.Z + len(self.stashpeermap)

        #push data in peers on the path to stash
        for i in self.peerdata["R"]:
            if (i != "dummy") and (i in self.positionmap):
                datatag = self.positionmap[i][0]
                self.__updatestashmap(i, datatag)

        for i in range(len(pathtag)):
            peertag = pathtag[:i+1]
            for j in self.peerdata[peertag]:
                if (j != "dummy") and (i in self.positionmap):
                    datatag = self.positionmap[j][0]
                    self.__updatestashmap(j, datatag)

        #record old positions for data in stash
        for i in self.stashmap:
            if i not in self.positionmap:
                oldposition[i] = (self.N + 1) * self.Z + len(self.stashpeermap) - 1 - self.stashpeermap[::-1].index(i) #from the rightmost data
            else:
                if self.positionmap[i][1] == "R":
                    oldposition[i] = self.positionmap[i][2]
                else:
                    oldposition[i] = self.Z * len(self.positionmap[i][1]) + self.positionmap[i][2]
                del self.positionmap[i]

        #set new position for each data, reset positionmap and peerdata
        for i in range(len(pathtag)):
            peertag = pathtag[:len(pathtag)-i]
            newposition[peertag] = []
            count = 0
            self.__resetpeerdata(peertag)
            for j in self.stashmap:
                dataid = j
                if self.stashmap[dataid][:len(peertag)] == peertag:

                    self.positionmap[dataid] = [self.stashmap[dataid], peertag, count]
                    #self.__resetpeerdata(peertag)
                    self.peerdata[peertag][count] = dataid
                    #newposition[dataid] = self.Z * len(peertag) + count
                    newposition[peertag].append(dataid)
                    count += 1
                    if count >= self.Z:
                        break
            for k in range(len(self.peerdata[peertag])):
                if self.peerdata[peertag][k] != "":
                    del self.stashmap[self.peerdata[peertag][k]]
                else:
                    self.peerdata[peertag][k] = "dummy"
                    newposition[peertag].append("dummy")

        count = 0
        newposition["R"] = []
        self.__resetpeerdata("R")
        for i in self.stashmap:
            dataid = i
            self.positionmap[dataid] = [self.stashmap[dataid], "R", count]
            self.peerdata["R"][count] = dataid
            newposition["R"].append(dataid)
            count += 1
            if count >= self.Z:
                break
        for k in range(len(self.peerdata["R"])):
            if self.peerdata["R"][k] != "":
                del self.stashmap[self.peerdata["R"][k]]
            else:
                self.peerdata["R"][k] = "dummy"
                newposition["R"].append("dummy")

        #dataid left in stash
        count = 0
        self.stashpeermap = []
        newposition["stashpeer"] = []
        for i in self.stashmap:
            dataid = i
            #newposition["data"] = (self.N + 1) * self.Z + count
            self.stashpeermap.append(dataid)
            newposition["stashpeer"].append(dataid)
            count += 1
        for i in range(count, (self.N+1)*self.Z):
            self.stashpeermap.append("dummy")
            newposition["stashpeer"].append("dummy")
        #delete stashpeermap

        datalist["pathpeerinfo"] = []
        datalist["pathpeerinfo"].append(self.peermap["R"])
        for i in range(len(pathtag)):
            datalist["pathpeerinfo"].append(self.peermap[pathtag[:i+1]])
        circuitpeers = [] #peers for a circuit
        #oldpoints = [] #points for each circuit peer, use number instead
        newpoints = [] #points for each circuit peer, use number instead
        datalist["circuitinfo"] = {}
        
        #oldpointsum = 0
        
        circuittags = self.__generaterandompeertags(self.C)
        for i in range(self.C):
            circuitpeers.append(self.peermap[circuittags[i]])
            

        for i in range(self.C):
            datalist["circuitinfo"][circuitpeers[i]] = {}
            for k in newposition:
                peertag = k
                datalist["circuitinfo"][circuitpeers[i]][peertag] = []
                #datalist["circuitinfo"][circuitpeers[k]][peertag] = []
                # for m in newposition[peertag]:
                #     dataid = m
                #     datalist["circuitinfo"][circuitpeers[i]][peertag] = []

        for k in newposition:
            peertag = k
            #datalist["circuitinfo"][circuitpeers[k]][peertag] = []
            for m in newposition[peertag]:
                dataid = m
                newpointsum = self.usedcurve.G * 0 #Fixed bug: initiate newpointsum for every dataid, previous this line is before the loop.
                xmapsum = [0 for k in range(totalsize)]
                for i in range(self.C):
                    #circuitpeers.append(self.peermap[self.__generaterandompeertag()])
                    #datalist["circuitinfo"][circuitpeers[i]] = {}
                    #oldpointnum = self.__generaterandomnumber()
                    #newpointnum = self.usedcurve.G * self.__generaterandomnumber()
                    newpointnum = self.__generaterandompoint()
                    #oldpointsum += oldpointnum
                    newpointsum += newpointnum
                    #oldpointstr = str(oldpointnum)
                    newpointstr = self.convertfrompointtostring(newpointnum)
                    #oldpoints.append(oldpointstr)
                    #newpoints.append(newpointstr)
                    xmap = []
                    
                    if i != (self.C-1):
                        for j in range(totalsize):
                            xnum = self.__generaterandomnumber()
                            xmap.append(str(xnum))
                            xmapsum[j] += xnum
                    else:
                        if dataid == "dummy":
                            for j in range(totalsize):
                                xnum = self.__generaterandomnumber()
                                xmap.append(str(xnum))                  
                        else:
                            for j in range(totalsize):
                                if j != oldposition[dataid]:
                                    xnum = (-xmapsum[j]) % self.usedcurve.n
                                    xmap.append(str(xnum))
                                else:
                                    xnum = (1 - xmapsum[j]) % self.usedcurve.n
                                    xmap.append(str(xnum))
                    datalist["circuitinfo"][circuitpeers[i]][peertag].append([newpointstr, xmap])
                if dataid != "dummy":
                    self.secretmap[dataid] = self.secretmap[dataid] + newpointsum
        print("old position:", oldposition)
        print("new position:", newposition)
        return datalist


    def __pushdummytopeer ( self, peertag ):
    #--------------------------------------------------------------------------
        """ Push dummy data in stash to a peer (peertag)
        """
        #Find real data in stash fit for peertag
        print ("function __pushdummytopeer")
        #print peertag
        count = 0
        respdata = [] #[data1, data2, ...]
        respdata = self.__generatedummy(self.Z)
        self.__resetpeerdata(peertag)
        for i in range(self.Z):

            self.peerdata[peertag][i] = "dummy"
        
        self.__debug("push to peertag: %s. dataid %s" % (peertag, self.peerdata[peertag]))
        return respdata

    def __initevictionpaths ( self ):
    #--------------------------------------------------------------------------
        """ Choose a path for eviction based on reverse-lexi order, e.g., 00, 10, 01, 11
        """
        #tags = self.tagmap.keys()
        tags = list(self.tagmap.keys())
        paths = {}
        for i in range(len(tags)):
            paths[tags[i][::-1]] = tags[i]
        reverselexiorderpaths = [paths[i] for i in sorted(paths)]
        return reverselexiorderpaths

    def __resetpeerdata ( self, peertag ):
    #--------------------------------------------------------------------------
        """ Reset peerdata for a peer.
        """
        self.peerdata[peertag] = ["" for i in range(self.Z)]

    def __removepositionmap (self, dataid):
    #--------------------------------------------------------------------------
        """ Remove the item of dataid in positionmap.
        """
        del self.positionmap[dataid]

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

    def __updatestashpeermap (self, dataid):
    #--------------------------------------------------------------------------
        """ dataid stored on stashpeer
        """
        self.stashpeermap.append(dataid)
        #self.__debug(self.stashmap)

    def __removestashpeermap (self, dataid):
    #--------------------------------------------------------------------------
        """ Remove a dataid/datatag mapping.
        """
        self.stashpeermap.remove(dataid)

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
            print (msg)

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

    def __init_randompoints( self, number ):
        """ Pre-generate random points
        """
        #initiation for peermap
        #for fast, in reality using self.usedcurve.G * random.randrange(0, self.usedcurve.n)
        #point = self.neutralpoint
        point = self.usedcurve.G * random.randrange(0, self.usedcurve.n)
        pointslist = []
        for i in range(number):
            #pointslist.append(self.usedcurve.G * random.randrange(0, self.usedcurve.n))
            #pointslist.append(self.neutralpoint)
            
            pointslist.append(point)
        print("__init_randompoints finished.")
        return pointslist

    def __generaterandompoint( self ):
        """ Get a random point
        """
        
        index = random.randrange(0, self.prerandompointsnum)
        return self.randompoints[index]
    


    def __init_tagmap( self, number):
    #--------------------------------------------------------------------------
        """ Generate bits as keys for tagmap
        """
        #initiation for tagmap
        for j in itertools.product( '01', repeat=number ):
            bits = ''.join(j)
            self.tagmap[bits] = 0
        #print self.tagmap

    def __generaterandomtag ( self ):
    #--------------------------------------------------------------------------
        """ Generate a random tag for real data not dummy data
        """
        #Generate a random tag for real data not dummy data
        tags = []
        for i in self.tagmap:
            tags.append(i)
            #if self.tagmap[i] < self.Z:
            #    tags.append(i)
        if len(tags) == 0:
            return None
        return generaterandomchoice(tags)

    def __generaterandomnumber( self ):
    #--------------------------------------------------------------------------
        """ Generate a random number based on self.usedcurve
        """
        return random.randrange(0, self.usedcurve.n)
        #return random.randrange(1, self.usedcurve.n)
        #return random.randrange(0, 1)
        #return 1

    def generaterandomnumber( self ):
    #--------------------------------------------------------------------------
        """ Generate a random number based on self.usedcurve
        """
        #return random.randrange(0, self.usedcurve.n)
        #return random.randrange(1, self.usedcurve.n)
        return self.__generaterandomnumber()

    def __generaterandompeertag ( self ):
    #--------------------------------------------------------------------------
        """ Generate random peers for a circuit
        """
        tags = []
        for i in self.peermap:
            tags.append(i)
        if len(tags) == 0:
            return None
        return generaterandomchoice(tags)

    def __generaterandompeertags ( self, number ):
    #--------------------------------------------------------------------------
        """ Generate random peers for a circuit
        """
        tags = []
        data = []
        for i in self.peermap:
            tags.append(i)
        if len(tags) == 0:
            return None
        for i in range(number):
            tag = generaterandomchoice(tags)
            data.append(tag)
            tags.remove(tag)
        return data


    def __generatedummy( self, number ):
    #--------------------------------------------------------------------------
        """ Generate a dummy data list based on number
        """
        data = []
        start_time1 = time.time()
        #baserandompoint = self.usedcurve.G * self.__generaterandomnumber()
        #baserandompoint = self.usedcurve.G
        for i in range(number):
            #start_time = time.time()
            #onepoint = baserandompoint
            start_time = time.time()
            #onepoint = self.usedcurve.G * self.__generaterandomnumber()
            onepoint = self.__generaterandompoint()
            #print("--- %s seconds ---" % (time.time() - start_time))
            #oneblock = str(self.__generaterandomnumber())
            oneblock = self.convertfrompointtostring(onepoint)
            for j in range(1, self.pointsnum):
                #onepoint = self.usedcurve.G * self.__generaterandomnumber()
                onepoint = self.__generaterandompoint()
                oneblock = oneblock + "|" + self.convertfrompointtostring(onepoint)
            data.append(oneblock)
        #self.__debug(data)
        print("--- %s seconds ---" % (time.time() - start_time1))
        return data

    def convertfrompointtostring( self, point ):
    #--------------------------------------------------------------------------
        """ Convert from a point to a string
        """
        return str(point.compress())

    def convertfromstringtopoint( self, str ):
    #--------------------------------------------------------------------------
        """ Convert from a string to a point
        """
        px = str.split(", ")[0][1:]
        py = str.split(", ")[1][:-1]
        ptuple = (int(px), int(py))
        return self.usedcurve.uncompress(ptuple)

    def convertfrompointlisttostring( self, pointlist ):
    #--------------------------------------------------------------------------
        """ Convert from a point list to a string (16 points * 4) 
        [[p1, p2, ...],[p3, p4, ...], ...]
        """

        data = []
        start_time1 = time.time()
        for i in pointlist:
            pointstr = []
            for j in i:
                pointstr.append(self.convertfrompointtostring(j))
            data.append("|".join(pointstr))
        print("--- Convert pointlist to string %s seconds ---" % (time.time() - start_time1))
        return ">>>".join(data)

    #--------------------------------------------------------------------------
    def convertfrompointliststringtostring( self, pointliststring ):
    #--------------------------------------------------------------------------
        """ Convert from a point list to a string (16 points * 4)
        """
        return ">>>".join(pointliststring)


    def convertfromstringtopointlist( self, str ):
    #--------------------------------------------------------------------------
        """ Convert from a string to a point list (16 points * 4)
        """
        data = []
        start_time1 = time.time()
        pointsstr = str.split(">>>")
        for i in pointsstr:
            pointstr = i.split("|")
            pointlist = []
            for j in pointstr:
                pointlist.append(self.convertfromstringtopoint(j))
            data.append(pointlist)
        print("--- Convert string to pointlist %s seconds ---" % (time.time() - start_time1))
        return data
