import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import api from '../lib/api';
import { setToken } from '../lib/auth';
import InputField from '../components/InputField';

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const sessionExpired = searchParams.get('session_expired');

  const [form, setForm] = useState({ email: '', kata_sandi: '' });
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
      const res = await api.post('/autentikasi/masuk', form);
      setToken(res.data.access_token);
      window.location.href = '/';
    } catch (err) {
      const msg =
        err.response?.data?.detail || 'Email atau kata sandi salah.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="text-headline-sm font-headline-sm text-primary mb-2">
        Masuk ke Akun Anda
      </h2>
      <p className="text-body-md font-body-md text-outline mb-8">
        Selamat datang kembali di Biblio.
      </p>

      {sessionExpired && (
        <div className="bg-error/10 text-error text-body-sm font-body-sm px-4 py-3 rounded-lg mb-6">
          Sesi Anda telah berakhir. Silakan masuk kembali.
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
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
          placeholder="Masukkan kata sandi"
          icon="lock"
          value={form.kata_sandi}
          onChange={handleChange}
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
          {loading ? 'Memproses…' : 'Masuk'}
        </button>
      </form>

      <p className="text-center text-body-md font-body-md text-outline mt-8">
        Belum memiliki akun?{' '}
        <Link
          to="/register"
          className="text-antique-gold hover:underline font-label-md"
        >
          Daftar sekarang
        </Link>
      </p>
    </div>
  );
}
