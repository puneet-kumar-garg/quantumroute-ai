import { useState } from 'react';
import { Sun, Moon, Monitor, ChevronDown, User, Settings, LogOut, Menu } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';

const PAGE_LABELS: Record<string, string> = {
  '/dashboard': 'Operations overview', '/optimize': 'Route workspace', '/simulation': 'Scenario lab',
  '/analytics': 'Measured analytics', '/quantum': 'Quantum evidence', '/ml': 'Traffic model',
  '/reports': 'Reports', '/settings': 'Preferences', '/profile': 'Account', '/admin': 'Administration',
};

export function Navbar({ onMenu }: { onMenu: () => void }) {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [showUser, setShowUser] = useState(false);

  return (
    <header
      className="fixed top-0 right-0 left-0 md:left-[var(--sidebar-width)] h-16 z-30 flex items-center px-4 sm:px-6 gap-3 bg-card/90 backdrop-blur-xl border-b border-border"
    >
      <button aria-label="Open navigation" onClick={onMenu} className="md:hidden p-2 -ml-2 rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"><Menu className="w-5 h-5" /></button>
      <div className="min-w-0 flex-1">
        <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">QuantumRoute AI</p>
        <p className="text-sm font-medium truncate">{PAGE_LABELS[pathname] ?? 'Transportation intelligence'}</p>
      </div>

      <div className="flex items-center gap-2">
        <div className="hidden sm:flex items-center gap-1 p-1 rounded-lg bg-background border border-border" aria-label="Theme">
          {(['light', 'dark', 'system'] as const).map((value) => {
            const Icon = value === 'light' ? Sun : value === 'dark' ? Moon : Monitor;
            return <button key={value} aria-label={`Use ${value} theme`} onClick={() => setTheme(value)} className={cn('p-1.5 rounded-md transition-colors', theme === value ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground')}><Icon className="w-3.5 h-3.5" /></button>;
          })}
        </div>

        <div className="relative">
          <button aria-expanded={showUser} onClick={() => setShowUser(value => !value)} className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-accent transition-colors">
            <div className="w-7 h-7 rounded-full bg-primary/15 text-primary flex items-center justify-center"><span className="text-xs font-bold">{user?.full_name?.[0]?.toUpperCase() || 'U'}</span></div>
            <span className="text-sm font-medium hidden sm:block">{user?.full_name?.split(' ')[0]}</span>
            <ChevronDown className="w-3 h-3 text-muted-foreground hidden sm:block" />
          </button>
          <AnimatePresence>
            {showUser && (
              <motion.div initial={{ opacity: 0, y: 8, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 8, scale: 0.96 }} className="absolute right-0 top-full mt-2 w-52 rounded-xl border border-border bg-card shadow-xl z-50 overflow-hidden">
                <div className="p-3 border-b border-border"><p className="text-sm font-medium">{user?.full_name}</p><p className="text-xs text-muted-foreground truncate">{user?.email}</p></div>
                {[
                  { icon: User, label: 'Profile', path: '/profile' },
                  { icon: Settings, label: 'Settings', path: '/settings' },
                ].map(item => <button key={item.path} onClick={() => { navigate(item.path); setShowUser(false); }} className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-accent transition-colors"><item.icon className="w-4 h-4 text-muted-foreground" />{item.label}</button>)}
                <div className="border-t border-border"><button onClick={async () => { await logout(); navigate('/login'); }} className="flex items-center gap-2 w-full px-3 py-2 text-sm text-rose-400 hover:bg-rose-500/10 transition-colors"><LogOut className="w-4 h-4" />Logout</button></div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
