<div align="center">

# 🔧 Morphe Custom AutoBuilds (Non-Root)

[![Daily Build](https://img.shields.io/github/actions/workflow/status/yashrajrocxx/Mophe-AutoBuilds/patch.yml?label=Daily%20Build&style=for-the-badge&color=2ea44f)](https://github.com/yashrajrocxx/Mophe-AutoBuilds/actions/workflows/patch.yml)
[![Latest Release](https://img.shields.io/github/v/release/yashrajrocxx/Mophe-AutoBuilds?style=for-the-badge&label=Latest%20Release&color=0366d6)](https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/latest)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/yashrajrocxx/Mophe-AutoBuilds?style=for-the-badge&color=orange)](LICENSE)

<p align="center">
  <a href="https://ko-fi.com/rookie_z" target="_blank"><img src="https://storage.ko-fi.com/cdn/kofi6.png?v=6" height="30" style="height:30px; border-radius:8px; display:inline-block;" alt="Donate via Ko-fi" /></a>
  &nbsp;&nbsp;
  <a href="https://buymeachai.ezee.li/RookieZ" target="_blank"><img src="https://raw.githubusercontent.com/TakiShiwa/donate-with-upi/ffbb38749891aeb62e758a3692698e346e3df2da/Button/SVG/UPI-light-blue-01.svg" height="30" style="height:30px; border-radius:8px; display:inline-block;" alt="Donate via UPI" /></a>
  <br />
  <a href="https://paypal.me/RookieEnough" target="_blank"><img src="https://raw.githubusercontent.com/stefan-niedermann/paypal-donate-button/master/paypal-donate-button.png" height="50" style="height:50px; border-radius:8px; display:inline-block; margin-top:8px;" alt="Donate via PayPal" /></a>
</p>

<p align="center">
  <strong>Professional, Automated Custom APK Builder</strong><br>
  Multi-source • Multi-architecture • GitHub Actions Powered
</p>

<p align="center">
A sophisticated, automated pipeline that builds ready-to-install custom patched applications for <strong>non-rooted Android devices</strong>. This project features a highly customized app selection utilizing diverse community patches instead of the standard official set. 
</p>

[![View Latest Release](https://img.shields.io/badge/View%20Latest%20Release-0A0A0A?style=flat&logo=github&logoColor=white)](https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/latest)
[![Report Bug](https://img.shields.io/badge/Report%20Bug-0A0A0A?style=flat&logo=github&logoColor=white)](https://github.com/yashrajrocxx/Mophe-AutoBuilds/issues)
[![Request Feature](https://img.shields.io/badge/Request%20Feature-0A0A0A?style=flat&logo=github&logoColor=white)](https://github.com/yashrajrocxx/Mophe-AutoBuilds/issues)

</div>

---

## ⚡ Quick Downloads

> **Last Updated:** August 11, 2026
> **Note:** All APKs are automatically rebuilt daily at 06:00 UTC to ensure you have the latest features and security patches.

### 📥 Download Links

| Mirror | Description | Link |
| :--- | :--- | :--- |
| **GitHub Releases** | Primary source. Contains all builds. | [**Download Latest Release**](https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/latest) |

### 📱 Supported Apps & Patch Repositories

This repository compiles optimized **arm64-v8a** builds using specific community patch repositories for a curated custom list of 20 applications:

| Application | Package Name | Patch Repository | arm64-v8a |
| :--- | :--- | :--- | :---: |
| **YouTube** | `com.google.android.youtube` | [MorpheApp](https://github.com/MorpheApp/morphe-patches) | ✅ |
| **YouTube Music** | `com.google.android.apps.youtube.music` | [MorpheApp](https://github.com/MorpheApp/morphe-patches) | ✅ |
| **Reddit** | `com.reddit.frontpage` | [MorpheApp](https://github.com/MorpheApp/morphe-patches) | ✅ |
| **Instagram** | `com.instagram.android` | [piko-patches](https://github.com/krvstek/piko-patches) | ✅ |
| **X (Twitter)** | `com.twitter.android` | [piko-patches](https://github.com/krvstek/piko-patches) | ✅ |
| **Pinterest** | `com.pinterest` | [browzomje](https://github.com/browzomje/morphe-patches) | ✅ |
| **Telegram** | `org.telegram.messenger` | [pareshdev](https://github.com/pareshdev/morphe-patches) | ✅ |
| **VN Video Editor** | `com.frontrow.vlog` | [pareshdev](https://github.com/pareshdev/morphe-patches) | ✅ |
| **SD Maid SE** | `eu.darken.sdmse` | [pareshdev](https://github.com/pareshdev/morphe-patches) | ✅ |
| **Threads** | `com.instagram.barcelona` | [RookieEnough](https://github.com/RookieEnough/revanced-patches) | ✅ |
| **Google Photos** | `com.google.android.apps.photos` | [RookieEnough](https://github.com/RookieEnough/revanced-patches) | ✅ |
| **TradingView** | `com.tradingview.tradingviewapp` | [rushiranpise](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **Depth Live Wallpaper** | `com.jndapp.depth.live.wallpaper` | [rushiranpise](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **Pocket Casts** | `au.com.shiftyjelly.pocketcasts` | [rushiranpise](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **Minimal Widgets** | `com.jndapp.minimal.widgets` | [rushiranpise](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **JioTV+** | `com.jio.media.jiotvplus` | [durgesh0505](https://github.com/durgesh0505/chiggi_morphe_patches) | ✅ |
| **Brave Browser** | `com.brave.browser` | [dh6k](https://github.com/dh6k/morphe-patches) | ✅ |

*(All builds are target-optimized for `arm64-v8a` to reduce bundle sizes and increase device efficiency).*

---

## ✨ Key Technical Enhancements

This project has been massively overhauled with custom logic to provide maximum reliability:

* **Direct Google Play Downloads (`gplaydl`):** Bypasses all scraping blocks (like APKMirror IP bans) by downloading split-APKs entirely directly and securely from Google Play servers.
* **Smart Version History Resolver:** Automatically detects the exact community-recommended app version required by the patcher and traces its exact historical Google Play `versionCode` dynamically, falling back to the absolute latest version available if the patch supports it.
* **Automated Split Merging:** Implements `APKEditor` to dynamically merge Google Play split `.apk` clusters into single, installable bases before applying patches.
* **Fully Automated Pipeline:** GitHub Actions workflow executes daily at 06:00 UTC, requiring zero manual intervention, securing your tokens automatically via GitHub Secrets.
* **Auto-Signing:** All APKs are signed with a consistent public keystore, making them ready to install immediately.
* **Clean Release Cycle:** Previous releases are replaced rather than archived, preventing clutter and making it easy for external managers to track updates.

---

## 🛠️ Repository Structure

```text
morphe-autobuilds/
├── .github/workflows/      # GitHub Actions automation
│   ├── patch.yml           # Daily automated builds (06:00 UTC)
│   └── manual-patch.yml    # Manual trigger workflow
├── apps/                   # APK source configurations
├── patches/                # Patch inclusion/exclusion rules
├── sources/                # ReVanced tool source definitions
├── src/                    # Core Python build logic
├── arch-config.json        # Architecture build matrix
├── patch-config.json       # Custom App build configuration
└── requirements.txt        # Project dependencies
```

---

## ⚙️ Configuration Guide

This builder is highly configurable. You can adjust the following files to customize the build output.

### 1. App Selection (`patch-config.json`)

Define which applications the pipeline should attempt to build.

```json
{
  "patch_list": [
    { "app_name": "youtube", "source": "morphe" },
    { "app_name": "instagram", "source": "piko" }
  ]
}
```

### 2. Architecture Matrix (`arch-config.json`)

Specify which CPU architectures to target for each application. By default, `arm64-v8a` is targeted.

### 3. Source Definitions

Located in the `apps/` directory.

### 4. Patch Rules

Located in `patches/`. Example for `patches/youtube-morphe.txt`. Use `+` to force include and `-` to exclude.

```text
# Essential patches
+ microg-support
+ premium-heading
+ hide-infocard-suggestions

# Exclusions
- custom-branding
- amoled
```

---

## 🚀 Local Build Instructions

If you prefer to build the APKs on your own machine, follow these steps.

### Prerequisites

* Python 3.11 or higher
* Java Runtime Environment (JRE)
* `zip` utility
* `apksigner` (part of Android SDK Build-Tools)

### Installation & Execution

1. **Clone the repository:**
```bash
git clone https://github.com/yashrajrocxx/Mophe-AutoBuilds.git
cd Mophe-AutoBuilds
```

2. **Setup Local Environment:**
Create a `.env` file in the root directory with your secure API tokens.

3. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install requests beautifulsoup4 python-dotenv
```

4. **Run the build:**
You can build for a specific app and source.
```bash
export APP_NAME="youtube"
export SOURCE="morphe"
python -m src
```

---

## 🔄 GitHub Actions Workflows

### Daily Automated Build (`patch.yml`)
* **Schedule:** Runs daily at 06:00 UTC.
* **Function:** Iterates through all configured apps and architectures using secure GitHub Secrets.
* **Output:** Updates the single "Latest" release tag.

### Manual Build (`manual-patch.yml`)
* **Trigger:** Manually via the GitHub Actions "Run workflow" button.
* **Capabilities:** Target specific apps, architectures, and force specific APK versions.

---

## 🤝 Contributing
Contributions to improve the toolchain or add support for new apps are welcome.
1. **Fork** the repository.
2. **Create** a feature branch (`git checkout -b feature/new-app`).
3. **Test** your changes locally using the Python scripts.
4. **Commit** your changes (`git commit -m "Add support for new-app"`).
5. **Push** to the branch (`git push origin feature/new-app`).
6. **Open** a Pull Request.

---

## ⚠️ Disclaimer & Legal

> **Important:** This project is an automated build tool. The APKs provided in the releases are generated automatically using official and community ReVanced/Morphe tools and patches.

* **Affiliation:** These builds are **not** officially affiliated with the original developers or the Morphe Team.
* **Usage:** Provided for educational and convenience purposes only. Use at your own risk.
* **GmsCore:** Morphe's MicroG-RE is required for apps relying on Google services to function correctly.
* **Updates:** Patches are automatically pulled from the latest custom sources; builds may occasionally contain experimental features.

---

<div align="center">

**If you found this project helpful, please consider giving it a ⭐ Star.**  
<br>
**Made with 💜 by RookieZ & Customized by Yashrajrocxx**

</div>
