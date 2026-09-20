<div align="center">

# Morphe Custom AutoBuilds (Non-Root)

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

## Quick Downloads

> **Last Updated:** August 11, 2026
> **Note:** All APKs are automatically rebuilt daily at 06:00 UTC to ensure you have the latest features and security patches.

### Download Links

| Mirror | Description | Link |
| :--- | :--- | :--- |
| **GitHub Releases** | Primary source. Contains all builds. | [**Download Latest Release**](https://github.com/yashrajrocxx/Mophe-AutoBuilds/releases/latest) |

### Obtainium Auto-Updates & 1-Click Install

This repository provides full first-class integration with [**Obtainium**](https://github.com/ImranR98/Obtainium), allowing you to install and automatically receive daily background updates for any or all apps directly from GitHub Releases with zero manual downloads.

#### Option 1: 1-Click Single App Install
Click the **Add to Obtainium** badge for any app in the catalog below on your Android device (with Obtainium installed). Obtainium will automatically open with the exact repository, APK filter regex, and version extractor preconfigured!

#### Option 2: Bulk Import All Apps
To import the entire curated catalog at once:
1. Open **Obtainium** on your Android device.
2. Tap the **+** button (or navigate to **Import / Export**) $\rightarrow$ select **Import from URL**.
3. Paste the configuration URL:
   ```text
   https://raw.githubusercontent.com/yashrajrocxx/Mophe-AutoBuilds/main/obtainium.json
   ```
4. Tap **Import**. All apps will be added to your Obtainium database and will automatically track daily releases.

> [!NOTE]
> **User Control & Local State:**
> In Obtainium, importing an app or the `obtainium.json` bundle adds the configuration to your device's local database. It is **not** a forced synchronization—you retain full freedom to install, delete, pause, or pin whichever apps you choose.

### Supported Apps & Patch Repositories

This repository compiles optimized builds using specific community patch repositories for our curated application catalog:

| Application | Package Name | Patch Source | Arch | Obtainium (1-Click) |
| :--- | :--- | :--- | :---: | :---: |
| **Brave Browser** | `com.brave.browser` | kveld9 | `arm64-v8a` | Pending build |
| **Depth Wallpaper** | `com.jndapp.depth.live.wallpaper` | rushiranpise | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.jndapp.depth.live.wallpaper%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Depth%2520Wallpaper%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Edepthwallpaper-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Edepthwallpaper-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Duolingo** | `com.duolingo` | hoodles | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.duolingo%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Duolingo%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Eduolingo-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Eduolingo-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Gboard** | `com.google.android.inputmethod.latin` | kveld9 | `arm64-v8a` | Pending build |
| **Google Photos** | `com.google.android.apps.photos` | rookie | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.google.android.apps.photos%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Google%2520Photos%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Egoogle-photos-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Egoogle-photos-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **HabitKit** | `com.roehl.habitkit` | paresh | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.roehl.habitkit%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522HabitKit%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Ehabitkit-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Ehabitkit-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Instagram** | `com.instagram.android` | piko | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.instagram.android%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Instagram%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Einstagram-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Einstagram-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **JioHotstar** | `in.startv.hotstar` | durgesh | `arm64-v8a` | Pending build |
| **Minimal Widgets** | `com.jndapp.minimal.widgets` | rushiranpise | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.jndapp.minimal.widgets%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Minimal%2520Widgets%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Eminimalwidgets-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Eminimalwidgets-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Notesnook** | `com.streetwriters.notesnook` | hxreborn | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.streetwriters.notesnook%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Notesnook%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Enotesnook-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Enotesnook-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Pinterest** | `com.pinterest` | browzomje | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.pinterest%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Pinterest%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Epinterest-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Epinterest-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Pocket Casts** | `au.com.shiftyjelly.pocketcasts` | rushiranpise | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522au.com.shiftyjelly.pocketcasts%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Pocket%2520Casts%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Epocketcasts-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Epocketcasts-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Proton Pass** | `proton.android.pass` | rushiranpise | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522proton.android.pass%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Proton%2520Pass%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Eprotonpass-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Eprotonpass-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Reddit** | `com.reddit.frontpage` | morphe | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.reddit.frontpage%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Reddit%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Ereddit-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Ereddit-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **SD Maid 2 / SE** | `eu.darken.sdmse` | paresh | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522eu.darken.sdmse%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522SD%2520Maid%25202%2520%2F%2520SE%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Esdmaidse-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Esdmaidse-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Server Auditor (Termius)** | `com.server.auditor.ssh.client` | rushiranpise | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.server.auditor.ssh.client%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Server%2520Auditor%2520%2528Termius%2529%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Eserverauditor-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Eserverauditor-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Telegram** | `org.telegram.messenger` | paresh | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522org.telegram.messenger%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Telegram%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Etelegram-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Etelegram-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Threads** | `com.instagram.barcelona` | rookie | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.instagram.barcelona%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Threads%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Ethreads-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Ethreads-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **Vivaldi Browser** | `com.vivaldi.browser` | kveld9 | `arm64-v8a` | Pending build |
| **Vocabulary** | `com.hrd.vocabulary` | morning-entree | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.hrd.vocabulary%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522Vocabulary%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Evocabulary-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Evocabulary-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **YouTube** | `com.google.android.youtube` | morphe | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.google.android.youtube%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522YouTube%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Eyoutube-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Eyoutube-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |
| **YouTube Music** | `com.google.android.apps.youtube.music` | morphe | `arm64-v8a` | [![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)](https://apps.obtainium.imranr.dev/redirect?r=obtainium%3A%2F%2Fapp%2F%257B%2522id%2522%253A%2522com.google.android.apps.youtube.music%2522%252C%2522url%2522%253A%2522https%253A%2F%2Fgithub.com%2Fyashrajrocxx%2FMophe-AutoBuilds%2522%252C%2522author%2522%253A%2522yashrajrocxx%2522%252C%2522name%2522%253A%2522YouTube%2520Music%2522%252C%2522preferredApkIndex%2522%253A0%252C%2522additionalSettings%2522%253A%2522%257B%255C%2522apkFilterRegEx%255C%2522%253A%255C%2522%255Eyoutube-music-arm64-v8a-.%252A-v.%252A%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522versionExtractionRegEx%255C%2522%253A%255C%2522%255Eyoutube-music-arm64-v8a-.%252A-v%2528.%252A%2529%255C%255C%255C%255C.apk%2524%255C%2522%252C%255C%2522matchGroupToUse%255C%2522%253A%255C%25221%255C%2522%257D%2522%257D) |

*(All builds are target-optimized for their respective architectures to reduce bundle sizes and increase device efficiency).*

---

## Key Technical Enhancements

This project has been massively overhauled with custom logic to provide maximum reliability:

* **Direct Google Play Downloads (`gplaydl`):** Bypasses all scraping blocks (like APKMirror IP bans) by downloading split-APKs entirely directly and securely from Google Play servers.
* **Smart Version History Resolver:** Automatically detects the exact community-recommended app version required by the patcher and traces its exact historical Google Play `versionCode` dynamically, falling back to the absolute latest version available if the patch supports it.
* **Automated Split Merging:** Implements `APKEditor` to dynamically merge Google Play split `.apk` clusters into single, installable bases before applying patches.
* **Fully Automated Pipeline:** GitHub Actions workflow executes daily at 06:00 UTC, requiring zero manual intervention, securing your tokens automatically via GitHub Secrets.
* **Auto-Signing:** All APKs are signed with a consistent public keystore, making them ready to install immediately.
* **Clean Release Cycle:** Previous releases are replaced rather than archived, preventing clutter and making it easy for external managers to track updates.

---

## Repository Structure

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

## Configuration Guide

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

## Local Build Instructions

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

## GitHub Actions Workflows

### Daily Automated Build (`patch.yml`)
* **Schedule:** Runs daily at 06:00 UTC.
* **Function:** Iterates through all configured apps and architectures using secure GitHub Secrets.
* **Output:** Updates the single "Latest" release tag.

### Manual Build (`manual-patch.yml`)
* **Trigger:** Manually via the GitHub Actions "Run workflow" button.
* **Capabilities:** Target specific apps, architectures, and force specific APK versions.

---

## Contributing
Contributions to improve the toolchain or add support for new apps are welcome.
1. **Fork** the repository.
2. **Create** a feature branch (`git checkout -b feature/new-app`).
3. **Test** your changes locally using the Python scripts.
4. **Commit** your changes (`git commit -m "Add support for new-app"`).
5. **Push** to the branch (`git push origin feature/new-app`).
6. **Open** a Pull Request.

---

## Disclaimer & Legal

> **Important:** This project is an automated build tool. The APKs provided in the releases are generated automatically using official and community ReVanced/Morphe tools and patches.

* **Affiliation:** These builds are **not** officially affiliated with the original developers or the Morphe Team.
* **Usage:** Provided for educational and convenience purposes only. Use at your own risk.
* **GmsCore:** Morphe's MicroG-RE is required for apps relying on Google services to function correctly.
* **Updates:** Patches are automatically pulled from the latest custom sources; builds may occasionally contain experimental features.

---

<div align="center">

**If you found this project helpful, please consider giving it a star.**  
<br>
**Maintained by RookieZ & Yashrajrocxx**

</div>
