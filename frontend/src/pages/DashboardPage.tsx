import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Route, Zap, Target, Clock, Fuel, Leaf, Timer, Activity } from 'lucide-react';
import { StatCard } from '@/components/ui/Card';
import { routeService } from '@/services/route.service';
import { useAuth } from '@/hooks/useAuth';
import { formatNumber, formatTime } from '@/lib/utils';
import { RecentOptimizations } from '@/components/charts/RecentOptimizations';
import { PerformanceChart } from '@/components/charts/PerformanceChart';
import { QuantumVsClassical } from '@/components/charts/QuantumVsClassical';
import { TrafficHeatmap } from '@/components/charts/TrafficHeatmap';

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: stats, isLoading, isError } = useQuery({ queryKey: ['stats'], queryFn: routeService.getDashboardStats, refetchInterval: 30000 });
  const { data: history } = useQuery({ queryKey: ['history'], queryFn: () => routeService.getHistory(8) });
  const { data: analytics } = useQuery({ queryKey: ['analytics'], queryFn: () => routeService.getAnalytics(30) });

  const statCards = [
    { title: 'Stored route runs', value: stats ? formatNumber(stats.total_routes) : '—', icon: <Route className="w-5 h-5" />, color: 'blue', change: 'Measured records' },
    { title: 'Scenario congestion', value: stats ? `${stats.avg_traffic.toFixed(0)}%` : '—', icon: <Activity className="w-5 h-5" />, color: 'amber', change: 'Synthetic model' },
    { title: 'Feasible runs', value: stats ? `${stats.success_rate.toFixed(1)}%` : '—', icon: <Target className="w-5 h-5" />, color: 'emerald', change: 'Route found' },
    { title: 'QAOA agreement', value: stats ? `${stats.quantum_accuracy.toFixed(1)}%` : '—', icon: <Zap className="w-5 h-5" />, color: 'purple', change: 'With exact selector' },
    { title: 'Avg scenario saving', value: stats ? formatTime(stats.avg_time_saved) : '—', icon: <Clock className="w-5 h-5" />, color: 'cyan', change: 'Against slowest result' },
    { title: 'Estimated fuel cost saved', value: stats ? `₹${formatNumber(stats.fuel_saved)}` : '—', icon: <Fuel className="w-5 h-5" />, color: 'emerald', change: 'Across stored runs' },
    { title: 'Estimated CO₂ avoided', value: stats ? `${formatNumber(stats.carbon_reduction)} kg` : '—', icon: <Leaf className="w-5 h-5" />, color: 'emerald', change: 'Fuel-derived estimate' },
    { title: 'Avg QAOA runtime', value: stats ? `${stats.avg_execution_time.toFixed(0)}ms` : '—', icon: <Timer className="w-5 h-5" />, color: 'blue', change: 'Aer simulation' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Operations overview
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Welcome back, {user?.full_name?.split(' ')[0]}. Every value below comes from a stored execution.
            </p>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${isError ? 'bg-rose-500/10 border-rose-500/20' : 'bg-emerald-500/10 border-emerald-500/20'}`}>
            <div className={`w-2 h-2 rounded-full ${isError ? 'bg-rose-400' : 'bg-emerald-400'}`} />
            <span className={`text-xs font-medium ${isError ? 'text-rose-400' : 'text-emerald-400'}`}>{isError ? 'API unavailable' : 'API connected'}</span>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <motion.div key={card.title} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <StatCard {...card} loading={isLoading} />
          </motion.div>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PerformanceChart data={analytics?.daily_stats || []} />
        </div>
        <div>
          <QuantumVsClassical data={analytics?.algorithm_comparison || []} />
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentOptimizations data={history || []} />
        </div>
        <div>
          <TrafficHeatmap data={analytics?.traffic_by_hour || []} />
        </div>
      </div>
    </div>
  );
}
