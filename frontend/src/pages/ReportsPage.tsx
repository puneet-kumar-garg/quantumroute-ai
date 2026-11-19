import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { FileText, TriangleAlert } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { routeService } from '@/services/route.service';
import { formatDistance, formatTime } from '@/lib/utils';

interface ReportItem {
  id: number;
  source: string;
  destination: string;
  algorithm: string;
  distance: number;
  time: number;
  objective_value: number;
  created_at: string;
}

export default function ReportsPage() {
  const { data: history, isLoading, isError, refetch } = useQuery({ queryKey: ['history', 20], queryFn: () => routeService.getHistory(20) });
  const [exporting, setExporting] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = async (id: number, format: 'pdf' | 'csv' | 'excel') => {
    setExporting(`${id}-${format}`);
    setExportError(null);
    try {
      const blob = await routeService.exportReport(id, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `route-report-${id}.${format === 'excel' ? 'xlsx' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setExportError('The report could not be generated. Retry after checking the backend connection.');
    } finally {
      setExporting(null);
    }
  };

  const items: ReportItem[] = (history ?? []) as ReportItem[];
  const avgObjective = items.length ? items.reduce((sum: number, item: ReportItem) => sum + item.objective_value, 0) / items.length : 0;

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Reports</h1>
            <p className="text-sm text-muted-foreground mt-0.5">Export optimization reports in multiple formats</p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Reports', value: items.length, color: 'text-blue-400' },
          { label: 'Feasible Runs', value: items.filter(item => item.distance > 0).length, color: 'text-purple-400' },
          { label: 'Mean Objective', value: avgObjective.toFixed(4), color: 'text-emerald-400' },
          { label: 'Export Formats', value: 'PDF · CSV · XLSX', color: 'text-cyan-400' },
        ].map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Card glass className="p-4 text-center">
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
            </Card>
          </motion.div>
        ))}
      </div>

      {exportError && <div role="alert" className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-500">{exportError}</div>}

      {isError && <Card><CardContent className="min-h-52 grid place-items-center text-center"><div><TriangleAlert className="mx-auto mb-2 text-rose-500"/><p className="font-medium">Report history unavailable</p><Button className="mt-3" variant="outline" onClick={() => refetch()}>Retry</Button></div></CardContent></Card>}

      {!isLoading && !isError && items.length === 0 && <Card><CardContent className="min-h-52 grid place-items-center text-center"><div><FileText className="mx-auto mb-2 text-muted-foreground"/><p className="font-medium">No reports yet</p><p className="mt-1 text-sm text-muted-foreground">Complete an optimization to create an exportable record.</p></div></CardContent></Card>}

      {items.length > 0 && <Card glass>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" />
            <CardTitle>Optimization Reports</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {['#', 'Route', 'Algorithm', 'Distance', 'Time', 'Objective', 'Date', 'Export'].map((h) => (
                    <th key={h} className="text-left py-2 px-3 text-muted-foreground font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((item: ReportItem, i: number) => (
                  <motion.tr
                    key={item.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    className="border-b border-border/50 hover:bg-accent/30 transition-colors"
                  >
                    <td className="py-3 px-3 text-muted-foreground">{item.id}</td>
                    <td className="py-3 px-3 font-medium">{item.source} → {item.destination}</td>
                    <td className="py-3 px-3"><Badge variant="info">{item.algorithm}</Badge></td>
                    <td className="py-3 px-3 font-mono">{formatDistance(item.distance)}</td>
                    <td className="py-3 px-3 font-mono">{formatTime(item.time)}</td>
                    <td className="py-3 px-3 font-mono">{item.objective_value.toFixed(6)}</td>
                    <td className="py-3 px-3 text-muted-foreground text-xs">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex gap-1">
                        {(['pdf', 'csv', 'excel'] as const).map((fmt) => (
                          <button
                            key={fmt}
                            onClick={() => handleExport(item.id, fmt)}
                            disabled={exporting === `${item.id}-${fmt}`}
                            className="cursor-pointer px-2 py-1 rounded text-xs bg-secondary hover:bg-accent transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {fmt.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>}
    </div>
  );
}
