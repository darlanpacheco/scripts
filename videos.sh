#!/usr/bin/env bash

cmd="${1}"

if [ -z "${cmd}" ]; then
	exit 1
fi

if [ "${cmd}" = "encode" ]; then
	dir="${2%/}"
	dest="${3%/}"
	file_track="${4}"
	audio_track="${5}"
	subtitle_track="${6}"
	subtitle_encoding="${7}"

	for file in "${dir}"/*.mkv; do
		[ -e "${file}" ] || continue

		crf=0
		height=$(ffprobe -v error -select_streams v:0 \
			-show_entries stream=height \
			-of default=noprint_wrappers=1:nokey=1 \
			"${file}")

		if [[ "${height}" == 480 ]]; then
			crf=22
		elif [[ "${height}" == 720 ]]; then
			crf=26
		elif [[ "${height}" == 1080 ]]; then
			crf=32
		fi

		if [[ "${crf}" -lt 0 ]]; then
			continue
		fi

		filename=$(basename -- "${file}")
		filename_no_ext="${filename%.*}"

		ffmpeg -i "${file}" \
			-map_metadata -1 -map_chapters -1 \
			-map 0:v:"${file_track}"? \
			-map 0:a:"${audio_track}"? \
			-map 0:s:"${subtitle_track}"? \
			-c:v libx265 -preset ultrafast -pix_fmt yuv420p -crf "${crf}" \
			-c:a libopus -b:a 64k \
			-c:s "${subtitle_encoding}" \
			"${dest}/${filename_no_ext}.mkv"
	done
elif [ "${cmd}" = "rename" ]; then
	dir="${2%/}"
	file_name="${3}"

	for file in "${dir}"/*.mkv; do
		ep=$(echo "${file}" | grep -oP ' - \K\d+')
		ep_fmt=$(printf "%03d" $((10#$ep)))

		file_name_new="${dir}/${file_name}-${ep_fmt}.mkv"

		mv -n "${file}" "${file_name_new}"
		mkvpropedit "${file_name_new}" --edit info --set title="$(basename "${file_name_new}")"
	done
fi
