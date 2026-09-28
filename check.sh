#!/usr/bin/env bash

dir="${1%/}"

find "${dir}" -maxdepth 1 -type d -exec sh -c '
for d; do
    if [ -d "${d}/.git" ]; then
        echo "📁 ${d} 📁"
        git -C "${d}" status
        echo
    fi
done
' sh {} +
