#!/usr/bin/env python3

import argparse, sys, random, string, math, pickle
from simplecrypt import encrypt, decrypt
from collections import deque


# Utility functions
# "abcdefg", 2 -> ["ab", "cd", "ef", "g"]
def split(data, n):
  return [data[i:i+n] for i in range(0, len(data), n)]

# [[1,2,3], [4,5,6], [7,8,9]] -> [[1,4,7], [2,5,8], [3,6,9]]
def transpose(L):
  return [[L[j][i] for j in range(len(L))] for i in range(len(L[0]))]


# Program functions
def parse_args(args):
  parser = argparse.ArgumentParser(
    prog="splits",
    description="Splits a file into n peices requiring r of them to reconstruct the original.")
  
  subparsers = parser.add_subparsers(dest="command")
  subparsers.required = True
  split_parser = subparsers.add_parser("split",
    help="Splits a file")
  merge_parser = subparsers.add_parser("merge",
    help="Merges a set of files")
  
  # Split
  split_parser.add_argument("file", 
    help="File to be split",
    type=argparse.FileType('rb'))
  split_parser.add_argument("-n", "--num-peices", 
    help="Number of peices file will be split into", 
    type=int, 
    required=True)
  split_parser.add_argument("-r", "--required-peices",
    help="Number of peices required to reconstruct the original",
    type=int)
  
  # Merge
  merge_parser.add_argument("files",
    help="Files to merge",
    type=argparse.FileType('r'),
    nargs="+")
  merge_parser.add_argument("-o", "--output",
    help="File name to output as",
    type=argparse.FileType('wb'),
    required=True)

  settings = parser.parse_args(args=args)
  
  if settings.command == "split" and settings.required_peices == None:
    settings.required_peices = settings.num_peices

  return settings

# Encrypts data and splits it into n chunks along with part of the passphrase used for encryption
# with each chunk
def split_into_group(data, n):
  passphrase = "".join([random.choice(string.printable) for _ in range(1024)])
  enc_file = encrypt(passphrase, data)

  data_peices = split(enc_file, math.ceil(len(enc_file) / n))

  # break up the passphrase evenly between the chunks
  passphrase_peices = split(passphrase, math.ceil(len(passphrase) / n))

  return [
    {"chunk": i, "phrase": p, "data": c} 
      for (i, (p, c)) in enumerate(zip(passphrase_peices, data_peices))]

# Takes a list of lists and returns a list of lists such that no list contains more
# than one element originally from any other list
def distribute_peices(groups):
  groups = transpose(groups)
  result = []
  for (i, g) in enumerate(groups):
    g = deque(g)
    g.rotate(i)
    result.append(list(g))
  return transpose(result)

def split_file(name, data, num_peices, req_peices):
  # generate n groups with r peices each
  groups = [{**split_into_group(data, req_peices), "group": i} for i in range(num_peices)]  
  
  #distribute peices into files
  distributed_peices = distribute_peices(groups)

  # Save each peice
  for (i, p) in enumerate(distributed_peices):
    with open(name + "." + str(i), "wb") as f:
      f.write(pickle.dumps({
        "required_peices": req_peices,
        "chunks": p
      }))

def merge(chunks):
  passphrase = ""
  data = b''

  for i in range(len(chunks)):
    c = chunks[i]
    passphrase += c["phrase"]
    data += c["data"]

  return decrypt(passphrase, data)


def merge_file(files, output):
  try:
    data = [pickle.loads(f.read()) for f in files]
  except Exception as e:
    print("Failed to load files: %s" % e)
    sys.exit(1)

  required_chunks = data[0]["required_peices"]

  if required_chunks < len(data):
    print("Found %s out of %s chunks. Aborting..." % (len(data), required_chunks))
    sys.exit(1)

  # See if we can find a full group
  groups = {}
  for d in data:
    for c in d["chunks"]:
      group = c["group"]

      if group not in groups:
        groups[group] = {}
      groups[group][c["chunk"]] = c

  full_groups = filter(
    lambda chunks: len(chunks) == required_chunks, 
    [chunks for chunks in groups.values()])

  if full_groups > 0:
    print("Found a full group")
    output.write(merge(full_groups[0]))

def main():
  settings = parse_args(sys.argv[1:])

  if settings.command == "split":
    data = settings.file.read()
    split_file(settings.file.name, data, settings.num_peices, settings.required_peices)
  elif settings.command == "merge":
    merge_file(settings.files, settings.output)
  

if __name__ == "__main__":
  main()