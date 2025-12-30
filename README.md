# OSINT-Nexus

<div align="center">

![OSINT-Nexus Logo](assets/app_icon.png)

**Cross-Platform OSINT Gathering and Visualization Application**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green?style=for-the-badge&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=for-the-badge)](https://github.com/)

</div>

---

## 🎯 Overview

OSINT-Nexus is a powerful, cross-platform Open-Source Intelligence (OSINT) gathering and visualization application. It combines the passive reconnaissance capabilities of tools like TheHarvester and SpiderFoot with the powerful visual link analysis of Maltego.

### ✨ Key Features

- **🔍 Multi-Source Reconnaissance** - Gather data from multiple sources including search engines, social media, DNS records, and WHOIS
- **🔗 Interactive Graph Visualization** - Maltego-style force-directed graph with entity relationships
- **🌙 Modern Dark Mode UI** - Beautiful, professional interface built with PyQt6
- **⚡ Asynchronous Scanning** - Non-blocking UI with parallel module execution
- **💾 Project Management** - SQLite-based local storage for investigations
- **📦 Cross-Platform** - Works on Windows and Linux with standalone installers

---

## 🖼️ Screenshots

| Target Scan | Graph View |
|:-----------:|:----------:|
| ![Scan Tab](docs/scan_tab.png) | ![Graph Tab](docs/graph_tab.png) |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/osint-nexus.git
cd osint-nexus

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

---

## 📊 OSINT Modules

| Module | Input | Output | Inspiration |
|--------|-------|--------|-------------|
| **Email Harvester** | Domain | Emails, Names, Subdomains | TheHarvester |
| **Social Profile Lookup** | Username, Email | Social media profiles | Sherlock |
| **Phone Number Recon** | Phone Number | Carrier, Location, Type | PhoneInfoga |
| **Domain Infrastructure** | Domain, IP | WHOIS, DNS, Open Ports | Recon-ng |
| **Document Metadata** | Domain | Indexed files, Metadata | Maltego |

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| GUI Framework | PyQt6 |
| Graph Visualization | Force-directed layout |
| Database | SQLite3 |
| Async | QThreadPool |
| Packaging | PyInstaller |

---

## 📁 Project Structure

```
osint-nexus/
├── src/
│   ├── main.py              # Application entry point
│   ├── osint_core.py        # Async engine
│   ├── database.py          # SQLite layer
│   ├── ui/
│   │   ├── main_window.py   # Main window
│   │   ├── target_scan_tab.py
│   │   ├── graph_view_tab.py
│   │   └── styles.py        # Dark mode theme
│   └── modules/
│       ├── email_harvester.py
│       ├── social_lookup.py
│       ├── phone_recon.py
│       ├── domain_infra.py
│       └── doc_metadata.py
├── assets/
├── installers/
│   ├── installer_win.ps1
│   └── installer_linux.sh
├── requirements.txt
└── build.spec
```

---

## 🔧 Building Executables

### Windows

```powershell
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller build.spec

# Run installer (as Administrator)
powershell -ExecutionPolicy Bypass -File installers\installer_win.ps1
```

### Linux

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller build.spec

# Run installer
sudo ./installers/installer_linux.sh
```

---

## ⚖️ Legal Disclaimer

> ⚠️ **OSINT-Nexus is designed for legitimate security research and authorized penetration testing only.**

By using this application, you agree to:
- Only gather information you are authorized to access
- Comply with all applicable laws and regulations
- Use gathered information responsibly and ethically

The developers are not responsible for any misuse of this tool.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">


**Made with ❤️ for the Security Community**

</div>
# OSINT-NEXUS
