import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { GitCompare } from 'lucide-react';
import type { OptimizationResult } from '@/types';
import { formatDistance, formatTime } from '@/lib/utils';

interface Props { result: OptimizationResult }

export function ComparisonTable({ result }: Props) {
  const algorithms = [
    { name: 'QAOA', data: result.quantum, badge: 'purple' as const, objective: result.quantum.quantum_cost, memory: null, status: result.quantum.status },
    { name: 'Dijkstra', data: result.dijkstra, badge: 'info' as const, objective: result.dijkstra.objective_value, memory: result.dijkstra.memory_usage_kb, status: result.dijkstra.feasible ? 'completed' : 'infeasible' },
    { name: 'A*', data: result.astar, badge: 'info' as const, objective: result.astar.objective_value, memory: result.astar.memory_usage_kb, status: result.astar.feasible ? 'completed' : 'infeasible' },
    { name: 'Bellman-Ford', data: result.bellman_ford, badge: 'warning' as const, objective: result.bellman_ford.objective_value, memory: result.bellman_ford.memory_usage_kb, status: result.bellman_ford.feasible ? 'completed' : 'infeasible' },
  ];

  const latencyData = algorithms.map(item => ({ algorithm: item.name, latency: item.data.execution_time_ms }));

  return (
    <Card glass>
      <CardHeader>
        <div className="flex items-center gap-2">
          <GitCompare className="w-4 h-4 text-blue-400" />
          <CardTitle>Algorithm Comparison</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {/* Table */}
        <div className="overflow-x-auto mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 px-3 text-muted-foreground font-medium">Algorithm</th>
                <th className="text-right py-2 px-3 text-muted-foreground font-medium">Distance</th>
                <th className="text-right py-2 px-3 text-muted-foreground font-medium">Time</th>
                <th className="text-right py-2 px-3 text-muted-foreground font-medium">Cost</th>
                <th className="text-right py-2 px-3 text-muted-foreground font-medium">Congestion</th>
                <th className="text-right py-2 px-3 text-muted-foreground font-medium">Objective</th>
                <th className="text-right py-2 px-3 text-muted-foreground font-medium">Exec Time</th>
                <th className="text-right py-2 px-3 text-muted-foreground font-medium">Memory</th>
                <th className="text-right py-2 px-3 text-muted-foreground font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {algorithms.map((algo, i) => (
                <motion.tr
                  key={algo.name}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="border-b border-border/50 hover:bg-accent/30 transition-colors"
                >
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <Badge variant={algo.badge}>{algo.name}</Badge>
                    </div>
                  </td>
                  <td className="text-right py-3 px-3 font-mono">{formatDistance(algo.data.distance)}</td>
                  <td className="text-right py-3 px-3 font-mono">{formatTime(algo.data.time)}</td>
                  <td className="text-right py-3 px-3 font-mono">₹{algo.data.cost.toFixed(2)}</td>
                  <td className="text-right py-3 px-3 font-mono">{algo.data.congestion_exposure.toFixed(2)}</td>
                  <td className="text-right py-3 px-3 font-mono">{algo.objective == null ? '—' : algo.objective.toFixed(4)}</td>
                  <td className="text-right py-3 px-3 font-mono">{algo.data.execution_time_ms.toFixed(1)}ms</td>
                  <td className="text-right py-3 px-3 font-mono">{algo.memory == null ? '—' : `${algo.memory.toFixed(0)}KB`}</td>
                  <td className="text-right py-3 px-3"><Badge variant={algo.status === 'completed' || algo.status === 'not_required' ? 'success' : 'warning'}>{algo.status.replace('_', ' ')}</Badge></td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Chart */}
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={latencyData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="algorithm" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: '#18181b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }} />
            <Bar dataKey="latency" name="Measured execution time (ms)" fill="#3b82f6" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>

        <p className="text-xs text-muted-foreground mt-3 text-center">
          All algorithms use the same graph and normalized objective. QAOA is measured on Qiskit Aer;
          no quantum-hardware or speedup claim is made.
        </p>
      </CardContent>
    </Card>
  );
}
