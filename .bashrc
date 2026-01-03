[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias yandex='~/../usr/bin/yandex-browser-stable'

brrtfetch -width 50 -height 50 -fps 14 -multiplier 100 -info "fastfetch --logo-type none" -offset 0 ~/Pictures/brrtfetch/gifs/cinnamoroll.gif && clear

PS1='[ \u@ \h \W ] \$'

