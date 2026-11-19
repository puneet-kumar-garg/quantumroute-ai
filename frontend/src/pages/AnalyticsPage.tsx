import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Activity, BarChart3, Clock3, TriangleAlert } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Badge';
import { routeService } from '@/services/route.service';

interface AnalyticsData {
  daily_stats: Array<Record<string, string | number>>;
  algorithm_comparison: Array<{ algorithm: string; runs: number; avg_execution_ms: number; avg_objective: number }>;
  traffic_by_hour: Array<{ hour: string; traffic: number }>;
  provenance: string;
}

export default function AnalyticsPage() {
  const query = useQuery<AnalyticsData>({ queryKey: ['analytics', 30], queryFn: () => routeService.getAnalytics(30) });
  const data = query.data;
  const hasRuns = Boolean(data?.daily_stats.length);

  return <div className="space-y-6">
    <motion.header initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
      <p className="text-xs font-mono uppercase tracking-[0.18em] text-blue-500">Measured executions</p>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight">Performance analytics</h1>
      <p className="mt-1 text-sm text-muted-foreground">Only persisted algorithm runs appear here.</p>
    </motion.header>

    {query.isLoading && <div className="min-h-64 grid place-items-center" role="status"><Spinner size="lg" /></div>}
    {query.isError && <Card><CardContent className="min-h-56 grid place-items-center text-center"><div><TriangleAlert className="mx-auto mb-3 text-rose-500"/><h2 className="font-semibold">Analytics unavailable</h2><p className="mt-1 text-sm text-muted-foreground">Stored executions could not be loaded.</p><Button className="mt-4" variant="outline" onClick={() => query.refetch()}>Retry</Button></div></CardContent></Card>}

    {data && !hasRuns && <Card><CardContent className="min-h-64 grid place-items-center text-center"><div><BarChart3 className="mx-auto mb-3 h-8 w-8 text-muted-foreground"/><h2 className="font-semibold">No measured runs yet</h2><p className="mt-1 max-w-md text-sm text-muted-foreground">Complete a route optimization to populate latency, objective, and traffic charts.</p></div></CardContent></Card>}

    {data && hasRuns && <>
      <div className="grid gap-6 xl:grid-cols-2">
        <Card><CardHeader><div className="flex items-center gap-2"><Activity className="h-4 w-4 text-blue-500"/><CardTitle>Daily execution latency</CardTitle></div></CardHeader><CardContent><ResponsiveContainer width="100%" height={280}><LineChart data={data.daily_stats}><CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))"/><XAxis dataKey="date" tick={{fontSize:10}}/><YAxis tick={{fontSize:10}} unit=" ms"/><Tooltip contentStyle={{background:'hsl(var(--card))',border:'1px solid hsl(var(--border))',borderRadius:10}}/><Line dataKey="quantum" stroke="#9B7BFF" name="QAOA" strokeWidth={2}/><Line dataKey="dijkstra" stroke="#2F7CF6" name="Dijkstra"/><Line dataKey="astar" stroke="#37C9D8" name="A*"/><Line dataKey="bellman_ford" stroke="#F5B642" name="Bellman-Ford"/></LineChart></ResponsiveContainer></CardContent></Card>
        <Card><CardHeader><div className="flex items-center gap-2"><Clock3 className="h-4 w-4 text-purple-400"/><CardTitle>Average runtime by algorithm</CardTitle></div></CardHeader><CardContent><ResponsiveContainer width="100%" height={280}><BarChart data={data.algorithm_comparison}><CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))"/><XAxis dataKey="algorithm" tick={{fontSize:10}}/><YAxis tick={{fontSize:10}} unit=" ms"/><Tooltip contentStyle={{background:'hsl(var(--card))',border:'1px solid hsl(var(--border))',borderRadius:10}}/><Bar dataKey="avg_execution_ms" fill="#2F7CF6" radius={[5,5,0,0]} name="Average runtime"/></BarChart></ResponsiveContainer></CardContent></Card>
      </div>
      <Card><CardHeader><CardTitle>Measured summary</CardTitle></CardHeader><CardContent><div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-left text-muted-foreground"><th className="py-2">Algorithm</th><th>Runs</th><th>Average runtime</th><th>Average objective</th></tr></thead><tbody>{data.algorithm_comparison.map(row=><tr key={row.algorithm} className="border-b border-border/60"><td className="py-3 font-medium capitalize">{row.algorithm.replace('_',' ')}</td><td>{row.runs}</td><td className="font-mono">{row.avg_execution_ms.toFixed(3)} ms</td><td className="font-mono">{row.avg_objective.toFixed(6)}</td></tr>)}</tbody></table></div></CardContent></Card>
    </>}
  </div>;
}
