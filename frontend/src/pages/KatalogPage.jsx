import { useState, useEffect } from 'react';
import api from '../lib/api';
import { getToken, decodeToken } from '../lib/auth';
import SearchBar from '../components/SearchBar';
import CategoryFilterSidebar from '../components/CategoryFilterSidebar';
import BookCard from '../components/BookCard';
import EmptyState from '../components/EmptyState';
import BookFormModal from '../components/BookFormModal';
import KelolaTable from '../components/KelolaTable';
import ConfirmDialog from '../components/ConfirmDialog';

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <div key={i} className="animate-pulse">
          <div className="aspect-[3/4] bg-surface-container rounded-xl" />
          <div className="mt-3 space-y-2">
            <div className="h-4 bg-surface-container rounded w-3/4" />
            <div className="h-3 bg-surface-container rounded w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

function loadBooks({ kataKunci, selectedCategories, tab, signal }) {
  const params = {};
  if (kataKunci) params.kata_kunci = kataKunci;
  if (tab === 'jelajah' && selectedCategories.length > 0) {
    params.kategori = selectedCategories;
  }
  return api.get('/buku', { params, signal });
}

export default function KatalogPage() {
  const [books, setBooks] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [kataKunci, setKataKunci] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);

  // Tab state (pustakawan only)
  const token = getToken();
  const decoded = token ? decodeToken(token) : null;
  const peran = decoded?.peran ?? 'mahasiswa';
  const [tab, setTab] = useState('jelajah');

  // Refresh key to trigger re-fetch after mutations
  const [refreshKey, setRefreshKey] = useState(0);

  // Kelola state
  const [showFormModal, setShowFormModal] = useState(false);
  const [formMode, setFormMode] = useState('add');
  const [editingBook, setEditingBook] = useState(null);
  const [deletingBook, setDeletingBook] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    const abortController = new AbortController();
    let cancelled = false;

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError('');

    loadBooks({ kataKunci, selectedCategories, tab, signal: abortController.signal })
      .then((res) => {
        if (!cancelled) {
          setBooks(res.data.items);
          setTotal(res.data.total);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError('Gagal memuat daftar buku. Silakan coba lagi.');
          setBooks([]);
          setTotal(0);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      abortController.abort();
    };
  }, [kataKunci, selectedCategories, tab, refreshKey]);

  // Fetch categories for modal datalist
  useEffect(() => {
    if (peran === 'pustakawan') {
      api
        .get('/buku/kategori')
        .then((res) => setCategories(res.data))
        .catch(() => {});
    }
  }, [peran]);

  // ---- Kelola handlers ----

  function handleOpenAdd() {
    setFormMode('add');
    setEditingBook(null);
    setShowFormModal(true);
  }

  function handleOpenEdit(buku) {
    setFormMode('edit');
    setEditingBook(buku);
    setShowFormModal(true);
  }

  function handleSaved() {
    setRefreshKey((k) => k + 1);
  }

  function handleDeleteClick(buku) {
    setDeletingBook(buku);
    setDeleteError('');
    setDeleteLoading(false);
  }

  async function handleDeleteConfirm() {
    if (!deletingBook) return;
    setDeleteLoading(true);
    setDeleteError('');
    try {
      await api.delete(`/buku/${deletingBook.id}`);
      setDeletingBook(null);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 409) {
        setDeleteError(
          detail ||
            `Buku "${deletingBook.judul}" tidak dapat dihapus karena masih memiliki salinan fisik. Hapus semua salinan terlebih dahulu.`,
        );
      } else {
        setDeleteError(detail || 'Gagal menghapus buku. Silakan coba lagi.');
      }
    } finally {
      setDeleteLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Page header + tab toggle (pustakawan only) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-headline-md font-headline-md text-primary">
            {tab === 'kelola' ? 'Kelola Katalog' : 'Katalog Buku'}
          </h1>
          <p className="text-body-md font-body-md text-outline mt-1">
            {tab === 'kelola'
              ? 'Kelola koleksi buku perpustakaan.'
              : 'Telusuri koleksi buku perpustakaan.'}
          </p>
        </div>

        {peran === 'pustakawan' && (
          <div className="flex items-center gap-1 bg-surface-container rounded-full p-1" role="tablist">
            <button
              role="tab"
              aria-selected={tab === 'jelajah'}
              onClick={() => setTab('jelajah')}
              className={`px-5 py-2 rounded-full text-label-sm font-label-sm min-h-[44px] transition-colors ${
                tab === 'jelajah'
                  ? 'bg-surface text-primary shadow-sm'
                  : 'text-outline hover:text-primary'
              }`}
            >
              Jelajah
            </button>
            <button
              role="tab"
              aria-selected={tab === 'kelola'}
              onClick={() => setTab('kelola')}
              className={`px-5 py-2 rounded-full text-label-sm font-label-sm min-h-[44px] transition-colors ${
                tab === 'kelola'
                  ? 'bg-surface text-primary shadow-sm'
                  : 'text-outline hover:text-primary'
              }`}
            >
              Kelola
            </button>
          </div>
        )}
      </div>

      {/* Search bar */}
      <SearchBar value={kataKunci} onChange={setKataKunci} />

      {tab === 'kelola' && peran === 'pustakawan' ? (
        /* ---- KELOLA TAB ---- */
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleOpenAdd}
              className="bg-antique-gold text-white rounded-full px-5 py-2.5 text-label-sm font-label-sm hover:opacity-90 transition-opacity inline-flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px]">add</span>
              Tambah Buku
            </button>
          </div>

          <KelolaTable
            books={books}
            onEdit={handleOpenEdit}
            onDelete={handleDeleteClick}
            loading={loading}
          />
        </div>
      ) : (
        /* ---- JELAJAH TAB ---- */
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Filter sidebar */}
          <CategoryFilterSidebar
            selected={selectedCategories}
            onChange={setSelectedCategories}
          />

          {/* Book grid */}
          <div className="flex-1 min-w-0">
            {loading ? (
              <SkeletonGrid />
            ) : error ? (
              <EmptyState
                icon="error"
                title="Terjadi Kesalahan"
                message={error}
                actionLabel="Coba Lagi"
                onAction={() => setRefreshKey((k) => k + 1)}
              />
            ) : books.length === 0 ? (
              <EmptyState
                icon="search_off"
                title="Buku Tidak Ditemukan"
                message={
                  kataKunci || selectedCategories.length > 0
                    ? 'Tidak ada buku yang sesuai dengan filter yang dipilih. Coba gunakan kata kunci lain atau hapus filter.'
                    : 'Belum ada buku dalam katalog.'
                }
                actionLabel={
                  kataKunci || selectedCategories.length > 0
                    ? 'Hapus Semua Filter'
                    : undefined
                }
                onAction={() => {
                  setKataKunci('');
                  setSelectedCategories([]);
                }}
              />
            ) : (
              <>
                <p className="text-body-sm font-body-sm text-outline mb-4">
                  Menampilkan {books.length} dari {total} buku
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6">
                  {books.map((buku) => (
                    <BookCard key={buku.id} buku={buku} />
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* BookFormModal (add/edit) */}
      {showFormModal && (
        <BookFormModal
          mode={formMode}
          buku={editingBook}
          categories={categories}
          onClose={() => setShowFormModal(false)}
          onSaved={handleSaved}
        />
      )}

      {/* Delete confirmation dialog */}
      {deletingBook && !deleteError && (
        <ConfirmDialog
          title="Hapus Buku?"
          message={`Buku "${deletingBook.judul}" akan dihapus secara permanen. Tindakan ini tidak dapat dibatalkan.`}
          confirmLabel="Hapus"
          destructive
          loading={deleteLoading}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeletingBook(null)}
        />
      )}

      {/* Delete FK-safe info variant */}
      {deletingBook && deleteError && (
        <ConfirmDialog
          title="Tidak Dapat Dihapus"
          message={deleteError}
          variant="info"
          onCancel={() => {
            setDeletingBook(null);
            setDeleteError('');
          }}
          onConfirm={() => {}}
        />
      )}
    </div>
  );
}
