#!/bin/bash


SINK=$(pactl info | grep "Default Sink" | awk '{print $3}')

if [ -z "$SINK" ]; then
    VOLUME=0
    IS_MUTED=false
else
    VOLUME=$(pactl get-sink-volume "$SINK" | awk 'NR==1{print int($5)}')
    IS_MUTED=$(pactl get-sink-mute "$SINK" | awk '{print $2}')

    if [ "$IS_MUTED" == "yes" ]; then
        IS_MUTED=true
    else
        IS_MUTED=false
    fi
fi

if [ "$IS_MUTED" = "true" ]; then
    ICON=""
elif [ "$VOLUME" -lt 1 ]; then
    ICON=" "
elif [ "$VOLUME" -lt 50 ]; then
    ICON=" "
else
    ICON=""
fi

echo "{\"text\": \"<span color=\\\"#ffc6ff\\\">$ICON</span>\", \"tooltip\": \"󰺢  $VOLUME%\"}"
