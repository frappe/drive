import FileUploaderComponent from './FileUploader.vue'
import { createApp } from 'vue'

// The stock "Library" tab of `frappe.ui.FileUploader` browses framework File
// records. We replace it with a richer picker that adds Drive (Home/Teams) on
// top of the same framework "Site" files, and can upload a new file straight
// into a Drive folder. Either way the file is handed to the framework engine via
// `library_file_name`, so the caller's on_success (form field + attachments)
// fires exactly as before — no framework files are patched.

// Inner SVG content of frappe's stock "Library" icon. The framework template
// renders this inside its own `<svg width=30 height=30>`, so supply children only.
const LIBRARY_ICON =
  '<circle cx="15" cy="15" r="15" fill="var(--subtle-fg)" />' +
  '<path d="M13.0245 11.5H8C7.72386 11.5 7.5 11.7239 7.5 12V20C7.5 21.1046 8.39543 22 9.5 22H20.5C21.6046 22 22.5 21.1046 22.5 20V14.5C22.5 14.2239 22.2761 14 22 14H15.2169C15.0492 14 14.8926 13.9159 14.8 13.776L13.4414 11.724C13.3488 11.5841 13.1922 11.5 13.0245 11.5Z" fill="none" stroke="var(--text-color)" stroke-miterlimit="10" stroke-linecap="square" />' +
  '<path d="M8.87939 9.5V8.5C8.87939 8.22386 9.10325 8 9.37939 8H20.6208C20.8969 8 21.1208 8.22386 21.1208 8.5V12" fill="none" stroke="var(--text-color)" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round" />'

const LIBRARY_UPLOADER = {
  label: __('Library'),
  icon: LIBRARY_ICON,
  action: async ({ dialog, uploader }) => {
    dialog.hide()
    const d = new frappe.ui.Dialog({
      title: __('Library'),
    })
    // The picker owns its own action buttons; drop the dialog's default footer.
    d.$wrapper.find('.modal-footer').hide()

    const app = createApp(FileUploaderComponent, {
      uploader,
      onComplete: () => d.hide(),
    })
    // Inject frappe's Vue globals (__, frappe, …) the same way the framework
    // uploader does, otherwise template calls like __() blow up.
    SetVueGlobals(app)
    app.mount(d.body)
    d.$wrapper.on('hidden.bs.modal', () => app.unmount())
    d.show()
  },
}

// Move the Library button into the second slot (after "My Device"), where the
// stock browser button used to sit. The button is always the last .btn-file-upload
// (Vue appends additional_upload_handlers after the built-in buttons), so we
// look it up by position — translation-safe.
function placeLibrarySecond(wrapper) {
  try {
    const root = wrapper && (wrapper.get ? wrapper.get(0) : wrapper)
    if (!root) return
    const btns = Array.from(root.querySelectorAll('.btn-file-upload'))
    if (btns.length < 2) return
    const lib = btns[btns.length - 1] // our handler is always appended last
    const first = btns[0]
    if (lib.parentNode === first.parentNode && first.nextElementSibling !== lib) {
      first.after(lib)
    }
  } catch (e) {
    // Non-fatal: the Library option still works wherever it lands.
  }
}

;(async () => {
  await frappe.require('file_uploader.bundle.js')
  const Original = frappe.ui.FileUploader
  if (!Original || Original.__driveWrapped) return

  // Replace the Library tab everywhere: default `disable_file_browser` to true so
  // the stock browser button is hidden, and surface Drive as the source instead.
  // Subclassing keeps every call site (form attachments, grid, attach control,
  // communication, file view, …) working unchanged.
  class DriveFileUploader extends Original {
    constructor(opts = {}) {
      if (opts.disable_file_browser === undefined) {
        opts.disable_file_browser = true
      }
      super(opts)
      // Vue renders the source buttons synchronously on mount; move Library into
      // the slot the stock browser used to occupy (right after "My Device").
      placeLibrarySecond(this.wrapper)
    }
  }
  DriveFileUploader.__driveWrapped = true
  frappe.ui.FileUploader = DriveFileUploader

  // UploadOptions is inherited from Original; register the Library picker once.
  if (!Original.UploadOptions.some((o) => o.label === LIBRARY_UPLOADER.label)) {
    Original.UploadOptions.push(LIBRARY_UPLOADER)
  }
})()
