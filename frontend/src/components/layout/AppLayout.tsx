import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const sidebarWidth = collapsed ? 72 : 240;
  const layoutStyle = { '--sidebar-width': `${sidebarWidth}px` } as React.CSSProperties;

  return (
    <div className="min-h-screen bg-background overflow-x-hidden" style={layoutStyle}>
      {mobileOpen && <button aria-label="Close navigation" onClick={() => setMobileOpen(false)} className="fixed inset-0 z-30 bg-slate-950/55 backdrop-blur-sm md:hidden" />}
      <Sidebar collapsed={collapsed} mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} onToggle={() => setCollapsed(!collapsed)} />
      <Navbar onMenu={() => setMobileOpen(true)} />
      <motion.main className="min-h-screen pt-16 md:ml-[var(--sidebar-width)]">
        <div className="p-4 sm:p-6">
          <Outlet />
        </div>
      </motion.main>
    </div>
  );
}
