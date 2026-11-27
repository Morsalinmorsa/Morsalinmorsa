package com.turbodl.app

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import androidx.core.app.NotificationCompat

object Notifications {
    const val CHANNEL_PROGRESS = "downloads_progress"
    const val CHANNEL_DONE = "downloads_done"
    const val ID_PROGRESS = 1

    fun createChannels(context: Context) {
        val nm = context.getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_PROGRESS, context.getString(R.string.channel_progress), NotificationManager.IMPORTANCE_LOW)
        )
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_DONE, context.getString(R.string.channel_done), NotificationManager.IMPORTANCE_DEFAULT)
        )
    }

    fun progress(context: Context): Notification {
        val active = DownloadStore.all().filter {
            it.status == Status.RUNNING || it.status == Status.CONNECTING || it.status == Status.SAVING
        }
        val speed = active.sumOf { it.speed }
        val total = active.sumOf { it.totalBytes.coerceAtLeast(0) }
        val done = active.sumOf { it.downloadedBytes }
        val known = active.isNotEmpty() && active.all { it.totalBytes > 0 } && total > 0
        val percent = if (known) (done * 100 / total).toInt().coerceIn(0, 100) else 0
        val title = when (active.size) {
            0 -> context.getString(R.string.notif_preparing)
            1 -> active[0].fileName
            else -> context.getString(R.string.notif_many, active.size)
        }
        val text = context.getString(R.string.speed, Format.bytes(speed)) + if (known) " · $percent%" else ""

        val open = PendingIntent.getActivity(
            context, 0,
            Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE,
        )
        val pauseAll = PendingIntent.getService(
            context, 1,
            Intent(context, DownloadService::class.java).setAction(DownloadService.ACTION_PAUSE_ALL),
            PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(context, CHANNEL_PROGRESS)
            .setSmallIcon(R.drawable.ic_stat_download)
            .setContentTitle(title)
            .setContentText(text)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setSilent(true)
            .setProgress(100, percent, !known)
            .setContentIntent(open)
            .addAction(R.drawable.ic_pause, context.getString(R.string.pause_all), pauseAll)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .build()
    }

    fun completed(context: Context, item: DownloadItem) {
        if (Build.VERSION.SDK_INT >= 33 &&
            context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) return
        val uri = item.savedUri?.let(Uri::parse) ?: return
        val view = Intent(Intent.ACTION_VIEW)
            .setDataAndType(uri, item.mimeType ?: "*/*")
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        val pending = PendingIntent.getActivity(
            context, item.id.toInt(), view,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_DONE)
            .setSmallIcon(R.drawable.ic_stat_download)
            .setContentTitle(item.fileName)
            .setContentText(context.getString(R.string.notif_done, Format.bytes(item.totalBytes)))
            .setContentIntent(pending)
            .setAutoCancel(true)
            .build()
        context.getSystemService(NotificationManager::class.java)
            .notify(("done" + item.id).hashCode(), notification)
    }
}
