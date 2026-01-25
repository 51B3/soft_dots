#!/usr/bin/env bash


PLAYERS=$(busctl --user list | awk '/org.mpris.MediaPlayer2/ {print $1}')

for p in $PLAYERS; do
    STATUS=$(busctl --user get-property "$p" \
        /org/mpris/MediaPlayer2 \
        org.mpris.MediaPlayer2.Player PlaybackStatus 2>/dev/null | \
        awk '{print $2}' | tr -d '"')

    if [ "$STATUS" = "Playing" ]; then
        echo "󰎇"
        exit 0
    fi
done

echo "󰎊"
