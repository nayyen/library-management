/**
 * DashboardPage — pustakawan landing page (DASH-01).
 *
 * Renders 4 stat cards (Total Buku, Peminjaman Aktif, Buku Terlambat,
 * Total Denda Belum Lunas) and a read-only preview of pending loan
 * approval requests.
 */

import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router';
import api from '../lib/api';
import BookCoverPlaceholder from '../components/BookCoverPlaceholder';
import EmptyState from '../components/EmptyState';

/* ── date helpers ── */
const MONTHS_ID = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];

function formatDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${d.getDate()} ${MONTHS_ID[d.getMonth()]} ${d.getFullYear()}, ${hh}:${mm}`;
}

/* ── Stat card skeleton ── */
function StatSkeleton() {
  return (
    <div className="bg-surface-container-lowest border border-paper-shadow rounded-xl p-6 relative overflow-hidden shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)] animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 rounded-lg bg-surface-container-high" />
        <div className="w-8 h-8 rounded-full bg-surface-container-high" />
      </div>
      <div className="h-8 w-24 bg-surface-container-high rounded mb-2" />
      <div className="h-4 w-32 bg-surface-container-high rounded" />
      <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-surface-container-high/50" />
    </div>
  );
}

/* ── BookCell for preview table ── */
function BookCell({ judul, penulis, kategori }) {
  return (
    <div className="flex items-center gap-3 min-w-0">
      <div className="w-10 h-14 flex-shrink-0 overflow-hidden rounded">
        <BookCoverPlaceholder judul={judul} kategori={kategori} />
      </div>
      <div className="min-w-0">
        <p className="text-body-sm font-body-sm text-primary truncate">{judul}</p>
        <p className="text-label-sm font-label-sm text-secondary truncate">{penulis}</p>
      </div>
    </div>
  );
}

/* ── Main component ── */
export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await api.get('/dashboard/stats');
      setData(resp.data);
    } catch {
      setError('Gagal memuat data dashboard. Periksa koneksi Anda dan coba lagi.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  /* ── Error state ── */
  if (error) {
    return (
      <main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12">
        <EmptyState
          icon="error_outline"
          title="Gagal Memuat"
          message={error}
          actionLabel="Coba Lagi"
          onAction={fetchStats}
        />
      </main>
    );
  }

  /* ── Loading state ── */
  if (loading || !data) {
    return (
      <main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
        <div>
          <h1 className="text-headline-md font-headline-md text-primary mb-1">Dashboard</h1>
          <p className="text-body-md font-body-md text-outline">Ringkasan aktivitas perpustakaan hari ini.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter mb-12">
          <StatSkeleton />
          <StatSkeleton />
          <StatSkeleton />
          <StatSkeleton />
        </div>
      </main>
    );
  }

  /* ── Active state ── */
  return (
    <main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-headline-md font-headline-md text-primary mb-1">Dashboard</h1>
        <p className="text-body-md font-body-md text-outline">Ringkasan aktivitas perpustakaan hari ini.</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter mb-12">
        {/* Card 1: Total Buku */}
        <div className="bg-surface-container-lowest border border-paper-shadow rounded-xl p-6 relative overflow-hidden shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)]">
          <div className="flex items-start justify-between mb-4">
            <span className="material-symbols-outlined text-3xl text-ink-blue">library_books</span>
            <div className="w-8 h-8 rounded-full bg-ink-blue/5" />
          </div>
          <p className="text-headline-md font-headline-md text-primary mb-1">
            {data.total_buku.toLocaleString('id-ID')}
          </p>
          <p className="text-label-sm font-label-sm text-secondary uppercase tracking-wider">Total Buku</p>
          <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-ink-blue/5" />
        </div>

        {/* Card 2: Peminjaman Aktif */}
        <div className="bg-surface-container-lowest border border-paper-shadow rounded-xl p-6 relative overflow-hidden shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)]">
          <div className="flex items-start justify-between mb-4">
            <span className="material-symbols-outlined text-3xl text-antique-gold">local_library</span>
            <div className="w-8 h-8 rounded-full bg-antique-gold/5" />
          </div>
          <p className="text-headline-md font-headline-md text-primary mb-1">{data.peminjaman_aktif}</p>
          <p className="text-label-sm font-label-sm text-secondary uppercase tracking-wider">Peminjaman Aktif</p>
          <div className="flex items-center gap-1 mt-2 text-body-sm font-body-sm text-secondary">
            <span className="material-symbols-outlined text-[16px]">schedule</span>
            <span>{data.menunggu_persetujuan_count} menunggu persetujuan</span>
          </div>
          <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-antique-gold/5" />
        </div>

        {/* Card 3: Buku Terlambat — clickable, crimson accent */}
        <Link
          to="/pinjaman"
          className="bg-surface-container-lowest border border-paper-shadow rounded-xl p-6 relative overflow-hidden shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)] border-l-4 border-l-alert-crimson block hover:shadow-[0_10px_40px_-6px_rgba(147,39,44,0.15)] transition-shadow"
        >
          <div className="flex items-start justify-between mb-4">
            <span className="material-symbols-outlined text-3xl text-alert-crimson">warning</span>
            <div className="w-8 h-8 rounded-full bg-alert-crimson/5" />
          </div>
          <p className="text-headline-md font-headline-md text-primary mb-1">{data.buku_terlambat}</p>
          <p className="text-label-sm font-label-sm text-secondary uppercase tracking-wider">Buku Terlambat</p>
          <div className="flex items-center gap-1 mt-2 text-body-sm font-body-sm text-alert-crimson">
            <span>Lihat detail</span>
            <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
          </div>
          <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-alert-crimson/5" />
        </Link>

        {/* Card 4: Total Denda Belum Lunas */}
        <div className="bg-surface-container-lowest border border-paper-shadow rounded-xl p-6 relative overflow-hidden shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)]">
          <div className="flex items-start justify-between mb-4">
            <span className="material-symbols-outlined text-3xl text-sage-green">payments</span>
            <div className="w-8 h-8 rounded-full bg-sage-green/5" />
          </div>
          <p className="text-headline-md font-headline-md text-primary mb-1">
            Rp {data.total_denda_belum_lunas.toLocaleString('id-ID')}
          </p>
          <p className="text-label-sm font-label-sm text-secondary uppercase tracking-wider">Total Denda Belum Lunas</p>
          <div className="flex items-center gap-1 mt-2 text-body-sm font-body-sm text-secondary">
            <span className="material-symbols-outlined text-[16px]">receipt_long</span>
            <span>dari {data.jumlah_mahasiswa_denda} mahasiswa</span>
          </div>
          <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-sage-green/5" />
        </div>
      </div>

      {/* Pending approval preview (D-03) */}
      <section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
        <div className="p-6 border-b border-paper-shadow bg-surface-container-low flex justify-between items-center">
          <div>
            <h2 className="text-headline-md font-headline-md text-primary">Daftar Pengajuan Peminjaman</h2>
            <p className="text-body-sm font-body-sm text-secondary">Menunggu persetujuan pustakawan</p>
          </div>
          <Link
            to="/pinjaman"
            className="text-ink-blue text-label-md font-label-md hover:underline flex items-center gap-1"
          >
            Lihat Semua
            <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
          </Link>
        </div>

        {data.pengajuan_preview.length === 0 ? (
          <EmptyState
            icon="inbox"
            title="Tidak Ada Pengajuan"
            message="Belum ada pengajuan peminjaman yang menunggu persetujuan saat ini."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-paper-shadow">
                  <th className="text-label-sm font-label-sm text-secondary uppercase tracking-wider px-6 py-4">Mahasiswa</th>
                  <th className="text-label-sm font-label-sm text-secondary uppercase tracking-wider px-6 py-4">Buku</th>
                  <th className="text-label-sm font-label-sm text-secondary uppercase tracking-wider px-6 py-4">Tanggal Pengajuan</th>
                </tr>
              </thead>
              <tbody>
                {data.pengajuan_preview.map((item) => (
                  <tr key={item.id} className="border-b border-outline-variant/20 last:border-b-0">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-primary-fixed text-primary-container text-label-sm font-label-sm flex items-center justify-center flex-shrink-0">
                          {item.nama_mahasiswa?.charAt(0)?.toUpperCase() || '?'}
                        </div>
                        <span className="text-body-sm font-body-sm text-primary">{item.nama_mahasiswa}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <BookCell
                        judul={item.judul}
                        penulis={item.penulis}
                        kategori={item.kategori}
                      />
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-body-sm font-body-sm text-outline">{formatDateTime(item.tanggal_pengajuan)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
