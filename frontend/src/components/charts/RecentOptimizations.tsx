import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Clock, MapPin } from 'lucide-react';
import type { RecentOptimization } from '@/types';
import { formatTime, formatDistance } from '@/lib/utils';

interface Props { data: RecentOptimization[] }

export function RecentOptimizations({ data }: Props) {
  const items = data;

  return (
    <Card glass>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <CardTitle>Recent Optimizations</CardTitle>
          </div>
          <Badge variant="info">{items.length} routes</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? <div className="min-h-40 grid place-items-center text-sm text-muted-foreground">No route history yet.</div> : <div className="space-y-2">
          {items.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-3 p-3 rounded-lg bg-background/50 hover:bg-accent/50 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center shrink-0">
                <MapPin className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{item.source} → {item.destination}</p>
                <p className="text-xs text-muted-foreground">{formatDistance(item.distance)} · {formatTime(item.time)}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant="info">{item.algorithm}</Badge>
                <span className="text-xs font-mono text-muted-foreground">obj {item.objective_value.toFixed(4)}</span>
              </div>
            </motion.div>
          ))}
        </div>}
      </CardContent>
    </Card>
  );
}
