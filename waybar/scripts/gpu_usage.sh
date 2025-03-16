#!/bin/bash

# Определяем тип видеокарты
detect_gpu() {
  if lspci | grep -i "nvidia" &> /dev/null; then
    echo "nvidia"
  elif lspci | grep -i "amd" &> /dev/null || lspci | grep -i "ati" &> /dev/null; then
    echo "amd"
  else
    echo "unknown"
  fi
}

# Получаем загруженность видеокарты
get_gpu_usage() {
  local gpu_type=$1

  if [[ "$gpu_type" == "nvidia" ]]; then
    if command -v nvidia-smi &> /dev/null; then
      nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | awk '{print $1"%"}'
    else
      echo "N/A"
    fi
  elif [[ "$gpu_type" == "amd" ]]; then
    if command -v radeontop &> /dev/null; then
      radeontop -d- -l1 | awk '/gpu/ {print $2"%"}'
    else
      echo "N/A"
    fi
  else
    echo "N/A"
  fi
}

# Основная логика
main() {
  # Определяем тип видеокарты
  gpu_type=$(detect_gpu)

  # Получаем загруженность видеокарты
  get_gpu_usage "$gpu_type"
}

# Запуск скрипта
main
