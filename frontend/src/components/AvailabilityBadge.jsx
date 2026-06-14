/**
 * AvailabilityBadge — shows book availability status.
 *
 * Props:
 *   tersedia  : boolean  — whether at least one copy is available
 *   compact   : boolean  — smaller variant for cards
 */

const variants = {
  tersedia: {
    label: 'Tersedia',
    class: 'bg-sage-green/10 text-sage-green border-sage-green/20',
    icon: 'check_circle',
  },
  tidak_tersedia: {
    label: 'Tidak Tersedia',
    class: 'bg-alert-crimson/10 text-alert-crimson border-alert-crimson/20',
    icon: 'block',
  },
};

export default function AvailabilityBadge({ tersedia, compact = false }) {
  const v = tersedia ? variants.tersedia : variants.tidak_tersedia;

  return (
    <span
      className={`inline-flex items-center gap-1 border rounded-full font-label-sm ${v.class} ${
        compact ? 'px-2 py-0.5 text-[11px]' : 'px-3 py-1 text-label-sm'
      }`}
    >
      <span className="material-symbols-outlined" style={{ fontSize: compact ? 14 : 16 }}>
        {v.icon}
      </span>
      {v.label}
    </span>
  );
}
