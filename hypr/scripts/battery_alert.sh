#!/bin/bash


get_battery_level() {
    cat /sys/class/power_supply/BAT1/capacity || echo 100
}


is_charging() {
    status=$(cat /sys/class/power_supply/BAT1/status)
    [[ "$status" == "Charging" || "$status" == "Full" ]]
}


notified_low=false
notified_critical=false
last_charging_state=$(is_charging && echo true || echo false)

while true; do
    battery_level=$(get_battery_level)
    current_charging_state=$(is_charging && echo true || echo false)

    if [[ $current_charging_state != $last_charging_state ]]; then
        if $current_charging_state; then
            notify-send "󰚥 Компьютер подключен к сети электропитания." "Текущий уровень заряда: $battery_level%"
            notified_low=false
            notified_critical=false
        else
            notify-send "󰚦 Компьютер отключен от сети электропитания." "Текущий уровень заряда: $battery_level%"
        fi
    fi

    if ! $current_charging_state; then
        if (( battery_level < 20 )) && (( battery_level >= 10 )); then
            if ! $notified_low; then
                notify-send "󰂎 Низкий уровень заряда." "Возможно, вам стоит подключить компьютер к сети электропитания."
                notified_low=true
            fi
        elif (( battery_level < 10 )); then
            if ! $notified_critical; then
                notify-send "󱃍 Критически низкий уровень заряда." "Подключите компьютер к сети электропитания прямо сейчас."
                notified_critical=true
            fi
        elif (( battery_level >= 20 )); then
            notified_low=false
            notified_critical=false
        fi
    else
        if (( battery_level >= 20 )); then
            notified_low=false
            notified_critical=false
        fi
    fi

    last_charging_state=$current_charging_state
    sleep 60
done
