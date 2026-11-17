package com.turbodl.app

import android.content.Context
import android.content.SharedPreferences
import android.net.Uri
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentHashMap

/** Runs the download queue: starts, pauses, resumes and removes downloads. */
object Downloader {
    private lateinit var app: Context
    private lateinit var prefs: SharedPreferences
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val jobs = ConcurrentHashMap<Long, Job>()
    private var lastId = 0L

    var maxConcurrent: Int
        get() = prefs.getInt("max_concurrent", 3)
        set(value) {
            prefs.edit().putInt("max_concurrent", value).apply()
            schedule()
        }

    var defaultThreads: Int
        get() = prefs.getInt("threads", 8)
        set(value) = prefs.edit().putInt("threads", value).apply()

    val activeCount: Int get() = jobs.size

    fun init(context: Context) {
        app = context.applicationContext
        prefs = app.getSharedPreferences("settings", Context.MODE_PRIVATE)
    }

    @Synchronized
    private fun newId(): Long {
        lastId = maxOf(System.currentTimeMillis(), lastId + 1)
        return lastId
    }

    fun add(url: String, name: String?, threads: Int): DownloadItem {
        val auto = name.isNullOrBlank()
        val fileName = if (auto) FileNames.fromUrl(url) else FileNames.sanitize(name!!)
        val item = DownloadItem(newId(), url.trim(), fileName, threads, auto)
        DownloadStore.add(item)
        schedule()
        return item
    }

    fun pause(id: Long) {
        val item = DownloadStore.get(id) ?: return
        if (item.status.isActive) item.status = Status.PAUSED
        jobs[id]?.cancel()
        item.speed = 0
        DownloadStore.changed()
        DownloadStore.save()
    }

    fun pauseAll() = DownloadStore.all().filter { it.status.isActive }.forEach { pause(it.id) }

    fun resume(id: Long) {
        val item = DownloadStore.get(id) ?: return
        if (item.status == Status.PAUSED || item.status == Status.FAILED) {
            item.status = Status.QUEUED
            item.error = null
            DownloadStore.changed()
            schedule()
        }
    }

    fun resumeAll() = DownloadStore.all().forEach { resume(it.id) }

    /** Throws away progress and downloads the file again from the start. */
    fun restart(id: Long) {
        val item = DownloadStore.get(id) ?: return
        jobs[id]?.cancel()
        Engine.tempFile(app, id).delete()
        item.parts = emptyList()
        item.totalBytes = -1
        item.savedUri = null
        item.error = null
        item.speed = 0
        item.status = Status.QUEUED
        DownloadStore.changed()
        schedule()
    }

    fun remove(id: Long, deleteFile: Boolean) {
        val item = DownloadStore.get(id) ?: return
        jobs[id]?.cancel()
        Engine.tempFile(app, id).delete()
        if (deleteFile) {
            item.savedUri?.let { runCatching { app.contentResolver.delete(Uri.parse(it), null, null) } }
        }
        DownloadStore.remove(id)
    }

    @Synchronized
    fun schedule() {
        val queued = DownloadStore.all().filter { it.status == Status.QUEUED }.sortedBy { it.createdAt }
        for (item in queued) {
            if (jobs.size >= maxConcurrent) break
            if (jobs.containsKey(item.id)) continue // old job still shutting down
            start(item)
        }
        if (jobs.isNotEmpty()) DownloadService.ensureRunning(app)
    }

    private fun start(item: DownloadItem) {
        item.status = Status.CONNECTING
        DownloadStore.changed()
        val job = scope.launch(start = CoroutineStart.LAZY) {
            try {
                Engine(app, item).run()
                if (isActive) item.status = Status.COMPLETED
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                if (isActive) {
                    item.status = Status.FAILED
                    item.error = e.message ?: e.javaClass.simpleName
                }
            }
        }
        jobs[item.id] = job
        job.invokeOnCompletion {
            jobs.remove(item.id, job)
            item.speed = 0
            DownloadStore.save()
            DownloadStore.changed()
            if (item.status == Status.COMPLETED) Notifications.completed(app, item)
            schedule()
        }
        job.start()
    }
}
