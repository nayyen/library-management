/**
 * AnggotaPage — pustakawan member roster (DASH-02).
 *
 * Displays a 2-column card grid of all mahasiswa with:
 *   - Search (client-side, name/email)
 *   - Status filter (Semua / Aktif / Diblokir)
 *   - Per-member: avatar, nama, email, StatusBadge, pinjaman_aktif count,
 *     total_denda (if blocked), and "Denda Lunas" action (if blocked + has denda)
 */

import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import { getToken, decodeToken } from '../lib/auth';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import Toast from '../components/Toast';
import ConfirmDialog from '../components/ConfirmDialog';

/* ── date helper for formatting ── */
const MONTHS_ID = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS_ID[d.getMonth()]} ${d.getFullYear()}`;
}

export default function AnggotaPage() {
  const token = getToken();
  const decoded = token ? decodeToken(token) : null;
  const peran = decoded?.peran ?? 'mahasiswa';

  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('semua');

  // Confirm dialog state
  const [confirm, setConfirm] = useState(null);

  // Refresh trigger
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchMembers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/anggota');
      setMembers(res.data.items ?? []);
    } catch {
      setError('Gagal memuat data anggota. Periksa koneksi Anda dan coba lagi.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers, refreshKey]);

  /* ── Confirm helpers ── */

  function showConfirm({ title, message, confirmLabel, destructive, onConfirm }) {
    setConfirm({ title, message, confirmLabel, destructive, onConfirm, loading: false });
  }

  function setConfirmLoading(loading) {
    setConfirm((prev) => (prev ? { ...prev, loading } : prev));
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

  /* ── Filter ── */

  const filteredMembers = members.filter((m) => {
    const matchesSearch =
      !searchQuery ||
      m.nama.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.email.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      statusFilter === 'semua' ||
      (statusFilter === 'aktif' && !m.is_diblokir) ||
      (statusFilter === 'diblokir' && m.is_diblokir);

    return matchesSearch && matchesStatus;
  });

  /* ── Loading skeleton ── */

  function MemberSkeleton() {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="bg-surface-container-lowest border border-paper-shadow rounded-xl p-6 animate-pulse"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-surface-container-high" />
              <div className="space-y-2 flex-1">
                <div className="h-4 bg-surface-container-high rounded w-1/2" />
                <div className="h-3 bg-surface-container-high rounded w-2/3" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="h-12 bg-surface-container-high rounded-xl" />
              <div className="h-12 bg-surface-container-high rounded-xl" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  /* ── Render ── */

  return (
    <main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-headline-md font-headline-md text-primary mb-1">
          Manajemen Anggota
        </h1>
        <p className="text-body-md font-body-md text-outline">
          Daftar seluruh mahasiswa terdaftar beserta status dan informasi peminjaman.
        </p>
      </div>

      {/* Toolbar: search + filter */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative w-full md:flex-1">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-outline text-[20px] pointer-events-none">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Cari berdasarkan Nama, Email..."
            className="w-full bg-surface-container-low border border-outline-variant rounded-full py-3 pl-12 pr-4 text-body-md font-body-md text-primary placeholder:text-outline-variant focus:outline-none focus:border-antique-gold focus:ring-1 focus:ring-antique-gold transition-all min-h-[44px]"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-surface-container-low border border-outline-variant rounded-full py-3 px-4 text-body-md font-body-md text-primary focus:outline-none focus:border-antique-gold focus:ring-1 focus:ring-antique-gold transition-all min-h-[44px]"
        >
          <option value="semua">Semua Status</option>
          <option value="aktif">Aktif</option>
          <option value="diblokir">Diblokir</option>
        </select>
      </div>

      {/* Error state */}
      {error && (
        <EmptyState
          icon="error"
          title="Gagal Memuat Data"
          message={error}
        />
      )}

      {/* Loading */}
      {loading && !error && <MemberSkeleton />}

      {/* Content */}
      {!loading && !error && (
        <>
          {members.length === 0 ? (
            <EmptyState
              icon="group_off"
              title="Belum Ada Anggota"
              message="Belum ada mahasiswa yang terdaftar di sistem."
            />
          ) : filteredMembers.length === 0 ? (
            <EmptyState
              icon="search_off"
              title="Tidak Ditemukan"
              message="Tidak ada anggota yang sesuai dengan pencarian atau filter Anda. Coba ubah kata kunci atau filter status."
            />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {filteredMembers.map((item) => (
                <div
                  key={item.id_pengguna}
                  className={`bg-surface-container-lowest border rounded-xl p-6 relative overflow-hidden ${
                    item.is_diblokir ? 'border-alert-crimson/30' : 'border-paper-shadow'
                  }`}
                >
                  {/* Avatar + name/email + status badge */}
                  <div className="flex items-start gap-4 mb-4">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm shrink-0 ${
                        item.is_diblokir
                          ? 'bg-alert-crimson/10 text-alert-crimson'
                          : 'bg-primary-fixed text-primary-container'
                      }`}
                    >
                      {item.nama?.charAt(0)?.toUpperCase() ?? '?'}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-body-md font-body-md text-primary truncate">
                        {item.nama}
                      </p>
                      <p className="text-body-sm font-body-sm text-outline truncate">
                        {item.email}
                      </p>
                      <div className="mt-2">
                        <StatusBadge
                          status={item.is_diblokir ? 'anggota_diblokir' : 'anggota_aktif'}
                          compact
                        />
                      </div>
                    </div>
                  </div>

                  {/* Info grid */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-surface-container-low rounded-xl p-3">
                      <p className="text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Pinjaman Aktif
                      </p>
                      <p className="text-headline-xs font-headline-xs text-primary mt-1">
                        {item.pinjaman_aktif}
                      </p>
                    </div>
                    <div className="bg-surface-container-low rounded-xl p-3">
                      <p className="text-label-sm font-label-sm text-outline uppercase tracking-wider">
                        Total Denda
                      </p>
                      <p className={`text-headline-xs font-headline-xs mt-1 ${
                        item.total_denda > 0
                          ? 'text-alert-crimson font-bold'
                          : 'text-primary'
                      }`}>
                        {item.total_denda > 0
                          ? `Rp ${item.total_denda.toLocaleString('id-ID')}`
                          : 'Rp 0'}
                      </p>
                    </div>
                  </div>

                  {/* Action row: Denda Lunas (blocked + has denda) */}
                  {item.is_diblokir && item.total_denda > 0 && (
                    <div className="flex justify-end gap-3 border-t border-paper-shadow pt-4">
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
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Toast */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      {/* Confirm dialog */}
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
    </main>
  );
}
