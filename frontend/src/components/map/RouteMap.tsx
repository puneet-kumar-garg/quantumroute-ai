import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Badge';
import { Navigation, Layers } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import type { OptimizationResult } from '@/types';
import { selectRoadGeometry } from '@/lib/routeGeometry';

interface Props {
  result: OptimizationResult | null;
  isLoading?: boolean;
  animateVehicle?: boolean;
  showTrafficOverlay?: boolean;
  vehicleSpeed?: number;
}

const CITY_CENTER: [number, number] = [30.7414, 76.7842];

export function RouteMap({ result, isLoading, animateVehicle = true, showTrafficOverlay = false, vehicleSpeed = 1 }: Props) {
  const mapRef        = useRef<any>(null);
  const containerRef  = useRef<HTMLDivElement>(null);
  const layersRef     = useRef<any[]>([]);
  const tileRef       = useRef<any>(null);
  const vehicleRef    = useRef<any>(null);
  const animRef       = useRef<number>(0);
  const speedRef      = useRef<number>(vehicleSpeed);
  const [mapReady, setMapReady] = useState(false);
  const [activeRoute, setActiveRoute] = useState<'priority' | 'quantum' | 'dijkstra' | 'astar' | 'bellman'>('priority');
  const { isDark } = useTheme();
  const vehicleIcon = result?.request.vehicle_type === 'bike' ? '🏍️'
    : result?.request.vehicle_type === 'truck' ? '🚚'
    : result?.request.vehicle_type === 'emergency' ? '🚑' : '🚗';

  useEffect(() => { speedRef.current = vehicleSpeed; }, [vehicleSpeed]);

  // ── Init map ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    let cancelled = false;

    import('leaflet').then((L) => {
      if (cancelled || !containerRef.current || mapRef.current) return;
      const map = L.map(containerRef.current!, {
        center: CITY_CENTER, zoom: 13, zoomControl: false,
      });

      const initialDark = document.documentElement.classList.contains('dark');
      const tileUrl = initialDark
        ? 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
        : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
      tileRef.current = L.tileLayer(tileUrl, {
        attribution: initialDark
          ? '© <a href="https://stadiamaps.com/">Stadia Maps</a> © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          : '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      L.control.zoom({ position: 'bottomright' }).addTo(map);
      mapRef.current = map;
      setMapReady(true);
    });

    return () => {
      cancelled = true;
      cancelAnimationFrame(animRef.current);
      if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; }
    };
  }, []);

  // ── Swap tile layer on theme change ───────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !mapReady) return;
    import('leaflet').then((L) => {
      if (tileRef.current) mapRef.current.removeLayer(tileRef.current);
      const tileUrl = isDark
        ? 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
        : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
      tileRef.current = L.tileLayer(tileUrl, {
        attribution: isDark
          ? '© <a href="https://stadiamaps.com/">Stadia Maps</a> © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          : '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(mapRef.current);
    });
  }, [isDark, mapReady]);

  // ── Draw routes + condition zones ─────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !result || !mapReady) return;

    const geometryFor = (path: string[], roadCoordinates: [number, number][]) => {
      const curatedFallback: [number, number][] = [];
      for (let i = 0; i < path.length - 1; i += 1) {
        const edge = result.edges.find(item => item.from === path[i] && item.to === path[i + 1]);
        const segment = edge?.geometry ?? [];
        curatedFallback.push(...(curatedFallback.length ? segment.slice(1) : segment));
      }
      return selectRoadGeometry(roadCoordinates, curatedFallback);
    };
    const routeDefs = [
      { key: 'dijkstra', coords: geometryFor(result.dijkstra.path, result.dijkstra.path_coords), color: '#3b82f6', dash: '8 5', w: 3, label: 'Dijkstra', dist: result.dijkstra.distance },
      { key: 'astar', coords: geometryFor(result.astar.path, result.astar.path_coords), color: '#06b6d4', dash: '4 4', w: 3, label: 'A*', dist: result.astar.distance },
      { key: 'bellman', coords: geometryFor(result.bellman_ford.path, result.bellman_ford.path_coords), color: '#f59e0b', dash: '2 5', w: 3, label: 'Bellman-Ford', dist: result.bellman_ford.distance },
      { key: 'quantum', coords: geometryFor(result.quantum.path, result.quantum.path_coords), color: '#8b5cf6', dash: '6 3', w: 3, label: 'QAOA', dist: result.quantum.distance },
      { key: 'priority', coords: geometryFor(result.recommendation.path, result.recommendation.path_coords), color: '#10b981', dash: '', w: 5, label: 'Recommended', dist: result.recommendation.distance },
    ];

    import('leaflet').then((L) => {
      layersRef.current.forEach(l => { try { mapRef.current.removeLayer(l); } catch {} });
      layersRef.current = [];
      cancelAnimationFrame(animRef.current);
      if (vehicleRef.current) { try { mapRef.current.removeLayer(vehicleRef.current); } catch {} vehicleRef.current = null; }

      const add = (layer: any) => { layer.addTo(mapRef.current); layersRef.current.push(layer); return layer; };

      // ── Condition zones from the selected scenario ──
      const zones = result.condition_zones ?? [];
      zones.forEach(zone => {
        const typeIcon = zone.type === 'traffic' ? '🚗' : zone.type === 'weather' ? (result.request.weather === 'rain' ? '🌧️' : '🌫️') : '🚧';
        const typeDesc = zone.type === 'traffic' ? 'High congestion area' : zone.type === 'weather' ? 'Weather affected area' : 'Road condition affected';
        add(L.circle([zone.lat, zone.lng], {
          radius: zone.radius,
          color: zone.color,
          fillColor: zone.color,
          fillOpacity: 0.22,
          weight: 2,
          dashArray: zone.type === 'weather' ? '6 4' : zone.type === 'road' ? '3 3' : undefined,
        }).bindPopup(
          `<div style="font-size:13px;line-height:1.6"><b>${typeIcon} ${zone.label}</b><br/><span style="color:${zone.color};font-size:11px">${typeDesc}</span></div>`
        ));
      });

      // ── Static traffic overlay (toggle) ──
      if (showTrafficOverlay) {
        [
          { lat: 30.7196, lng: 76.7839, r: 300, color: '#ef4444' },
          { lat: 30.7076, lng: 76.7916, r: 250, color: '#f59e0b' },
          { lat: 30.7414, lng: 76.7842, r: 200, color: '#f97316' },
        ].forEach(h => add(L.circle([h.lat, h.lng], {
          radius: h.r, color: h.color, fillColor: h.color, fillOpacity: 0.12, weight: 1,
        })));
      }

      // ── Route polylines ──
      routeDefs.forEach(r => {
        if (!r.coords?.length) return;
        add(L.polyline(r.coords, {
          color: r.color, weight: r.w,
          opacity: r.key === activeRoute ? 1 : 0.4,
          dashArray: r.dash || undefined,
        }).bindPopup(`<b>${r.label}</b><br/>Distance: ${r.dist} km`));
      });

      // ── Markers ──
      result.nodes.forEach(node => {
        const isSrc  = node.name === result.request.source;
        const isDest = node.name === result.request.destination;
        const priorityPath = result.recommendation.path;
        const isOnPath = priorityPath.includes(node.name);
        if (isSrc || isDest) {
          const color = isSrc ? '#10b981' : '#ef4444';
          add(L.marker([node.lat, node.lng], {
            icon: L.divIcon({
              html: `<div style="width:18px;height:18px;background:${color};border-radius:50%;border:3px solid white;box-shadow:0 0 12px ${color};"></div>`,
              iconSize: [18, 18], className: '',
            }),
          }).bindPopup(`<b>${isSrc ? '🟢 Source' : '🔴 Destination'}</b><br/>${node.name}`));
        } else if (isOnPath) {
          add(L.circleMarker([node.lat, node.lng], {
            radius: 5, fillColor: '#8b5cf6', color: '#fff', weight: 1.5, fillOpacity: 0.9,
          }).bindPopup(`<b>${node.name}</b>`));
        }
      });

      const startVehicle = (roadCoords: [number, number][]) => {
        if (!animateVehicle || roadCoords.length < 2) return;
        vehicleRef.current = L.marker(roadCoords[0], {
          icon: L.divIcon({
            html: `<div style="width:20px;height:20px;background:#10b981;border-radius:50%;border:3px solid white;box-shadow:0 0 14px #10b981;display:flex;align-items:center;justify-content:center;font-size:10px;">${vehicleIcon}</div>`,
            iconSize: [20, 20], className: '',
          }),
        }).addTo(mapRef.current);
        let seg = 0, progress = 0;
        const animate = () => {
          if (!vehicleRef.current) return;
          progress += 0.002 * speedRef.current;
          if (progress >= 1) { progress = 0; seg = (seg + 1) % (roadCoords.length - 1); }
          const from = roadCoords[seg], to = roadCoords[seg + 1];
          vehicleRef.current.setLatLng([from[0] + (to[0] - from[0]) * progress, from[1] + (to[1] - from[1]) * progress]);
          animRef.current = requestAnimationFrame(animate);
        };
        animRef.current = requestAnimationFrame(animate);
      };

      const allStraight = routeDefs.flatMap(r => r.coords);
      if (allStraight.length > 1) mapRef.current.fitBounds(L.latLngBounds(allStraight), { padding: [50, 50] });

      const priorityCoords = geometryFor(result.recommendation.path, result.recommendation.path_coords);
      startVehicle(priorityCoords);

    });
  }, [result, mapReady, activeRoute, animateVehicle, showTrafficOverlay, vehicleIcon]);

  // Derive active condition zones for legend
  const zones = result?.condition_zones ?? [];
  const hasTraffic = zones.some(z => z.type === 'traffic');
  const hasWeather = zones.some(z => z.type === 'weather');
  const hasRoad    = zones.some(z => z.type === 'road');

  return (
    <Card glass>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-emerald-400" />
            <CardTitle>Interactive Route Map</CardTitle>
            <Badge variant="info" className="text-xs">Chandigarh</Badge>
            {result && (
              <Badge variant={result.road_geometry.status === 'complete' ? 'success' : 'warning'} className="text-xs">
                {result.road_geometry.status === 'complete' ? 'OSRM road geometry' : 'OSRM partial fallback'}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {/* Condition zone legend */}
            {(hasTraffic || hasWeather || hasRoad) && (
              <div className="flex items-center gap-2">
                {hasTraffic && (
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-500/15 border border-red-500/30 text-red-400">
                    <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> High Traffic
                  </span>
                )}
                {hasWeather && (
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-400">
                    <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /> {result?.request.weather === 'rain' ? 'Rain' : 'Fog'} Zone
                  </span>
                )}
                {hasRoad && (
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400">
                    <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> Road Condition
                  </span>
                )}
              </div>
            )}

            {result && (
              <div className="flex items-center gap-1 p-1 rounded-lg bg-background border border-border">
                {([
                  { key: 'priority', label: 'Recommended', color: 'bg-emerald-500' },
                  { key: 'dijkstra', label: 'Dijkstra', color: 'bg-blue-500' },
                  { key: 'astar',    label: 'A*',        color: 'bg-cyan-500' },
                  { key: 'bellman',  label: 'Bellman-Ford', color: 'bg-amber-500' },
                  { key: 'quantum',  label: 'QAOA',      color: 'bg-purple-500' },
                ] as const).map(r => (
                  <button
                    key={r.key}
                    onClick={() => setActiveRoute(r.key)}
                    className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-all ${
                      activeRoute === r.key ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${r.color}`} />
                    {r.label}
                  </button>
                ))}
              </div>
            )}
            {!result && (
              <div className="flex items-center gap-3">
                {[
                  { color: 'bg-emerald-400', label: 'QAOA' },
                  { color: 'bg-blue-400',    label: 'Dijkstra' },
                  { color: 'bg-cyan-400',    label: 'A*' },
                ].map(l => (
                  <div key={l.label} className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${l.color}`} />
                    <span className="text-xs text-muted-foreground">{l.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 relative">
        <div ref={containerRef} className="w-full rounded-b-xl overflow-hidden" style={{ height: '500px' }} />

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/70 backdrop-blur-sm rounded-b-xl">
            <div className="flex flex-col items-center gap-3">
              <Spinner size="lg" />
              <p className="text-sm text-muted-foreground">Computing optimal routes…</p>
            </div>
          </div>
        )}

        {!result && !isLoading && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center space-y-2">
              <Layers className="w-8 h-8 text-muted-foreground mx-auto" />
              <p className="text-sm text-muted-foreground">Select source & destination, then click Optimize Route</p>
            </div>
          </div>
        )}

        {/* ── Always-visible map legend ── */}
        <div className="absolute top-3 left-3 pointer-events-none z-[999] bg-background/85 backdrop-blur-sm border border-border rounded-xl px-3 py-2.5 shadow-lg space-y-1.5">
          <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">Map Legend</p>
          {[
            { color: '#ef4444', label: 'High Traffic Zone',     icon: '🚗', dash: false },
            { color: '#f97316', label: 'Moderate Traffic Zone', icon: '🚗', dash: false },
            { color: '#f59e0b', label: 'Medium Traffic / Road', icon: '⚠️', dash: false },
            { color: '#3b82f6', label: 'Rain / Flood Zone',     icon: '🌧️', dash: true  },
            { color: '#94a3b8', label: 'Fog / Low Visibility',  icon: '🌫️', dash: true  },
            { color: '#dc2626', label: 'Poor Road Condition',   icon: '🚧', dash: true  },
          ].map(({ color, label, icon, dash }) => (
            <div key={label} className="flex items-center gap-2">
              <span
                className="inline-block w-5 h-2.5 rounded-sm flex-shrink-0"
                style={{
                  background: color + '44',
                  border: `2px ${dash ? 'dashed' : 'solid'} ${color}`,
                }}
              />
              <span className="text-[11px] text-foreground/80">{icon} {label}</span>
            </div>
          ))}
        </div>

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-4 left-4 right-4 flex flex-wrap gap-2 pointer-events-none"
          >
            {[
              { label: 'Recommended', dist: result.recommendation.distance, time: result.recommendation.time, color: 'bg-emerald-500/90' },
              { label: 'Dijkstra', dist: result.dijkstra.distance, time: result.dijkstra.time, color: 'bg-blue-500/90' },
              { label: 'A*',       dist: result.astar.distance,    time: result.astar.time,    color: 'bg-cyan-500/90' },
            ].map(r => (
              <div key={r.label} className={`${r.color} backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-full font-medium shadow-lg`}>
                {r.label}: {r.dist.toFixed(1)}km · {r.time.toFixed(0)}min
              </div>
            ))}
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}
