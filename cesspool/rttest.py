#!/usr/bin/python

import pool
import time

p=pool.Pool()

def do(cmd):
	print p.doCommand(cmd)

def spin(cmd,secs,freq): 
	for i in range(secs*freq): 
		do(cmd)
		time.sleep(1.0/freq)

do({'cmd':'add','args':{'type':'torrent','args':{'url':'magnet:?xt=urn:btih:0d067e6a15a75fa1d562a78c3409d20907488fcb&dn=Die+Hard+%5B1988%5D+DvdRip+%5BEng%5D+-+Thizz&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Ftracker.ccc.de%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337'}}})
spin({'cmd':'pool'},15,2)
do({'cmd':'rm','args':{'uid':0}})
spin({'cmd':'pool'},3,2)
