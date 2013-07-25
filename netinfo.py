#!/usr/bin/env python3

import sys
import os.path
import re
import urllib.request
from bs4 import BeautifulSoup

import userauth

# ----------------------- #
# ~~ Globals/constants ~~ #
# ----------------------- #

CONFIG_DIR = os.path.expanduser("~/.config/netinfo/")
MAC_REGEX = r"([0-9a-f]{2}:){5}[0-9a-f]{2}$"

# ----------------------- #
# ~~ Backend functions ~~ #
# ----------------------- #

def init_config_file():
	"Create the config folder if it doesn't already exist"
	
	if not os.path.isdir(CONFIG_DIR):
		print("First run, creating config dir in ~/.config/netinfo")
		os.makedirs(CONFIG_DIR)

def read_known_dev():
	"Reads the list of known devices from file and returns a dictionary keyed by MAC addresses"
	known_devices = {}
	
	path = CONFIG_DIR + "known_devices"

	if (os.path.isfile(path)):
		file = open(path, "r")
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

def parse_online_device_html(html_device_list):
	"""Convert a list of appropriately formatted table rows to a dictionary
	of IPs keyed by MAC addresses"""
	online_devices = {}

	for device in html_device_list:
		info = device.findAll("td")
		ip = info[0].string
		mac = info[1].string.lower()
		online_devices[mac] = ip

	return online_devices

def print_online_dev(online_devices, known_devices, header=""):
	if (len(online_devices) == 0):
		return

	print(header, end="")
	
	for mac in online_devices:
		name = mac
		if mac in known_devices:
			name = known_devices[mac]
		print("%s @ %s" % (name, online_devices[mac]))

# ------------------------------------ #
# ~~ Commandline callable functions ~~ #
# ------------------------------------ #

def users(known_devices):
	"Print a list of online users and their IP addresses"
	
	# Download data
	ip_table = get_url_data('http://192.168.1.254/status/arp.html')
	
	# ~~ Extract the device info from the HTML ~~ #
	
	soup = BeautifulSoup(ip_table)

	# Get the two 'Wired' and 'Wireless' html tables
	tables = soup.findAll("table", "cfgframe")
	if (len(tables) != 2):
		print("Error parsing ARP table")
		return
	wired = tables[0];
	wired = wired.findAll("tr")
	wireless = tables[1];
	wireless = wireless.findAll("tr")
	del tables

	# Parse the lists of online devices (skip the styling rows)
	e_online = parse_online_device_html(wired[2:])
	w_online = parse_online_device_html(wireless[2:])

	# Print results
	print_online_dev(e_online, known_devices, "~ Wired Devices ~\n")
	print_online_dev(w_online, known_devices, "~ Wireless Devices ~\n")

def known(known_devices):
	"Print a list of known devices"
	for mac in known_devices:
		print("%s %s" % (mac, known_devices[mac]))

def add(known_devices):
	"Add a device to the list of known devices"

	mac = input("MAC address: ").lower()
	
	# Check it's a valid MAC address
	valid_mac = re.match(MAC_REGEX, mac)
	if not valid_mac:
		print("That MAC address is invalid! Cease this assault to decency at once!")
		return

	# Check that the MAC address hasn't already been used
	if mac in known_devices:
		print("WARNING: A device called `%s` exists for that MAC address" % (known_devices[mac],))
		response = input("Overwrite? [y/N] ").lower()
		if response in ("no", "n", ""):
			print("Not overwritten.")
			return

	desc = input("Description: ")

	# Write to file
	file = open(CONFIG_DIR + "known_devices", "a")
	string = "%s | %s\n" % (mac, desc)
	file.write(string)
	file.close()

def help(null):
	"Display usage information"
	print("Usage: netinfo [known|add|users]")

def run(fname):
	"Run a function from a string function name"
	this_module = sys.modules[__name__]
	function = getattr(this_module, fname, this_module.help)
	function(known_devices)

if __name__ == "__main__":
	init_config_file()

	# Run the given command, or display usage information if none is given
	if (len(sys.argv) > 1):
		# Initial setup
		known_devices = read_known_dev()
		init_url_opener()

		command = sys.argv[1]
		run(command)
	else:
		help(None)
