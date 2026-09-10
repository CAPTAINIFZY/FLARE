"use client";

import { useEffect, useState, useCallback } from "react";
import {
  TrendingUp, TrendingDown, Minus, RefreshCw, AlertCircle,
  Info, ExternalLink, ChevronDown, ChevronUp, BarChart3,
  Activity, Plane, Globe
} from "lucide-react";
import { cn } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Source labels for each data source
const SOURCE_LABELS: Record<string, { label: string; badge: string; color: string }> = {
  makemytrip:       { label: "MakeMyTrip",       badge: "OTA",   color: "bg-orange-500" },
  cleartrip:        { label: "Cleartrip",         badge: "OTA",   color: "bg-blue-500" },
  ixigo:            { label: "Ixigo",             badge: "OTA",   color: "bg-purple-500" },
  yatra:            { label: "Yatra",             badge: "OTA",   color: "bg-teal-500" },
  goibibo:          { label: "Goibibo",           badge: "OTA",   color: "bg-red-500" },
  easemytrip:       { label: "EaseMyTrip",        badge: "OTA",   color: "bg-green-600" },
  airindia_official:{ label: "Air India (GoI)",   badge: "GOVT",  color: "bg-amber-600" },
  indigo_direct:    { label: "IndiGo Direct",     badge: "AIRLINE",color:"bg-indigo-600" },
  google_flights:   { label: "Google Flights",    badge: "META",  color: "bg-sky-500" },
  amadeus:          { label: "Amadeus GDS",       badge: "GDS",   color: "bg-slate-500" },
  demo_generator:   { label: "Demo Data",         badge: "DEMO",  color: "bg-gray-400" },
};

interface KPI {
  label: string;
  value: string | number | null;
  subLabel?: string;
  change?: number | null;
  color: string;
  icon: React.ReactNode;
  tooltip?: string;
  isOfficial?: boolean;
}

interface CPIRecord {
  period: string;
  value: number;
  yoy_inflation_pct?: number | null;
  source?: string;
  source_url?: string;
}

interface SourceStat {
  source: string;
  source_type: string;
  display_label: string;
  observation_count: number;
  avg_fare: number;
  min_fare: number;
  max_fare: number;
}

interface ComparisonRecord {
  period: string;
  airfare_index: number | null;
  airfare_yoy_pct: number | null;
  official_cpi: number | null;
  official_cpi_yoy_pct: number | null;
  inflation_gap: number | null;
  official_cpi_source_url?: string | null;
}

