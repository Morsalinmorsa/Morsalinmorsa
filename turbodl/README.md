# TurboDL

A fast download manager for Android (Android 10+), in the style of apps like 1DM.

## Features

- **High-speed downloads:** each file is split into up to 16 parts that download at the same time over separate connections.
- **Segmented progress bar:** see every connection's part fill up.
- **Pause and resume:** progress is saved; downloads continue where they stopped, even after closing the app.
- **Auto-retry:** dropped connections retry up to 5 times.
- **Download queue:** choose how many files download at once (1–5).
- **Background downloads** with a progress notification, speed, and a "Pause all" button.
- **Share to download:** share a link from Chrome or any app to TurboDL, or paste a link (it reads the clipboard).
- Finished files are saved to **Download/TurboDL** and can be opened from the app or the notification.

## Getting the APK

Every push that changes `turbodl/` builds the app on GitHub Actions. Open the repository's
**Releases** page and download `TurboDL.apk` from the newest "TurboDL build". On your phone, allow
"Install unknown apps" for your browser or file manager when asked.

## Building it yourself

Install Android Studio, open the `turbodl` folder, and press Run. Or from a terminal with the Android SDK:

```
cd turbodl
./gradlew assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

## How the speed works

1. TurboDL asks the server for the first byte of the file (`Range: bytes=0-`). A `206` reply means the
   server allows downloading in parts, and `Content-Range` gives the file size.
2. The file is split into equal parts (at least 256 KB each), and each part is downloaded on its own
   connection, written straight into its place in the file.
3. Each part's progress is saved every couple of seconds, so pausing or a crash loses almost nothing.
4. When every part is done, the file is copied into your Downloads folder.

Servers that don't allow parts are downloaded over a single connection.
