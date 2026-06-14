import { useAuth } from '../hooks/useAuth';
import RoleBadge from '../components/RoleBadge';

export default function WelcomePage() {
  const { user, logout } = useAuth();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="w-24 h-24 rounded-full bg-[#2C1810] flex items-center justify-center mb-6">
        <span className="material-symbols-outlined text-[#C8A27A] text-5xl">
          menu_book
        </span>
      </div>

      <h1 className="text-headline-lg font-headline-lg text-primary mb-3">
        Selamat datang, {user?.nama}
      </h1>

      <RoleBadge peran={user?.peran} />

      <p className="text-body-md font-body-md text-outline mt-6 max-w-md">
        Anda telah berhasil masuk ke sistem manajemen perpustakaan Biblio.
        Gunakan navigasi di atas untuk memulai.
      </p>

      <button
        onClick={logout}
        className="mt-8 text-outline hover:text-error transition-colors text-label-sm font-label-sm flex items-center gap-2"
      >
        <span className="material-symbols-outlined text-[18px]">logout</span>
        Keluar
      </button>
    </div>
  );
}
