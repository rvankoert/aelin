#!/bin/bash

#change to the directory where the images are stored
dir=CHANGE_TO_INPUT_DIRECTORY/
# number of threads should be paramaterize
#


>/tmp/toconvert2jp2.txt
for file in `find $dir -name '*.jp2'` ; do
  base=${file%%.*}
  echo $base
  if [ ! -f $base.jpg ]; then
    echo "File not found! " $base.jpg
    echo $file >> /tmp/toconvert2jp2.txt
  fi
done

cat /tmp/toconvert2jp2.txt | xargs -n1 -P16 -I{} magick {} {}.jpg

for file in `find $dir -name '*.jp2.jpg'`; do
  mv "$file" "${file%jp2\.jpg}jpg"; 
done

