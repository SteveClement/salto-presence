#!/usr/bin/env bash
# This script is used to make web sized versions out of huge images. (eg >4000px)
SAVEIFS=$IFS 
IFS=$(echo -en "\n\b")
for a in $(ls| grep -v webize); do
  cd $a
  magick mogrify -resize 15% -format jpeg -sampling-factor 4:2:0 -strip -quality 75 -interlace JPEG -colorspace sRGB pic.jpg && mv pic.jpeg pic_web.jpg && cd ../
done
IFS=$SAVEIFS
