import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Cpu } from 'lucide-react';

interface Props { data: any[] }

export function QuantumVsClassical({ data }: Props) {
  const measured = data.filter(item => Number(item.runs) > 0);
  return (
    <Card glass>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-purple-400" />
          <CardTitle>Average runtime</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {measured.length === 0 ? <div className="h-[220px] grid place-items-center text-sm text-muted-foreground">No measured executions yet.</div> : <ResponsiveContainer width="100%" height={220}>
          <BarChart data={measured} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="algorithm" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#18181b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
            />
            <Bar dataKey="avg_execution_ms" fill="#2F7CF6" radius={[4, 4, 0, 0]} name="Runtime (ms)" />
          </BarChart>
        </ResponsiveContainer>}
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Solver execution only; QAOA includes Aer sampling and COBYLA optimization.
        </p>
      </CardContent>
    </Card>
  );
}
