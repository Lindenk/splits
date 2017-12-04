#!/usr/bin/env python3

# File layout is saved as such:
# {
#   "required_peices": <int>,
#   "chunks": [{
#     "group": <int>,
#     "chunk": <int>,
#     "phrase": <str>,
#     "data": <bytes>
#   }]
# }

import argparse, sys, random, string, math, pickle
from simplecrypt import encrypt, decrypt
from multiprocessing import Pool
from itertools import combinations
from functools import partial, reduce


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
    type=argparse.FileType('rb'),
    nargs="+")
  merge_parser.add_argument("-o", "--output",
    help="File name to output as",
    type=argparse.FileType('wb'),
    required=True)

  settings = parser.parse_args(args=args)
  
  if settings.command == "split" and settings.required_peices == None:
    settings.required_peices = settings.num_peices

  return settings



### Splitting functions ###

# "abcdefg", 2 -> ["ab", "cd", "ef", "g"]
def split(data, n):
  return [data[i:i+n] for i in range(0, len(data), n)]

# Encrypts data and splits it into n chunks along with part of the passphrase used for encryption
# with each chunk
def generate_group(data, n):
  passphrase = "".join([random.choice(string.printable) for _ in range(1024)])
  enc_file = encrypt(passphrase, data)

  data_peices = split(enc_file, math.ceil(len(enc_file) / n))

  # break up the passphrase evenly between the chunks
  passphrase_peices = split(passphrase, math.ceil(len(passphrase) / n))

  return [
    {"chunk": i, "phrase": p, "data": c} 
      for (i, (p, c)) in enumerate(zip(passphrase_peices, data_peices))]

# Creates a group and assigns each peice as the value to keys in iter
# Iter should contain the file number that will contain the chunk
def assign_chunks(data, iter):
  group = generate_group(data, len(iter))
  return {x: group[i] for (i, x) in enumerate(iter)}

# Split command entry point
def split_file(name, data, num_peices, req_peices):
  # generate (n C r) groups with r peices each
  # generate a pair for every combo of files
  print("Generating unique file groups...")
  with Pool() as p:
    file_data = p.map(
      partial(assign_chunks, data), 
      combinations(range(num_peices), req_peices))
  
  # number them
  for (i, f) in enumerate(file_data):
    for v in f.values():
      v["group"] = i

  # flatten array of results to a single object with file_no -> [chunks] pairs
  def flatten_to_files(obj, chunks):
    for (k, v) in chunks.items():
      if k not in obj:
        obj[k] = []
      obj[k].append(v)
    return obj

  files = reduce(flatten_to_files, file_data, {})

  # Save each peice
  print("Saving files...")
  for (i, p) in enumerate(files.values()):
    with open(name + "." + str(i), "wb") as f:
      f.write(pickle.dumps({
        "required_peices": req_peices,
        "chunks": p
      }))


### Merging Functions ###

# Merges and decrypts chunks 
def merge(chunks):
  passphrase = ""
  data = b''

  for i in range(len(chunks)):
    c = chunks[i]
    passphrase += c["phrase"]
    data += c["data"]

  return decrypt(passphrase, data)

# Merge command entry point
def merge_file(files, output):
  try:
    data = [pickle.loads(f.read()) for f in files]
  except Exception as e:
    print("Failed to load files: %s" % e)
    sys.exit(1)

  required_chunks = data[0]["required_peices"]

  # Make sure we have enough
  if len(data) < required_chunks:
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

  full_groups = list(filter(
    lambda chunks: len(chunks) == required_chunks, 
    [chunks for chunks in groups.values()]))

  if len(full_groups) > 0:
    print("Found a full group! Merging...")
    output.write(merge(full_groups[0]))
  else:
    print("No full groups found! Aborting...")
    sys.exit(1)

def main():
  settings = parse_args(sys.argv[1:])

  if settings.command == "split":
    data = settings.file.read()
    split_file(settings.file.name, data, settings.num_peices, settings.required_peices)
  elif settings.command == "merge":
    merge_file(settings.files, settings.output)
  

if __name__ == "__main__":
  main()