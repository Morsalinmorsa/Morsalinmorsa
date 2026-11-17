package com.turbodl.app

import org.json.JSONArray
import org.json.JSONObject

enum class Status {
    QUEUED, CONNECTING, RUNNING, SAVING, PAUSED, COMPLETED, FAILED;

    val isActive: Boolean get() = this == QUEUED || this == CONNECTING || this == RUNNING || this == SAVING
}

class DownloadItem(
    val id: Long,
    val url: String,
    @Volatile var fileName: String,
    val threads: Int,
    val autoName: Boolean,
    val createdAt: Long = System.currentTimeMillis(),
) {
    @Volatile var status = Status.QUEUED
    @Volatile var totalBytes = -1L
    @Volatile var supportsRanges = false
    @Volatile var mimeType: String? = null
    @Volatile var parts: List<Part> = emptyList()
    @Volatile var error: String? = null
    @Volatile var savedUri: String? = null

    /** Bytes per second, smoothed. Not saved. */
    @Volatile var speed = 0L

    val downloadedBytes: Long get() = parts.sumOf { it.downloaded }

    val progress: Int
        get() = when {
            status == Status.COMPLETED -> 100
            totalBytes > 0 -> (downloadedBytes * 100 / totalBytes).toInt().coerceIn(0, 100)
            else -> 0
        }

    fun toJson(): JSONObject = JSONObject().apply {
        put("id", id)
        put("url", url)
        put("name", fileName)
        put("threads", threads)
        put("autoName", autoName)
        put("created", createdAt)
        put("status", status.name)
        put("total", totalBytes)
        put("ranges", supportsRanges)
        put("mime", mimeType)
        put("error", error)
        put("uri", savedUri)
        put("parts", JSONArray().apply {
            parts.forEach { p -> put(JSONObject().put("s", p.start).put("e", p.end).put("d", p.downloaded)) }
        })
    }

    companion object {
        fun fromJson(o: JSONObject): DownloadItem {
            val item = DownloadItem(
                id = o.getLong("id"),
                url = o.getString("url"),
                fileName = o.getString("name"),
                threads = o.optInt("threads", 8),
                autoName = o.optBoolean("autoName", false),
                createdAt = o.optLong("created", System.currentTimeMillis()),
            )
            item.status = runCatching { Status.valueOf(o.getString("status")) }.getOrDefault(Status.PAUSED)
            item.totalBytes = o.optLong("total", -1)
            item.supportsRanges = o.optBoolean("ranges", false)
            item.mimeType = o.optString("mime").ifEmpty { null }
            item.error = o.optString("error").ifEmpty { null }
            item.savedUri = o.optString("uri").ifEmpty { null }
            val arr = o.optJSONArray("parts") ?: JSONArray()
            item.parts = List(arr.length()) { i ->
                val p = arr.getJSONObject(i)
                Part(p.getLong("s"), p.getLong("e"), p.getLong("d"))
            }
            return item
        }
    }
}
