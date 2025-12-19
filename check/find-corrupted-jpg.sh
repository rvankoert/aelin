#!/bin/bash
# find-corrupted-jpg.sh
# Description: checks all jpg images in the given directory for corruption single-threadedly
# Usage: ./find-corrupted-jpg.sh /PATH/TO/IMAGES
# Expected output: 0 for valid images, 1 for corrupted ones, other numbers for errors
# Dependencies: ImageMagick

if [ -z "$1" ]; then 
    echo "please provide path to images to be checked"
    exit 1
fi

# check jpg images for corruption. Only use one process at a time to avoid race conditions in the output
find -L "$1" -name '*.jpg' -type f |
    xargs -P 1 -I % sh -c '
        identify -regard-warnings -verbose % > /dev/null 2>&1
        echo % $?
    '
