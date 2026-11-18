package com.turbodl.app

import java.net.URI
import java.net.URLDecoder
import java.util.Locale

/** One byte range of a file, fetched by its own connection. [end] is inclusive; -1 means "until the stream ends". */
class Part(val start: Long, val end: Long, downloaded: Long = 0) {
    @Volatile
    var downloaded: Long = downloaded

    val length: Long get() = if (end < 0) -1L else end - start + 1
    val isDone: Boolean get() = end >= 0 && downloaded >= length
}

object Splitter {
    /** Parts smaller than this are not worth an extra connection. */
    const val MIN_PART_SIZE = 256L * 1024
    const val MAX_THREADS = 32

    fun split(total: Long, threads: Int): List<Part> {
        if (total <= 0) return listOf(Part(0, -1))
        val count = threads.coerceIn(1, MAX_THREADS).toLong()
            .coerceAtMost(maxOf(1L, total / MIN_PART_SIZE)).toInt()
        val size = total / count
        return List(count) { i ->
            val start = i * size
            val end = if (i == count - 1) total - 1 else start + size - 1
            Part(start, end)
        }
    }
}

object Headers {
    /** "bytes 0-0/12345" -> 12345, or -1 when unknown. */
    fun totalFromContentRange(value: String?): Long {
        if (value == null || !value.contains('/')) return -1
        return value.substringAfterLast('/').trim().toLongOrNull() ?: -1
    }
}

object FileNames {
    private val illegal = Regex("[\\\\/:*?\"<>|\\p{Cntrl}]")

    fun sanitize(name: String): String {
        val clean = illegal.replace(name, "_").trim().trim('.').take(150).trim()
        return clean.ifBlank { "download" }
    }

    fun fromUrl(url: String): String {
        val path = try {
            URI(url).rawPath
        } catch (e: Exception) {
            null
        } ?: url.substringBefore('?').substringBefore('#')
        val last = path.substringAfterLast('/')
        val decoded = try {
            URLDecoder.decode(last.replace("+", "%2B"), "UTF-8")
        } catch (e: Exception) {
            last
        }
        return sanitize(decoded)
    }

    fun fromContentDisposition(value: String?): String? {
        if (value.isNullOrBlank()) return null
        Regex("filename\\*\\s*=\\s*([^']*)'[^']*'([^;]+)", RegexOption.IGNORE_CASE).find(value)?.let { m ->
            val charset = m.groupValues[1].trim().ifBlank { "UTF-8" }
            return try {
                sanitize(URLDecoder.decode(m.groupValues[2].trim().trim('"'), charset))
            } catch (e: Exception) {
                null
            }
        }
        Regex("filename\\s*=\\s*\"([^\"]*)\"", RegexOption.IGNORE_CASE).find(value)?.let {
            return sanitize(it.groupValues[1])
        }
        Regex("filename\\s*=\\s*([^;]+)", RegexOption.IGNORE_CASE).find(value)?.let {
            return sanitize(it.groupValues[1].trim())
        }
        return null
    }
}

object Format {
    private val units = arrayOf("KB", "MB", "GB", "TB")

    fun bytes(bytes: Long): String {
        if (bytes < 1024) return "$bytes B"
        var value = bytes / 1024.0
        var i = 0
        while (value >= 1024 && i < units.size - 1) {
            value /= 1024
            i++
        }
        return String.format(Locale.US, if (value >= 100) "%.0f %s" else "%.1f %s", value, units[i])
    }

    fun duration(seconds: Long): String = when {
        seconds < 60 -> "${seconds}s"
        seconds < 3600 -> "${seconds / 60}m ${seconds % 60}s"
        else -> "${seconds / 3600}h ${(seconds % 3600) / 60}m"
    }
}
