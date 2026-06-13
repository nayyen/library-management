import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router';
import api from '../lib/api';
import { getToken, decodeToken } from '../lib/auth';
import BookCoverPlaceholder from '../components/BookCoverPlaceholder';
import AvailabilityBadge from '../components/AvailabilityBadge';
import SalinanTable from '../components/SalinanTable';
import BookFormModal from '../components/BookFormModal';
import TambahSalinanForm from '../components/TambahSalinanForm';

export default function BukuDetailPage() {
  const { id } = useParams();
  const [buku, setBuku] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Role
  const token = getToken();
  const decoded = token ? decodeToken(token) : null;
  const peran = decoded?.peran ?? 'mahasiswa';

  // Edit modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [categories, setCategories] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch categories once for edit modal datalist
  useEffect(() => {
    if (peran === 'pustakawan') {
      api
        .get('/buku/kategori')
        .then((res) => setCategories(res.data))
        .catch(() => {});
    }
  }, [peran]);

  useEffect(() => {
    const abortController = new AbortController();

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError('');

    api
      .get(`/buku/${id}`, { signal: abortController.signal })
      .then((res) => {
        if (!abortController.signal.aborted) setBuku(res.data);
      })
      .catch((err) => {
        if (abortController.signal.aborted) return;
        if (err.response?.status === 404) {
          setError('Buku tidak ditemukan.');
        } else {
          setError('Gagal memuat detail buku.');
        }
      })
      .finally(() => {
        if (!abortController.signal.aborted) setLoading(false);
      });

    return () => abortController.abort();
  }, [id, refreshKey]);

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-6 w-32 bg-surface-container rounded" />
        <div className="flex gap-8">
          <div className="w-48 aspect-[3/4] bg-surface-container rounded-xl shrink-0" />
          <div className="flex-1 space-y-4">
            <div className="h-8 bg-surface-container rounded w-3/4" />
            <div className="h-4 bg-surface-container rounded w-1/2" />
            <div className="h-4 bg-surface-container rounded w-1/3" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <span className="material-symbols-outlined text-6xl text-outline-variant mb-4">
          {error.includes('tidak ditemukan') ? 'book_off' : 'error'}
        </span>
        <h2 className="text-headline-sm font-headline-sm text-primary mb-2">
          {error.includes('tidak ditemukan') ? 'Buku Tidak Ditemukan' : 'Terjadi Kesalahan'}
        </h2>
        <p className="text-body-md font-body-md text-outline mb-6">{error}</p>
        <Link
          to="/katalog"
          className="bg-antique-gold text-white rounded-full px-6 py-2.5 text-label-sm font-label-sm hover:opacity-90 transition-opacity no-underline inline-flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          Kembali ke Katalog
        </Link>
      </div>
    );
  }

  if (!buku) return null;

  return (
    <div className="space-y-8">
      {/* Back link */}
      <Link
        to="/katalog"
        className="inline-flex items-center gap-2 text-outline hover:text-primary transition-colors text-body-md font-body-md no-underline"
      >
        <span className="material-symbols-outlined text-[18px]">arrow_back</span>
        Kembali ke Katalog
      </Link>

      {/* Book header */}
      <div className="flex flex-col md:flex-row gap-8">
        {/* Cover */}
        <div className="w-40 md:w-48 shrink-0">
          <BookCoverPlaceholder
            judul={buku.judul}
            kategori={buku.kategori}
          />
        </div>

        {/* Info */}
        <div className="flex-1 space-y-4">
          <div className="flex items-start gap-3 flex-wrap">
            <h1 className="text-headline-md font-headline-md text-primary">
              {buku.judul}
            </h1>
            <AvailabilityBadge tersedia={buku.tersedia} />
            {peran === 'pustakawan' && (
              <button
                type="button"
                onClick={() => setShowEditModal(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm text-outline border border-outline-variant hover:bg-surface-container transition-colors"
                aria-label={`Edit ${buku.judul}`}
              >
                <span className="material-symbols-outlined text-[18px]">edit</span>
                Edit
              </button>
            )}
          </div>

          <p className="text-body-lg font-body-lg text-outline">
            {buku.penulis}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2">
            <div>
              <p className="text-label-sm font-label-sm text-outline-variant uppercase tracking-wider">
                Kategori
              </p>
              <p className="text-body-md font-body-md text-primary mt-0.5">
                {buku.kategori}
              </p>
            </div>
            <div>
              <p className="text-label-sm font-label-sm text-outline-variant uppercase tracking-wider">
                ISBN
              </p>
              <p className="text-body-md font-body-md text-primary mt-0.5">
                {buku.isbn}
              </p>
            </div>
            <div>
              <p className="text-label-sm font-label-sm text-outline-variant uppercase tracking-wider">
                Tahun Terbit
              </p>
              <p className="text-body-md font-body-md text-primary mt-0.5">
                {buku.tahun_terbit}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Copies section */}
      <section className="bg-surface-container-low rounded-xl p-6">
        <h2 className="text-headline-sm font-headline-sm text-primary mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-[22px] text-outline">content_copy</span>
          Salinan Buku
        </h2>
        <SalinanTable salinan={buku.salinan} />
      </section>

      {/* Pustakawan: Tambah Salinan form */}
      {peran === 'pustakawan' && (
        <TambahSalinanForm
          idBuku={buku.id}
          onAdded={(newSalinan) => {
            setBuku((prev) => ({
              ...prev,
              salinan: [...prev.salinan, newSalinan],
              tersedia:
                newSalinan.status_ketersediaan === 'tersedia' || prev.tersedia,
            }));
          }}
        />
      )}

      {/* Pustakawan: Edit modal */}
      {showEditModal && (
        <BookFormModal
          mode="edit"
          buku={buku}
          categories={categories}
          onClose={() => setShowEditModal(false)}
          onSaved={() => {
            setShowEditModal(false);
            setRefreshKey((k) => k + 1);
          }}
        />
      )}
    </div>
  );
}
