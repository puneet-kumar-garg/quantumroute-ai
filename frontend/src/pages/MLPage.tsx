import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Brain, Database, FlaskConical, ShieldCheck, TriangleAlert } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge, Spinner } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { routeService } from '@/services/route.service';

const modelLabels: Record<string, string> = {
  linear_regression: 'Linear regression',
  random_forest: 'Random forest',
  gradient_boosting: 'Gradient boosting',
};

export default function MLPage() {
  const query = useQuery({ queryKey: ['traffic-model'], queryFn: routeService.getTrafficModel });
  const report = query.data;
  const chartData = report?.metrics.map((metric) => ({
    model: modelLabels[metric.name] ?? metric.name,
    MAE: metric.mae,
    RMSE: metric.rmse,
  })) ?? [];

  return (
    <div className="space-y-6">
      <motion.header initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-mono uppercase tracking-[0.18em] text-cyan-500">Model registry</p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight">Traffic scenario model</h1>
            <p className="mt-1 text-sm text-muted-foreground">Evaluation evidence for the synthetic Chandigarh scenario dataset.</p>
          </div>
          {report && <Badge variant="warning">Synthetic data</Badge>}
        </div>
      </motion.header>

      {query.isLoading && <div className="min-h-64 grid place-items-center" role="status"><Spinner size="lg" /></div>}
      {query.isError && (
        <Card><CardContent className="min-h-56 grid place-items-center text-center gap-3">
          <div><TriangleAlert className="mx-auto mb-3 h-7 w-7 text-rose-500" /><h2 className="font-semibold">Model report unavailable</h2><p className="mt-1 text-sm text-muted-foreground">The backend could not load the evaluated model metadata.</p></div>
          <Button variant="outline" onClick={() => query.refetch()}>Retry</Button>
        </CardContent></Card>
      )}

      {report && <>
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="p-5"><Brain className="h-5 w-5 text-purple-400" /><p className="mt-4 text-xs text-muted-foreground">Selected by lowest holdout RMSE</p><p className="mt-1 text-lg font-semibold">{modelLabels[report.selected_model] ?? report.selected_model}</p></Card>
          <Card className="p-5"><Database className="h-5 w-5 text-blue-400" /><p className="mt-4 text-xs text-muted-foreground">Chronological split</p><p className="mt-1 text-lg font-semibold">{report.training_rows.toLocaleString()} train · {report.test_rows.toLocaleString()} test</p></Card>
          <Card className="p-5"><ShieldCheck className="h-5 w-5 text-emerald-400" /><p className="mt-4 text-xs text-muted-foreground">Dataset fingerprint</p><p className="mt-1 truncate font-mono text-sm" title={report.dataset_fingerprint}>{report.dataset_fingerprint.slice(0, 18)}…</p></Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <Card>
            <CardHeader><CardTitle>Holdout error by model</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} margin={{ left: 4, right: 12 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="model" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 10 }} />
                  <Bar dataKey="MAE" fill="#2F7CF6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="RMSE" fill="#9B7BFF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b text-left text-muted-foreground"><th className="py-2">Model</th><th>MAE</th><th>RMSE</th><th>R²</th></tr></thead>
                  <tbody>{report.metrics.map((metric) => <tr key={metric.name} className="border-b border-border/60"><td className="py-3 font-medium">{modelLabels[metric.name] ?? metric.name}</td><td className="font-mono">{metric.mae.toFixed(2)}</td><td className="font-mono">{metric.rmse.toFixed(2)}</td><td className="font-mono">{metric.r2.toFixed(3)}</td></tr>)}</tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><div className="flex items-center gap-2"><FlaskConical className="h-4 w-4 text-amber-500" /><CardTitle>Evidence boundary</CardTitle></div></CardHeader>
            <CardContent className="space-y-4 text-sm">
              <p className="rounded-xl border border-amber-500/25 bg-amber-500/8 p-4 leading-6 text-muted-foreground">{report.limitation}</p>
              <div><p className="font-medium">Inputs</p><p className="mt-1 text-muted-foreground">Hour, day, weather, vehicle density, road category, and surface condition.</p></div>
              <div><p className="font-medium">Validation</p><p className="mt-1 text-muted-foreground">A chronological 80/20 split prevents future scenario rows from leaking into training.</p></div>
              <div><p className="font-medium">Production status</p><p className="mt-1 text-muted-foreground">Real-world Chandigarh accuracy remains unavailable until a timestamped, road-linked dataset is supplied.</p></div>
            </CardContent>
          </Card>
        </div>
      </>}
    </div>
  );
}
