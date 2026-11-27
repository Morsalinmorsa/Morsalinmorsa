package com.turbodl.app

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import org.json.JSONArray
import java.io.File
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicBoolean

/** The download list, kept in memory and saved to a JSON file so it survives restarts. */
object DownloadStore {
    private lateinit var file: File
    private val items = ArrayList<DownloadItem>()
    private val listeners = CopyOnWriteArrayList<() -> Unit>()
    private val main = Handler(Looper.getMainLooper())
    private val pending = AtomicBoolean(false)
    private val dispatch = Runnable {
        pending.set(false)
        listeners.forEach { it() }
    }

    fun init(context: Context) {
        file = File(context.filesDir, "downloads.json")
        if (!file.exists()) return
        try {
            val arr = JSONArray(file.readText())
            for (i in 0 until arr.length()) {
                val item = DownloadItem.fromJson(arr.getJSONObject(i))
                // Anything that was running when the app died waits for the user to resume it.
                if (item.status.isActive) item.status = Status.PAUSED
                items.add(item)
            }
        } catch (e: Exception) {
            Log.w("TurboDL", "Could not read download list", e)
        }
    }

    fun all(): List<DownloadItem> = synchronized(items) { items.toList() }

    fun get(id: Long): DownloadItem? = synchronized(items) { items.firstOrNull { it.id == id } }

    fun add(item: DownloadItem) {
        synchronized(items) { items.add(item) }
        changed()
        save()
    }

    fun remove(id: Long) {
        synchronized(items) { items.removeAll { it.id == id } }
        changed()
        save()
    }

    fun addListener(listener: () -> Unit) = listeners.add(listener)
    fun removeListener(listener: () -> Unit) = listeners.remove(listener)

    /** Tell the UI to redraw. Calls are merged, so this is cheap to call often. */
    fun changed() {
        if (pending.compareAndSet(false, true)) main.post(dispatch)
    }

    fun save() {
        val json = synchronized(items) { JSONArray().apply { items.forEach { put(it.toJson()) } }.toString() }
        synchronized(this) {
            try {
                val tmp = File(file.path + ".tmp")
                tmp.writeText(json)
                tmp.renameTo(file)
            } catch (e: Exception) {
                Log.w("TurboDL", "Could not save download list", e)
            }
        }
    }
}
