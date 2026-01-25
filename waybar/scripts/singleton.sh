#!/bin/bash


FILE="$HOME/.config/waybar/$1"

[[ -z "$1" ]] && exit 1
[[ ! -f "$FILE" ]] && exit 1

if pgrep -f "python .*${FILE}" > /dev/null; then
    exit 0
fi

. "$HOME/.config/waybar/venv/bin/activate"
exec python "$FILE"
