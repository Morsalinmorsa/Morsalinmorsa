package com.turbodl.app

import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

object Http {
    private const val USER_AGENT =
        "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"

    class Response(val conn: HttpURLConnection, val finalUrl: String)

    /** Opens [url], following redirects (including http -> https), optionally asking for bytes [from]..[to]. */
    fun open(url: String, from: Long?, to: Long?): Response {
        var current = url
        repeat(10) {
            val conn = URL(current).openConnection() as HttpURLConnection
            conn.instanceFollowRedirects = false
            conn.connectTimeout = 15_000
            conn.readTimeout = 30_000
            conn.setRequestProperty("User-Agent", USER_AGENT)
            conn.setRequestProperty("Accept", "*/*")
            conn.setRequestProperty("Accept-Encoding", "identity")
            if (from != null) conn.setRequestProperty("Range", "bytes=$from-${to?.toString() ?: ""}")
            val code = conn.responseCode
            if (code in 301..308 && code != 304) {
                val location = conn.getHeaderField("Location")
                if (location != null) {
                    conn.disconnect()
                    current = URL(URL(current), location).toString()
                    return@repeat
                }
            }
            return Response(conn, current)
        }
        throw IOException("Too many redirects")
    }
}
