package com.turbodl.app

import android.app.Application

class TurboApp : Application() {
    override fun onCreate() {
        super.onCreate()
        DownloadStore.init(this)
        Downloader.init(this)
        Notifications.createChannels(this)
    }
}
