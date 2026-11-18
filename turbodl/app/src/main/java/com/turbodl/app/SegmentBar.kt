package com.turbodl.app

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat

/** Progress bar that shows every connection's part separately, so you can see the threads working. */
class SegmentBar @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    private fun paint(color: Int) = Paint(Paint.ANTI_ALIAS_FLAG).apply { this.color = ContextCompat.getColor(context, color) }

    private val trackPaint = paint(R.color.seg_track)
    private val fillPaint = paint(R.color.seg_fill)
    private val pausedPaint = paint(R.color.seg_paused)
    private val errorPaint = paint(R.color.seg_error)
    private val rect = RectF()
    private val clip = Path()

    private var total = 0L
    private var starts = LongArray(0)
    private var done = LongArray(0)
    private var status = Status.QUEUED

    fun bind(item: DownloadItem) {
        val parts = item.parts
        total = item.totalBytes
        starts = LongArray(parts.size) { parts[it].start }
        done = LongArray(parts.size) { parts[it].downloaded }
        status = item.status
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        val r = h / 2
        rect.set(0f, 0f, w, h)
        canvas.drawRoundRect(rect, r, r, trackPaint)
        if (status == Status.COMPLETED) {
            canvas.drawRoundRect(rect, r, r, fillPaint)
            return
        }
        if (total <= 0) return
        val paint = when (status) {
            Status.FAILED -> errorPaint
            Status.PAUSED -> pausedPaint
            else -> fillPaint
        }
        val gap = if (starts.size > 1) resources.displayMetrics.density else 0f
        canvas.save()
        clip.reset()
        clip.addRoundRect(rect, r, r, Path.Direction.CW)
        canvas.clipPath(clip)
        for (i in starts.indices) {
            val x0 = starts[i].toFloat() / total * w + if (starts[i] > 0) gap else 0f
            val x1 = (starts[i] + done[i]).toFloat() / total * w
            if (x1 > x0) canvas.drawRect(x0, 0f, x1, h, paint)
        }
        canvas.restore()
    }
}
