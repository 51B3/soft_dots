sudo pacman -S --needed base-devel git
git clone https://aur.archlinux.org/yay.git
cd yay && makepkg -si
sudo pacman -S kitty fastfetch brrtfetch waybar btop rofi mako wlogout
yay -S nerd-fonts