export default function EconomicDashboard() {
  const [indexData, setIndexData] = useState<any>(null);
  const [cpiData, setCpiData] = useState<{ latest: CPIRecord | null; records: CPIRecord[] }>({ latest: null, records: [] });
  const [comparison, setComparison] = useState<ComparisonRecord[]>([]);
  const [sources, setSources] = useState<SourceStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [showProvenance, setShowProvenance] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [idxRes, cpiRes, cmpRes, srcRes] = await Promise.allSettled([
        fetch(`${API}/api/v1/index/airfare`).then(r => r.json()),
        fetch(`${API}/api/v1/cpi/government?limit=12`).then(r => r.json()),
        fetch(`${API}/api/v1/inflation/comparison`).then(r => r.json()),
        fetch(`${API}/api/v1/inflation/pressure`).then(r => r.json()),
      ]);

      if (idxRes.status === "fulfilled") setIndexData(idxRes.value);
      if (cpiRes.status === "fulfilled") {
        const d = cpiRes.value;
        setCpiData({ latest: d.latest || null, records: d.records || [] });
      }
      if (cmpRes.status === "fulfilled") setComparison(cmpRes.value?.comparison || []);
      if (srcRes.status === "fulfilled") setSources(srcRes.value?.sources || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 60_000); // refresh every 60s
    return () => clearInterval(interval);
  }, [fetchAll]);

  const triggerCalculation = async () => {
    setCalculating(true);
    try {
      await fetch(`${API}/api/v1/index/calculate`, { method: "POST" });
      await fetchAll();
    } finally {
      setCalculating(false);
    }
  };

  // Derived KPIs
  const airfareIndex = indexData?.index_value ?? null;
  const latestCPI = cpiData.latest?.value ?? null;
  const latestCPIYoY = cpiData.latest?.yoy_inflation_pct ?? null;

  // Find latest comparison entry with airfare yoy
  const latestCmp = [...comparison].reverse().find(c => c.airfare_yoy_pct != null);
  const airfareYoY = latestCmp?.airfare_yoy_pct ?? null;
  const inflationGap = latestCmp?.inflation_gap ?? null;

  // Estimated contribution (Mode A if transport weight 8.59% available)
  const TRANSPORT_WEIGHT = 0.0859;
  const estimatedContribution = airfareYoY != null
    ? +(airfareYoY * TRANSPORT_WEIGHT).toFixed(2)
    : null;

  const kpis: KPI[] = [
    {
      label: "Airfare Price Index",
      value: airfareIndex != null ? airfareIndex.toFixed(1) : "—",
      subLabel: `Base: ${indexData?.base_period ?? "2025-01"} = 100`,
      color: "from-violet-600 to-purple-700",
      icon: <TrendingUp className="h-6 w-6" />,
      tooltip: "Computed Airfare Price Index (Experimental) — NOT an official government CPI",
    },
    {
      label: "Airfare Inflation YoY",
      value: airfareYoY != null ? `${airfareYoY > 0 ? "+" : ""}${airfareYoY.toFixed(1)}%` : "—",
      subLabel: "vs. same period last year",
      change: airfareYoY,
      color: airfareYoY != null && airfareYoY > 5 ? "from-red-600 to-red-700" : "from-emerald-600 to-green-700",
      icon: <BarChart3 className="h-6 w-6" />,
      tooltip: "Year-on-year change in computed airfare index",
    },
    {
      label: "Official CPI Inflation",
      value: latestCPIYoY != null ? `${latestCPIYoY > 0 ? "+" : ""}${latestCPIYoY.toFixed(1)}%` : "—",
      subLabel: "MoSPI/NSO — Official Government Data",
      change: latestCPIYoY,
      color: "from-blue-600 to-cyan-700",
      icon: <Globe className="h-6 w-6" />,
      tooltip: "Official Government of India CPI inflation (MoSPI/NSO, Base 2012=100)",
      isOfficial: true,
    },
    {
      label: "Airfare Inflation Gap",
      value: inflationGap != null ? `${inflationGap > 0 ? "+" : ""}${inflationGap.toFixed(1)} pp` : "—",
      subLabel: "Airfare inflation − Official CPI inflation",
      change: inflationGap,
      color: inflationGap != null && inflationGap > 0 ? "from-orange-500 to-amber-600" : "from-slate-600 to-slate-700",
      icon: <Activity className="h-6 w-6" />,
      tooltip: "Percentage points by which airfare inflation exceeds general CPI inflation",
    },
    {
      label: "Est. CPI Contribution",
      value: estimatedContribution != null ? `${estimatedContribution > 0 ? "+" : ""}${estimatedContribution.toFixed(2)} pp` : "—",
      subLabel: "Airfare YoY × CPI Transport Weight (8.59%)",
      color: "from-teal-600 to-emerald-700",
      icon: <Plane className="h-6 w-6" />,
      tooltip:
        "Mode A estimate: Airfare inflation × official CPI Transport & Communication weight (8.59%, NSO Base 2012=100). " +
        "This is an analytical estimate — NOT an official government CPI contribution figure.",
    },
  ];

  // Recent CPI records (last 6)
  const recentCPI = [...cpiData.records].slice(-6).reverse();

  // Observation count across all sources
  const totalObs = sources.reduce((s, r) => s + r.observation_count, 0);
  const govtSources = sources.filter(s => s.source_type === "govt_airline_scrape");
  const otaSources = sources.filter(s => s.source_type === "ota_scrape");

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Airfare Inflation &amp; Economic Impact</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Computed Airfare Price Index · Official Government CPI Comparison · Economic Analysis
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={triggerCalculation}
            disabled={calculating}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition disabled:opacity-50"
          >
            <RefreshCw className={cn("h-4 w-4", calculating && "animate-spin")} />
            {calculating ? "Calculating..." : "Recalculate Index"}
          </button>
          <button
            onClick={fetchAll}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-secondary transition disabled:opacity-50"
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      {/* Disclaimer banner */}
      <div className="flex items-start gap-3 p-4 rounded-xl border border-amber-200 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800">
        <AlertCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-sm text-amber-800 dark:text-amber-300">
          <span className="font-semibold">Data Separation Notice: </span>
          The <em>Computed Airfare Price Index</em> is produced by FLARE from collected fare observations and is <strong>not</strong> an official Government of India CPI index.
          Official CPI values are sourced from MoSPI/NSO press releases and are clearly labelled.
          Estimated CPI contribution figures are analytical estimates only.
        </div>
      </div>

      {/* 5 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
        {kpis.map((kpi) => (
          <div
            key={kpi.label}
            className={cn(
              "relative rounded-2xl p-5 text-white overflow-hidden shadow-lg",
              `bg-gradient-to-br ${kpi.color}`
            )}
            title={kpi.tooltip}
          >
            {kpi.isOfficial && (
              <span className="absolute top-2 right-2 text-[10px] font-bold bg-white/20 px-2 py-0.5 rounded-full">
                OFFICIAL GOVT
              </span>
            )}
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 bg-white/20 rounded-lg">{kpi.icon}</div>
            </div>
            <div className="text-2xl font-bold mb-1">{loading ? "..." : kpi.value}</div>
            <div className="text-xs font-medium text-white/80 mb-1">{kpi.label}</div>
            {kpi.subLabel && (
              <div className="text-[11px] text-white/60">{kpi.subLabel}</div>
            )}
          </div>
        ))}
      </div>

      {/* Main 2-col grid: Comparison table + CPI data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Airfare Index vs Official CPI */}
        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="text-lg font-semibold mb-1">Airfare Index vs Official CPI</h2>
          <p className="text-xs text-muted-foreground mb-4">
            Computed Airfare Price Index (Experimental) compared with Official MoSPI CPI
          </p>
          {comparison.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground text-sm gap-2">
              <Info className="h-8 w-8 opacity-40" />
              <span>No index data yet — trigger a calculation above</span>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-muted-foreground border-b border-border">
                    <th className="text-left py-2 pr-4">Period</th>
                    <th className="text-right py-2 pr-4">Airfare Index</th>
                    <th className="text-right py-2 pr-4">Airfare YoY</th>
                    <th className="text-right py-2 pr-4">Official CPI</th>
                    <th className="text-right py-2">CPI YoY</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.slice(-8).reverse().map((row) => (
                    <tr key={row.period} className="border-b border-border/50 hover:bg-secondary/30 transition">
                      <td className="py-2 pr-4 font-medium">{row.period}</td>
                      <td className="py-2 pr-4 text-right text-violet-600 font-semibold">
                        {row.airfare_index?.toFixed(1) ?? <span className="text-muted-foreground text-xs">—</span>}
                      </td>
                      <td className={cn("py-2 pr-4 text-right text-xs font-medium",
                        row.airfare_yoy_pct == null ? "text-muted-foreground"
                          : row.airfare_yoy_pct > 0 ? "text-red-500" : "text-emerald-500")}>
                        {row.airfare_yoy_pct != null
                          ? `${row.airfare_yoy_pct > 0 ? "+" : ""}${row.airfare_yoy_pct.toFixed(1)}%`
                          : "—"}
                      </td>
                      <td className="py-2 pr-4 text-right text-blue-600 font-semibold">
                        {row.official_cpi != null ? (
                          <a
                            href={row.official_cpi_source_url ?? "#"}
                            target="_blank" rel="noopener noreferrer"
                            className="hover:underline inline-flex items-center gap-1"
                          >
                            {row.official_cpi.toFixed(1)}
                            <ExternalLink className="h-3 w-3 opacity-50" />
                          </a>
                        ) : (
                          <span className="text-muted-foreground text-xs">Unavailable</span>
                        )}
                      </td>
                      <td className={cn("py-2 text-right text-xs font-medium",
                        row.official_cpi_yoy_pct == null ? "text-muted-foreground"
                          : row.official_cpi_yoy_pct > 0 ? "text-orange-500" : "text-emerald-500")}>
                        {row.official_cpi_yoy_pct != null
                          ? `${row.official_cpi_yoy_pct > 0 ? "+" : ""}${row.official_cpi_yoy_pct.toFixed(1)}%`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Official CPI Data */}
        <div className="rounded-2xl border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-lg font-semibold">Official Government CPI</h2>
            <span className="text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 px-2 py-0.5 rounded-full font-semibold">
              OFFICIAL GOVT DATA
            </span>
          </div>
          <p className="text-xs text-muted-foreground mb-4">
            Source: MoSPI/NSO — Ministry of Statistics &amp; Programme Implementation, GoI · Base Year 2012=100
          </p>
          {recentCPI.length === 0 ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-4">
              <Info className="h-5 w-5" />
              Government CPI data unavailable
            </div>
          ) : (
            <div className="space-y-2">
              {recentCPI.map((rec) => (
                <div key={rec.period} className="flex items-center justify-between py-2 border-b border-border/50">
                  <div className="text-sm font-medium">{rec.period}</div>
                  <div className="flex items-center gap-4">
                    <div className="text-blue-600 font-semibold text-sm">{rec.value.toFixed(1)}</div>
                    {rec.yoy_inflation_pct != null && (
                      <div className={cn(
                        "text-xs font-medium px-2 py-0.5 rounded-full",
                        rec.yoy_inflation_pct > 0 ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" : "bg-green-100 text-green-600"
                      )}>
                        {rec.yoy_inflation_pct > 0 ? "+" : ""}{rec.yoy_inflation_pct.toFixed(1)}% YoY
                      </div>
                    )}
                    {rec.source_url && (
                      <a href={rec.source_url} target="_blank" rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-foreground">
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
              <p className="text-[11px] text-muted-foreground pt-2">
                Combined CPI (Rural + Urban), Base 2012=100. All values from official MoSPI press releases.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Estimated CPI Contribution */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="text-lg font-semibold mb-1">Estimated Airfare Contribution to CPI</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
          <div className="rounded-xl bg-secondary/50 p-5 text-center">
            <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Airfare Inflation (Computed)</div>
            <div className="text-3xl font-bold text-violet-600">
              {airfareYoY != null ? `${airfareYoY > 0 ? "+" : ""}${airfareYoY.toFixed(1)}%` : "Insufficient data"}
            </div>
          </div>
          <div className="rounded-xl bg-secondary/50 p-5 text-center">
            <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">CPI Transport Weight (Official)</div>
            <div className="text-3xl font-bold text-blue-600">8.59%</div>
            <div className="text-xs text-muted-foreground mt-1">NSO CPI Basket, Base 2012=100</div>
          </div>
          <div className="rounded-xl bg-secondary/50 p-5 text-center">
            <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Est. Contribution (Mode A)</div>
            <div className="text-3xl font-bold text-teal-600">
              {estimatedContribution != null
                ? `${estimatedContribution > 0 ? "+" : ""}${estimatedContribution.toFixed(2)} pp`
                : "Calculation unavailable — required official data/weight not available."}
            </div>
          </div>
        </div>
        <div className="mt-4 text-xs text-muted-foreground border-t border-border pt-3">
          <strong>Disclaimer:</strong> This is an analytical estimate based on Mode A methodology (Airfare inflation × official CPI
          Transport &amp; Communication weight). It is <strong>not</strong> an official Government of India CPI contribution figure.
          The NSO CPI basket does not publish a separate national weight for domestic air transport specifically.
          Official weight source:{" "}
          <a href="https://mospi.gov.in/sites/default/files/publication_reports/Technical_Note_CPI.pdf"
            target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
            NSO CPI Technical Notes
          </a>
        </div>
      </div>

      {/* Data Sources — All Booking Sites */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold">Data Sources</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              {totalObs.toLocaleString()} total observations across {sources.length} sources
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {/* Always show all known sources with their status */}
          {Object.entries(SOURCE_LABELS).map(([key, meta]) => {
            const stat = sources.find(s => s.source === key);
            return (
              <div key={key} className="flex items-center gap-3 p-3 rounded-xl border border-border/60 bg-secondary/20">
                <div className={cn("w-2.5 h-2.5 rounded-full shrink-0", meta.color)} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{meta.label}</div>
                  <div className="text-xs text-muted-foreground">
                    {stat ? `${stat.observation_count} obs · avg ₹${stat.avg_fare.toLocaleString()}` : "No data yet"}
                  </div>
                </div>
                <span className={cn(
                  "text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0",
                  meta.badge === "GOVT" ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
                    : meta.badge === "OTA" ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40"
                    : "bg-secondary text-muted-foreground"
                )}>
                  {meta.badge}
                </span>
              </div>
            );
          })}
        </div>
        <div className="mt-4 text-xs text-muted-foreground">
          <span className="font-semibold">OTA</span> = Online Travel Agency · <span className="font-semibold">GOVT</span> = Government of India owned airline ·
          <span className="font-semibold"> GDS</span> = Global Distribution System
        </div>
      </div>

      {/* Data Provenance Trail */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <button
          onClick={() => setShowProvenance(!showProvenance)}
          className="flex items-center justify-between w-full text-left"
        >
          <div>
            <h2 className="text-lg font-semibold">Data Provenance Trail</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              View calculation details — every displayed number is traceable
            </p>
          </div>
          {showProvenance ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
        </button>

        {showProvenance && (
          <div className="mt-4 space-y-3 text-sm">
            <div className="p-4 rounded-xl bg-secondary/40 space-y-2">
              <div className="font-semibold text-base">Index Calculation Chain</div>
              <div className="space-y-1 text-muted-foreground text-xs">
                <div>1. <strong className="text-foreground">Raw Observations</strong> → collected from 8 sources via scrape.do + Amadeus + Google Flights</div>
                <div>2. <strong className="text-foreground">Validation</strong> → fare range ₹800–₹1,50,000, advance purchase T+7 to T+30</div>
                <div>3. <strong className="text-foreground">Deduplication</strong> → same route/date/airline/fare within 1hr</div>
                <div>4. <strong className="text-foreground">Outlier Detection</strong> → Z-score &gt; 3.0 flagged (not deleted)</div>
                <div>5. <strong className="text-foreground">Route Weights</strong> → 12 major routes, weights from DGCA traffic data</div>
                <div>6. <strong className="text-foreground">Laspeyres Index</strong> → weighted average relative to base period ({indexData?.base_period ?? "2025-01"} = 100)</div>
                <div>7. <strong className="text-foreground">Calculation Run ID</strong>: <code className="text-xs">{indexData?.calculation_run_id ?? "Run index/calculate to generate"}</code></div>
              </div>
            </div>
            <div className="p-4 rounded-xl bg-secondary/40 space-y-2">
              <div className="font-semibold text-base">Official CPI Data Provenance</div>
              <div className="space-y-1 text-muted-foreground text-xs">
                <div>Source: <strong className="text-foreground">Ministry of Statistics & Programme Implementation (MoSPI), Government of India</strong></div>
                <div>Dataset: Consumer Price Index — Combined (Rural+Urban), Base Year 2012=100</div>
                <div>Data via: Official MoSPI press releases + data.gov.in CKAN API (attempted on startup)</div>
                <div>Website: <a href="https://mospi.gov.in" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">mospi.gov.in</a></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
