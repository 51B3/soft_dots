sudo pacman -Syu
sudo pacman -S kitty fastfetch brrtfetch waybar btop rofi mako wlogout nautilus swaybg mpv gthumb hyprwave gnome-themes-extra gtk4 gtk3 nwg-look python
python -m venv venv
source venv/bin/activate
pip install PyQt6
deactivate
chmod +x power_menu.py
sudo pacman -S --needed base-devel git
git clone https://aur.archlinux.org/yay.git
cd yay && makepkg -si
yay -Syu
yay -S nerd-fonts
