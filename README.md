sudo pacman -Syu
sudo pacman -S kitty fastfetch brrtfetch waybar btop rofi mako wlogout nautilus swaybg mpv gthumb
sudo pacman -S --needed base-devel git
git clone https://aur.archlinux.org/yay.git
cd yay && makepkg -si
yay -Syu
yay -S nerd-fonts
