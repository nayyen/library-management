import { Link } from 'react-router';

export default function ComingSoonPage({ title = 'Segera Hadir' }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <span className="material-symbols-outlined text-7xl text-outline-variant mb-6">
        construction
      </span>

      <h1 className="text-headline-lg font-headline-lg text-primary mb-3">
        {title}
      </h1>

      <p className="text-body-md font-body-md text-outline mt-2 max-w-md">
        Fitur ini sedang dalam tahap pengembangan dan akan segera tersedia.
        Pantau terus informasi terbaru dari kami.
      </p>

      <Link
        to="/"
        className="mt-8 bg-antique-gold text-white rounded-full px-8 py-3 text-label-sm font-label-sm hover:opacity-90 transition-opacity no-underline inline-flex items-center gap-2"
      >
        <span className="material-symbols-outlined text-[18px]">arrow_back</span>
        Kembali ke Beranda
      </Link>
    </div>
  );
}
