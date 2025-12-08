#!/bin/bash

input_dir=CHANGE_TO_INPUT_DIRECTORY/
output_dir=/data/thumbnails/


find $input_dir -maxdepth 1 -type d|xargs -n 1 -P8 -I{} mkdir -p $output_dir/{}

find $input_dir -name '*.jp2'|xargs -n 1 -P 4 -I{} bash -c "if [ ! -f $output_dir/{}.thumbnail.jpg ]; then echo File not found; convert {} -resize 1000x1000 -strip -interlace Plane -gaussian-blur 0.05 -quality 85% $output_dir/{}.thumbnail.jpg; fi "

