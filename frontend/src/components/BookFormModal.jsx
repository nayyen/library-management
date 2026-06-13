import { useState, useEffect } from 'react';
import api from '../lib/api';
import InputField from './InputField';

const CURRENT_YEAR = new Date().getFullYear();

export default function BookFormModal({ mode, buku, categories, onClose, onSaved }) {
  const [form, setForm] = useState({ judul: '', penulis: '', isbn: '', kategori: '', tahun_terbit: '' });
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const isEdit = mode === 'edit';

  useEffect(() => {
    if (isEdit && buku) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setForm({
        judul: buku.judul ?? '',
        penulis: buku.penulis ?? '',
        isbn: buku.isbn ?? '',
        kategori: buku.kategori ?? '',
        tahun_terbit: buku.tahun_terbit?.toString() ?? '',
      });
    }
  }, [isEdit, buku]);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    // Clear field error on change
    if (fieldErrors[e.target.name]) {
      setFieldErrors((prev) => ({ ...prev, [e.target.name]: '' }));
    }
    setSubmitError('');
  }

  function validate() {
    const errors = {};
    const fields = {
      judul: 'Judul',
      penulis: 'Penulis',
      isbn: 'ISBN',
      kategori: 'Kategori',
      tahun_terbit: 'Tahun Terbit',
    };

    for (const [key, label] of Object.entries(fields)) {
      if (!form[key]?.trim()) {
        errors[key] = `${label} wajib diisi.`;
      }
    }

    if (form.isbn && !errors.isbn) {
      const digits = form.isbn.replace(/-/g, '');
      if (!/^\d+$/.test(digits)) {
        errors.isbn = 'ISBN harus berupa angka (boleh mengandung tanda hubung).';
      } else if (digits.length !== 10 && digits.length !== 13) {
        errors.isbn = 'ISBN harus berupa 10 atau 13 digit angka (boleh mengandung tanda hubung).';
      }
    }

    if (form.tahun_terbit && !errors.tahun_terbit) {
      const year = parseInt(form.tahun_terbit, 10);
      if (isNaN(year) || year < 1900 || year > CURRENT_YEAR) {
        errors.tahun_terbit = `Tahun terbit harus antara 1900 dan ${CURRENT_YEAR}.`;
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setSubmitError('');

    const payload = {
      ...form,
      tahun_terbit: parseInt(form.tahun_terbit, 10),
    };

    try {
      const res = isEdit
        ? await api.put(`/buku/${buku.id}`, payload)
        : await api.post('/buku', payload);
      onSaved(res.data);
      onClose();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 409) {
        setSubmitError(detail || 'ISBN sudah terdaftar.');
      } else if (err.response?.status === 422 && detail) {
        // Map server validation errors to fields
        if (Array.isArray(detail)) {
          const serverErrors = {};
          for (const d of detail) {
            const field = d.loc?.at(-1);
            if (field) serverErrors[field] = d.msg;
          }
          setFieldErrors((prev) => ({ ...prev, ...serverErrors }));
        } else {
          setSubmitError(detail);
        }
      } else {
        setSubmitError(detail || 'Gagal menyimpan buku. Silakan coba lagi.');
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-primary/40 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="form-modal-title"
      onClick={handleBackdrop}
      onKeyDown={handleKeyDown}
    >
      <div className="bg-surface-container-lowest rounded-xl border border-paper-shadow p-6 max-w-md w-full book-shadow max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 id="form-modal-title" className="text-headline-sm font-headline-sm text-primary">
            {isEdit ? 'Edit Buku' : 'Tambah Buku'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="w-11 h-11 flex items-center justify-center rounded-full hover:bg-surface-container transition-colors"
            aria-label="Tutup"
          >
            <span className="material-symbols-outlined text-outline">close</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <InputField
            autoFocus
            label="Judul"
            name="judul"
            placeholder="Masukkan judul buku"
            icon="title"
            value={form.judul}
            onChange={handleChange}
            error={fieldErrors.judul}
            required
          />
          <InputField
            label="Penulis"
            name="penulis"
            placeholder="Masukkan nama penulis"
            icon="person"
            value={form.penulis}
            onChange={handleChange}
            error={fieldErrors.penulis}
            required
          />
          <InputField
            label="ISBN"
            name="isbn"
            placeholder="978xxxxxxxxxx"
            icon="qr_code_2"
            value={form.isbn}
            onChange={handleChange}
            error={fieldErrors.isbn}
            required
          />
          <InputField
            label="Kategori"
            name="kategori"
            placeholder="Fiksi, Non-Fiksi, dll."
            icon="category"
            value={form.kategori}
            onChange={handleChange}
            error={fieldErrors.kategori}
            required
            list="kategori-list"
          />
          <datalist id="kategori-list">
            {(categories ?? []).map((kat) => (
              <option key={kat} value={kat} />
            ))}
          </datalist>

          <InputField
            label="Tahun Terbit"
            name="tahun_terbit"
            type="number"
            placeholder="Contoh: 2020"
            icon="calendar_today"
            value={form.tahun_terbit}
            onChange={handleChange}
            error={fieldErrors.tahun_terbit}
            min={1900}
            max={CURRENT_YEAR}
            required
          />

          {submitError && (
            <p className="text-body-sm font-body-sm text-error">{submitError}</p>
          )}

          {/* Footer */}
          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-full text-label-sm font-label-sm text-outline border border-outline-variant hover:bg-surface-container transition-colors"
            >
              Batal
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-full text-label-sm font-label-sm text-white bg-antique-gold hover:opacity-90 transition-opacity disabled:opacity-50 inline-flex items-center gap-2"
            >
              {loading && (
                <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>
              )}
              {isEdit ? 'Simpan Perubahan' : 'Simpan Buku'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
