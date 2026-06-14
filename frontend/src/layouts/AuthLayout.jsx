import { Navigate, Outlet, Link } from 'react-router';
import { getToken } from '../lib/auth';

export default function AuthLayout() {
  const token = getToken();
  if (token) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      {/* Spine accent */}
      <div className="fixed left-0 top-0 w-2 h-full bg-gradient-to-b from-[#2C1810] via-[#C8A27A] to-[#2C1810]" />

      <div className="w-full max-w-md">
        {/* Logo + brand */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[#2C1810] flex items-center justify-center">
            <span className="material-symbols-outlined text-[#C8A27A] text-3xl">
              menu_book
            </span>
          </div>
          <h1 className="text-headline-lg font-headline-lg text-primary">
            Biblio
          </h1>
          <p className="text-body-md font-body-md text-outline mt-2">
            Sistem Manajemen Perpustakaan
          </p>
        </div>

        {/* Auth card */}
        <div className="bg-surface rounded-3xl shadow-lg p-8">
          <Outlet />
        </div>

        {/* Footer */}
        <p className="text-center text-body-sm font-body-sm text-outline mt-8">
          &copy; {new Date().getFullYear()} Biblio. All rights reserved.
        </p>
      </div>
    </div>
  );
}
