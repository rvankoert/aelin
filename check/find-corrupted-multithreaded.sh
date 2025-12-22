#!/bin/bash
# find-corrupted-multithreaded.sh
# Description: checks all jpg images in the given directory and its subdirectories for corruption using multiple threads
# Usage: ./find-corrupted-multithreaded.sh /PATH/TO/IMAGES NUM_THREADS [OUTPUT_FILE]
# Warning: all input paths are considered to be without special characters like spaces. This script is provided as is and won't work with paths with special characters.
# Expected output: a summary file listing check results, by default named corrupted_jpgs_summary.txt in the input directory. Use the optional [OUTPUT_FILE] argument to specify a different output file.
# Dependencies: ImageMagick, find-corrupted-jpg.sh

input_dir="$1"
numthreads="$2"
if [ -z "$input_dir" ] || [ -z "$numthreads" ]; then
    echo "Usage: $0 /PATH/TO/IMAGES NUM_THREADS"
    exit 1
fi

dirs=$(find "$input_dir" -type d -mindepth 1)
# use xargs
echo "$dirs" |
    xargs -I {} -P $numthreads bash -c '
    ./find-corrupted-jpg.sh "{}" > "{}"/corrupted_jpgs.txt
    '
    
# summarize results into one file
output_file="$input_dir/corrupted_jpgs_summary.txt"
if [ -n "$3" ]; then
  output_file="$3"
  echo "Setting output_file=$3"
fi
echo "" > "$output_file"  # clear output file
for dir in $dirs; do
    corrupted_file="${dir}/corrupted_jpgs.txt"
    if [ -f "$corrupted_file" ]; then
        echo "Directory: $dir" >> "$output_file"
        cat "$corrupted_file" >> "$output_file"
        echo -e "\n" >> "$output_file"
    fi
done
