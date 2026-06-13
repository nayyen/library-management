/**
 * StatusBadge — peminjaman status pill badge for all 5 statuses.
 *
 * Props:
 *   status  : string — one of menunggu_persetujuan, siap_diambil, dipinjam, ditolak, dibatalkan
 *   compact : boolean — smaller variant for dense tables
 */

const variants = {
  menunggu_persetujuan: {
    label: 'Menunggu Persetujuan',
    class: 'bg-antique-gold/10 text-antique-gold border-antique-gold/20',
    icon: 'hourglass_empty',
  },
  siap_diambil: {
    label: 'Siap Diambil',
    class: 'bg-sage-green/10 text-sage-green border-sage-green/20',
    icon: 'event_available',
  },
  dipinjam: {
    label: 'Dipinjam',
    class: 'bg-primary-container/10 text-primary-container border-primary-fixed',
    icon: 'inventory_2',
  },
  ditolak: {
    label: 'Ditolak',
    class: 'bg-alert-crimson/10 text-alert-crimson border-alert-crimson/20',
    icon: 'cancel',
  },
  dibatalkan: {
    label: 'Dibatalkan',
    class: 'bg-surface-container text-on-surface-variant border-outline-variant',
    icon: 'close',
  },
};

export default function StatusBadge({ status, compact = false }) {
  const v = variants[status] ?? {
    label: status ?? 'Unknown',
    class: 'bg-surface-container text-on-surface-variant border-outline-variant',
    icon: 'help',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 border rounded-full font-label-sm ${v.class} ${
        compact ? 'px-2 py-0.5 text-[11px]' : 'px-3 py-1 text-label-sm'
      }`}
    >
      <span
        className="material-symbols-outlined"
        style={{ fontSize: compact ? 14 : 16 }}
        aria-hidden="true"
      >
        {v.icon}
      </span>
      {v.label}
    </span>
  );
}
