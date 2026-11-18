package com.turbodl.app

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.ClipData
import android.content.ClipboardManager
import android.content.DialogInterface
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.PopupMenu
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.recyclerview.widget.SimpleItemAnimator
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.slider.Slider
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import java.net.URL

class MainActivity : AppCompatActivity() {
    private lateinit var adapter: DownloadAdapter
    private lateinit var emptyView: View
    private val listener: () -> Unit = { refresh() }
    private val notificationPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) {}

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        setSupportActionBar(findViewById(R.id.toolbar))

        emptyView = findViewById(R.id.empty)
        adapter = DownloadAdapter(::onPrimaryAction, ::onMore)
        val list = findViewById<RecyclerView>(R.id.list)
        list.layoutManager = LinearLayoutManager(this)
        list.adapter = adapter
        (list.itemAnimator as? SimpleItemAnimator)?.supportsChangeAnimations = false

        findViewById<View>(R.id.fab).setOnClickListener { showAddDialog(null) }

        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }

        if (savedInstanceState == null) handleIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)
    }

    override fun onStart() {
        super.onStart()
        DownloadStore.addListener(listener)
        refresh()
    }

    override fun onStop() {
        DownloadStore.removeListener(listener)
        super.onStop()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        when (item.itemId) {
            R.id.action_pause_all -> Downloader.pauseAll()
            R.id.action_resume_all -> Downloader.resumeAll()
            R.id.action_clear_completed -> DownloadStore.all()
                .filter { it.status == Status.COMPLETED }
                .forEach { Downloader.remove(it.id, deleteFile = false) }
            R.id.action_settings -> showSettingsDialog()
            else -> return super.onOptionsItemSelected(item)
        }
        return true
    }

    private fun refresh() {
        val items = DownloadStore.all().sortedByDescending { it.createdAt }
        adapter.submit(items)
        emptyView.isVisible = items.isEmpty()
    }

    private fun handleIntent(intent: Intent?) {
        val text = when (intent?.action) {
            Intent.ACTION_SEND -> intent.getStringExtra(Intent.EXTRA_TEXT)
            Intent.ACTION_VIEW -> intent.dataString
            else -> null
        } ?: return
        val url = URL_REGEX.find(text)?.value ?: return
        showAddDialog(url)
    }

    private fun onPrimaryAction(item: DownloadItem) {
        when (item.status) {
            Status.QUEUED, Status.CONNECTING, Status.RUNNING -> Downloader.pause(item.id)
            Status.PAUSED, Status.FAILED -> Downloader.resume(item.id)
            Status.COMPLETED -> openFile(item)
            Status.SAVING -> Unit
        }
    }

    private fun onMore(item: DownloadItem, anchor: View) {
        val popup = PopupMenu(this, anchor)
        val menu = popup.menu
        menu.add(0, MENU_COPY, 0, R.string.copy_link)
        menu.add(0, MENU_RESTART, 1, R.string.download_again)
        menu.add(0, MENU_REMOVE, 2, R.string.remove_from_list)
        if (item.savedUri != null) menu.add(0, MENU_DELETE, 3, R.string.delete_file)
        popup.setOnMenuItemClickListener {
            when (it.itemId) {
                MENU_COPY -> {
                    getSystemService(ClipboardManager::class.java)
                        ?.setPrimaryClip(ClipData.newPlainText("link", item.url))
                    Toast.makeText(this, R.string.link_copied, Toast.LENGTH_SHORT).show()
                }
                MENU_RESTART -> Downloader.restart(item.id)
                MENU_REMOVE -> Downloader.remove(item.id, deleteFile = false)
                MENU_DELETE -> MaterialAlertDialogBuilder(this)
                    .setTitle(R.string.delete_file)
                    .setMessage(getString(R.string.delete_confirm, item.fileName))
                    .setPositiveButton(R.string.delete) { _, _ -> Downloader.remove(item.id, deleteFile = true) }
                    .setNegativeButton(android.R.string.cancel, null)
                    .show()
            }
            true
        }
        popup.show()
    }

    private fun openFile(item: DownloadItem) {
        val uri = item.savedUri?.let(Uri::parse) ?: return
        val intent = Intent(Intent.ACTION_VIEW)
            .setDataAndType(uri, item.mimeType ?: "*/*")
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        try {
            startActivity(intent)
        } catch (e: ActivityNotFoundException) {
            Toast.makeText(this, R.string.no_app, Toast.LENGTH_SHORT).show()
        }
    }

    private fun showAddDialog(prefill: String?) {
        val view = layoutInflater.inflate(R.layout.dialog_add, null)
        val urlLayout = view.findViewById<TextInputLayout>(R.id.layout_url)
        val urlInput = view.findViewById<TextInputEditText>(R.id.input_url)
        val nameInput = view.findViewById<TextInputEditText>(R.id.input_name)
        val slider = view.findViewById<Slider>(R.id.slider_threads)
        val label = view.findViewById<TextView>(R.id.label_threads)

        urlInput.setText(prefill ?: clipboardUrl())
        slider.value = Downloader.defaultThreads.toFloat().coerceIn(slider.valueFrom, slider.valueTo)
        val updateLabel = { label.text = getString(R.string.threads_label, slider.value.toInt()) }
        updateLabel()
        slider.addOnChangeListener { _, _, _ -> updateLabel() }

        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle(R.string.new_download)
            .setView(view)
            .setPositiveButton(R.string.download, null)
            .setNegativeButton(android.R.string.cancel, null)
            .create()
        dialog.setOnShowListener {
            dialog.getButton(DialogInterface.BUTTON_POSITIVE).setOnClickListener {
                val url = urlInput.text?.toString()?.trim().orEmpty()
                if (!isValidUrl(url)) {
                    urlLayout.error = getString(R.string.invalid_url)
                    return@setOnClickListener
                }
                Downloader.add(url, nameInput.text?.toString(), slider.value.toInt())
                dialog.dismiss()
            }
        }
        dialog.show()
    }

    private fun showSettingsDialog() {
        val view = layoutInflater.inflate(R.layout.dialog_settings, null)
        val threads = view.findViewById<Slider>(R.id.slider_threads)
        val threadsLabel = view.findViewById<TextView>(R.id.label_threads)
        val parallel = view.findViewById<Slider>(R.id.slider_parallel)
        val parallelLabel = view.findViewById<TextView>(R.id.label_parallel)

        threads.value = Downloader.defaultThreads.toFloat().coerceIn(threads.valueFrom, threads.valueTo)
        parallel.value = Downloader.maxConcurrent.toFloat().coerceIn(parallel.valueFrom, parallel.valueTo)
        val update = {
            threadsLabel.text = getString(R.string.threads_label, threads.value.toInt())
            parallelLabel.text = getString(R.string.parallel_label, parallel.value.toInt())
        }
        update()
        threads.addOnChangeListener { _, _, _ -> update() }
        parallel.addOnChangeListener { _, _, _ -> update() }

        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.settings)
            .setView(view)
            .setPositiveButton(R.string.save) { _, _ ->
                Downloader.defaultThreads = threads.value.toInt()
                Downloader.maxConcurrent = parallel.value.toInt()
            }
            .setNegativeButton(android.R.string.cancel, null)
            .show()
    }

    private fun clipboardUrl(): String? {
        val clip = getSystemService(ClipboardManager::class.java)?.primaryClip ?: return null
        if (clip.itemCount == 0) return null
        val text = clip.getItemAt(0).coerceToText(this)?.toString() ?: return null
        return URL_REGEX.find(text)?.value
    }

    private fun isValidUrl(url: String): Boolean = try {
        val u = URL(url)
        (u.protocol == "http" || u.protocol == "https") && !u.host.isNullOrBlank()
    } catch (e: Exception) {
        false
    }

    companion object {
        private val URL_REGEX = Regex("https?://\\S+", RegexOption.IGNORE_CASE)
        private const val MENU_COPY = 1
        private const val MENU_RESTART = 2
        private const val MENU_REMOVE = 3
        private const val MENU_DELETE = 4
    }
}
