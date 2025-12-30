#!/bin/bash
# OSINT-Nexus Linux Installer
# Run with: sudo ./installer_linux.sh

set -e

APP_NAME="osint-nexus"
DISPLAY_NAME="OSINT-Nexus"
INSTALL_DIR="/opt/OSINT-Nexus"
BIN_LINK="/usr/local/bin/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"
ICON_FILE="$ICON_DIR/$APP_NAME.png"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_banner() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           OSINT-Nexus Installer           ║${NC}"
    echo -e "${CYAN}║   Cross-Platform OSINT Gathering Tool     ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════╝${NC}"
    echo ""
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}[!] Please run as root (sudo)${NC}"
        exit 1
    fi
}

install_app() {
    print_banner
    check_root
    
    echo -e "${GREEN}[*] Starting installation...${NC}"
    
    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    DIST_DIR="$(dirname "$SCRIPT_DIR")/dist"
    ASSETS_DIR="$(dirname "$SCRIPT_DIR")/assets"
    
    # Create installation directory
    echo -e "${CYAN}[*] Creating installation directory...${NC}"
    mkdir -p "$INSTALL_DIR"
    echo "    Created: $INSTALL_DIR"
    
    # Copy binary
    if [ -f "$DIST_DIR/$APP_NAME" ]; then
        echo -e "${CYAN}[*] Copying application binary...${NC}"
        cp "$DIST_DIR/$APP_NAME" "$INSTALL_DIR/$APP_NAME"
        chmod +x "$INSTALL_DIR/$APP_NAME"
        echo "    Copied: $APP_NAME"
    else
        echo -e "${YELLOW}[!] Binary not found in $DIST_DIR${NC}"
        echo "    Please run PyInstaller first: pyinstaller build.spec"
    fi
    
    # Copy assets
    if [ -d "$ASSETS_DIR" ]; then
        echo -e "${CYAN}[*] Copying assets...${NC}"
        cp -r "$ASSETS_DIR" "$INSTALL_DIR/assets"
        echo "    Copied: assets/"
    fi
    
    # Create symlink in /usr/local/bin
    echo -e "${CYAN}[*] Creating command-line symlink...${NC}"
    ln -sf "$INSTALL_DIR/$APP_NAME" "$BIN_LINK"
    echo "    Created: $BIN_LINK"
    
    # Create icon directory and copy icon
    echo -e "${CYAN}[*] Installing application icon...${NC}"
    mkdir -p "$ICON_DIR"
    
    if [ -f "$ASSETS_DIR/app_icon.png" ]; then
        cp "$ASSETS_DIR/app_icon.png" "$ICON_FILE"
        echo "    Installed: $ICON_FILE"
    else
        echo -e "${YELLOW}    Icon not found, using default${NC}"
    fi
    
    # Create .desktop file
    echo -e "${CYAN}[*] Creating application launcher...${NC}"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$DISPLAY_NAME
Comment=Cross-Platform OSINT Gathering and Visualization Tool
Exec=$INSTALL_DIR/$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Security;Network;Utility;
Keywords=osint;security;reconnaissance;intelligence;
StartupWMClass=osint-nexus
EOF
    
    chmod 644 "$DESKTOP_FILE"
    echo "    Created: $DESKTOP_FILE"
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/share/applications/ 2>/dev/null || true
    fi
    
    # Update icon cache
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
    fi
    
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN} Installation Complete!${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e " Location: ${CYAN}$INSTALL_DIR${NC}"
    echo ""
    echo " Launch from:"
    echo "   • Application menu (search 'OSINT-Nexus')"
    echo "   • Command line: ${CYAN}osint-nexus${NC}"
    echo ""
}

uninstall_app() {
    print_banner
    check_root
    
    echo -e "${YELLOW}[*] Starting uninstallation...${NC}"
    
    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        echo "    Removed: $INSTALL_DIR"
    fi
    
    # Remove symlink
    if [ -L "$BIN_LINK" ]; then
        rm -f "$BIN_LINK"
        echo "    Removed: $BIN_LINK"
    fi
    
    # Remove desktop file
    if [ -f "$DESKTOP_FILE" ]; then
        rm -f "$DESKTOP_FILE"
        echo "    Removed: $DESKTOP_FILE"
    fi
    
    # Remove icon
    if [ -f "$ICON_FILE" ]; then
        rm -f "$ICON_FILE"
        echo "    Removed: $ICON_FILE"
    fi
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/share/applications/ 2>/dev/null || true
    fi
    
    echo ""
    echo -e "${GREEN}Uninstallation complete!${NC}"
    echo ""
}

show_help() {
    print_banner
    echo "Usage: sudo $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  install     Install OSINT-Nexus (default)"
    echo "  uninstall   Remove OSINT-Nexus from the system"
    echo "  --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo $0                  # Install"
    echo "  sudo $0 install          # Install"
    echo "  sudo $0 uninstall        # Uninstall"
    echo ""
}

# Main execution
case "${1:-install}" in
    install)
        install_app
        ;;
    uninstall)
        uninstall_app
        ;;
    --help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac
