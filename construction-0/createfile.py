#!/usr/bin/python

import sys

N = int(sys.argv[1])

infile = open('dummy.txt', 'r')
indata = infile.read()
infile.close()

outdata = ""
for i in range(N):
	outdata += indata

outfilename = "dummy" + str(N) + ".txt"
outfile = open(outfilename, "w")
outfile.write(outdata)
outfile.close()