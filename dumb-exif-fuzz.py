#!/usr/bin/env python3

import argparse
import base64
import os
import random
import sys
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

# Read bytes from a JPEG and return them in a mutable bytearray 
def get_bytes(filename: str) -> bytearray:
	f = open(filename, "rb").read()
	return bytearray(f)

# Reads a file or directory of files and returns a list of bytearrays to represent the corpus
def get_corpus(path: str) -> list[bytearray]:
	corpus = []
	if os.path.isfile(path):
		corpus.append(get_bytes(path))
	elif os.path.isdir(path):
		for file in os.listdir(path):
			if os.path.isfile(file):
				corpus.append(get_bytes(file))
	return corpus

# Writes new data to mutation file
def create_new(data: bytearray) -> None:
	f = open("mutated.jpg", "wb+")
	f.write(data)
	f.close()

# Takes a bit and flips it
def flip_bit(byte: bytes) -> bytes:
	return byte ^ random.choice([1, 2, 4, 8, 16, 32, 64, 128])

# Takes a byte and returns a random byte
def flip_byte(byte: bytes) -> bytes:
	return random.getrandbits(8)

# Takes a byte at an index and replaces it (and any neccessary following bytes) with a random magic byte	
def magic(data: bytearray, idx: int) -> None:
	chosen_magic = random.choice(MAGIC_VALS)
	# TODO: Add guard clause to prevent going over/under buffer size
	# print(f"Flipping value {data[idx]} at index {idx} to magic value: {chosen_magic}")
	offset = 0
	for byte in chosen_magic:
		data[idx + offset] = byte
		offset += 1

# Mutation function
def mutate(data: bytearray) -> bytearray:
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

# Runs the target exif program and saves crashes
def exif(data: bytearray, count: int) -> None:
	p = Popen(["exif", "mutated.jpg", "-verbose"], stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	if p.returncode == -11:
		with open(f"crashes/crash_{count}.jpg", "wb+") as f:
			f.write(data)

# Fuzz loop
def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-c', '--corpus', help="Target JPEG or directory containing target JPEGs", required=True)
	parser.add_argument('-r', '--rounds', help="Number of rounds to run", default=500)
	parser.add_argument('-s', '--seed', help="PRNG seed")
	args = parser.parse_args()
	corpus = get_corpus(args.corpus)
	
	if args.seed:
		start_seed = base64.b64decode(args.seed)
	else:
		start_seed = os.urandom(24)
		
	random.seed(start_seed)
	print("Starting new run with seed {}".format(base64.b64encode(start_seed).decode('utf-8')))	
		
	for file in corpus:
		count = 0
		while count < args.rounds:
			data = file[:]
			mutated_data = mutate(data)
			create_new(mutated_data)
			exif(mutated_data, count)
			count += 1

if __name__ == "__main__":
    main()




