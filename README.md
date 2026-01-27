sudo pacman -Syu
sudo pacman -S kitty fastfetch brrtfetch waybar btop rofi mako wlogout nautilus swaybg mpv gthumb hyprwave gnome-themes-extra gtk4 gtk3 nwg-look python playerctl
python -m venv venv
source venv/bin/activate
pip install PyQt6 dbus-python requests pillow
deactivate
chmod +x power_menu.sh
chmod +x audio_player.sh
sudo pacman -S --needed base-devel git
git clone https://aur.archlinux.org/yay.git
cd yay && makepkg -si
yay -Syu
yay -S nerd-fonts
