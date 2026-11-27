package com.turbodl.app

import android.content.ContentValues
import android.content.Context
import android.os.Environment
import android.os.SystemClock
import android.provider.MediaStore
import android.webkit.MimeTypeMap
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.launch
import java.io.File
import java.io.IOException
import java.io.RandomAccessFile

/**
 * Downloads one item. The file is split into parts and every part is fetched
 * over its own connection at the same time, which is what makes it fast.
 * Progress of each part is saved, so a paused or failed download continues
 * where it stopped.
 */
class Engine(private val context: Context, private val item: DownloadItem) {
    private var resolvedUrl: String? = null

    suspend fun run() {
        coroutineScope {
            val tmp = tempFile(context, item.id)
            if (item.parts.isEmpty() || !tmp.exists()) prepare(tmp)
            setStatus(Status.RUNNING)
            val ticker = launch { trackProgress() }
            try {
                item.parts.map { part -> async { downloadPart(part, tmp) } }.awaitAll()
            } finally {
                ticker.cancel()
            }
            item.speed = 0
            if (item.totalBytes < 0) {
                item.totalBytes = item.downloadedBytes
                RandomAccessFile(tmp, "rw").use { it.setLength(item.totalBytes) }
            }
            setStatus(Status.SAVING)
            publish(tmp)
        }
    }

    private suspend fun setStatus(status: Status) {
        currentCoroutineContext().ensureActive()
        item.status = status
        DownloadStore.changed()
    }

    /** Asks the server for the size and whether it allows downloading in parts. */
    private fun prepare(tmp: File) {
        val res = Http.open(item.url, 0L, null)
        val conn = res.conn
        try {
            val code = conn.responseCode
            if (code !in 200..299) throw IOException("Server returned HTTP $code")
            resolvedUrl = res.finalUrl
            item.supportsRanges = code == 206
            item.totalBytes = if (code == 206) {
                Headers.totalFromContentRange(conn.getHeaderField("Content-Range"))
            } else {
                conn.contentLengthLong
            }
            conn.contentType?.substringBefore(';')?.trim()?.lowercase()?.let { item.mimeType = it }
            if (item.autoName) {
                val name = FileNames.fromContentDisposition(conn.getHeaderField("Content-Disposition"))
                    ?: FileNames.fromUrl(res.finalUrl)
                item.fileName = withExtension(name, item.mimeType)
            }
        } finally {
            conn.disconnect()
        }
        if (item.totalBytes <= 0) item.supportsRanges = false
        item.parts = Splitter.split(item.totalBytes, if (item.supportsRanges) item.threads else 1)
        tmp.parentFile?.mkdirs()
        RandomAccessFile(tmp, "rw").use { it.setLength(maxOf(item.totalBytes, 0L)) }
        DownloadStore.save()
    }

    private suspend fun downloadPart(part: Part, tmp: File) {
        var attempt = 0
        while (true) {
            currentCoroutineContext().ensureActive()
            if (part.isDone) return
            // Without range support the only way to retry is from the start.
            if (!item.supportsRanges) part.downloaded = 0
            try {
                transfer(part, tmp)
                if (part.end < 0 || part.isDone) return
            } catch (e: IOException) {
                if (++attempt > MAX_RETRIES) throw e
                delay(1000L * attempt)
            }
        }
    }

    private suspend fun transfer(part: Part, tmp: File) {
        val from = part.start + part.downloaded
        val url = resolvedUrl ?: item.url
        val res = if (item.supportsRanges) Http.open(url, from, part.end) else Http.open(url, null, null)
        val conn = res.conn
        try {
            val code = conn.responseCode
            if (item.supportsRanges && code != 206) {
                throw IOException("Server stopped allowing resume (HTTP $code)")
            }
            if (code !in 200..299) throw IOException("Server returned HTTP $code")
            resolvedUrl = res.finalUrl
            RandomAccessFile(tmp, "rw").use { raf ->
                raf.seek(from)
                conn.inputStream.use { input ->
                    val buffer = ByteArray(BUFFER_SIZE)
                    while (true) {
                        currentCoroutineContext().ensureActive()
                        val remaining = if (part.end >= 0) part.length - part.downloaded else Long.MAX_VALUE
                        if (remaining <= 0) break
                        val n = input.read(buffer, 0, minOf(buffer.size.toLong(), remaining).toInt())
                        if (n < 0) break
                        raf.write(buffer, 0, n)
                        part.downloaded += n
                    }
                }
            }
            if (part.end >= 0 && !part.isDone) throw IOException("Connection closed early")
        } finally {
            conn.disconnect()
        }
    }

    private suspend fun trackProgress() {
        var lastBytes = item.downloadedBytes
        var lastTime = SystemClock.elapsedRealtime()
        var ticks = 0
        while (true) {
            delay(500)
            val now = SystemClock.elapsedRealtime()
            val bytes = item.downloadedBytes
            val instant = (bytes - lastBytes) * 1000 / (now - lastTime).coerceAtLeast(1)
            item.speed = if (item.speed == 0L) instant else (item.speed * 0.6 + instant * 0.4).toLong()
            lastBytes = bytes
            lastTime = now
            DownloadStore.changed()
            if (++ticks % 4 == 0) DownloadStore.save()
        }
    }

    /** Copies the finished file into the phone's Download/TurboDL folder. */
    private fun publish(tmp: File) {
        val resolver = context.contentResolver
        val mime = item.mimeType?.takeIf { it != "application/octet-stream" } ?: guessMime(item.fileName)
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, item.fileName)
            put(MediaStore.MediaColumns.MIME_TYPE, mime)
            put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/TurboDL")
            put(MediaStore.MediaColumns.IS_PENDING, 1)
        }
        val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
            ?: throw IOException("Could not create the file in Downloads")
        try {
            val out = resolver.openOutputStream(uri) ?: throw IOException("Could not write to Downloads")
            out.use { o -> tmp.inputStream().use { it.copyTo(o, BUFFER_SIZE) } }
            values.clear()
            values.put(MediaStore.MediaColumns.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        } catch (e: Exception) {
            resolver.delete(uri, null, null)
            throw e
        }
        tmp.delete()
        item.mimeType = mime
        item.savedUri = uri.toString()
    }

    companion object {
        private const val MAX_RETRIES = 5
        private const val BUFFER_SIZE = 64 * 1024

        fun tempFile(context: Context, id: Long): File =
            File(context.getExternalFilesDir(null) ?: context.filesDir, "partial/$id.part")

        fun guessMime(name: String): String {
            val ext = name.substringAfterLast('.', "").lowercase()
            return MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext) ?: "application/octet-stream"
        }

        fun withExtension(name: String, mime: String?): String {
            if (name.contains('.') || mime == null) return name
            val ext = MimeTypeMap.getSingleton().getExtensionFromMimeType(mime) ?: return name
            return "$name.$ext"
        }
    }
}
