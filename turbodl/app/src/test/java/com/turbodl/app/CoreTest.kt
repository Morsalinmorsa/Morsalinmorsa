package com.turbodl.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class CoreTest {
    @Test
    fun smallFileUsesOneConnection() {
        val parts = Splitter.split(1000, 8)
        assertEquals(1, parts.size)
        assertEquals(0L, parts[0].start)
        assertEquals(999L, parts[0].end)
    }

    @Test
    fun partsCoverWholeFileWithoutGaps() {
        val total = 10L * 1024 * 1024 + 7
        val parts = Splitter.split(total, 8)
        assertEquals(8, parts.size)
        assertEquals(0L, parts.first().start)
        assertEquals(total - 1, parts.last().end)
        for (i in 1 until parts.size) assertEquals(parts[i - 1].end + 1, parts[i].start)
        assertEquals(total, parts.sumOf { it.length })
    }

    @Test
    fun unknownSizeStreamsToEnd() {
        val parts = Splitter.split(-1, 8)
        assertEquals(1, parts.size)
        assertEquals(-1L, parts[0].end)
    }

    @Test
    fun contentRangeTotal() {
        assertEquals(12345L, Headers.totalFromContentRange("bytes 0-0/12345"))
        assertEquals(-1L, Headers.totalFromContentRange("bytes 0-0/*"))
        assertEquals(-1L, Headers.totalFromContentRange(null))
    }

    @Test
    fun fileNames() {
        assertEquals("report.pdf", FileNames.fromContentDisposition("attachment; filename=\"report.pdf\""))
        assertEquals("naïve file.txt", FileNames.fromContentDisposition("attachment; filename*=UTF-8''na%C3%AFve%20file.txt"))
        assertEquals("plain.zip", FileNames.fromContentDisposition("attachment; filename=plain.zip"))
        assertNull(FileNames.fromContentDisposition("inline"))
        assertEquals("My File.zip", FileNames.fromUrl("https://example.com/a/b/My%20File.zip?x=1"))
        assertEquals("download", FileNames.fromUrl("https://example.com/"))
        assertEquals("a_b_c", FileNames.sanitize("a/b:c"))
    }

    @Test
    fun formatting() {
        assertEquals("512 B", Format.bytes(512))
        assertEquals("1.5 KB", Format.bytes(1536))
        assertEquals("1m 5s", Format.duration(65))
    }
}
