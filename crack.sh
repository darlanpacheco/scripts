#!/usr/bin/env bash

game_dir="${1%/}"
find_script="${2%/}"
settings_dir="${3%/}"
new_api_32="${4%/}"
new_api_64="${5%/}"

found_api_32=$(find "${game_dir}" -type f -iname "steam_api.dll")
found_api_64=$(find "${game_dir}" -type f -iname "steam_api64.dll")

if [ -n "${found_api_32}" ]; then
	orig_dir=$(dirname "${found_api_32}")
	echo "found 32-bit at: ${orig_dir}"

	echo "generating steam_interfaces.txt..."
	bash "${find_script}" "${found_api_32}" >"${game_dir}/steam_interfaces.txt"
	bash "${find_script}" "${found_api_32}" >"${orig_dir}/steam_interfaces.txt"

	if [ -n "${new_api_32}" ] && [ -f "${new_api_32}" ]; then
		rm -f "${found_api_32}"
		cp "${new_api_32}" "${game_dir}/"
		cp "${new_api_32}" "${orig_dir}/"
		echo "steam_api.dll replaced/copied."
	fi
fi
if [ -n "${found_api_64}" ]; then
	orig_dir=$(dirname "${found_api_64}")
	echo "found 64-bit at: ${orig_dir}"

	echo "generating steam_interfaces.txt..."
	bash "${find_script}" "${found_api_64}" >"${game_dir}/steam_interfaces.txt"
	bash "${find_script}" "${found_api_64}" >"${orig_dir}/steam_interfaces.txt"

	if [ -n "${new_api_64}" ] && [ -f "${new_api_64}" ]; then
		rm -f "${found_api_64}"
		cp "${new_api_64}" "${game_dir}/"
		cp "${new_api_64}" "${orig_dir}/"
		echo "steam_api64.dll replaced/copied."
	fi
fi

if [ -d "${settings_dir}" ]; then
	echo "copying configuration files..."
	cp -r "${settings_dir}"/ "${game_dir}/"

	if [ -n "${found_api_32}" ]; then
		cp -r "${settings_dir}"/ "$(dirname "${found_api_32}")/"
	fi
	if [ -n "${found_api_64}" ]; then
		cp -r "${settings_dir}"/ "$(dirname "${found_api_64}")/"
	fi
	echo "process completed successfully!"
else
	echo "error: settings directory not found."
	exit 1
fi
