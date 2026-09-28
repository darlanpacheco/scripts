#!/usr/bin/env bash

arcade=(
	"fatfury1" # fatal-fury
	"fatfury2" # fatal-fury-ii
	"fatfury3" # fatal-fury-iii
	"rbff1"    # fatal-fury-iv
	"garou"    # fatal-fury-v
	"kof98"    # kof-v
	"kof99"    # kof-vi
	"kof2000"  # kof-vii
	"kof2001"  # kof-viii
	"kof2002"  # kof-ix
	"mvscu"    # marvel-vs-capcom
	"mshvsfu1" # marvel-vs-sf
	"mslug"    # ms
	"mslug2"   # ms-ii
	"mslug3"   # ms-iii
	"mslug4"   # ms-iv
	"mslug5"   # ms-v
	"sfau"     # sf-alpha
	"sfa2u"    # sf-alpha-ii
	"sfa3u"    # sf-alpha-iii
	"ssf2tu"   # sf-ii
	"sfiii3n"  # sf-iii
)
nintendo=(
	"chrono-trigger"
	"donkey-kong-country-ii"
	"donkey-kong-country-iii"
	"donkey-kong-country"
	"kirby-iv"
	"kirby-v"
	"super-mario-world-ii"
	"super-mario-world"
)
nintendo2=(
	"donkey-kong-64"
	"super-mario-64"
	"zelda-v"
	"zelda-vi"
)
nintendo3=(
	"dragonball-aa"
	"kirby-vi"
	"kirby-vii"
	"onepiece-sj"
	"pokemon-emerald"
	"pokemon-firered"
	"super-mario-advance-ii"
	"super-mario-advance-iii"
	"super-mario-advance-iv"
	"super-mario-advance"
	"zelda-viii"
	"zelda-xi"
)
sony=()
sony2=(
	"gta-iii"
	"gta-san-andreas"
	"gta-vice-city"
	"gow-ii"
	"gow"
	"ico"
	"shadow-of-the-colossus"
	"nfs-underground-ii"
	"nfs-underground"
)
native=(
	"broforce"
	"charlie-murder"
	"cult-of-the-lamb"
	"cuphead"
	"dark-souls-ii"
	"dark-souls"
	"dead-cells"
	"enter-the-gungeon"
	"exit-the-gungeon"
	"hades-ii"
	"hades"
	"hollow-knight-ii"
	"hollow-knight"
	"katana-zero"
	"kingdom-two-crowns"
	"sekiro"
	"south-park-ii"
	"south-park"
)

# "bully"
# "celeste"
# "dark-souls-ii"
# "dark-souls-iii"
# "dark-souls"
# "devil-may-cry-ii"
# "devil-may-cry-iii"
# "devil-may-cry"
# "dragon-ball-z-budokai-tenkaichi-ii"
# "dragon-ball-z-budokai-tenkaichi-iii"
# "dragon-ball-z-budokai-tenkaichi"
# "elden-ring-ii"
# "elden-ring"
# "half-life-ii"
# "half-life"
# "kingdom-hearts-ii"
# "kingdom-hearts"
# "life-is-strange-ii"
# "life-is-strange"
# "mina-the-hollower"
# "naruto-ultimate-ninja-ii"
# "naruto-ultimate-ninja-iii"
# "naruto-ultimate-ninja-iv"
# "naruto-ultimate-ninja-v"
# "naruto-ultimate-ninja"
# "nine-sols"
# "onepiece-iii"
# "onepiece-iv"
# "overcooked-ii"
# "overcooked"
# "portal-ii"
# "portal"
# "ratchet-and-clank-ii"
# "ratchet-and-clank-iii"
# "ratchet-and-clank"
# "resident-evil-ii"
# "resident-evil-iii"
# "resident-evil-iv"
# "resident-evil-vii"
# "resident-evil-viii"
# "resident-evil"
# "sekiro"
# "sf-iv"
# "shovel-knight"
# "the-elder-scrolls-iv"
# "the-elder-scrolls-v"
# "undertale"
# "gta-iv"
# "gta-v"
# "zelda-breath-of-the-wild"
# "zelda-tears-of-the-kingdom"
# "tekken-iii"
# "tekken-iv"
# "tekken-v"
# "burnout-ii"
# "burnout-iii"
# "burnout"

# will of playing
# controller good experience
# lighter possible
# childhood

roms=$((${#arcade[@]} + ${#nintendo[@]} + ${#nintendo2[@]} + ${#nintendo3[@]} + ${#sony[@]} + ${#native[@]}))
echo "${roms}"

dir="${1%/}"
if [ -z "${dir}" ]; then
	exit 1
fi

check_differences() {
	local category_name="${1}"
	local category_dir="${dir}/${category_name}"
	local rom_list=("${@}")

	for rom in "${rom_list[@]}"; do
		[[ "${rom}" == "${category_name}" ]] && continue

		if [[ -z $(ls "${category_dir}/${rom}".* 2>/dev/null) ]]; then
			echo "[ MISSING ] ${rom}"
		fi
	done
	for actual_file in "${category_dir}"/*; do
		[[ -e "${actual_file}" ]] || continue
		file_name=$(basename "${actual_file}")
		name_only="${file_name%.*}"
		[[ "${name_only}" == "${category_name}" ]] && continue
		found=false
		for rom in "${rom_list[@]}"; do
			[[ "${rom}" == "${category_name}" ]] && continue
			if [[ "${rom}" == "${name_only}" ]]; then
				found=true
				break
			fi
		done
		if [[ "${found}" == false ]]; then
			echo "[ EXTRA ] ${file_name}"
		fi
	done
}

check_differences "arcade" "${arcade[@]}"
check_differences "nintendo" "${nintendo[@]}"
check_differences "nintendo2" "${nintendo2[@]}"
check_differences "nintendo3" "${nintendo3[@]}"
check_differences "sony" "${sony[@]}"
check_differences "sony2" "${sony2[@]}"
check_differences "native" "${native[@]}"
