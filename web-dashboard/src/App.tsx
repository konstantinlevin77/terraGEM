import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router';
import { AuthProvider } from '@/hooks/useAuth';
import { ScopeProvider } from '@/hooks/useScope';
import { I18nProvider } from '@/i18n';
import { ToastProvider } from '@/components/toast';
import { RedirectIfAuthed, RequireAuth } from '@/components/layout/guards';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { OverviewPage } from '@/pages/OverviewPage';
import { GreenhousesPage } from '@/pages/GreenhousesPage';
import { SensorsPage } from '@/pages/SensorsPage';
import { HistoryPage } from '@/pages/HistoryPage';
import { SettingsPage } from '@/pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (failureCount, error) => {
        const status = (error as { status?: number }).status;
        if (status !== undefined && status < 500) return false;
        return failureCount < 2;
      },
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <AuthProvider>
          <ScopeProvider>
            <ToastProvider>
              <BrowserRouter>
                <Routes>
                  <Route
                    path="/login"
                    element={
                      <RedirectIfAuthed>
                        <LoginPage />
                      </RedirectIfAuthed>
                    }
                  />
                  <Route
                    element={
                      <RequireAuth>
                        <AppLayout />
                      </RequireAuth>
                    }
                  >
                    <Route path="/" element={<Navigate to="/overview" replace />} />
                    <Route path="/overview" element={<OverviewPage />} />
                    <Route path="/greenhouses" element={<GreenhousesPage />} />
                    <Route path="/sensors" element={<SensorsPage />} />
                    <Route path="/history" element={<HistoryPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                  </Route>
                  <Route path="*" element={<Navigate to="/overview" replace />} />
                </Routes>
              </BrowserRouter>
            </ToastProvider>
          </ScopeProvider>
        </AuthProvider>
      </I18nProvider>
    </QueryClientProvider>
  );
}
