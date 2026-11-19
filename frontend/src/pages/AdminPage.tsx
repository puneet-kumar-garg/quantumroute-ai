import { motion } from 'framer-motion';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Shield, Users, Database, Activity, RefreshCw, UserRoundCheck } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import api from '@/lib/api';
import type { DashboardStats, User } from '@/types';

export default function AdminPage() {
  const queryClient = useQueryClient();
  const usersQuery = useQuery<User[]>({
    queryKey: ['admin-users'],
    queryFn: async () => (await api.get('/admin/users')).data,
  });
  const statsQuery = useQuery<DashboardStats>({
    queryKey: ['admin-stats'],
    queryFn: async () => (await api.get('/routes/stats')).data,
  });
  const healthQuery = useQuery<{ status: string; version: string; database: string; quantum_backend: string | null }>({
    queryKey: ['health'],
    queryFn: async () => (await api.get('/health')).data,
  });
  const toggleUser = useMutation({
    mutationFn: async (userId: number) => (await api.patch(`/admin/users/${userId}/toggle`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  const users = usersQuery.data ?? [];
  const stats = [
    { label: 'Registered Users', value: usersQuery.isLoading ? '…' : users.length, icon: Users, color: 'text-blue-400' },
    { label: 'Active Users', value: usersQuery.isLoading ? '…' : users.filter(user => user.is_active).length, icon: UserRoundCheck, color: 'text-emerald-400' },
    { label: 'Stored Routes', value: statsQuery.data?.total_routes ?? '—', icon: Database, color: 'text-purple-400' },
    { label: 'API Health', value: healthQuery.data?.status ?? (healthQuery.isLoading ? 'checking' : 'unavailable'), icon: Activity, color: healthQuery.data?.status === 'healthy' ? 'text-emerald-400' : 'text-amber-400' },
  ];

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-2"><Shield className="w-6 h-6 text-purple-400" /><h1 className="text-2xl font-bold">Admin Console</h1></div>
        <p className="text-sm text-muted-foreground mt-1">Measured service state and account administration</p>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((item, index) => (
          <motion.div key={item.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}>
            <Card glass className="p-4"><div className="flex items-center gap-3"><item.icon className={`w-5 h-5 ${item.color}`} /><div><p className="text-xs text-muted-foreground">{item.label}</p><p className="text-xl font-bold capitalize">{item.value}</p></div></div></Card>
          </motion.div>
        ))}
      </div>

      <Card glass>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div><CardTitle>User Management</CardTitle><p className="text-xs text-muted-foreground mt-1">Changes are persisted by the PostgreSQL-backed admin API.</p></div>
            <Button variant="outline" size="sm" onClick={() => usersQuery.refetch()}><RefreshCw className="w-3.5 h-3.5" /> Refresh</Button>
          </div>
        </CardHeader>
        <CardContent>
          {usersQuery.isError && <p className="text-sm text-rose-400">Users could not be loaded.</p>}
          {!usersQuery.isLoading && !usersQuery.isError && users.length === 0 && <p className="text-sm text-muted-foreground">No users are registered.</p>}
          <div className="space-y-2">
            {users.map((user, index) => (
              <motion.div key={user.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.04 }} className="flex flex-col sm:flex-row sm:items-center gap-3 p-3 rounded-lg bg-background/50 border border-border">
                <div className="w-9 h-9 rounded-full bg-primary/15 text-primary flex items-center justify-center shrink-0 font-bold">{user.full_name.slice(0, 1).toUpperCase()}</div>
                <div className="flex-1 min-w-0"><p className="text-sm font-medium truncate">{user.full_name}</p><p className="text-xs text-muted-foreground truncate">{user.email} · joined {new Date(user.created_at).toLocaleDateString()}</p></div>
                <Badge variant={user.role === 'admin' ? 'purple' : 'info'}>{user.role}</Badge>
                <Button variant={user.is_active ? 'outline' : 'default'} size="sm" loading={toggleUser.isPending} onClick={() => toggleUser.mutate(user.id)}>{user.is_active ? 'Deactivate' : 'Activate'}</Button>
              </motion.div>
            ))}
          </div>
          {toggleUser.isError && <p className="text-xs text-rose-400 mt-3">{(toggleUser.error as any)?.response?.data?.detail ?? 'The account status could not be changed.'}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="py-4 text-sm text-muted-foreground">
          This release does not fabricate operational logs. Structured backend logs are emitted to the server process; a durable log store can be connected for production observability.
        </CardContent>
      </Card>
    </div>
  );
}
