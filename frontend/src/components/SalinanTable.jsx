/**
 * SalinanTable — displays copies of a book in a table.
 *
 * Props:
 *   salinan       : array of { id, lokasi_rak, kondisi, status_ketersediaan }
 *   peran         : string    — 'mahasiswa' | 'pustakawan'
 *   onPinjam      : (salinan) => void — callback when Pinjam is clicked
 *   pinjamDisabled: boolean   — disable Pinjam button (blocked/at-limit)
 */

const kondisiLabel = {
  bagus: 'Bagus',
  rusak_ringan: 'Rusak Ringan',
  rusak_berat: 'Rusak Berat',
};

const statusLabel = {
  tersedia: 'Tersedia',
  dipesan: 'Dipesan',
  dipinjam: 'Dipinjam',
};

const statusColor = {
  tersedia: 'text-sage-green',
  dipesan: 'text-antique-gold',
  dipinjam: 'text-alert-crimson',
};

export default function SalinanTable({ salinan = [], peran, onPinjam, pinjamDisabled = false }) {
  if (salinan.length === 0) {
    return (
      <p className="text-body-md font-body-md text-outline-variant italic">
        Belum ada salinan buku ini.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-outline-variant/40">
            <th className="pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
              Rak
            </th>
            <th className="pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
              Kondisi
            </th>
            <th className="pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
              Status
            </th>
            {peran === 'mahasiswa' && (
              <th className="pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                Aksi
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {salinan.map((s) => (
            <tr
              key={s.id}
              className="border-b border-outline-variant/20 last:border-none"
            >
              <td className="py-3 text-body-md font-body-md text-primary">
                {s.lokasi_rak}
              </td>
              <td className="py-3 text-body-md font-body-md text-outline">
                {kondisiLabel[s.kondisi] ?? s.kondisi}
              </td>
              <td className="py-3">
                <span
                  className={`inline-flex items-center gap-1 text-body-sm font-body-sm ${statusColor[s.status_ketersediaan] ?? 'text-outline'}`}
                >
                  <span className="material-symbols-outlined text-[16px]">
                    {s.status_ketersediaan === 'tersedia'
                      ? 'check_circle'
                      : s.status_ketersediaan === 'dipinjam'
                        ? 'sync'
                        : 'schedule'}
                  </span>
                  {statusLabel[s.status_ketersediaan] ?? s.status_ketersediaan}
                </span>
              </td>
              {peran === 'mahasiswa' && (
                <td className="py-3">
                  {s.status_ketersediaan === 'tersedia' ? (
                    <button
                      type="button"
                      onClick={() => onPinjam?.(s)}
                      disabled={pinjamDisabled}
                      aria-disabled={pinjamDisabled}
                      aria-label={`Pinjam salinan di ${s.lokasi_rak}`}
                      className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm text-white transition-opacity min-h-[44px] ${
                        pinjamDisabled
                          ? 'bg-sage-green/50 cursor-not-allowed'
                          : 'bg-sage-green hover:opacity-90'
                      }`}
                    >
                      <span className="material-symbols-outlined text-[18px]">bookmark_add</span>
                      Pinjam
                    </button>
                  ) : (
                    <span className="text-body-sm font-body-sm text-outline-variant">&mdash;</span>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
