import { Link } from 'react-router';
import AvailabilityBadge from './AvailabilityBadge';
import EmptyState from './EmptyState';

function SkeletonRows() {
  return (
    <tbody>
      {[1, 2, 3, 4, 5].map((i) => (
        <tr key={i} className="animate-pulse border-b border-outline-variant/20">
          {[1, 2, 3, 4, 5, 6, 7].map((j) => (
            <td key={j} className="py-3 px-2">
              <div className="h-4 bg-surface-container rounded w-3/4" />
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  );
}

/**
 * KelolaTable — pustakawan admin table with edit/delete actions.
 *
 * Props:
 *   books    : array
 *   onEdit   : (book) => void
 *   onDelete : (book) => void
 *   loading  : boolean
 */
export default function KelolaTable({ books = [], onEdit, onDelete, loading = false }) {
  if (loading) {
    return (
      <div className="overflow-x-auto bg-surface-container-lowest rounded-xl border border-outline-variant/40 book-shadow">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-outline-variant/40">
              {['Judul', 'Penulis', 'ISBN', 'Kategori', 'Tahun', 'Ketersediaan', 'Aksi'].map((h) => (
                <th key={h} className="px-3 py-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                  {h === 'Tahun' ? 'Tahun Terbit' : h}
                </th>
              ))}
            </tr>
          </thead>
          <SkeletonRows />
        </table>
      </div>
    );
  }

  if (books.length === 0) {
    return (
      <EmptyState
        icon="inventory_2"
        title="Belum Ada Buku"
        message="Belum ada buku dalam katalog. Tambah buku baru untuk memulai."
      />
    );
  }

  return (
    <div className="overflow-x-auto bg-surface-container-lowest rounded-xl border border-outline-variant/40 book-shadow">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-outline-variant/40">
            <th className="px-3 py-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">Judul</th>
            <th className="px-3 py-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">Penulis</th>
            <th className="px-3 py-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">ISBN</th>
            <th className="px-3 py-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">Kategori</th>
            <th className="px-3 py-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">Tahun Terbit</th>
            <th className="px-3 py-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">Ketersediaan</th>
            <th className="px-3 py-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">Aksi</th>
          </tr>
        </thead>
        <tbody>
          {books.map((buku, idx) => (
            <tr
              key={buku.id}
              className={`border-b border-outline-variant/20 last:border-none transition-colors ${
                idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-primary/[0.03]'
              }`}
            >
              <td className="px-3 py-3">
                <Link
                  to={`/katalog/${buku.id}`}
                  className="text-body-md font-label-md text-primary hover:text-antique-gold transition-colors no-underline"
                >
                  {buku.judul}
                </Link>
              </td>
              <td className="px-3 py-3 text-body-sm font-body-sm text-outline">{buku.penulis}</td>
              <td className="px-3 py-3 text-body-sm font-body-sm text-outline-variant font-mono">{buku.isbn}</td>
              <td className="px-3 py-3 text-body-sm font-body-sm text-outline">{buku.kategori}</td>
              <td className="px-3 py-3 text-body-sm font-body-sm text-outline">{buku.tahun_terbit}</td>
              <td className="px-3 py-3">
                <AvailabilityBadge tersedia={buku.tersedia} compact />
              </td>
              <td className="px-3 py-3">
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => onEdit(buku)}
                    className="w-11 h-11 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors"
                    aria-label={`Edit ${buku.judul}`}
                  >
                    <span className="material-symbols-outlined text-[20px] text-outline">edit</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(buku)}
                    className="w-11 h-11 flex items-center justify-center rounded-full hover:bg-error/10 transition-colors"
                    aria-label={`Hapus ${buku.judul}`}
                  >
                    <span className="material-symbols-outlined text-[20px] text-alert-crimson">delete</span>
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
