#!/usr/bin/env bash

dir="${1%/}"
files=("mp3")

for ext in "${files[@]}"; do
  for file in "${dir}"*.${ext}; do
    [ -e "${file}" ] || continue

    name="${file%.*}"

    if ffmpeg -i "${file}" -c:a libvorbis "${name}.ogg"; then
      rm "${file}"
    fi
  done
done
