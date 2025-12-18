#!/bin/bash

input_dir="$1"
if [ -z "$input_dir" ] ; then
    echo "please provide path to images to be checked"
    exit 1
fi

# default to 1 thread if not provided
numthreads="${2:-1}"

output_file="${input_dir}/corrupted_jpgs_summary.txt"

# check jpg images for corruption
find -L "$input_dir" -name '*.jpg' -type f |
    xargs -P $numthreads -I % sh -c '
        (identify -regard-warnings -verbose "%" >/dev/null 2>&1 && echo "% 0") || echo "% 1"
    ' | tee "$output_file"
