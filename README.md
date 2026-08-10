<div align="center">

# 🔧 Morphe Non-Root Builder

[![Daily Build](https://img.shields.io/github/actions/workflow/status/RookieEnough/Revanced-AutoBuilds/patch.yml?label=Daily%20Build&style=for-the-badge&color=2ea44f)](https://github.com/RookieEnough/Revanced-AutoBuilds/actions/workflows/patch.yml)
[![Latest Release](https://img.shields.io/github/v/release/RookieEnough/Revanced-AutoBuilds?style=for-the-badge&label=Latest%20Release&color=0366d6)](https://github.com/RookieEnough/Revanced-AutoBuilds/releases/latest)
[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/RookieEnough/Revanced-AutoBuilds?style=for-the-badge&color=orange)](LICENSE)


<p align="center">
  <a href="https://ko-fi.com/rookie_z" target="_blank"><img src="https://storage.ko-fi.com/cdn/kofi6.png?v=6" height="30" style="height:30px; border-radius:8px; display:inline-block;" alt="Donate via Ko-fi" /></a>
  &nbsp;&nbsp;
  <a href="https://buymeachai.ezee.li/RookieZ" target="_blank"><img src="https://raw.githubusercontent.com/TakiShiwa/donate-with-upi/ffbb38749891aeb62e758a3692698e346e3df2da/Button/SVG/UPI-light-blue-01.svg" height="30" style="height:30px; border-radius:8px; display:inline-block;" alt="Donate via UPI" /></a>
  <br />
  <a href="https://paypal.me/RookieEnough" target="_blank"><img src="https://raw.githubusercontent.com/stefan-niedermann/paypal-donate-button/master/paypal-donate-button.png" height="50" style="height:50px; border-radius:8px; display:inline-block; margin-top:8px;" alt="Donate via PayPal" /></a>
</p>



<p align="center">
  <strong>Professional, Automated ReVanced APK Builder</strong><br>
  Multi-source • Multi-architecture • GitHub Actions Powered
</p>

<p align="center">
A sophisticated, automated pipeline that builds ready-to-install Morphe applications for <strong>non-rooted Android devices</strong>. This system automatically fetches the latest Morphe tools, downloads base APKs from multiple sources, applies patches, and publishes optimized APKs with architecture-specific builds.
</p>

[![View Latest Release](https://img.shields.io/badge/View%20Latest%20Release-0A0A0A?style=flat&logo=github&logoColor=white)](https://github.com/RookieEnough/Revanced-AutoBuilds/releases/latest)
[![Report Bug](https://img.shields.io/badge/Report%20Bug-0A0A0A?style=flat&logo=github&logoColor=white)](https://github.com/RookieEnough/Revanced-AutoBuilds/issues)
[![Request Feature](https://img.shields.io/badge/Request%20Feature-0A0A0A?style=flat&logo=github&logoColor=white)](https://github.com/RookieEnough/Revanced-AutoBuilds/issues)


</div>

---

## ⚡ Quick Downloads

> **Note:** All APKs are automatically rebuilt daily at 06:00 UTC to ensure you have the latest features and security patches.

### 📥 Download Links

| Mirror | Description | Link |
| :--- | :--- | :--- |
| **GitHub Releases** | Primary source. Contains all builds. | [**Download Latest Release**](https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/latest) |

### 📱 Supported Apps & Patch Repositories

This repository compiles optimized **arm64-v8a** builds using specific community patch repositories for each application:

| Application | Package Name | Patch Repository | arm64-v8a |
| :--- | :--- | :--- | :---: |
| **YouTube** | `com.google.android.youtube` | [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches) | ✅ |
| **YouTube Music** | `com.google.android.apps.youtube.music` | [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches) | ✅ |
| **Reddit** | `com.reddit.frontpage` | [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches) | ✅ |
| **Instagram** | `com.instagram.android` | [krvstek/piko-patches](https://github.com/krvstek/piko-patches) | ✅ |
| **Pinterest** | `com.pinterest` | [browzomje/morphe-patches](https://github.com/browzomje/morphe-patches) | ✅ |
| **Telegram** | `org.telegram.messenger` | [pareshdev/morphe-patches](https://github.com/pareshdev/morphe-patches) | ✅ |
| **JioHotstar Mobile** | `in.startv.hotstar` (Mobile) | [pareshdev/morphe-patches](https://github.com/pareshdev/morphe-patches) | ✅ |
| **VN Video Editor** | `com.frontrow.vlog` | [pareshdev/morphe-patches](https://github.com/pareshdev/morphe-patches) | ✅ |
| **SD Maid SE** | `eu.darken.sdmse` | [pareshdev/morphe-patches](https://github.com/pareshdev/morphe-patches) | ✅ |
| **Threads** | `com.instagram.threads` | [RookieEnough/revanced-patches](https://github.com/RookieEnough/revanced-patches) | ✅ |
| **Google Photos** | `com.google.android.apps.photos` | [RookieEnough/revanced-patches](https://github.com/RookieEnough/revanced-patches) | ✅ |
| **X (Twitter)** | `com.twitter.android` | [krvstek/piko-patches](https://github.com/krvstek/piko-patches) | ✅ |
| **Canva** | `com.canva.editor` | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **TradingView** | `com.tradingview.tradingviewapp` | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **Depth Live Wallpaper** | `com.jndapp.depth.live.wallpaper` | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **Pocket Casts** | `au.com.shiftyjelly.pocketcasts` | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **Minimal Widgets** | `com.jndapp.minimal.widgets` | [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches) | ✅ |
| **JioTV+** | `com.jio.media.jiotvplus` | [durgesh0505/chiggi_morphe_patches](https://github.com/durgesh0505/chiggi_morphe_patches) | ✅ |
| **JioHotstar TV** | `in.startv.hotstar` (Android TV) | [durgesh0505/chiggi_morphe_patches](https://github.com/durgesh0505/chiggi_morphe_patches) | ✅ |
| **Brave Browser** | `com.brave.browser` | [dh6k/morphe-patches](https://github.com/dh6k/morphe-patches) | ✅ |

*(All builds are target-optimized for `arm64-v8a` to reduce bundle sizes and increase device efficiency).*

---

## ✨ Key Features

This repository utilizes a robust Python-based pipeline to ensure high reliability and optimization.

* **Fully Automated:** GitHub Actions workflow executes daily at 06:00 UTC, requiring zero manual intervention.
* **Architecture Optimization:** Builds specific `arm64-v8a`, `armeabi-v7a`, and `universal` APKs to reduce file size and improve performance on target devices.
* **Multi-Source Strategy:** Intelligent fetching from APKMirror, APKPure, and Uptodown ensures high success rates even if one source is down.
* **Granular Patch Control:** Simple text-based configuration allows for precise inclusion or exclusion of specific patches.
* **Smart Failover:** The system automatically switches download sources if a fetch attempt fails.
* **Auto-Signing:** All APKs are signed with a consistent public keystore, making them ready to install immediately.
* **Clean Release Cycle:** Previous releases are replaced rather than archived, preventing clutter and making it easy for external managers (like Orion) to track updates.

---

## 🛠️ Repository Structure

```text
revanced-nonroot/
├── .github/workflows/      # GitHub Actions automation
│   ├── patch.yml           # Daily automated builds (06:00 UTC)
│   └── manual-patch.yml    # Manual trigger workflow
├── apps/                   # APK source configurations
│   ├── apkmirror/          # APKMirror definitions
│   ├── apkpure/            # APKPure definitions
│   └── uptodown/           # UptoDown definitions
├── patches/                # Patch inclusion/exclusion rules
├── sources/                # ReVanced tool source definitions
├── src/                    # Core Python build logic
├── arch-config.json        # Architecture build matrix
├── patch-config.json       # App build configuration
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
    { "app_name": "youtube-music", "source": "morphe" },
    { "app_name": "X", "source": "crimera" }
  ]
}

```

### 2. Architecture Matrix (`arch-config.json`)

Specify which CPU architectures to target for each application.

```json
[
  {
    "app_name": "youtube",
    "source": "morphe",
    "arches": ["arm64-v8a", "armeabi-v7a", "universal"]
  },
  {
    "app_name": "youtube-music",
    "source": "morphe",
    "arches": ["arm64-v8a", "armeabi-v7a"]
  }
]

```

### 3. Source Definitions

Located in the `apps/` directory. Example for `apps/apkmirror/youtube.json`:

```json
{
  "org": "google-inc",
  "name": "youtube",
  "type": "APK",
  "arch": "universal",
  "dpi": "nodpi",
  "package": "com.google.android.youtube",
  "version": ""
}

```

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
git clone https://github.com/RookieEnough/morphe-AutoBuilds.git
cd morphe-nonroot

```


2. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install requests beautifulsoup4

```


3. **Run the build:**
You can build for a specific app and source.
```bash
export APP_NAME="youtube"
export SOURCE="morphe"
python -m src

```


4. **Target specific architecture (Optional):**
```bash
export APP_NAME="youtube"
export SOURCE="morphe"
export ARCH="arm64-v8a"  # Options: arm64-v8a, armeabi-v7a, universal
python -m src

```



---

## 🔄 GitHub Actions Workflows

### Daily Automated Build (`patch.yml`)

* **Schedule:** Runs daily at 06:00 UTC.
* **Function:** Iterates through all configured apps and architectures.
* **Output:** Updates the single "Latest" release tag.

### Manual Build (`manual-patch.yml`)

* **Trigger:** Manually via the GitHub Actions "Run workflow" button.
* **Capabilities:**
* Target specific apps.
* Target specific architectures.
* Force specific APK versions.
* Option to update the public release or just build artifacts.



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

> **Important:** This project is an automated build tool. The APKs provided in the releases are generated automatically using official Morphe tools and patches.

* **Affiliation:** These builds are **not** officially affiliated with the Morphe Team.
* **Usage:** Provided for educational and convenience purposes only. Use at your own risk.
* **GmsCore:** Morphe's MicroG-RE is required for these non-root apps to function correctly.
* **Updates:** Patches are automatically pulled from the latest sources; builds may occasionally contain experimental features.

---

<div align="center">

**If you found this project helpful, please consider giving it a ⭐ Star.**  
<br>
**Made with 💜 by RookieZ**

