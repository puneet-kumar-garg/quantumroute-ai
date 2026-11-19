import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Zap, Route, Car, Bike, Truck, AlertTriangle, RotateCcw, MapPin, Clock, Layers, Gauge, SlidersHorizontal } from 'lucide-react';
import { routeService } from '@/services/route.service';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { RouteMap } from '@/components/map/RouteMap';
import { ComparisonTable } from '@/components/quantum/ComparisonTable';
import { QuantumPanel } from '@/components/quantum/QuantumPanel';
import type { OptimizationResult, RouteOptimizationRequest } from '@/types';
import { cn } from '@/lib/utils';
import { loadPreferences } from '@/lib/preferences';
import { describeRouteChange, type RouteChangeExplanation } from '@/lib/routeChange';
import { selectAvailableLocation } from '@/lib/locationSelection';
import { buildRouteRequest } from '@/lib/routeRequest';
import { RouteDecisionExplanation } from '@/components/routes/RouteDecisionExplanation';

const schema = z.object({
  source: z.string().min(1),
  destination: z.string().min(1),
  vehicle_type: z.enum(['car', 'bike', 'truck', 'emergency']),
  traffic_density: z.enum(['low', 'medium', 'high']),
  weather: z.enum(['sunny', 'rain', 'fog']),
  road_condition: z.enum(['good', 'moderate', 'poor']),
  optimization_priority: z.enum(['fastest', 'shortest', 'least_fuel', 'least_traffic', 'balanced']),
  time_of_day: z.string(),
  qaoa_layers: z.number().min(1).max(5),
  qaoa_shots: z.number().min(128).max(4096),
  traffic_overlay: z.boolean(),
  animate_vehicle: z.boolean(),
  disruption_type: z.enum(['none', 'closure', 'construction']),
  disruption_segment: z.string(),
}).superRefine((values, context) => {
  if (values.disruption_type !== 'none' && !values.disruption_segment) {
    context.addIssue({
      code: 'custom',
      path: ['disruption_segment'],
      message: 'Select the road segment affected by this disruption.',
    });
  }
});
type FormData = z.infer<typeof schema>;

const VEHICLE_OPTIONS = [
  { value: 'car', label: 'Car', icon: Car },
  { value: 'bike', label: 'Bike', icon: Bike },
  { value: 'truck', label: 'Truck', icon: Truck },
  { value: 'emergency', label: 'Emergency', icon: AlertTriangle },
] as const;

