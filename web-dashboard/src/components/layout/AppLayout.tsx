import { Outlet } from 'react-router';
import { Sidebar } from '@/components/layout/Sidebar';
import { Topbar } from '@/components/layout/Topbar';

export function AppLayout() {
  return (
    <div className="flex h-full min-h-full flex-col md:flex-row">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col md:h-full">
        <Topbar />
        <main className="flex-1 overflow-y-auto px-4 pt-5 pb-15 md:px-7">
          <div className="mx-auto max-w-[1280px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
