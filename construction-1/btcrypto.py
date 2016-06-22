import base64
import os
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Random import random
from random import shuffle

class AESCipher:
    
    def __init__( self, key ):
        self.key = key
        self.BS = 16
        self.pad = lambda s: s + (self.BS - len(s) % self.BS) * chr(self.BS - len(s) % self.BS) 
        self.unpad = lambda s : s[:-ord(s[len(s)-1:])]

    def encrypt( self, raw ):
        raw = self.pad(raw)
        #print AES.block_size
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) ) 

    def decrypt( self, enc ):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return self.unpad(cipher.decrypt( enc[16:] ))

def generateKey( size ):
    return Random.new().read(size)

def generaterandomchoice( choicelist ):
    return random.choice(choicelist)

