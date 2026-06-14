import { Link } from 'react-router';
import BookCoverPlaceholder from './BookCoverPlaceholder';
import AvailabilityBadge from './AvailabilityBadge';

export default function BookCard({ buku }) {
  return (
    <Link
      to={`/katalog/${buku.id}`}
      className="group block bg-surface rounded-xl border border-outline-variant/40 overflow-hidden shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 no-underline"
    >
      <BookCoverPlaceholder
        judul={buku.judul}
        kategori={buku.kategori}
        className="rounded-none"
      />
      <div className="p-4 space-y-2">
        <h3 className="text-body-md font-label-md text-primary line-clamp-2 group-hover:text-antique-gold transition-colors">
          {buku.judul}
        </h3>
        <p className="text-body-sm font-body-sm text-outline line-clamp-1">
          {buku.penulis}
        </p>
        <AvailabilityBadge tersedia={buku.tersedia} compact />
      </div>
    </Link>
  );
}
