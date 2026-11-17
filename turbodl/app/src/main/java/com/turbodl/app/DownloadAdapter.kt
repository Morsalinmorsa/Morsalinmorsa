package com.turbodl.app

import android.annotation.SuppressLint
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.recyclerview.widget.RecyclerView

class DownloadAdapter(
    private val onPrimary: (DownloadItem) -> Unit,
    private val onMore: (DownloadItem, View) -> Unit,
) : RecyclerView.Adapter<DownloadAdapter.Holder>() {

    private var items: List<DownloadItem> = emptyList()

    init {
        setHasStableIds(true)
    }

    @SuppressLint("NotifyDataSetChanged")
    fun submit(list: List<DownloadItem>) {
        items = list
        notifyDataSetChanged()
    }

    override fun getItemCount() = items.size
    override fun getItemId(position: Int) = items[position].id

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) =
        Holder(LayoutInflater.from(parent.context).inflate(R.layout.item_download, parent, false))

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(view: View) : RecyclerView.ViewHolder(view) {
        private val title: TextView = view.findViewById(R.id.title)
        private val status: TextView = view.findViewById(R.id.status)
        private val percent: TextView = view.findViewById(R.id.percent)
        private val bar: SegmentBar = view.findViewById(R.id.bar)
        private val action: ImageButton = view.findViewById(R.id.action)
        private val more: ImageButton = view.findViewById(R.id.more)

        fun bind(item: DownloadItem) {
            val ctx = itemView.context
            title.text = item.fileName
            bar.bind(item)

            val done = item.downloadedBytes
            val total = item.totalBytes
            val size = if (total > 0) "${Format.bytes(done)} / ${Format.bytes(total)}" else Format.bytes(done)
            val threads = item.parts.size
            status.text = when (item.status) {
                Status.QUEUED -> ctx.getString(R.string.status_queued)
                Status.CONNECTING -> ctx.getString(R.string.status_connecting)
                Status.RUNNING -> buildString {
                    append(size)
                    append(" · ")
                    append(ctx.getString(R.string.speed, Format.bytes(item.speed)))
                    if (total > 0 && item.speed > 0) {
                        append(" · ")
                        append(ctx.getString(R.string.time_left, Format.duration((total - done) / item.speed)))
                    }
                    append(" · ")
                    append(ctx.resources.getQuantityString(R.plurals.threads, threads, threads))
                }
                Status.SAVING -> ctx.getString(R.string.status_saving)
                Status.PAUSED -> ctx.getString(R.string.status_paused, size)
                Status.COMPLETED -> ctx.getString(R.string.status_completed, Format.bytes(total))
                Status.FAILED -> ctx.getString(R.string.status_failed, item.error ?: "")
            }
            percent.text = if (total > 0 || item.status == Status.COMPLETED) "${item.progress}%" else ""

            val (icon, label) = when (item.status) {
                Status.QUEUED, Status.CONNECTING, Status.RUNNING, Status.SAVING -> R.drawable.ic_pause to R.string.pause
                Status.PAUSED -> R.drawable.ic_play to R.string.resume
                Status.FAILED -> R.drawable.ic_refresh to R.string.retry
                Status.COMPLETED -> R.drawable.ic_open to R.string.open
            }
            action.setImageResource(icon)
            action.contentDescription = ctx.getString(label)
            action.isVisible = item.status != Status.SAVING
            action.setOnClickListener { onPrimary(item) }
            more.setOnClickListener { onMore(item, it) }
            itemView.setOnClickListener { if (item.status == Status.COMPLETED) onPrimary(item) }
        }
    }
}
