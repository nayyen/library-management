/**
 * BookCoverPlaceholder — colored placeholder with book icon.
 * Uses the first letter of kategori to derive a deterministic colour.
 */

const CATEGORY_COLORS = {
  F: 'bg-amber-100 text-amber-800',
  N: 'bg-sky-100 text-sky-800',
  S: 'bg-emerald-100 text-emerald-800',
  E: 'bg-violet-100 text-violet-800',
  P: 'bg-rose-100 text-rose-800',
};

function getColor(kategori) {
  const first = (kategori ?? 'U').charAt(0).toUpperCase();
  return CATEGORY_COLORS[first] ?? 'bg-surface-container-highest text-on-surface-variant';
}

export default function BookCoverPlaceholder({ judul, kategori, className = '' }) {
  const colorClass = getColor(kategori);
  return (
    <div
      className={`w-full aspect-[3/4] rounded-lg flex flex-col items-center justify-center ${colorClass} ${className}`}
      role="img"
      aria-label={`Sampul buku ${judul}`}
    >
      <span className="material-symbols-outlined text-4xl mb-1">menu_book</span>
      <span className="text-body-sm font-body-sm text-center px-2 line-clamp-2">
        {kategori}
      </span>
    </div>
  );
}
