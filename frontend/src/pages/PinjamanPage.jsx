/**
 * PinjamanPage — shared page for loan management (D-05 through D-11).
 *
 * Mahasiswa view:  single "Pinjaman Saya" table with StatusBadge per row.
 * Pustakawan view: stacked "Menunggu Persetujuan" + "Siap Diambil" sections.
 *                  Action buttons are wired in Plan 03-03.
 */

import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import { getToken, decodeToken } from '../lib/auth';
import BookCoverPlaceholder from '../components/BookCoverPlaceholder';
import StatusBadge from '../components/StatusBadge';
import BlockedBanner from '../components/BlockedBanner';
import EmptyState from '../components/EmptyState';
import Toast from '../components/Toast';
import ConfirmDialog from '../components/ConfirmDialog';

/* ── date helpers ── */
const MONTHS_ID = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS_ID[d.getMonth()]} ${d.getFullYear()}`;
}

function formatDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${d.getDate()} ${MONTHS_ID[d.getMonth()]} ${d.getFullYear()}, ${hh}:${mm}`;
}

function formatAmbilSebelum(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  d.setDate(d.getDate() + 2);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `Ambil sebelum ${d.getDate()} ${MONTHS_ID[d.getMonth()]} ${d.getFullYear()}, ${hh}:${mm}`;
}

/* ── Tanggal column per status ── */
function TanggalCell({ item }) {
  const status = item.status_peminjaman;

  if (status === 'menunggu_persetujuan') {
    return <>{formatDateTime(item.tanggal_pengajuan)}</>;
  }
  if (status === 'siap_diambil') {
    return <>{formatAmbilSebelum(item.tanggal_siap_ambil)}</>;
  }
  if (status === 'dipinjam') {
    return <>Tenggat {formatDate(item.tanggal_tenggat)}</>;
  }
  // ditolak / dibatalkan
  return <>{formatDateTime(item.tanggal_pengajuan)}</>;
}

/* ── Skeleton rows for loading state ── */
function SkeletonRows({ count = 3 }) {
  return Array.from({ length: count }, (_, i) => (
    <tr key={i} className="border-b border-outline-variant/20">
      <td className="py-3 pr-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-14 bg-surface-container-high rounded animate-pulse" />
          <div className="space-y-2 flex-1">
            <div className="h-4 bg-surface-container-high rounded animate-pulse w-3/4" />
            <div className="h-3 bg-surface-container-high rounded animate-pulse w-1/2" />
          </div>
        </div>
      </td>
      <td className="py-3">
        <div className="h-6 bg-surface-container-high rounded-full animate-pulse w-32" />
      </td>
      <td className="py-3">
        <div className="h-4 bg-surface-container-high rounded animate-pulse w-28" />
      </td>
      <td className="py-3">
        <div className="h-4 bg-surface-container-high rounded animate-pulse w-28 float-right" />
      </td>
    </tr>
  ));
}

/* ── Helper to check pickup deadline urgency ── */
function isDeadlineUrgent(tanggalSiapAmbil) {
  if (!tanggalSiapAmbil) return false;
  const deadline = new Date(tanggalSiapAmbil);
  deadline.setDate(deadline.getDate() + 2);
  return deadline.getTime() - Date.now() < 6 * 60 * 60 * 1000;
}

