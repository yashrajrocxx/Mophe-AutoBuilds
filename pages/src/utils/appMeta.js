/**
 * Display metadata and icons for the apps currently in the build matrix.
 */

export const APP_METADATA = {
  "youtube": {
    name: "YouTube",
    category: "Video & Streaming",
    package: "com.google.android.youtube",
    icon: "https://play-lh.googleusercontent.com/QNmuZQc9I6Zbe3mWnSr0hycnENqGFCI5p3yE29Hkxtf22T0IWS6zTrpxULLyyjWpB7ONAXDsDQXnXcVWokl3eg=w240-h480",
    color: "#FF0000"
  },
  "youtube-music": {
    name: "YouTube Music",
    category: "Audio & Music",
    package: "com.google.android.apps.youtube.music",
    icon: "https://play-lh.googleusercontent.com/MyptZXmcCyF59phIWPsNCfHq6zSO_ojEdw_4rMYYWPOGdikSjqeOXcoszBZ053VYpINe5K7ZR9KV1nkFWgxdOw=w240-h480",
    color: "#FF0000"
  },
  "reddit": {
    name: "Reddit",
    category: "Social & Forums",
    package: "com.reddit.frontpage",
    icon: "https://play-lh.googleusercontent.com/8FVS0kvM60JwqZWRNzBIlwrZZxJa8vpli8IWaaTo8QXRe1PHmCNJ8UpWoXkGPV3jKEaTY2OVAeYoisOnGJXY=w240-h480",
    color: "#FF4500"
  },
  "instagram": {
    name: "Instagram",
    category: "Photo & Video",
    package: "com.instagram.android",
    icon: "https://play-lh.googleusercontent.com/yHi59jmO_lVamcyJ1i3rM1_E8bAiAspShnGjjURq05ipQQSUksO3QVEsXTegRSqul038-4YNA7O644XAcx251Q=w240-h480",
    color: "#E1306C"
  },
  "twitter": {
    name: "X (Twitter)",
    category: "Social",
    package: "com.twitter.android",
    icon: "https://play-lh.googleusercontent.com/TKHnIPNIAiEcvJWFqOTcnWqVFXxGJumIBfTLXdSy70hVUq5IkAZ2R3hOW08mHqEAmg=w240-h480",
    color: "#000000"
  },
  "pinterest": {
    name: "Pinterest",
    category: "Lifestyle & Design",
    package: "com.pinterest",
    icon: "https://play-lh.googleusercontent.com/dV49tQz7_kR743r9u8s932yU0s9=w240-h480",
    color: "#BD081C"
  },
  "telegram": {
    name: "Telegram",
    category: "Messaging",
    package: "org.telegram.messenger.web",
    icon: "https://play-lh.googleusercontent.com/ZU9AnVdaacxATubdaFCVYduw2WPmnwapkcm4ApduPrFGbaAzIlMr4-9wfA1ajSBQiz8=w240-h480",
    color: "#229ED9"
  },
  "sdmaidse": {
    name: "SD Maid 2 / SE",
    category: "System Tools",
    package: "eu.darken.sdmse",
    icon: "https://play-lh.googleusercontent.com/H6_eZ_xS8d9M8b6Xm9Q8_x=w240-h480",
    color: "#2E7D32"
  },
  "threads": {
    name: "Threads",
    category: "Social Network",
    package: "com.instagram.barcelona",
    icon: "https://play-lh.googleusercontent.com/qLh5M_hKq6q8v8=w240-h480",
    color: "#000000"
  },
  "google-photos": {
    name: "Google Photos",
    category: "Cloud & Photos",
    package: "com.google.android.apps.photos",
    icon: "https://play-lh.googleusercontent.com/u_Yv0X9uT0Z_z0K0q0x0v8=w240-h480",
    color: "#4285F4"
  },
  "pocketcasts": {
    name: "Pocket Casts",
    category: "Podcasts & Audio",
    package: "au.com.shiftyjelly.pocketcasts",
    icon: "https://play-lh.googleusercontent.com/dK8q_x9=w240-h480",
    color: "#F43E37"
  },
  "depthwallpaper": {
    name: "Depth Wallpaper",
    category: "Personalization",
    package: "com.depth.wallpaper",
    icon: "https://play-lh.googleusercontent.com/d6_x8q9=w240-h480",
    color: "#673AB7"
  },
  "minimalwidgets": {
    name: "Minimal Widgets",
    category: "Personalization",
    package: "com.minimal.widgets",
    icon: "https://play-lh.googleusercontent.com/m8_x8q9=w240-h480",
    color: "#3F51B5"
  },
  "gboard": {
    name: "Gboard",
    category: "Tools & Keyboard",
    package: "com.google.android.inputmethod.latin",
    icon: "https://play-lh.googleusercontent.com/g8_x9f0=w240-h480",
    color: "#4285F4"
  },
  "duolingo": {
    name: "Duolingo",
    category: "Education & Languages",
    package: "com.duolingo",
    icon: "https://play-lh.googleusercontent.com/1-hPxO5dascgnIbEd3NIHRJ3mEsio8YphRCYDVdxPtRFaqBXurPUtdjqTRUCIDCHeyE=w240-h480",
    color: "#58CC02"
  },
  "brave": {
    name: "Brave Browser",
    category: "Web Browser",
    package: "com.brave.browser",
    icon: "https://play-lh.googleusercontent.com/78b9_x8=w240-h480",
    color: "#FF3B00"
  },
  "discord": {
    name: "Discord",
    category: "Communication",
    package: "com.discord",
    icon: "https://play-lh.googleusercontent.com/0oO5mmZMt5ZrqA4aqlFTnnUD005nAsKiPqa9qaQAuBpOb5SpST6UWi61IXxPeQN7XWQ=w240-h480",
    color: "#5865F2"
  },
  "chess": {
    name: "Chess.com",
    category: "Board Games",
    package: "com.chess",
    icon: "https://play-lh.googleusercontent.com/6U8YqjKvdvOQkO9YFkU5nK9uE_7wVqXkZ6zP=w240-h480",
    color: "#81B64C"
  }
};

export function getAppMeta(appName) {
  const key = (appName || "").toLowerCase().trim();
  const meta = APP_METADATA[key] || {};
  return {
    name: meta.name || appName.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    category: meta.category || "Application",
    package: meta.package || "",
    icon: meta.icon || "",
    color: meta.color || "#FF6F61"
  };
}
