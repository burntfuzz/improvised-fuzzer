#!/usr/bin/env python3

import sys
import random
from subprocess import Popen, PIPE

FLIP_RATIO = 0.01
MAGIC_VALS = [
  [0xFF],
  [0x7F],
  [0x00],
  [0xFF, 0xFF], # 0xFFFF
  [0x00, 0x00], # 0x0000
  [0xFF, 0xFF, 0xFF, 0xFF], # 0xFFFFFFFF
  [0x00, 0x00, 0x00, 0x00], # 0x80000000
  [0x00, 0x00, 0x00, 0x80], # 0x80000000
  [0x00, 0x00, 0x00, 0x40], # 0x40000000
  [0xFF, 0xFF, 0xFF, 0x7F], # 0x7FFFFFFF
]

# read bytes from our valid JPEG and return them in a mutable bytearray 
def get_bytes(filename):
	f = open(filename, "rb").read()
	return bytearray(f)

def create_new(data):
	f = open("mutated.jpg", "wb+")
	f.write(data)
	f.close()

def flip_bit(byte):
	return byte ^ random.choice([1, 2, 4, 8, 16, 32, 64, 128])

def flip_byte(byte):
	return random.getrandbits(8)
	
def magic(data, idx):
	chosen_magic = random.choice(MAGIC_VALS)
	# TODO: Add guard clause to prevent going over/under buffer size
	#print(f"Flipping value {data[idx]} at index {idx} to magic value: {chosen_magic}")
	offset = 0
	for byte in chosen_magic:
		data[idx + offset] = byte
		offset += 1

def mutate(data):
	num_flips = int((len(data) - 4) * FLIP_RATIO)
	possible_indices = range(4, len(data) - 4) # Exclude SOI and EOI markers
	chosen_indices = random.choices(possible_indices, k=num_flips)
	methods = [0,1]
	
	for i in chosen_indices:
		method = random.choice(methods)
		if method == 0:
				new_bit = flip_bit(data[i])
				#print(f"Flipping value {data[i]} at index {i} to new value: {new_bit}")
				data[i] = new_bit
		else:
			magic(data,i)
	
	return data
	
def exif(data):
	p = Popen(["exif", "mutated.jpg", "-verbose"], stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	if p.returncode == -11:
		with open(f"crashes/crash_{count}.jpg", "wb+") as f:
			f.write(data)

if len(sys.argv) < 2:
	print("[+] Usage: dumbfuzz.py <valid_jpg>")
	exit()
	
filename = sys.argv[1]

count = 0
while count < 1000:
	data = get_bytes(filename)
	mutated_data = mutate(data)
	create_new(mutated_data)
	exif(mutated_data)
	count += 1





