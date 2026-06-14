/**
 * BlockedBanner — persistent disable banner (D-04, LOAN-02/LOAN-03).
 *
 * Props:
 *   variant     : 'limit' | 'blocked' | null — renders nothing if falsy
 *   dendaAmount : number — outstanding denda amount for the blocked variant
 */

const variantConfig = {
  limit: {
    heading: 'Batas Pinjaman Tercapai',
    body: 'Anda memiliki 5 pinjaman aktif, batas maksimum yang diizinkan. Selesaikan atau kembalikan salah satu pinjaman sebelum mengajukan yang baru.',
    icon: 'inventory_2',
    class: 'bg-antique-gold/10 border-antique-gold/30 text-on-surface',
    iconClass: 'text-antique-gold',
  },
  blocked: {
    heading: 'Akun Diblokir',
    body: (dendaAmount) =>
      `Akun Anda diblokir karena denda Rp ${dendaAmount.toLocaleString('id-ID')} belum dibayar. Selesaikan pembayaran denda di perpustakaan untuk mengajukan pinjaman baru.`,
    icon: 'block',
    class: 'bg-alert-crimson/10 border-alert-crimson/30 text-alert-crimson',
    iconClass: 'text-alert-crimson',
  },
};

export default function BlockedBanner({ variant, dendaAmount }) {
  if (!variant) return null;

  const config = variantConfig[variant];
  if (!config) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`rounded-lg border p-4 flex items-start gap-3 mb-6 ${config.class}`}
    >
      <span
        className={`material-symbols-outlined text-2xl shrink-0 ${config.iconClass}`}
        aria-hidden="true"
      >
        {config.icon}
      </span>
      <div>
        <p className="text-label-md font-label-md">{config.heading}</p>
        <p className="text-body-lg font-body-lg mt-1">
          {typeof config.body === 'function'
            ? config.body(dendaAmount ?? 0)
            : config.body}
        </p>
      </div>
    </div>
  );
}