/* ── Main component ── */
export default function PinjamanPage() {
  const token = getToken();
  const decoded = token ? decodeToken(token) : null;
  const peran = decoded?.peran ?? 'mahasiswa';

  const [loanData, setLoanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState(null);

  // Confirm dialog state (pustakawan actions)
  const [confirm, setConfirm] = useState(null);

  // Refresh trigger for re-fetching after actions
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchLoans = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/peminjaman');
      setLoanData(res.data);
    } catch {
      setError('Gagal memuat data pinjaman. Periksa koneksi Anda dan coba lagi.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchLoans();
  }, [fetchLoans, refreshKey]);

  /* ── Pustakawan action helpers ── */

  function showConfirm({ title, message, confirmLabel, destructive, onConfirm }) {
    setConfirm({ title, message, confirmLabel, destructive, onConfirm, loading: false });
  }

  function setConfirmLoading(loading) {
    setConfirm((prev) => (prev ? { ...prev, loading } : prev));
  }

  async function handleApprove(item) {
    showConfirm({
      title: 'Setujui Pengajuan?',
      message: `Pengajuan peminjaman "${item.judul}" oleh ${item.nama_mahasiswa} akan disetujui. Mahasiswa memiliki waktu 2x24 jam untuk mengambil buku.`,
      confirmLabel: 'Setujui',
      destructive: false,
      onConfirm: async () => {
        setConfirmLoading(true);
        try {
          await api.put(`/peminjaman/${item.id}/persetujuan`, { aksi: 'setujui' });
          setConfirm(null);
          setToast({ type: 'success', message: `Pengajuan disetujui. ${item.nama_mahasiswa} dapat mengambil buku dalam 2x24 jam.` });
          setRefreshKey((k) => k + 1);
        } catch {
          setConfirm(null);
          setToast({ type: 'error', message: 'Gagal memproses tindakan. Silakan coba lagi.' });
        }
      },
    });
  }

  async function handleReject(item) {
    showConfirm({
      title: 'Tolak Pengajuan?',
      message: `Pengajuan peminjaman "${item.judul}" oleh ${item.nama_mahasiswa} akan ditolak. Tindakan ini tidak dapat dibatalkan.`,
      confirmLabel: 'Tolak',
      destructive: true,
      onConfirm: async () => {
        setConfirmLoading(true);
        try {
          await api.put(`/peminjaman/${item.id}/persetujuan`, { aksi: 'tolak' });
          setConfirm(null);
          setToast({ type: 'success', message: 'Pengajuan ditolak.' });
          setRefreshKey((k) => k + 1);
        } catch {
          setConfirm(null);
          setToast({ type: 'error', message: 'Gagal memproses tindakan. Silakan coba lagi.' });
        }
      },
    });
  }

  async function handleHandover(item) {
    const tenggat = new Date();
    tenggat.setDate(tenggat.getDate() + 14);
    const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
      'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
    const formatted = `${tenggat.getDate()} ${months[tenggat.getMonth()]} ${tenggat.getFullYear()}`;

    showConfirm({
      title: 'Tandai Sudah Diserahkan?',
      message: `Buku "${item.judul}" akan ditandai sebagai diserahkan kepada ${item.nama_mahasiswa}. Tenggat pengembalian akan diatur ke 14 hari dari sekarang (${formatted}).`,
      confirmLabel: 'Serahkan',
      destructive: false,
      onConfirm: async () => {
        setConfirmLoading(true);
        try {
          await api.put(`/peminjaman/${item.id}/serahkan`);
          setConfirm(null);
          setToast({ type: 'success', message: `Buku berhasil diserahkan. Tenggat pengembalian: ${formatted}.` });
          setRefreshKey((k) => k + 1);
        } catch {
          setConfirm(null);
          setToast({ type: 'error', message: 'Gagal memproses tindakan. Silakan coba lagi.' });
        }
      },
    });
  }

  async function handleKembalikan(item) {
    const now = new Date();
    const tenggat = new Date(item.tanggal_tenggat);
    const isOverdue = tenggat < now;
    const daysLate = isOverdue
      ? Math.floor((now - tenggat) / 86400000)
      : 0;

    showConfirm({
      title: 'Tandai Sudah Dikembalikan?',
      message: isOverdue
        ? `Buku "${item.judul}" terlambat ${daysLate} hari. Denda Rp ${(daysLate * 1000).toLocaleString('id-ID')} akan tercatat dan akun ${item.nama_mahasiswa} akan diblokir.`
        : 'Tandai buku ini sudah dikembalikan?',
      confirmLabel: 'Kembalikan',
      destructive: isOverdue,
      onConfirm: async () => {
        setConfirmLoading(true);
        try {
          const res = await api.put(`/peminjaman/${item.id}/kembalikan`);
          setConfirm(null);
          const denda = res.data.total_denda ?? 0;
          setToast({
            type: 'success',
            message: denda > 0
              ? `Buku berhasil dikembalikan. Denda Rp ${denda.toLocaleString('id-ID')} tercatat dan akun mahasiswa diblokir.`
              : 'Buku berhasil dikembalikan.',
          });
          setRefreshKey((k) => k + 1);
        } catch {
          setConfirm(null);
          setToast({ type: 'error', message: 'Gagal memproses tindakan. Silakan coba lagi.' });
        }
      },
    });
  }

  async function handleLunasiDenda(item) {
    showConfirm({
      title: 'Tandai Denda Lunas?',
      message: `Denda sebesar Rp ${item.total_denda.toLocaleString('id-ID')} milik ${item.nama} akan dinyatakan lunas dan akun akan dibuka kembali.`,
      confirmLabel: 'Denda Lunas',
      destructive: false,
      onConfirm: async () => {
        setConfirmLoading(true);
        try {
          await api.put(`/peminjaman/anggota/${item.id_pengguna}/lunasi_denda`);
          setConfirm(null);
          setToast({
            type: 'success',
            message: `Denda dinyatakan lunas. Akun ${item.nama} tidak lagi diblokir.`,
          });
          setRefreshKey((k) => k + 1);
        } catch {
          setConfirm(null);
          setToast({ type: 'error', message: 'Gagal memproses tindakan. Silakan coba lagi.' });
        }
      },
    });
  }

  /* ── Book cell (reused in both tables) ── */
  function BookCell({ item }) {
    return (
      <td className="py-3 pr-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-14 shrink-0 rounded overflow-hidden">
            <BookCoverPlaceholder judul={item.judul} kategori={item.kategori ?? ''} />
          </div>
          <div className="min-w-0">
            <p className="text-body-md font-body-md text-primary truncate">
              {item.judul}
            </p>
            <p className="text-body-sm font-body-sm text-outline truncate">
              {item.penulis}
            </p>
          </div>
        </div>
      </td>
    );
  }

  /* ── Loading state ── */
  if (loading && !loanData) {
    return (
      <main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
        <div className="animate-pulse space-y-2">
          <div className="h-8 w-32 bg-surface-container-high rounded" />
          <div className="h-4 w-64 bg-surface-container-high rounded" />
        </div>
        <section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
          <div className="p-6 border-b border-paper-shadow bg-surface-container-low">
            <div className="h-6 w-40 bg-surface-container-high rounded animate-pulse" />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-outline-variant/40">
                  <th className="pb-3 px-6 pt-4 text-label-sm">Buku</th>
                  <th className="pb-3 px-6 pt-4 text-label-sm">Status</th>
                  <th className="pb-3 px-6 pt-4 text-label-sm">Tanggal</th>
                </tr>
              </thead>
              <tbody>
                <SkeletonRows />
              </tbody>
            </table>
          </div>
        </section>
      </main>
    );
  }

  /* ── Error state ── */
  if (error && !loanData) {
    return (
      <main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
        <EmptyState
          icon="error_outline"
          title="Gagal Memuat"
          message={error}
          actionLabel="Coba Lagi"
          onAction={fetchLoans}
        />
      </main>
    );
  }

  /* ── Derived data (mahasiswa) ── */
  const isMahasiswa = peran === 'mahasiswa';
  const items = loanData?.items ?? [];
  const isDiblokir = !!loanData?.is_diblokir;
  const activeCount = items.filter(
    (i) =>
      i.status_peminjamen === 'menunggu_persetujuan' ||
      i.status_peminjamen === 'siap_diambil' ||
      i.status_peminjamen === 'dipinjam',
  ).length;
  // Fallback for different key spellings from the API
  const safeItems = items.map((item) => ({
    ...item,
    status_peminjaman: item.status_peminjaman ?? item.status_peminjamen,
  }));

  const menunggu = loanData?.menunggu_persetujuan ?? [];
  const siapDiambil = loanData?.siap_diambil ?? [];
  const sedangDipinjam = loanData?.sedang_dipinjam ?? [];
  const anggotaDiblokir = loanData?.anggota_diblokir ?? [];

  return (
    <main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-headline-md font-headline-md text-primary mb-1">Pinjaman</h1>
        <p className="text-body-md font-body-md text-outline">
          {isMahasiswa
            ? 'Riwayat dan status pengajuan peminjaman Anda.'
            : 'Kelola pengajuan peminjaman dan proses pengambilan buku.'}
        </p>
      </div>

      {/* BlockedBanner (mahasiswa only) */}
      {isMahasiswa && (
        <BlockedBanner
          variant={isDiblokir ? 'blocked' : activeCount >= 5 ? 'limit' : null}
          dendaAmount={loanData?.denda_tertunggak ?? 0}
        />
      )}

      {/* ── MAHASISWA: Pinjaman Saya table ── */}
      {isMahasiswa && (
        <section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
          <div className="p-6 border-b border-paper-shadow bg-surface-container-low">
            <h2 className="text-headline-sm font-headline-sm text-primary">
              Pinjaman Saya
            </h2>
          </div>

          {safeItems.length === 0 && !loading ? (
            <EmptyState
              icon="local_library"
              title="Belum Ada Pinjaman"
              message="Anda belum pernah mengajukan peminjaman. Jelajahi katalog untuk meminjam buku."
              actionLabel="Jelajahi Katalog"
              onAction={() => window.location.href = '/katalog'}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-paper-shadow">
                    <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                      Buku
                    </th>
                    <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                      Tanggal
                    </th>
                    <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider text-right">
                      Denda
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <SkeletonRows />
                  ) : (
                    safeItems.map((item, idx) => (
                      <tr
                        key={item.id}
                        className={`border-b border-outline-variant/20 last:border-none ${
                          idx % 2 === 0 ? '' : 'bg-surface-container-low'
                        }`}
                      >
                        <BookCell item={item} />
                        <td className="py-3 px-6">
                          <StatusBadge status={item.is_terlambat ? 'terlambat' : item.status_peminjaman} />
                        </td>
                        <td className="py-3 px-6 text-body-sm font-body-sm text-outline">
                          <TanggalCell item={item} />
                        </td>
                        <td className="py-3 px-6 text-right text-body-sm font-body-sm">
                          {item.status_peminjaman === 'dikembalikan' && item.total_denda > 0 ? (
                            <span className="text-alert-crimson font-medium">
                              Rp {item.total_denda.toLocaleString('id-ID')}
                            </span>
                          ) : (
                            <span className="text-outline">-</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* ── PUSTAKAWAN: approve queue ── */}
      {!isMahasiswa && !loading && (
        <div className="space-y-8">
          {/* Section 1: Menunggu Persetujuan */}
          <section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
            <div className="p-6 border-b border-paper-shadow bg-surface-container-low">
              <h2 className="text-headline-sm font-headline-sm text-primary">
                Menunggu Persetujuan
              </h2>
              <p className="text-body-sm font-body-sm text-outline mt-1">
                Pengajuan peminjaman yang menunggu persetujuan Anda.
              </p>
            </div>

            {menunggu.length === 0 ? (
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
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Mahasiswa
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Buku
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Tanggal Pengajuan
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Aksi
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {menunggu.map((item) => (
                      <tr
                        key={item.id}
                        className="border-b border-outline-variant/20 last:border-none"
                      >
                        {/* Mahasiswa cell */}
                        <td className="py-3 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-surface-tint text-on-primary flex items-center justify-center font-bold text-xs shrink-0">
                              {item.nama_mahasiswa?.charAt(0)?.toUpperCase() ?? '?'}
                            </div>
                            <div>
                              <p className="text-body-md font-body-md text-primary">
                                {item.nama_mahasiswa}
                              </p>
                              <p className="text-body-sm font-body-sm text-outline">
                                Mahasiswa
                              </p>
                            </div>
                          </div>
                        </td>
                        <BookCell item={item} />
                        <td className="py-3 px-6 text-body-sm font-body-sm text-outline">
                          {formatDateTime(item.tanggal_pengajuan)}
                        </td>
                        <td className="py-3 px-6">
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => handleApprove(item)}
                              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm text-white bg-sage-green hover:opacity-90 transition-opacity min-h-[44px]"
                              aria-label={`Setujui pengajuan ${item.judul}`}
                            >
                              <span className="material-symbols-outlined text-[18px]">check</span>
                              Setujui
                            </button>
                            <button
                              type="button"
                              onClick={() => handleReject(item)}
                              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm text-outline border border-outline hover:bg-surface-container transition-colors min-h-[44px]"
                              aria-label={`Tolak pengajuan ${item.judul}`}
                            >
                              <span className="material-symbols-outlined text-[18px]">close</span>
                              Tolak
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Section 2: Siap Diambil */}
          <section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
            <div className="p-6 border-b border-paper-shadow bg-surface-container-low">
              <h2 className="text-headline-sm font-headline-sm text-primary">
                Siap Diambil
              </h2>
              <p className="text-body-sm font-body-sm text-outline mt-1">
                Pinjaman yang disetujui dan menunggu diambil oleh mahasiswa.
              </p>
            </div>

            {siapDiambil.length === 0 ? (
              <EmptyState
                icon="shelves"
                title="Tidak Ada Buku Siap Diambil"
                message="Tidak ada pinjaman yang menunggu pengambilan saat ini."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-paper-shadow">
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Mahasiswa
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Buku
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Batas Pengambilan
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Aksi
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {siapDiambil.map((item) => {
                      const isUrgent = isDeadlineUrgent(item.tanggal_siap_ambil);

                      return (
                        <tr
                          key={item.id}
                          className="border-b border-outline-variant/20 last:border-none"
                        >
                          {/* Mahasiswa cell */}
                          <td className="py-3 px-6">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-surface-tint text-on-primary flex items-center justify-center font-bold text-xs shrink-0">
                                {item.nama_mahasiswa?.charAt(0)?.toUpperCase() ?? '?'}
                              </div>
                              <div>
                                <p className="text-body-md font-body-md text-primary">
                                  {item.nama_mahasiswa}
                                </p>
                                <p className="text-body-sm font-body-sm text-outline">
                                  Mahasiswa
                                </p>
                              </div>
                            </div>
                          </td>
                          <BookCell item={item} />
                          <td className="py-3 px-6">
                            <span
                              className={`inline-flex items-center gap-1 text-body-sm font-body-sm ${
                                isUrgent ? 'text-alert-crimson' : 'text-outline'
                              }`}
                            >
                              <span
                                className="material-symbols-outlined text-[16px]"
                                aria-hidden="true"
                              >
                                event_available
                              </span>
                              {formatDateTime(item.tanggal_siap_ambil)}
                            </span>
                          </td>
                          <td className="py-3 px-6">
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() => handleHandover(item)}
                                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm text-white bg-ink-blue hover:opacity-90 transition-opacity min-h-[44px]"
                                aria-label={`Serahkan buku ${item.judul}`}
                              >
                                <span className="material-symbols-outlined text-[18px]">inventory_2</span>
                                Serahkan
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Section 3: Sedang Dipinjam */}
          <section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
            <div className="p-6 border-b border-paper-shadow bg-surface-container-low">
              <h2 className="text-headline-sm font-headline-sm text-primary">
                Sedang Dipinjam
              </h2>
              <p className="text-body-sm font-body-sm text-outline mt-1">
                Semua buku yang sedang dipinjam, diurutkan berdasarkan yang paling terlambat.
              </p>
            </div>

            {sedangDipinjam.length === 0 ? (
              <EmptyState
                icon="inventory_2"
                title="Tidak Ada Pinjaman Aktif"
                message="Tidak ada buku yang sedang dipinjam saat ini."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-paper-shadow">
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Mahasiswa
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Buku
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Tenggat
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Aksi
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sedangDipinjam.map((item) => (
                      <tr
                        key={item.id}
                        className="border-b border-outline-variant/20 last:border-none"
                      >
                        {/* Mahasiswa cell */}
                        <td className="py-3 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-surface-tint text-on-primary flex items-center justify-center font-bold text-xs shrink-0">
                              {item.nama_mahasiswa?.charAt(0)?.toUpperCase() ?? '?'}
                            </div>
                            <div>
                              <p className="text-body-md font-body-md text-primary">
                                {item.nama_mahasiswa}
                              </p>
                              <p className="text-body-sm font-body-sm text-outline">
                                Mahasiswa
                              </p>
                            </div>
                          </div>
                        </td>
                        <BookCell item={item} />
                        <td className="py-3 px-6">
                          <span className={`inline-flex items-center gap-1 text-body-sm font-body-sm ${item.is_terlambat ? 'text-alert-crimson font-medium' : 'text-outline'}`}>
                            <span
                              className="material-symbols-outlined text-[16px]"
                              aria-hidden="true"
                            >
                              calendar_today
                            </span>
                            {formatDate(item.tanggal_tenggat)}
                          </span>
                        </td>
                        <td className="py-3 px-6">
                          <StatusBadge status={item.is_terlambat ? 'terlambat' : 'dipinjam'} />
                        </td>
                        <td className="py-3 px-6">
                          <button
                            type="button"
                            onClick={() => handleKembalikan(item)}
                            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm text-white bg-ink-blue hover:opacity-90 transition-opacity min-h-[44px]"
                            aria-label={`Tandai buku ${item.judul} sudah dikembalikan`}
                          >
                            <span className="material-symbols-outlined text-[18px]">assignment_return</span>
                            Kembalikan
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Section 4: Anggota Diblokir */}
          <section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
            <div className="p-6 border-b border-paper-shadow bg-surface-container-low">
              <h2 className="text-headline-sm font-headline-sm text-primary">
                Anggota Diblokir
              </h2>
              <p className="text-body-sm font-body-sm text-outline mt-1">
                Anggota dengan denda tertunggak — buka blokir setelah denda dibayar.
              </p>
            </div>

            {anggotaDiblokir.length === 0 ? (
              <EmptyState
                icon="task_alt"
                title="Tidak Ada Anggota Diblokir"
                message="Semua anggota dalam status baik — tidak ada denda tertunggak."
              />
            ) : (
              <div className="p-6 space-y-4">
                {anggotaDiblokir.map((item) => (
                  <div
                    key={item.id_pengguna}
                    className="flex items-center justify-between p-4 rounded-xl bg-surface-container-low border border-paper-shadow"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-alert-crimson/20 text-alert-crimson flex items-center justify-center font-bold text-sm shrink-0">
                        {item.nama?.charAt(0)?.toUpperCase() ?? '?'}
                      </div>
                      <div>
                        <p className="text-body-md font-body-md text-primary">
                          {item.nama}
                        </p>
                        <p className="text-body-sm font-body-sm text-outline">
                          {item.email}
                        </p>
                        <p className="text-body-sm font-body-sm text-outline mt-1">
                          Denda Tertunggak:{' '}
                          <span className="text-alert-crimson font-semibold">
                            Rp {item.total_denda.toLocaleString('id-ID')}
                          </span>
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleLunasiDenda(item)}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm text-white bg-sage-green hover:opacity-90 transition-opacity min-h-[44px] shrink-0"
                      aria-label={`Tandai denda ${item.nama} lunas`}
                    >
                      <span className="material-symbols-outlined text-[18px]">lock_open</span>
                      Denda Lunas
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {/* ── PUSTAKAWAN loading (skeleton) ── */}
      {!isMahasiswa && loading && (
        <div className="space-y-8">
          {[1, 2, 3, 4].map((sec) => (
            <section
              key={sec}
              className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden"
            >
              <div className="p-6 border-b border-paper-shadow bg-surface-container-low">
                <div className="h-6 w-48 bg-surface-container-high rounded animate-pulse" />
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-outline-variant/40">
                      <th className="pb-3 px-6 pt-4 text-label-sm">Mahasiswa</th>
                      <th className="pb-3 px-6 pt-4 text-label-sm">Buku</th>
                      <th className="pb-3 px-6 pt-4 text-label-sm">Tanggal</th>
                      <th className="pb-3 px-6 pt-4 text-label-sm">Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    <SkeletonRows />
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </div>
      )}

      {/* ── ConfirmDialog (wired in Plan 03-03) ── */}
      {confirm && (
        <ConfirmDialog
          title={confirm.title}
          message={confirm.message}
          confirmLabel={confirm.confirmLabel}
          destructive={confirm.destructive}
          loading={confirm.loading}
          onConfirm={confirm.onConfirm}
          onCancel={() => setConfirm(null)}
        />
      )}

      {/* Toast */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}
    </main>
  );
}
