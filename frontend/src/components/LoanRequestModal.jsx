/**
 * LoanRequestModal — 3-section confirmation modal for loan requests (D-03).
 *
 * Props:
 *   buku     : object — { judul, penulis, kategori, ... }
 *   salinan  : object — { id, lokasi_rak, ... }
 *   user     : object — { nama, peran, ... }
 *   onClose  : () => void
 *   onSuccess: () => void — called after successful submission
 */

import { useState } from 'react';
import api from '../lib/api';
import BookCoverPlaceholder from './BookCoverPlaceholder';

const MONTHS_ID = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];

function formatDate(date) {
  return `${date.getDate()} ${MONTHS_ID[date.getMonth()]} ${date.getFullYear()}`;
}

function getEstimatedDue() {
  const d = new Date();
  d.setDate(d.getDate() + 14);
  return formatDate(d);
}

export default function LoanRequestModal({ buku, salinan, user, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setSubmitError('');

    try {
      await api.post('/peminjaman/ajukan', {
        id_salinan_buku: salinan.id,
      });
      onClose();
      onSuccess?.();
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 400) {
        if (detail && detail.toLowerCase().includes('diblokir')) {
          setSubmitError(
            'Akun Anda diblokir karena denda belum lunas. Hubungi pustakawan untuk informasi lebih lanjut.',
          );
        } else if (detail && detail.toLowerCase().includes('5 pinjaman')) {
          setSubmitError(
            'Anda sudah memiliki 5 pinjaman aktif. Selesaikan salah satu sebelum mengajukan pinjaman baru.',
          );
        } else {
          setSubmitError(detail || 'Gagal mengirim pengajuan. Silakan coba lagi.');
        }
      } else if (status === 409) {
        setSubmitError('Salinan ini sudah tidak tersedia. Pilih salinan lain.');
      } else {
        setSubmitError(
          detail || 'Gagal mengirim pengajuan. Silakan coba lagi.',
        );
      }
    } finally {
      setLoading(false);
    }
  }

  function handleBackdrop(e) {
    if (e.target === e.currentTarget) onClose();
  }

  function handleKeyDown(e) {
    if (e.key === 'Escape') onClose();
  }

  return (
    <>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-primary/40 backdrop-blur-sm p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="loan-modal-title"
        onClick={handleBackdrop}
        onKeyDown={handleKeyDown}
      >
        <div className="relative bg-surface-container-lowest rounded-xl border border-paper-shadow shadow-2xl z-50 w-full max-w-lg overflow-hidden flex flex-col">
          {/* Header */}
          <div className="px-6 py-5 border-b border-paper-shadow bg-surface-container-lowest flex justify-between items-center">
            <div>
              <h2
                id="loan-modal-title"
                className="text-headline-md font-headline-md text-primary"
              >
                Formulir Peminjaman
              </h2>
              <p className="text-body-sm font-body-sm text-outline mt-0.5">
                Sistem Manajemen Perpustakaan
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="w-11 h-11 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors shrink-0"
              aria-label="Tutup"
            >
              <span className="material-symbols-outlined text-outline">close</span>
            </button>
          </div>

          {/* Body */}
          <form
            onSubmit={handleSubmit}
            className="px-6 py-6 space-y-8 overflow-y-auto max-h-[70vh]"
          >
            {/* Section 1: Buku Terpilih */}
            <section>
              <p className="text-label-sm font-label-sm text-antique-gold uppercase tracking-wider mb-3">
                Buku Terpilih
              </p>
              <div className="flex gap-4 p-4 bg-surface-container-low rounded-lg border border-paper-shadow">
                <div className="w-20 h-28 shrink-0 border-l-4 border-antique-gold rounded overflow-hidden">
                  <BookCoverPlaceholder
                    judul={buku?.judul}
                    kategori={buku?.kategori}
                    className="rounded-none"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-headline-sm font-headline-sm text-primary truncate">
                    {buku?.judul}
                  </p>
                  <p className="text-body-sm font-body-sm text-outline mt-1 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
                      person
                    </span>
                    {buku?.penulis}
                  </p>
                  <p className="text-body-sm font-body-sm text-outline mt-1 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
                      barcode
                    </span>
                    Lokasi Rak: {salinan?.lokasi_rak}
                  </p>
                </div>
              </div>
            </section>

            {/* Section 2: Informasi Peminjam */}
            <section>
              <p className="text-label-sm font-label-sm text-outline uppercase tracking-wider border-b border-paper-shadow pb-2 mb-4">
                Informasi Peminjam
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3 bg-surface-container-low border border-paper-shadow rounded px-3 py-2">
                  <span
                    className="material-symbols-outlined text-outline shrink-0"
                    aria-hidden="true"
                  >
                    account_circle
                  </span>
                  <div>
                    <p className="text-label-sm font-label-sm text-outline-variant uppercase tracking-wider">
                      Nama Lengkap
                    </p>
                    <p className="text-body-md font-body-md text-primary">
                      {user?.nama}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 bg-surface-container-low border border-paper-shadow rounded px-3 py-2">
                  <span
                    className="material-symbols-outlined text-outline shrink-0"
                    aria-hidden="true"
                  >
                    school
                  </span>
                  <div>
                    <p className="text-label-sm font-label-sm text-outline-variant uppercase tracking-wider">
                      Peran
                    </p>
                    <p className="text-body-md font-body-md text-primary capitalize">
                      {user?.peran}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Section 3: Ringkasan Peminjaman */}
            <section className="bg-primary-fixed/30 rounded-lg p-4 border border-primary-fixed-dim">
              <p className="text-label-sm font-label-sm text-ink-blue flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                  info
                </span>
                Ringkasan Peminjaman
              </p>
              <p className="text-body-sm font-body-sm text-on-surface-variant mt-2">
                Peminjaman berlaku selama{' '}
                <strong>14 hari</strong> setelah buku diserahkan oleh pustakawan.
                Pastikan mengembalikan buku tepat waktu untuk menghindari denda
                sebesar Rp 1.000/hari.
              </p>
              <div className="flex justify-between items-center bg-surface rounded px-3 py-2 border border-paper-shadow mt-3">
                <span className="text-label-md font-label-md text-outline">
                  Estimasi Tenggat Waktu
                </span>
                <span className="text-label-md font-label-md text-primary">
                  {getEstimatedDue()}
                </span>
              </div>
              <p className="text-label-sm font-label-sm text-outline-variant mt-1 italic">
                *Tanggal pasti akan ditentukan saat buku diserahkan oleh pustakawan.
              </p>
            </section>

            {/* Error */}
            {submitError && (
              <div
                className="bg-alert-crimson/10 border border-alert-crimson/20 rounded-lg px-4 py-3 text-body-sm font-body-sm text-alert-crimson flex items-start gap-2"
                role="alert"
              >
                <span className="material-symbols-outlined text-[18px] shrink-0" aria-hidden="true">
                  error
                </span>
                {submitError}
              </div>
            )}
          </form>

          {/* Footer */}
          <div className="px-6 py-5 bg-surface-container-lowest border-t border-paper-shadow flex flex-col-reverse sm:flex-row justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-5 py-2.5 rounded-full text-label-sm font-label-sm text-outline border border-outline-variant hover:bg-surface-container transition-colors disabled:opacity-50"
            >
              Batal
            </button>
            <button
              type="submit"
              onClick={handleSubmit}
              disabled={loading}
              className="px-6 py-2.5 rounded-full text-label-sm font-label-sm text-white bg-antique-gold hover:opacity-90 transition-opacity disabled:opacity-50 inline-flex items-center gap-2 justify-center"
            >
              {loading && (
                <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
              )}
              <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                send
              </span>
              Ajukan Peminjaman
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
