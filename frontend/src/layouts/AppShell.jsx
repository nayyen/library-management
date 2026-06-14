import { Outlet, Link, useLocation } from 'react-router';
import { getToken, decodeToken } from '../lib/auth';

const MAHASISWA_NAV = [
  { label: 'Katalog', path: '/katalog', icon: 'search' },
  { label: 'Pinjaman', path: '/pinjaman', icon: 'bookmark' },
];

const PUSTAKAWAN_NAV = [
  { label: 'Katalog', path: '/katalog', icon: 'search' },
  { label: 'Pinjaman', path: '/pinjaman', icon: 'bookmark' },
  { label: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
  { label: 'Anggota', path: '/anggota', icon: 'group' },
];

export default function AppShell() {
  const { pathname } = useLocation();
  const token = getToken();
  const decoded = token ? decodeToken(token) : null;
  const peran = decoded?.peran ?? 'mahasiswa';
  const navItems = peran === 'pustakawan' ? PUSTAKAWAN_NAV : MAHASISWA_NAV;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="bg-surface shadow-sm">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <Link to="/" className="flex items-center gap-3 no-underline">
            <div className="w-10 h-10 rounded-full bg-[#2C1810] flex items-center justify-center">
              <span className="material-symbols-outlined text-[#C8A27A] text-xl">
                menu_book
              </span>
            </div>
            <span className="text-title-md font-title-md text-primary">
              Biblio
            </span>
          </Link>

          <nav className="flex items-center gap-2">
            {navItems.map((item) => {
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-label-sm font-label-sm transition-colors no-underline ${
                    isActive
                      ? 'bg-secondary-container text-on-secondary-container'
                      : 'text-outline hover:bg-outline-variant/30'
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {item.icon}
                  </span>
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
