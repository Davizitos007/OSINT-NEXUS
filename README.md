# OSINT-Nexus

<div align="center">

![OSINT-Nexus Logo](assets/app_icon.png)

**Cross-Platform OSINT Gathering and Visualization Application**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green?style=for-the-badge&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=for-the-badge)](https://github.com/)
[![AI-Powered](https://img.shields.io/badge/AI-Gemini_Powered-ff6f61?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

</div>

---

## 🎯 Overview

OSINT-Nexus is a powerful, cross-platform Open-Source Intelligence (OSINT) gathering and visualization application. It combines the passive reconnaissance capabilities of tools like TheHarvester and SpiderFoot with the powerful visual link analysis of Maltego, enhanced with **AI-powered analysis** and **advanced graph analytics**.

### ✨ Key Features

- **🔍 Multi-Source Reconnaissance** - Gather data from multiple sources including search engines, social media, DNS records, and WHOIS
- **🔗 Interactive Graph Visualization** - Maltego-style force-directed graph with entity relationships
- **🤖 AI-Powered Analysis** - Google Gemini integration for intelligent entity correlation and natural language querying
- **📊 Advanced Graph Analytics** - Community detection, centrality analysis, and anomaly detection
- **🔓 Breach Intelligence** - Check emails against HaveIBeenPwned and breach databases
- **📷 Image Forensics** - Extract EXIF metadata, GPS coordinates, and camera information
- **📄 Professional Reports** - Generate HTML, PDF, and STIX 2.1 format intelligence reports
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
- (Optional) Google Gemini API key for AI features
- (Optional) HaveIBeenPwned API key for breach intelligence

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

### Core Modules

| Module | Input | Output | Inspiration |
|--------|-------|--------|-------------|
| **Email Harvester** | Domain, Email | Emails, Names, Subdomains | TheHarvester |
| **Social Profile Lookup** | Username, Email | Social media profiles | Sherlock |
| **Phone Number Recon** | Phone Number | Carrier, Location, Type | PhoneInfoga |
| **Domain Infrastructure** | Domain, IP | WHOIS, DNS, Open Ports | Recon-ng |
| **Document Metadata** | Domain | Indexed files, Metadata | Maltego |
| **GitHub Recon** | Username | Repos, Emails, Activity | - |
| **Steam Recon** | Username | Profile, Friends, Games | - |

### Advanced Modules (NEW)

| Module | Input | Output | Description |
|--------|-------|--------|-------------|
| **🔓 Breach Intelligence** | Email, Domain | Breach records, Password exposure | HaveIBeenPwned integration |
| **📷 Image Forensics** | Domain, URL | EXIF data, GPS coordinates, Camera info | Image metadata extraction |
| **🔍 GeoIP Lookup** | IP | Location, ISP, Organization | Geographic intelligence |
| **⏳ Wayback Machine** | Domain | Archived URLs | Historical website data |
| **🔒 Shodan Transform** | IP, Domain | Open ports, Services, Vulnerabilities | Infrastructure scanning |

---

## 🤖 AI-Powered Features (NEW)

OSINT-Nexus includes cutting-edge AI capabilities powered by **Google Gemini**:

### Entity Correlation
Automatically identify hidden patterns and correlations between discovered entities.

### Threat Assessment
Generate risk scores and threat narratives for individual entities.

### Natural Language Querying
Query your OSINT graph using natural language:
- *"Show me all emails from gmail.com"*
- *"Find IPs connected to suspicious domains"*
- *"What social media accounts belong to this username?"*

### Executive Summaries
Auto-generate professional executive summaries for your investigations.

> **Setup**: Add your Gemini API key in `Settings → API Keys → Gemini API Key`

---

## 📊 Graph Analytics (NEW)

Advanced network analysis algorithms for intelligence extraction:

| Feature | Algorithm | Description |
|---------|-----------|-------------|
| **Community Detection** | Louvain | Identify clusters of related entities |
| **Centrality Analysis** | PageRank, Betweenness | Find key entities and bridges |
| **Anomaly Detection** | Statistical | Detect unusual patterns and outliers |
| **Path Finding** | Dijkstra | Find shortest paths between entities |

---

## 📄 Professional Reporting (NEW)

Export your intelligence in professional formats:

| Format | Description | Use Case |
|--------|-------------|----------|
| **HTML Report** | Beautiful dark-themed report | Presentations, sharing |
| **PDF Report** | Print-ready document | Formal reports |
| **STIX 2.1** | Cyber Threat Intelligence format | Integration with CTI platforms |
| **JSON/CSV** | Raw data export | Analysis, archival |

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| GUI Framework | PyQt6 |
| Graph Visualization | Force-directed layout (NetworkX) |
| AI Integration | Google Gemini API |
| Graph Analytics | NetworkX (Louvain, PageRank) |
| Database | SQLite3 |
| PDF Generation | ReportLab |
| Image Analysis | Pillow (EXIF) |
| Async | QThreadPool + aiohttp |
| Packaging | PyInstaller |

---

## 📁 Project Structure

```
osint-nexus/
├── src/
│   ├── main.py              # Application entry point
│   ├── osint_core.py        # Async engine
│   ├── database.py          # SQLite layer
│   ├── config.py            # Configuration management
│   ├── ai/                  # AI-powered features (NEW)
│   │   ├── ai_engine.py     # Gemini integration
│   │   └── __init__.py
│   ├── analytics/           # Graph analytics (NEW)
│   │   ├── graph_analytics.py
│   │   └── __init__.py
│   ├── reports/             # Report generation (NEW)
│   │   ├── report_generator.py
│   │   └── __init__.py
│   ├── ui/
│   │   ├── main_window.py   # Main window
│   │   ├── target_scan_tab.py
│   │   ├── graph_view_tab.py
│   │   ├── settings_dialog.py
│   │   └── styles.py        # Dark mode theme
│   └── modules/
│       ├── email_harvester.py
│       ├── social_lookup.py
│       ├── phone_recon.py
│       ├── domain_infra.py
│       ├── breach_intel.py    # NEW
│       ├── image_forensics.py # NEW
│       └── transforms.py
├── assets/
├── installers/
├── requirements.txt
└── build.spec
```

---

## ⚙️ Configuration

### API Keys

Configure API keys in `Settings → API Keys`:

| Service | Required | Features Enabled |
|---------|----------|------------------|
| Gemini API | Optional | AI analysis, NL queries, summaries |
| HaveIBeenPwned | Optional | Breach intelligence |
| Shodan | Optional | Infrastructure scanning |
| VirusTotal | Optional | Threat intelligence |

### Getting API Keys

1. **Gemini API**: [Google AI Studio](https://aistudio.google.com/app/apikey) (Free tier available)
2. **HaveIBeenPwned**: [haveibeenpwned.com/API](https://haveibeenpwned.com/API/Key)
3. **Shodan**: [account.shodan.io](https://account.shodan.io/)
4. **VirusTotal**: [virustotal.com/gui/join-us](https://www.virustotal.com/gui/join-us)

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

*Featuring AI-powered intelligence analysis and professional reporting*

</div>
