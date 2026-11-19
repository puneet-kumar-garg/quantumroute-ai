import { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '@/hooks/useAuth';
import { ThemeProvider } from '@/hooks/useTheme';
import { AppLayout } from '@/components/layout/AppLayout';
import { Spinner } from '@/components/ui/Badge';

const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const OptimizePage = lazy(() => import('@/pages/OptimizePage'));
const SimulationPage = lazy(() => import('@/pages/SimulationPage'));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'));
const QuantumEnginePage = lazy(() => import('@/pages/QuantumEnginePage'));
const MLPage = lazy(() => import('@/pages/MLPage'));
const ReportsPage = lazy(() => import('@/pages/ReportsPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const ProfilePage = lazy(() => import('@/pages/ProfilePage'));
const AdminPage = lazy(() => import('@/pages/AdminPage'));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><Spinner size="lg" /></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== 'admin') return <ForbiddenPage />;
  return <>{children}</>;
}

const TITLES: Record<string, string> = {
  '/login': 'Sign in', '/register': 'Create account', '/dashboard': 'Operations overview',
  '/optimize': 'Route workspace', '/simulation': 'Scenario simulation', '/analytics': 'Analytics',
  '/quantum': 'Quantum evidence', '/ml': 'Traffic model', '/reports': 'Reports',
  '/settings': 'Settings', '/profile': 'Profile', '/admin': 'Administration',
};

function RouteTitle() {
  const { pathname } = useLocation();
  const title = TITLES[pathname] ?? 'Page not found';
  useEffect(() => {
    document.title = `${title} | QuantumRoute AI`;
  }, [title]);
  return null;
}

function ForbiddenPage() {
  return (
    <main className="min-h-[60vh] grid place-items-center p-6">
      <div className="max-w-md text-center space-y-3">
        <p className="text-xs font-mono uppercase tracking-[0.2em] text-amber-500">403 · Restricted</p>
        <h1 className="text-3xl font-semibold">Administrator access required</h1>
        <p className="text-muted-foreground">Your account is signed in, but it cannot manage users or system operations.</p>
        <Link className="inline-flex h-10 items-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground" to="/dashboard">Return to dashboard</Link>
      </div>
    </main>
  );
}

function NotFoundPage() {
  return (
    <main className="min-h-[60vh] grid place-items-center p-6 text-center">
      <div className="space-y-3"><p className="font-mono text-muted-foreground">404</p><h1 className="text-3xl font-semibold">Route not found</h1><Link className="text-primary underline" to="/dashboard">Open dashboard</Link></div>
    </main>
  );
}

const PageLoader = () => (
  <div className="flex items-center justify-center h-64">
    <Spinner size="lg" />
  </div>
);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <RouteTitle />
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/optimize" element={<OptimizePage />} />
                  <Route path="/simulation" element={<SimulationPage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  <Route path="/quantum" element={<QuantumEnginePage />} />
                  <Route path="/ml" element={<MLPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/admin" element={<AdminRoute><AdminPage /></AdminRoute>} />
                </Route>
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
