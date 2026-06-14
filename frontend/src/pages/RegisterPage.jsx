import { useState } from 'react';
import { Link } from 'react-router';
import api from '../lib/api';
import { setToken } from '../lib/auth';
import InputField from '../components/InputField';

export default function RegisterPage() {
  const [form, setForm] = useState({ nama: '', email: '', kata_sandi: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/autentikasi/registrasi', form);
      setToken(res.data.access_token);
      window.location.href = '/';
    } catch (err) {
      const msg =
        err.response?.data?.detail || 'Gagal mendaftarkan akun. Silakan coba lagi.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="text-headline-sm font-headline-sm text-primary mb-2">
        Buat Akun Baru
      </h2>
      <p className="text-body-md font-body-md text-outline mb-8">
        Daftar untuk mulai menggunakan Biblio.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <InputField
          label="Nama Lengkap"
          type="text"
          name="nama"
          placeholder="Nama lengkap Anda"
          icon="person"
          value={form.nama}
          onChange={handleChange}
          required
        />
        <InputField
          label="Email"
          type="email"
          name="email"
          placeholder="contoh@email.com"
          icon="mail"
          value={form.email}
          onChange={handleChange}
          required
        />
        <InputField
          label="Kata Sandi"
          type="password"
          name="kata_sandi"
          placeholder="Minimal 8 karakter"
          icon="lock"
          value={form.kata_sandi}
          onChange={handleChange}
          minLength={8}
          required
        />

        {error && (
          <p className="text-body-sm font-body-sm text-error">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-antique-gold text-white rounded-full py-3 text-label-sm font-label-sm hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {loading ? 'Memproses…' : 'Daftar'}
        </button>
      </form>

      <p className="text-center text-body-md font-body-md text-outline mt-8">
        Sudah punya akun?{' '}
        <Link
          to="/login"
          className="text-antique-gold hover:underline font-label-md"
        >
          Masuk
        </Link>
      </p>
    </div>
  );
}
