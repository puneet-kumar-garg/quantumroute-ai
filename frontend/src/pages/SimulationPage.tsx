import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Activity, AlertTriangle, Construction, CloudRain, RefreshCw, Play, Pause } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { routeService } from '@/services/route.service';
import { useTheme } from '@/hooks/useTheme';
import type { SimulationData } from '@/types';
import { loadPreferences } from '@/lib/preferences';

const CITY_CENTER: [number, number] = [30.7414, 76.7842];
const VEHICLE_PATH: [number, number][] = [
  [30.7414, 76.7842], [30.7333, 76.7794], [30.7196, 76.7839],
  [30.7076, 76.7916], [30.7056, 76.8013], [30.7310, 76.8050], [30.7414, 76.7842],
];

export default function SimulationPage() {
  const [preferences] = useState(loadPreferences);
  const mapRef = useRef<any>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const tileRef = useRef<any>(null);
  const scenarioLayerRef = useRef<any>(null);
  const vehicleRef = useRef<any>(null);
  const animFrameRef = useRef<number>(0);
  const [running, setRunning] = useState(false);
  const { isDark } = useTheme();

  const { data: simData, refetch, isLoading, isError } = useQuery<SimulationData>({
    queryKey: ['simulation'],
    queryFn: routeService.getSimulationData,
  });

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;
    let cancelled = false;
    import('leaflet').then((L) => {
      if (cancelled || !mapContainerRef.current || mapRef.current) return;
      const map = L.map(mapContainerRef.current!, { center: CITY_CENTER, zoom: 12, zoomControl: false });
      tileRef.current = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors', maxZoom: 19,
      }).addTo(map);
      L.control.zoom({ position: 'bottomright' }).addTo(map);
      vehicleRef.current = L.marker(VEHICLE_PATH[0], {
        icon: L.divIcon({
          html: '<div style="width:16px;height:16px;background:#10b981;border-radius:50%;border:2px solid white;box-shadow:0 0 8px #10b981"></div>',
          iconSize: [16, 16], className: '',
        }),
      }).addTo(map);
      mapRef.current = map;
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(animFrameRef.current);
      if (mapRef.current) mapRef.current.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    import('leaflet').then((L) => {
      if (tileRef.current) mapRef.current.removeLayer(tileRef.current);
      const url = isDark
        ? 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
        : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
      tileRef.current = L.tileLayer(url, { attribution: '© OpenStreetMap contributors', maxZoom: 19 }).addTo(mapRef.current);
    });
  }, [isDark]);

  useEffect(() => {
    if (!mapRef.current || !simData) return;
    import('leaflet').then((L) => {
      if (scenarioLayerRef.current) mapRef.current.removeLayer(scenarioLayerRef.current);
      const group = L.layerGroup().addTo(mapRef.current);
      if (preferences.showScenarioAccidents) simData.accidents.forEach(event => {
        L.circleMarker([event.lat, event.lng], { radius: 10, fillColor: '#ef4444', color: '#fff', weight: 2, fillOpacity: 0.85 })
          .bindPopup(`<b>Scenario accident</b><br/>${event.description}`).addTo(group);
      });
      simData.road_closures.forEach(event => {
        L.circleMarker([event.lat, event.lng], { radius: 10, fillColor: '#f59e0b', color: '#fff', weight: 2, fillOpacity: 0.85 })
          .bindPopup(`<b>Scenario closure</b><br/>${event.description}`).addTo(group);
      });
      simData.traffic_hotspots.forEach(hotspot => {
        L.circle([hotspot.lat, hotspot.lng], {
          radius: 180 + hotspot.intensity * 280, color: '#f97316', fillColor: '#f97316',
          fillOpacity: 0.14 + hotspot.intensity * 0.16, weight: 1.5,
        }).bindPopup(`<b>${hotspot.label}</b><br/>Scenario intensity ${(hotspot.intensity * 100).toFixed(0)}%`).addTo(group);
      });
      scenarioLayerRef.current = group;
    });
  }, [preferences.showScenarioAccidents, simData]);

  useEffect(() => {
    if (!running || !vehicleRef.current) return;
    let idx = 0;
    let progress = 0;
    const animate = () => {
      if (!vehicleRef.current) return;
      progress += 0.005 * preferences.simulationSpeed;
      if (progress >= 1) { progress = 0; idx = (idx + 1) % (VEHICLE_PATH.length - 1); }
      const from = VEHICLE_PATH[idx];
      const to = VEHICLE_PATH[idx + 1];
      vehicleRef.current.setLatLng([from[0] + (to[0] - from[0]) * progress, from[1] + (to[1] - from[1]) * progress]);
      animFrameRef.current = requestAnimationFrame(animate);
    };
    animFrameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [preferences.simulationSpeed, running]);

  const stats = [
    { label: 'Scenario Vehicles', value: simData?.active_vehicles ?? '—', icon: Activity, color: 'text-blue-400' },
    { label: 'Accidents', value: simData?.accidents.length ?? '—', icon: AlertTriangle, color: 'text-rose-400' },
    { label: 'Road Closures', value: simData?.road_closures.length ?? '—', icon: Construction, color: 'text-amber-400' },
    { label: 'Weather Alerts', value: simData?.weather_alerts.length ?? '—', icon: CloudRain, color: 'text-blue-400' },
  ];
  const scenarioEvents = simData ? [
    ...simData.accidents.map(event => ({ label: 'Accident', detail: event.description, severity: event.severity })),
    ...simData.road_closures.map(event => ({ label: 'Road closure', detail: event.description, severity: event.severity })),
    ...simData.traffic_hotspots.map(event => ({ label: 'Traffic hotspot', detail: `${event.label} · ${(event.intensity * 100).toFixed(0)}% intensity`, severity: event.intensity > 0.8 ? 'high' : 'medium' })),
  ] : [];

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-2 flex-wrap"><h1 className="text-2xl font-bold">Traffic Scenario Lab</h1><Badge variant="warning">Synthetic data</Badge></div>
        <p className="text-sm text-muted-foreground mt-1">{simData?.scenario_label ?? 'Loading a deterministic Chandigarh scenario…'}</p>
      </motion.div>

      {isError && <p className="text-sm text-rose-400">The scenario API could not be loaded. Check the backend connection.</p>}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((item, index) => (
          <motion.div key={item.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}>
            <Card glass className="p-4"><div className="flex items-center gap-3"><item.icon className={`w-5 h-5 ${item.color}`} /><div><p className="text-xs text-muted-foreground">{item.label}</p><p className="text-xl font-bold">{isLoading ? '…' : item.value}</p></div></div></Card>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <div className="xl:col-span-3">
          <Card glass>
            <CardHeader><div className="flex items-center justify-between gap-4"><div><CardTitle>Scenario map</CardTitle><p className="text-xs text-muted-foreground mt-1">Animation is illustrative; event positions and intensities come from the scenario API.</p></div><div className="flex items-center gap-2"><Button variant="outline" size="sm" onClick={() => refetch()}><RefreshCw className="w-3.5 h-3.5" /> Reload</Button><Button variant={running ? 'outline' : 'gradient'} size="sm" onClick={() => setRunning(value => !value)}>{running ? <><Pause className="w-3.5 h-3.5" /> Pause</> : <><Play className="w-3.5 h-3.5" /> Animate</>}</Button></div></div></CardHeader>
            <CardContent className="p-0"><div ref={mapContainerRef} className="w-full rounded-b-xl" style={{ height: '450px' }} /></CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <Card glass><CardHeader><CardTitle className="text-sm">Scenario events</CardTitle></CardHeader><CardContent><div className="space-y-2">{scenarioEvents.map((event, index) => <div key={`${event.label}-${index}`} className="p-2 rounded-lg bg-background/50 border border-border"><div className="flex items-center gap-2"><Badge variant={event.severity === 'high' ? 'danger' : 'warning'}>{event.severity}</Badge><p className="text-xs font-medium">{event.label}</p></div><p className="text-xs text-muted-foreground mt-1">{event.detail}</p></div>)}{!isLoading && scenarioEvents.length === 0 && <p className="text-xs text-muted-foreground">No scenario events.</p>}</div></CardContent></Card>
          <Card glass><CardHeader><CardTitle className="text-sm">Data provenance</CardTitle></CardHeader><CardContent className="space-y-2 text-xs text-muted-foreground"><p>{simData?.provenance?.split('_').join(' ') ?? '—'}</p><p>ID: <span className="font-mono">{simData?.scenario_id ?? '—'}</span></p><p>This view is not a live traffic feed.</p></CardContent></Card>
        </div>
      </div>
    </div>
  );
}
