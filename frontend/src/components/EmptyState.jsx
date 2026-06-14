/**
 * EmptyState — shown when search/filter yields no results.
 *
 * Props:
 *   icon       : string   — Material Symbols icon name
 *   title      : string
 *   message    : string
 *   actionLabel: string   — optional reset button label
 *   onAction   : () => void
 */
export default function EmptyState({
  icon = 'search_off',
  title = 'Tidak Ditemukan',
  message = 'Tidak ada buku yang sesuai dengan pencarian Anda.',
  actionLabel,
  onAction,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <span className="material-symbols-outlined text-6xl text-outline-variant mb-4">
        {icon}
      </span>
      <h3 className="text-headline-sm font-headline-sm text-primary mb-2">{title}</h3>
      <p className="text-body-md font-body-md text-outline max-w-sm">{message}</p>
      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="mt-6 bg-antique-gold text-white rounded-full px-6 py-2.5 text-label-sm font-label-sm hover:opacity-90 transition-opacity"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
