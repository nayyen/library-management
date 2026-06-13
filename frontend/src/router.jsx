import { createBrowserRouter } from 'react-router';
import AuthLayout from './layouts/AuthLayout';
import AppShell from './layouts/AppShell';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import WelcomePage from './pages/WelcomePage';
import ComingSoonPage from './pages/ComingSoonPage';
import KatalogPage from './pages/KatalogPage';
import BukuDetailPage from './pages/BukuDetailPage';

const router = createBrowserRouter([
  {
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <WelcomePage /> },
          { path: 'katalog', element: <KatalogPage /> },
          { path: 'katalog/:id', element: <BukuDetailPage /> },
          { path: 'pinjaman', element: <ComingSoonPage title="Riwayat Peminjaman" /> },
          { path: 'dashboard', element: <ComingSoonPage title="Dashboard Pustakawan" /> },
          { path: 'anggota', element: <ComingSoonPage title="Manajemen Anggota" /> },
        ],
      },
    ],
  },
]);

export default router;
