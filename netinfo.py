#!/usr/bin/env python3

import sys
import urllib.request
from bs4 import BeautifulSoup

import netinfo
import userauth

def read_known_dev():
	"Reads the list of known devices from file and returns a dictionary keyed by MAC addresses"
	known_devices = {}
	file = open("known_devices", "r")
	for l in file:
		pair = l.rstrip().split('|')
		if (len(pair) != 2):
			print("Malformed known_devices file")
		else:
			known_devices[pair[0].rstrip()] = pair[1].lstrip()
	file.close()	
	return known_devices	

def init_url_opener():
	top_lvl_url = "http://192.168.1.254"
	username = userauth.USERNAME
	password = userauth.PASSWORD

	password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
	password_mgr.add_password(None, top_lvl_url, username, password)
	
	# Create a request handler with our password
	handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
	
	# Create a URL opener
	opener = urllib.request.build_opener(handler)

	# Attach our opener as the default one
	urllib.request.install_opener(opener)

def get_url_data(url):
	response = urllib.request.urlopen(url)
	return response.read()

def users(known_devices):
	"Print a list of online users and their IP addresses"
	ip_table = get_url_data('http://192.168.1.254/status/arp.html')
	soup = BeautifulSoup(ip_table)
	print(soup.prettify())

def known(known_devices):
	"Print a list of known devices"
	for mac in known_devices:
		print("%s %s" % (mac, known_devices[mac]))

def add(known_devices):
	mac = input("MAC address: ") 
	# TODO: check it's a valid mac
	desc = input("Description: ")

	# Write to file
	file = open("known_devices", "a")
	string = "%s | %s\n" % (mac, desc)
	file.write(string)
	file.close()

def help(null):
	print("Usage: netinfo [known|add|users]")

def run(fname):
	function = getattr(netinfo, fname, netinfo.help)
	function(known_devices)

if __name__ == "__main__":
	# Run the given command, or display usage information if none is given
	if (len(sys.argv) > 1):
		# Initial setup
		known_devices = read_known_dev()
		init_url_opener()

		command = sys.argv[1]
		run(command)
	else:
		help(None)
