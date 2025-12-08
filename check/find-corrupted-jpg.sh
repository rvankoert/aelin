#!/bin/bash

numcores=$(nproc --all)
numcores=1
if [ -z "$1" ]; then echo "please provide path to images to be checked" && exit 1; fi;

find -L $1 -name '*.jpg' -type f| xargs -n 1 -P $numcores -I % sh -c 'identify -regard-warnings -verbose % > /dev/null 2>&1;echo % $?'
