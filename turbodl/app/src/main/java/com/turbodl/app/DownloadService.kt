package com.turbodl.app

import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import androidx.core.content.ContextCompat

/** Keeps downloads running while the app is in the background and shows the progress notification. */
class DownloadService : Service() {
    private val handler = Handler(Looper.getMainLooper())
    private val ticker = object : Runnable {
        override fun run() {
            refresh()
            if (running) handler.postDelayed(this, 1000)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        running = true
        Notifications.createChannels(this)
        goForeground()
        handler.postDelayed(ticker, 1000)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        goForeground()
        if (intent?.action == ACTION_PAUSE_ALL) Downloader.pauseAll()
        return START_NOT_STICKY
    }

    private fun goForeground() {
        startForeground(
            Notifications.ID_PROGRESS,
            Notifications.progress(this),
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC,
        )
    }

    private fun refresh() {
        if (Downloader.activeCount == 0) {
            running = false
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
            return
        }
        getSystemService(NotificationManager::class.java)
            .notify(Notifications.ID_PROGRESS, Notifications.progress(this))
    }

    override fun onTimeout(startId: Int, fgsType: Int) {
        // Android 15 limits background data transfers; pause so they can be resumed later.
        Downloader.pauseAll()
        stopSelf()
    }

    override fun onDestroy() {
        running = false
        handler.removeCallbacks(ticker)
        super.onDestroy()
    }

    companion object {
        const val ACTION_PAUSE_ALL = "com.turbodl.app.PAUSE_ALL"

        @Volatile
        private var running = false

        fun ensureRunning(context: Context) {
            if (running) return
            try {
                ContextCompat.startForegroundService(context, Intent(context, DownloadService::class.java))
            } catch (e: Exception) {
                Log.w("TurboDL", "Could not start download service", e)
            }
        }
    }
}
