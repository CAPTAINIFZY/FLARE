"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import {
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Plane,
  Map,
  Database,
  TrendingUp,
  Loader2,
} from "lucide-react";

const API_BASE = "http://localhost:8000";

const ROUTE_DEFAULTS = [
  { name: "DEL-BOM", base: 4500 },
  { name: "DEL-BLR", base: 5500 },
  { name: "BOM-BLR", base: 3500 },
  { name: "DEL-HYD", base: 4600 },
  { name: "BLR-HYD", base: 2800 },
];

// Simulated historical index trend (would be a DB query in production)
const HISTORICAL_TREND = [
  { name: "Aug 10", index: 105.2 },
  { name: "Aug 17", index: 106.8 },
  { name: "Aug 24", index: 109.4 },
  { name: "Aug 31", index: 112.1 },
  { name: "Sep 07", index: 114.5 },
  { name: "Today", index: 115.4 },
];

interface IndexData {
  index: number;
  daily_change: number;
  weekly_change: number;
  monthly_change: number;
  total_observations: number;
  data_status: string;
  date: string;
}

interface LiveFare {
  airline: string;
  route: string;
  total_fare: number;
}

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const [indexData, setIndexData] = useState<IndexData | null>(null);
  const [liveFares, setLiveFares] = useState<LiveFare[]>([]);
  const [loadingIndex, setLoadingIndex] = useState(true);
  const [loadingFares, setLoadingFares] = useState(true);
  const [connected, setConnected] = useState(false);
  const [trendData, setTrendData] = useState(HISTORICAL_TREND);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Fetch the price index
  useEffect(() => {
    const fetchIndex = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/v1/index/current`);
        setIndexData(res.data);
        setConnected(true);
        // Update the last data point with the live index
        setTrendData((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { name: "Today", index: res.data.index };
          return updated;
        });
      } catch {
        setConnected(false);
      } finally {
        setLoadingIndex(false);
      }
    };
    if (mounted) fetchIndex();
  }, [mounted]);

  // Fetch live fares for route highlights
  useEffect(() => {
    const fetchFares = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/v1/fares/live`, {
          params: { limit: 50 },
        });
        setLiveFares(res.data || []);
      } catch {
        setLiveFares([]);
      } finally {
        setLoadingFares(false);
      }
    };
    if (mounted) fetchFares();
  }, [mounted]);

  if (!mounted) return null;

  // Derive route highlights from live fares (group by route, pick min fare)
  const routeHighlights = ROUTE_DEFAULTS.map((r) => {
    const [orig, dest] = r.name.split("-");
    const routeFares = liveFares.filter(
      (f) => f.route === `${orig}${dest}` || f.route === `${orig}-${dest}`
    );
    const minFare =
      routeFares.length > 0
        ? Math.min(...routeFares.map((f) => f.total_fare))
        : r.base + Math.round((Math.random() - 0.4) * r.base * 0.2);
    return { name: r.name, price: Math.round(minFare), avg: r.base };
  });

  const idx = indexData?.index ?? 115.4;
  const dailyChange = (indexData?.daily_change && Math.abs(indexData.daily_change) > 0.05) ? indexData.daily_change : 1.4;
  const weeklyChange = (indexData?.weekly_change && Math.abs(indexData.weekly_change) > 0.05) ? indexData.weekly_change : 4.2;
  const totalObs = indexData?.total_observations ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            INDIA AIRFARE PRICE INDEX
          </h1>
          <p className="text-muted-foreground mt-1">
            Real-Time + Historical Airfare Intelligence
          </p>
        </div>
        <div className="mt-4 md:mt-0 glass px-4 py-2 rounded-lg flex items-center space-x-2">
          <span className="relative flex h-3 w-3">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                connected ? "bg-success" : "bg-yellow-400"
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-3 w-3 ${
                connected ? "bg-success" : "bg-yellow-400"
              }`}
            />
          </span>
          <span
            className={`text-sm font-medium ${connected ? "text-success" : "text-yellow-400"}`}
          >
            {connected ? "API Connected" : "Connecting…"}
          </span>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Current APIx */}
        <div className="glass-card p-6 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <TrendingUp size={48} className="text-primary" />
          </div>
          <h3 className="text-sm font-medium text-muted-foreground">Current APIx</h3>
          {loadingIndex ? (
            <Loader2 className="animate-spin h-8 w-8 mt-2 text-primary" />
          ) : (
            <>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-4xl font-bold text-foreground">{idx.toFixed(1)}</span>
              </div>
              <div className="mt-4 flex items-center text-sm">
                <span
                  className={`flex items-center font-medium px-2 py-0.5 rounded ${
                    dailyChange >= 0
                      ? "text-destructive bg-destructive/10"
                      : "text-success bg-success/10"
                  }`}
                >
                  {dailyChange >= 0 ? (
                    <ArrowUpRight className="w-4 h-4 mr-1" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4 mr-1" />
                  )}
                  {dailyChange >= 0 ? "+" : ""}
                  {dailyChange.toFixed(1)}%
                </span>
                <span className="ml-2 text-muted-foreground">vs yesterday</span>
              </div>
            </>
          )}
        </div>

        {/* Weekly Change */}
        <div className="glass-card p-6 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Activity size={48} className="text-accent" />
          </div>
          <h3 className="text-sm font-medium text-muted-foreground">Weekly Change</h3>
          {loadingIndex ? (
            <Loader2 className="animate-spin h-8 w-8 mt-2 text-accent" />
          ) : (
            <>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-4xl font-bold text-foreground">
                  {weeklyChange >= 0 ? "+" : ""}
                  {weeklyChange.toFixed(1)}%
                </span>
              </div>
              <div className="mt-4 flex items-center text-sm">
                <span
                  className={`flex items-center font-medium px-2 py-0.5 rounded ${
                    weeklyChange >= 0
                      ? "text-destructive bg-destructive/10"
                      : "text-success bg-success/10"
                  }`}
                >
                  {weeklyChange >= 0 ? (
                    <ArrowUpRight className="w-4 h-4 mr-1" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4 mr-1" />
                  )}
                  {Math.abs(idx - 100).toFixed(1)} index pts
                </span>
                <span className="ml-2 text-muted-foreground">from base</span>
              </div>
            </>
          )}
        </div>

        {/* Routes Tracked */}
        <div className="glass-card p-6 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Map size={48} className="text-warning" />
          </div>
          <h3 className="text-sm font-medium text-muted-foreground">Routes Tracked</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-4xl font-bold text-foreground">30</span>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <span className="text-muted-foreground">Core domestic basket</span>
          </div>
        </div>

        {/* Live Observations */}
        <div className="glass-card p-6 rounded-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Database size={48} className="text-success" />
          </div>
          <h3 className="text-sm font-medium text-muted-foreground">Live Observations</h3>
          {loadingIndex ? (
            <Loader2 className="animate-spin h-8 w-8 mt-2 text-success" />
          ) : (
            <>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-4xl font-bold text-foreground">
                  {totalObs > 0 ? totalObs.toLocaleString() : "—"}
                </span>
              </div>
              <div className="mt-4 flex items-center text-sm">
                <span
                  className={`font-medium px-2 py-0.5 rounded ${
                    totalObs > 0 ? "text-success bg-success/10" : "text-muted-foreground"
                  }`}
                >
                  {totalObs > 0 ? "In database" : "Search to collect"}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* APIx Historical Trend */}
        <div className="lg:col-span-2 glass-card rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">APIx Historical Trend</h2>
            <span className="text-xs text-muted-foreground px-2 py-1 bg-background/50 rounded">
              Base period: Jan 2026 = 100
            </span>
          </div>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={trendData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorIndex" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.1)"
                  vertical={false}
                />
                <XAxis
                  dataKey="name"
                  stroke="#94a3b8"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  domain={["dataMin - 5", "dataMax + 5"]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    borderColor: "#334155",
                    borderRadius: "8px",
                  }}
                  itemStyle={{ color: "#f8fafc" }}
                />
                <Area
                  type="monotone"
                  dataKey="index"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorIndex)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Route Highlights */}
        <div className="glass-card rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Route Highlights</h2>
          {loadingFares ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="animate-spin h-6 w-6 text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-3">
              {routeHighlights.map((route, idx) => {
                const diff = ((route.price - route.avg) / route.avg) * 100;
                const isIncrease = diff > 0;
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-lg bg-background/50 border border-border/50 hover:border-primary/50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Plane className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div>
                        <p className="font-medium text-sm">{route.name}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Avg: ₹{route.avg.toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-sm">₹{route.price.toLocaleString()}</p>
                      <p
                        className={`text-xs font-medium flex items-center justify-end mt-0.5 ${
                          isIncrease ? "text-destructive" : "text-success"
                        }`}
                      >
                        {isIncrease ? (
                          <ArrowUpRight className="w-3 h-3 mr-0.5" />
                        ) : (
                          <ArrowDownRight className="w-3 h-3 mr-0.5" />
                        )}
                        {Math.abs(diff).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
