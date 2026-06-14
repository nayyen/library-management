/**
 * ConfirmDialog — reusable confirmation modal.
 *
 * Props:
 *   title     : string
 *   message   : string
 *   confirmLabel : string  (default "Hapus")
 *   onConfirm : () => void
 *   onCancel  : () => void
 *   destructive: boolean  (default true — red confirm button)
 *   variant   : 'confirm' | 'info'  (info variant has only a Tutup button)
 *   loading   : boolean
 */
export default function ConfirmDialog({
  title = 'Konfirmasi',
  message = '',
  confirmLabel = 'Hapus',
  onConfirm,
  onCancel,
  destructive = true,
  variant = 'confirm',
  loading = false,
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-primary/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
    >
      <div className="bg-surface-container-lowest rounded-xl border border-paper-shadow p-6 max-w-sm w-full mx-4 book-shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 id="confirm-title" className="text-headline-sm font-headline-sm text-primary">
            {title}
          </h2>
          <button
            type="button"
            onClick={onCancel}
            className="w-11 h-11 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors"
            aria-label="Tutup"
          >
            <span className="material-symbols-outlined text-outline">close</span>
          </button>
        </div>

        <p className="text-body-md font-body-md text-outline mb-6">
          {message}
        </p>

        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={onCancel}
            className="px-5 py-2.5 rounded-full text-label-sm font-label-sm text-outline border border-outline-variant hover:bg-surface-container transition-colors"
          >
            {variant === 'info' ? 'Tutup' : 'Batal'}
          </button>

          {variant === 'confirm' && (
            <button
              type="button"
              onClick={onConfirm}
              disabled={loading}
              className={`px-5 py-2.5 rounded-full text-label-sm font-label-sm text-white transition-opacity disabled:opacity-50 inline-flex items-center gap-2 ${
                destructive ? 'bg-alert-crimson hover:opacity-90' : 'bg-antique-gold hover:opacity-90'
              }`}
            >
              {loading && (
                <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>
              )}
              {confirmLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