export default function OptimizePage() {
  const [preferences] = useState(loadPreferences);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [vehicleSpeed, setVehicleSpeed] = useState(1);
  const [submittedValues, setSubmittedValues] = useState<RouteOptimizationRequest | null>(null);
  const [useCustomWeights, setUseCustomWeights] = useState(false);
  const [weights, setWeights] = useState({ distance: 30, time: 30, fuel: 15, congestion: 15, risk: 10 });
  const [submittedWeights, setSubmittedWeights] = useState<typeof weights | null>(null);
  const [routeChange, setRouteChange] = useState<RouteChangeExplanation | null>(null);
  const previousResultRef = useRef<OptimizationResult | null>(null);
  const locationsQuery = useQuery({ queryKey: ['route-locations'], queryFn: routeService.getLocations });
  const segmentsQuery = useQuery({ queryKey: ['road-segments'], queryFn: routeService.getSegments });
  const locations = useMemo(() => locationsQuery.data ?? [], [locationsQuery.data]);
  const segments = useMemo(() => segmentsQuery.data ?? [], [segmentsQuery.data]);

  const { register, handleSubmit, watch, reset, setValue, getValues, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      source: 'Rock Garden',
      destination: 'Elante Mall',
      vehicle_type: 'car',
      traffic_density: 'high',
      weather: 'rain',
      road_condition: 'moderate',
      optimization_priority: 'shortest',
      time_of_day: '09:00',
      qaoa_layers: 2,
      qaoa_shots: 1024,
      traffic_overlay: preferences.showTrafficOverlay,
      animate_vehicle: preferences.animateRoutes,
      disruption_type: 'none',
      disruption_segment: '',
    },
  });

  const mutation = useMutation({
    mutationFn: (data: RouteOptimizationRequest) => routeService.optimize(data),
    onSuccess: (data, vars) => {
      const previous = previousResultRef.current;
      setRouteChange(previous ? describeRouteChange(
        previous.request,
        vars,
        previous.recommendation.path,
        data.recommendation.path,
      ) : null);
      previousResultRef.current = data;
      setResult(data);
      setSubmittedValues(vars);
      setSubmittedWeights(vars.weights ? { ...weights } : null);
    },
  });

  const requestFor = useCallback((data: FormData) => buildRouteRequest(
    data,
    useCustomWeights ? weights : undefined,
    previousResultRef.current?.recommendation.path,
    previousResultRef.current?.request,
  ), [useCustomWeights, weights]);
  const onSubmit = (data: FormData) => mutation.mutate(requestFor(data));
  const fv = watch();

  useEffect(() => {
    if (locations.length === 0) return;

    const source = selectAvailableLocation(fv.source, locations, fv.destination, 'Rock Garden');
    const destination = selectAvailableLocation(fv.destination, locations, source, 'Elante Mall');

    if (source !== fv.source) setValue('source', source);
    if (destination !== fv.destination) setValue('destination', destination);
  }, [locations, fv.source, fv.destination, setValue]);

  const isStale = result && submittedValues && (
    fv.vehicle_type !== submittedValues.vehicle_type ||
    fv.traffic_density !== submittedValues.traffic_density ||
    fv.weather !== submittedValues.weather ||
    fv.road_condition !== submittedValues.road_condition ||
    fv.source !== submittedValues.source ||
    fv.destination !== submittedValues.destination ||
    fv.optimization_priority !== submittedValues.optimization_priority ||
    fv.time_of_day !== submittedValues.time_of_day ||
    fv.qaoa_layers !== submittedValues.qaoa_layers ||
    fv.qaoa_shots !== submittedValues.qaoa_shots ||
    fv.disruption_type !== (submittedValues.closed_segments?.length ? 'closure' : submittedValues.construction_segments?.length ? 'construction' : 'none') ||
    (fv.disruption_type !== 'none' && ![...(submittedValues.closed_segments ?? []), ...(submittedValues.construction_segments ?? [])].includes(fv.disruption_segment)) ||
    useCustomWeights !== Boolean(submittedValues.weights) ||
    (useCustomWeights && JSON.stringify(weights) !== JSON.stringify(submittedWeights))
  );

  const scenarioIsStale = Boolean(result && submittedValues && (
    fv.vehicle_type !== submittedValues.vehicle_type ||
    fv.traffic_density !== submittedValues.traffic_density ||
    fv.weather !== submittedValues.weather ||
    fv.road_condition !== submittedValues.road_condition ||
    fv.source !== submittedValues.source ||
    fv.destination !== submittedValues.destination ||
    fv.optimization_priority !== submittedValues.optimization_priority ||
    fv.time_of_day !== submittedValues.time_of_day ||
    fv.disruption_type !== (submittedValues.closed_segments?.length ? 'closure' : submittedValues.construction_segments?.length ? 'construction' : 'none') ||
    (fv.disruption_type !== 'none' && ![...(submittedValues.closed_segments ?? []), ...(submittedValues.construction_segments ?? [])].includes(fv.disruption_segment))
  ));
  const scenarioSignature = [
    fv.source, fv.destination, fv.vehicle_type, fv.traffic_density,
    fv.weather, fv.road_condition, fv.optimization_priority, fv.time_of_day,
    fv.disruption_type, fv.disruption_segment,
  ].join('|');

  useEffect(() => {
    if (!scenarioIsStale || mutation.isPending) return;
    if (fv.disruption_type !== 'none' && !fv.disruption_segment) return;
    const timer = window.setTimeout(() => {
      const current = getValues();
      mutation.mutate(requestFor(current));
    }, 650);
    return () => window.clearTimeout(timer);
  }, [scenarioSignature, scenarioIsStale, mutation.isPending, mutation, getValues, requestFor, fv.disruption_type, fv.disruption_segment]);

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold">Route Optimization</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Quantum-assisted optimization with OSRM road-following geometry
        </p>
      </motion.div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* ── Form Panel ── */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
          <Card glass className="h-fit">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Route className="w-4 h-4 text-blue-400" />
                <CardTitle>Route Parameters</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <form noValidate onSubmit={handleSubmit(onSubmit)} className="space-y-4">

                {/* Source */}
                <div className="space-y-1.5">
                  <label className="text-sm font-medium flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-emerald-400" /> Source
                  </label>
                  <select
                    {...register('source')}
                    className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
                  >
                    {locations.filter(l => l !== fv.destination).map(l => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>

                {/* Destination */}
                <div className="space-y-1.5">
                  <label className="text-sm font-medium flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-rose-400" /> Destination
                  </label>
                  <select
                    {...register('destination')}
                    className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
                  >
                    {locations.filter(l => l !== fv.source).map(l => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
                {locationsQuery.isError && <p className="text-xs text-rose-400">Location catalogue could not be loaded.</p>}

                {/* Vehicle Type */}
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Vehicle Type</label>
                  <div className="grid grid-cols-2 gap-2">
                    {VEHICLE_OPTIONS.map(({ value, label, icon: Icon }) => (
                      <label
                        key={value}
                        className={cn(
                          'flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-all',
                          fv.vehicle_type === value
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-border hover:border-primary/50'
                        )}
                      >
                        <input {...register('vehicle_type')} type="radio" value={value} className="sr-only" />
                        <Icon className="w-4 h-4" />
                        <span className="text-xs font-medium">{label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Traffic + Weather */}
                <div className="grid grid-cols-2 gap-3">
                  <Select
                    {...register('traffic_density')}
                    label="Traffic Density"
                    options={[
                      { value: 'low', label: '🟢 Low' },
                      { value: 'medium', label: '🟡 Medium' },
                      { value: 'high', label: '🔴 High' },
                    ]}
                  />
                  <Select
                    {...register('weather')}
                    label="Weather"
                    options={[
                      { value: 'sunny', label: '☀️ Sunny' },
                      { value: 'rain', label: '🌧️ Rain' },
                      { value: 'fog', label: '🌫️ Fog' },
                    ]}
                  />
                </div>

                {/* Road Condition */}
                <Select
                  {...register('road_condition')}
                  label="Road Condition"
                  options={[
                    { value: 'good', label: '✅ Good' },
                    { value: 'moderate', label: '⚠️ Moderate' },
                    { value: 'poor', label: '❌ Poor' },
                  ]}
                />

                <div className="rounded-lg border border-border p-3 space-y-3">
                  <Select
                    {...register('disruption_type')}
                    label="Temporary Road Disruption"
                    options={[
                      { value: 'none', label: 'No disruption' },
                      { value: 'closure', label: 'Closed road' },
                      { value: 'construction', label: 'Road construction' },
                    ]}
                  />
                  {fv.disruption_type !== 'none' && (
                    <div className="space-y-1.5">
                      <label className="text-sm font-medium" htmlFor="disruption-segment">Affected road segment</label>
                      <select
                        id="disruption-segment"
                        {...register('disruption_segment')}
                        className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
                      >
                        <option value="">Select a segment</option>
                        {segments.map(segment => (
                          <option key={segment.id} value={segment.id}>
                            {segment.label} · {segment.road_type} · {segment.speed_limit_kmh} km/h
                          </option>
                        ))}
                      </select>
                      {errors.disruption_segment && <p className="text-xs text-rose-400">{errors.disruption_segment.message}</p>}
                      <p className="text-[11px] text-muted-foreground">
                        {fv.disruption_type === 'closure'
                          ? 'The segment is removed before every solver runs.'
                          : 'Measured construction delay and risk are added to this segment.'}
                      </p>
                    </div>
                  )}
                  {segmentsQuery.isError && <p className="text-xs text-rose-400">Road segment catalogue could not be loaded.</p>}
                </div>

                {/* Priority */}
                <Select
                  {...register('optimization_priority')}
                  label="Optimization Priority"
                  options={[
                    { value: 'fastest', label: '⏱ Fastest Route' },
                    { value: 'shortest', label: '📍 Shortest Route' },
                    { value: 'least_fuel', label: '⛽ Least Fuel' },
                    { value: 'least_traffic', label: '🚦 Least Traffic' },
                    { value: 'balanced', label: '⚖️ Balanced' },
                  ]}
                />

                <div className="rounded-lg border border-border p-3 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium flex items-center gap-1.5">
                      <SlidersHorizontal className="w-3.5 h-3.5 text-blue-400" /> Custom objective weights
                    </span>
                    <button
                      type="button"
                      aria-pressed={useCustomWeights}
                      onClick={() => setUseCustomWeights(value => !value)}
                      className={cn('w-10 h-5 rounded-full transition-colors relative', useCustomWeights ? 'bg-primary' : 'bg-secondary')}
                    >
                      <span className={cn('w-3.5 h-3.5 rounded-full bg-white absolute top-0.5 transition-transform shadow', useCustomWeights ? 'translate-x-5' : 'translate-x-0.5')} />
                    </button>
                  </div>
                  {useCustomWeights && (
                    <div className="space-y-2">
                      {(Object.keys(weights) as Array<keyof typeof weights>).map(key => (
                        <label key={key} className="grid grid-cols-[84px_1fr_36px] items-center gap-2 text-xs">
                          <span className="capitalize text-muted-foreground">{key}</span>
                          <input
                            type="range" min={0} max={100} step={5} value={weights[key]}
                            onChange={event => setWeights(current => ({ ...current, [key]: Number(event.target.value) }))}
                            className="w-full accent-blue-500"
                          />
                          <span className="text-right font-mono">{weights[key]}</span>
                        </label>
                      ))}
                      <p className="text-[11px] text-muted-foreground">Weights are normalized by the API; at least one must be non-zero.</p>
                    </div>
                  )}
                </div>

                {/* Time of Day */}
                <div className="space-y-1.5">
                  <label className="text-sm font-medium flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-cyan-400" /> Time of Day
                  </label>
                  <input
                    {...register('time_of_day')}
                    type="time"
                    className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring transition-colors"
                  />
                </div>

                {/* QAOA Layers */}
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-purple-400" /> QAOA Layers (p)
                    </span>
                    <Badge variant="purple">{fv.qaoa_layers}</Badge>
                  </label>
                  <input
                    type="range" min={1} max={5} step={1}
                    value={fv.qaoa_layers}
                    onChange={e => setValue('qaoa_layers', Number(e.target.value))}
                    className="w-full accent-purple-500"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>1 (fast)</span><span>3 (balanced)</span><span>5 (deep)</span>
                  </div>
                </div>

                <Select
                  {...register('qaoa_shots', { valueAsNumber: true })}
                  label="Aer measurement shots"
                  options={[
                    { value: '256', label: '256 (quick)' },
                    { value: '512', label: '512' },
                    { value: '1024', label: '1024 (default)' },
                    { value: '2048', label: '2048 (higher sampling)' },
                  ]}
                />

                {/* Toggles + Speed */}
                <div className="space-y-2 pt-1">
                  {[
                    { field: 'traffic_overlay' as const, label: 'Traffic Overlay', color: 'bg-amber-500' },
                    { field: 'animate_vehicle' as const, label: 'Animate Vehicle', color: 'bg-emerald-500' },
                  ].map(({ field, label, color }) => (
                    <div key={field} className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">{label}</span>
                      <button
                        type="button"
                        onClick={() => setValue(field, !fv[field])}
                        className={cn('w-10 h-5 rounded-full transition-colors relative', fv[field] ? color : 'bg-secondary')}
                      >
                        <div className={cn('w-3.5 h-3.5 rounded-full bg-white absolute top-0.5 transition-transform shadow', fv[field] ? 'translate-x-5' : 'translate-x-0.5')} />
                      </button>
                    </div>
                  ))}

                  {/* Vehicle Speed — only shown when animate_vehicle is on */}
                  {fv.animate_vehicle && (
                    <div className="pt-1 space-y-1.5">
                      <label className="text-sm font-medium flex items-center justify-between">
                        <span className="flex items-center gap-1.5">
                          <Gauge className="w-3.5 h-3.5 text-emerald-400" /> Animation Speed
                        </span>
                        <Badge variant="success">{vehicleSpeed}x</Badge>
                      </label>
                      <div className="flex gap-1.5">
                        {[0.5, 1, 2, 5, 10, 20].map(s => (
                          <button
                            key={s}
                            type="button"
                            onClick={() => setVehicleSpeed(s)}
                            className={cn(
                              'flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors',
                              vehicleSpeed === s ? 'bg-emerald-500 text-white' : 'bg-secondary hover:bg-accent'
                            )}
                          >
                            {s}x
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Submit */}
                <div className="flex gap-2 pt-2">
                  <Button type="submit" variant="gradient" className="flex-1" loading={mutation.isPending}>
                    <Zap className="w-4 h-4" />
                    {mutation.isPending ? 'Optimizing...' : 'Optimize Route'}
                  </Button>
                  <Button type="button" variant="outline" size="icon"
                    onClick={() => {
                      reset();
                      setResult(null);
                      setSubmittedValues(null);
                      setSubmittedWeights(null);
                      setRouteChange(null);
                      previousResultRef.current = null;
                      setUseCustomWeights(false);
                    }}>
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                </div>

                {scenarioIsStale && (
                  <p className="text-xs text-amber-400 text-center bg-amber-400/10 border border-amber-400/30 rounded-lg px-3 py-2">
                    Updating the route for the changed scenario…
                  </p>
                )}

                {isStale && !scenarioIsStale && (
                  <p className="text-xs text-amber-400 text-center bg-amber-400/10 border border-amber-400/30 rounded-lg px-3 py-2">
                    Solver settings changed — click <b>Optimize Route</b> to rerun QAOA
                  </p>
                )}

                {mutation.isError && (
                  <p className="text-xs text-rose-400 text-center">
                    Optimization failed. Check backend connection.
                  </p>
                )}
              </form>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Map ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }} className="xl:col-span-2"
        >
          <RouteMap
            result={result}
            isLoading={mutation.isPending}
            animateVehicle={fv.animate_vehicle}
            showTrafficOverlay={fv.traffic_overlay}
            vehicleSpeed={vehicleSpeed}
          />
        </motion.div>
      </div>

      <AnimatePresence mode="wait">
        {mutation.isPending ? (
          <motion.div
            key="spinner"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-10 space-y-4"
          >
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 rounded-full border-2 border-purple-500/30 animate-spin" style={{ animationDuration: '3s' }} />
              <div className="absolute inset-2 rounded-full border-2 border-blue-500/50 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
              <div className="absolute inset-4 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
            </div>
            <div className="text-center">
              <p className="font-semibold">Running QAOA (p={fv.qaoa_layers})</p>
              <p className="text-sm text-muted-foreground">Solving QUBO on Qiskit Aer Simulator…</p>
            </div>
          </motion.div>
        ) : result ? (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }} className="space-y-6"
          >
            <QuantumPanel result={result.quantum} />
            <Card className="border-blue-500/30 bg-blue-500/5">
              <CardContent className="py-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold">Traffic model estimate</p>
                    <p className="text-xs text-muted-foreground mt-1">Synthetic scenario model · {result.traffic_prediction.model_name?.split('_').join(' ')}</p>
                  </div>
                  <div className="flex gap-5 text-sm">
                    <span><strong>{result.traffic_prediction.predicted_traffic.toFixed(1)}%</strong><br/><span className="text-xs text-muted-foreground">congestion</span></span>
                    <span><strong>{result.traffic_prediction.estimated_delay_min?.toFixed(1)} min</strong><br/><span className="text-xs text-muted-foreground">estimated delay</span></span>
                    <span><strong>{result.traffic_prediction.expected_travel_time_min?.toFixed(1)} min</strong><br/><span className="text-xs text-muted-foreground">expected trip</span></span>
                  </div>
                </div>
              </CardContent>
            </Card>
            <RouteDecisionExplanation result={result} routeChange={routeChange} />
            <ComparisonTable result={result} />
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
