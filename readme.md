# Splits #

`splits` is a cli tool for splitting files into peices such that any n peices can be reassembled into the original file. Ideally this is for hiding sensitive information between several locations where not all may be accessable. This program is rather inefficiant for large files because of the amount of extra data stored at each location. As a recommendation, any split file should be encrypted beforehand to prevent parts from having any meaning on their own.

## Usage ##

### General usage ###

```
usage: splits [-h] {split,merge} ...

Splits a file into n peices requiring r of them to reconstruct the original.

positional arguments:
  {split,merge}
    split        Splits a file
    merge        Merges a set of files

optional arguments:
  -h, --help     show this help message and exit
```

### Split ###

```
usage: splits split [-h] -n NUM_PEICES [-r REQUIRED_PEICES] file

positional arguments:
  file                  File to be split

optional arguments:
  -h, --help            show this help message and exit
  -n NUM_PEICES, --num-peices NUM_PEICES
                        Number of peices file will be split into
  -r REQUIRED_PEICES, --required-peices REQUIRED_PEICES
                        Number of peices required to reconstruct the original
```

### Merge ###

```
usage: splits merge [-h] -o OUTPUT files [files ...]

positional arguments:
  files                 Files to merge

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        File name to output as
```