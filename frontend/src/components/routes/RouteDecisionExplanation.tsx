import { AlertTriangle, CheckCircle2, GitCompareArrows, Info, Route, Search } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import type { OptimizationResult } from '@/types';
import type { RouteChangeExplanation } from '@/lib/routeChange';

interface Props {
  result: OptimizationResult;
  routeChange: RouteChangeExplanation | null;
}

const IMPACT_LABELS: Record<string, string> = {
  free_flow_time_min: 'Free-flow driving',
  traffic_delay_min: 'Traffic delay',
  weather_delay_min: 'Weather delay',
  surface_delay_min: 'Road surface delay',
  intersection_delay_min: 'Intersections & signals',
  construction_delay_min: 'Construction delay',
};

const fmt = (value: number, digits = 1) => Number(value ?? 0).toFixed(digits);

export function RouteDecisionExplanation({ result, routeChange }: Props) {
  const explanation = result.recommendation.explanation;
  const characteristics = explanation.route_characteristics;
  const previous = explanation.previous_route_comparison;
  const search = explanation.search_scope;

  return (
    <Card className="border-emerald-500/30 bg-emerald-500/5">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Route className="h-4 w-4 text-emerald-400" />
            <CardTitle>Route Decision Explanation</CardTitle>
          </div>
          <Badge variant="success">Verified recommendation</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {routeChange && (
          <section className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-4" aria-live="polite">
            <div className="flex flex-wrap items-center gap-2">
              <GitCompareArrows className="h-4 w-4 text-cyan-300" />
              <p className="text-sm font-semibold text-cyan-300">{routeChange.title}</p>
              {routeChange.changedInputs.map(input => <Badge key={input} variant="info">{input}</Badge>)}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">New path: <span className="text-foreground">{routeChange.newPath}</span></p>
          </section>
        )}

        <section>
          <p className="text-base font-semibold">{explanation.headline}</p>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{explanation.summary}</p>
          <p className="mt-2 text-xs text-foreground/80">{explanation.path.join(' → ')}</p>
        </section>

        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Recommended route metrics">
          {[
            ['Distance', `${fmt(result.recommendation.distance)} km`],
            ['Expected time', `${fmt(result.recommendation.time)} min`],
            ['Fuel / travel cost', `${fmt(result.recommendation.fuel_l, 2)} L · ₹${fmt(result.recommendation.cost)}`],
            ['Weighted objective', fmt(result.recommendation.objective_value, 4)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-border bg-background/70 p-3">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="mt-1 text-sm font-semibold">{value}</p>
            </div>
          ))}
        </section>

        <section>
          <h3 className="text-sm font-semibold">What influenced the decision</h3>
          <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {explanation.factors.map(factor => (
              <div key={factor.label} className="rounded-lg border border-border bg-background/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-muted-foreground">{factor.label}</span>
                  <span className="text-xs font-semibold">{factor.value}</span>
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{factor.effect}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-border bg-background/50 p-4">
            <h3 className="text-sm font-semibold">Road characteristics & accessibility</h3>
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
              <div><dt className="text-muted-foreground">Width range</dt><dd className="mt-1 font-medium">{fmt(characteristics.minimum_width_m)}–{fmt(characteristics.maximum_width_m)} m</dd></div>
              <div><dt className="text-muted-foreground">Speed limits</dt><dd className="mt-1 font-medium">{characteristics.speed_limits_kmh.join(', ')} km/h</dd></div>
              <div><dt className="text-muted-foreground">Road classes</dt><dd className="mt-1 font-medium capitalize">{characteristics.road_types.join(', ')}</dd></div>
              <div><dt className="text-muted-foreground">Vehicle access</dt><dd className="mt-1 flex items-center gap-1 font-medium">{characteristics.all_segments_accessible ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />}{characteristics.all_segments_accessible ? 'All segments valid' : 'Restriction detected'}</dd></div>
            </dl>
            {characteristics.construction_segments.length > 0 && <p className="mt-3 text-xs text-amber-400">Construction: {characteristics.construction_segments.join(', ')}</p>}
          </div>

          <div className="rounded-xl border border-border bg-background/50 p-4">
            <h3 className="text-sm font-semibold">Expected-time impact</h3>
            <div className="mt-3 space-y-2">
              {Object.entries(explanation.impact_breakdown).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-muted-foreground">{IMPACT_LABELS[key] ?? key}</span>
                  <span className="font-mono font-medium">{fmt(value, 2)} min</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-semibold">Road-by-road evidence</h3>
          <div className="mt-3 overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-[940px] text-left text-xs">
              <thead className="bg-muted/60 text-muted-foreground">
                <tr><th className="px-3 py-2">Segment</th><th className="px-3 py-2">Class</th><th className="px-3 py-2">Width</th><th className="px-3 py-2">Limit</th><th className="px-3 py-2">Distance</th><th className="px-3 py-2">Expected</th><th className="px-3 py-2">Traffic</th><th className="px-3 py-2">Weather</th><th className="px-3 py-2">Surface / works</th></tr>
              </thead>
              <tbody className="divide-y divide-border">
                {characteristics.segments.map(segment => (
                  <tr key={segment.segment_id} className="bg-background/40">
                    <td className="px-3 py-2 font-medium">{segment.segment}</td>
                    <td className="px-3 py-2 capitalize">{segment.road_type}</td>
                    <td className="px-3 py-2">{fmt(segment.road_width_m)} m</td>
                    <td className="px-3 py-2">{fmt(segment.speed_limit_kmh, 0)} km/h</td>
                    <td className="px-3 py-2">{fmt(segment.distance_km)} km</td>
                    <td className="px-3 py-2 font-medium">{fmt(segment.expected_time_min, 2)} min</td>
                    <td className="px-3 py-2">+{fmt(segment.traffic_delay_min, 2)}</td>
                    <td className="px-3 py-2">+{fmt(segment.weather_delay_min, 2)}</td>
                    <td className="px-3 py-2">+{fmt(segment.surface_delay_min + segment.construction_delay_min, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h3 className="text-sm font-semibold">Compared with feasible alternatives</h3>
          <div className="mt-3 overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-[900px] text-left text-xs">
              <thead className="bg-muted/60 text-muted-foreground"><tr><th className="px-3 py-2">Rank</th><th className="px-3 py-2">Route</th><th className="px-3 py-2">Distance</th><th className="px-3 py-2">Time</th><th className="px-3 py-2">Fuel cost</th><th className="px-3 py-2">Objective</th><th className="px-3 py-2">Decision</th></tr></thead>
              <tbody className="divide-y divide-border">
                {explanation.alternatives.map(alternative => (
                  <tr key={`${alternative.rank}-${alternative.path.join('-')}`} className={alternative.selected ? 'bg-emerald-500/10' : 'bg-background/40'}>
                    <td className="px-3 py-3">#{alternative.rank}</td>
                    <td className="px-3 py-3 font-medium">{alternative.path.join(' → ')}</td>
                    <td className="px-3 py-3">{fmt(alternative.distance_km)} km</td>
                    <td className="px-3 py-3">{fmt(alternative.time_min)} min</td>
                    <td className="px-3 py-3">₹{fmt(alternative.fuel_cost_inr)}</td>
                    <td className="px-3 py-3 font-mono">{fmt(alternative.objective_value, 4)}</td>
                    <td className="px-3 py-3 text-muted-foreground">{alternative.why_not_selected.join(' ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-border bg-background/50 p-4">
            <div className="flex items-center gap-2"><GitCompareArrows className="h-4 w-4 text-cyan-400" /><h3 className="text-sm font-semibold">Previous route comparison</h3></div>
            {previous.status === 'not_available' ? (
              <p className="mt-3 text-xs text-muted-foreground">Generate or change a scenario to compare it with the previous recommendation.</p>
            ) : (
              <div className="mt-3 space-y-2 text-xs">
                <Badge variant={previous.status === 'changed' ? 'info' : 'success'}>{previous.status === 'changed' ? 'Route changed' : 'Route unchanged'}</Badge>
                <p className="text-muted-foreground">Previous: {previous.previous_path.join(' → ')}</p>
                {previous.reasons.map(reason => <p key={reason} className="flex gap-2 text-muted-foreground"><span aria-hidden>•</span><span>{reason}</span></p>)}
              </div>
            )}
          </div>

          <div className="rounded-xl border border-border bg-background/50 p-4">
            <div className="flex items-center gap-2"><Search className="h-4 w-4 text-blue-400" /><h3 className="text-sm font-semibold">Search coverage & constraints</h3></div>
            <div className="mt-3 space-y-2 text-xs text-muted-foreground">
              <p>Optimal route: {search.optimal_route_guarantee?.split('_').join(' ')}</p>
              <p>{search.alternative_search}</p>
              <p>{search.alternatives_evaluated ?? 0} loopless alternatives evaluated (limit {search.alternative_limit ?? 0}) across {search.graph_nodes ?? 0} nodes / {search.graph_edges ?? 0} directed edges.</p>
              <p className="flex gap-2"><Info className="mt-0.5 h-3.5 w-3.5 shrink-0" /><span>{search.note}</span></p>
              <p>{explanation.constraints.closed_segments.length} closure(s); {explanation.constraints.excluded_segments.length} constrained or removed road segment record(s).</p>
            </div>
          </div>
        </section>

        <p className="text-xs text-muted-foreground">Network {result.network_version} · Geometry {result.recommendation.geometry_source.toUpperCase()}</p>
      </CardContent>
    </Card>
  );
}
