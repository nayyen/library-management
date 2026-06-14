export default function RoleBadge({ peran }) {
  const isPustakawan = peran === 'pustakawan';

  return (
    <span
      className={`inline-block px-3 py-1 rounded text-label-sm font-label-sm ${
        isPustakawan
          ? 'bg-primary-container text-on-primary-container'
          : 'bg-secondary-container text-on-secondary-container'
      }`}
    >
      {peran}
    </span>
  );
}
