#!/bin/bash
 
VOL=$(wpctl get-volume @DEFAULT_SINK@ 2>/dev/null | awk '{print int($2*100)}')
MUTED=$(wpctl get-volume @DEFAULT_SINK@ 2>/dev/null | grep -o "MUTED")

if [ ! -z "$MUTED" ]; then
    echo '{"text": "<span color=\"#ffc6ff\"></span>"}'
elif [ "$VOL" -lt 1 ]; then
    echo '{"text": "<span color=\"#ffc6ff\"></span>", "tooltip": "󰺢  '$VOL'%"}'
elif [ "$VOL" -gt 0 ] && [ "$VOL" -lt 50 ]; then
    echo '{"text": "<span color=\"#ffc6ff\"></span>", "tooltip": "󰺢  '$VOL'%"}'
else
    echo '{"text": "<span color=\"#ffc6ff\"></span>", "tooltip": "󰺢  '$VOL'%"}'
fi
