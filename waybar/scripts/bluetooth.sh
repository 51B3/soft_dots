#!/bin/bash

STATUS=$(bluetoothctl show | grep "Powered: yes" | wc -l)

if [ $STATUS -eq 0 ]; then
    echo "disabled"
else
    IS_CONNECTED=$(bluetoothctl info | grep "Connected: yes" | wc -l)
    if [ $IS_CONNECTED -eq 0 ]; then
        echo "disconnected"
    else
        echo "connected"
    fi
fi

