import { useState } from 'react';
import api from '../lib/api';
import InputField from './InputField';

/**
 * TambahSalinanForm — add a copy to a book.
 *
 * Props:
 *   idBuku : string  — book UUID
 *   onAdded: (salinan) => void
 */
export default function TambahSalinanForm({ idBuku, onAdded }) {
  const [form, setForm] = useState({
    lokasi_rak: '',
    kondisi: 'bagus',
    status_ketersediaan: 'tersedia',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.lokasi_rak.trim()) {
      setError('Lokasi rak wajib diisi.');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const res = await api.post(`/buku/${idBuku}/salinan`, form);
      onAdded(res.data);
      setForm({ lokasi_rak: '', kondisi: 'bagus', status_ketersediaan: 'tersedia' });
    } catch (err) {
      setError(err.response?.data?.detail || 'Gagal menambah salinan. Silakan coba lagi.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-surface-container-low rounded-xl p-6 book-shadow">
      <h3 className="text-label-md font-label-md text-primary mb-4 uppercase tracking-wider flex items-center gap-2">
        <span className="material-symbols-outlined text-[18px] text-outline">add_box</span>
        Tambah Salinan
      </h3>

      <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4 items-end">
        <div className="flex-1 min-w-0">
          <InputField
            label="Lokasi Rak"
            name="lokasi_rak"
            placeholder="Contoh: A-1"
            icon="shelves"
            value={form.lokasi_rak}
            onChange={handleChange}
            required
          />
        </div>

        <div className="w-full md:w-44">
          <label className="block text-label-md font-label-md text-primary mb-1">
            Kondisi
          </label>
          <select
            name="kondisi"
            value={form.kondisi}
            onChange={handleChange}
            className="w-full bg-transparent border-b-2 border-outline-variant py-3 text-body-md font-body-md text-primary focus:outline-none focus:border-antique-gold transition-colors"
          >
            <option value="bagus">Bagus</option>
            <option value="rusak_ringan">Rusak Ringan</option>
            <option value="rusak_berat">Rusak Berat</option>
          </select>
        </div>

        <div className="w-full md:w-44">
          <label className="block text-label-md font-label-md text-primary mb-1">
            Status
          </label>
          <select
            name="status_ketersediaan"
            value={form.status_ketersediaan}
            onChange={handleChange}
            className="w-full bg-transparent border-b-2 border-outline-variant py-3 text-body-md font-body-md text-primary focus:outline-none focus:border-antique-gold transition-colors"
          >
            <option value="tersedia">Tersedia</option>
            <option value="dipesan">Dipesan</option>
            <option value="dipinjam">Dipinjam</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full md:w-auto bg-antique-gold text-white rounded-full px-6 py-3 text-label-sm font-label-sm hover:opacity-90 transition-opacity disabled:opacity-50 inline-flex items-center justify-center gap-2 shrink-0"
        >
          {loading && (
            <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>
          )}
          Tambah Salinan
        </button>
      </form>

      {error && (
        <p className="text-body-sm font-body-sm text-error mt-3">{error}</p>
      )}
    </div>
  );
}
