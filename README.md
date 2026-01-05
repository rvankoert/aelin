# Aelin

## Overview
Aelin is a collection of various scripts/tools which can be used for various purposes. Use at your own risk. 

## Tools
| Tool | Description | Status |
| --- | --- | --- |
| Check | checks corrupted jpgs | Complete |
| Convert | converts jp2 to jpeg | To be documented and tested |
| Image Analysis | identifies dimensions of primary subject within each image | To be documented and tested |
| Text | finds ngrams | To be documented and tested |

## Tool Documentation

### Check

#### Description
This contains two checkers for corrupted jpgs in a given directory, a single-threaded one and a multi-threaded one.

#### Usage
```bash
./check/find-corrupted-jpg.sh /PATH/TO/IMAGES
./check/find-corrupted-multithreaded.sh /PATH/TO/IMAGES NUM_THREADS [OUTPUT_FILE]
```

### Convert
Documentation coming soon

### Image Analysis
Documentation coming soon

### Text
Documentation coming soon

## Automated Tests
Tests are located in the `tests` folder:

```bash
# example for the two checkers
bats find-corrupted-jpg.bats
bats find-corrupted-multithreaded.bats
