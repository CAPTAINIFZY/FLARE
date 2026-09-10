"use client";

import { useEffect, useState, useCallback } from "react";
import { ArrowUpRight, ArrowDownRight, Minus, RefreshCw, Plane, Radio, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Source metadata for display
const SOURCE_META: Record<string, { label: string; badge: string; color: string; badgeClass: string }> = {
  makemytrip:        { label: "MakeMyTrip",       badge: "OTA",    color: "bg-orange-500",  badgeClass: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" },
  cleartrip:         { label: "Cleartrip",         badge: "OTA",    color: "bg-blue-500",    badgeClass: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" },
  ixigo:             { label: "Ixigo",             badge: "OTA",    color: "bg-purple-500",  badgeClass: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300" },
  yatra:             { label: "Yatra",             badge: "OTA",    color: "bg-teal-500",    badgeClass: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300" },
  goibibo:           { label: "Goibibo",           badge: "OTA",    color: "bg-red-500",     badgeClass: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300" },
  easemytrip:        { label: "EaseMyTrip",        badge: "OTA",    color: "bg-green-600",   badgeClass: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" },
  airindia_official: { label: "Air India (GoI)",   badge: "GOVT",   color: "bg-amber-600",   badgeClass: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300" },
  indigo_direct:     { label: "IndiGo Direct",     badge: "AIRLINE",color: "bg-indigo-600",  badgeClass: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300" },
  google_flights:    { label: "Google Flights",    badge: "META",   color: "bg-sky-500",     badgeClass: "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300" },
  amadeus:           { label: "Amadeus GDS",       badge: "GDS",    color: "bg-slate-500",   badgeClass: "bg-slate-100 text-slate-700 dark:bg-slate-900/40" },
  demo_generator:    { label: "Demo Data",         badge: "DEMO",   color: "bg-gray-400",    badgeClass: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400" },
};

function getSourceMeta(source: string) {
  return SOURCE_META[source] ?? { label: source, badge: "OTHER", color: "bg-gray-400", badgeClass: "bg-gray-100 text-gray-600" };
}

interface FareRow {
  id: number;
  route: string;
  origin: string;
  destination: string;
  airline: string;
  total_fare: number;
  source: string;
  source_type: string;
  data_status: string;
  observation_timestamp: string;
  travel_date: string;
  stops: number;
  advance_purchase_days: number;
}

export default function LiveAirfares() {
  const [fares, setFares] = useState<FareRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  const fetchFares = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/fares/live?limit=50`);
      if (res.ok) {
        const data = await res.json();
        // Handle both array and object response
        const rows = Array.isArray(data) ? data : (data.fares || data.results || []);
        setFares(rows);
        setLastUpdate(new Date());
      }
    } catch (e) {
      // silent — keep existing data
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFares();
    const interval = setInterval(fetchFares, 30_000); // poll every 30s
    return () => clearInterval(interval);
  }, [fetchFares]);

  // Trigger a live collection for DEL→BOM (today +8d) across all sources
  const triggerCollection = async () => {
    setTriggering(true);
    setTriggerMsg("Triggering live collection across all sources with scrape.do API...");
    try {
      const travelDate = new Date();
      travelDate.setDate(travelDate.getDate() + 8);
      const dateStr = travelDate.toISOString().split("T")[0];
      
      const res = await fetch(
        `${API}/api/v1/fares/trigger-collection?origin=DEL&destination=BOM&travel_date=${dateStr}`,
        { method: "POST" }
      );
      if (res.ok) {
        setTriggerMsg("Live collection in progress via scrape.do API. Observations updating shortly...");
        setTimeout(fetchFares, 3000);
        setTimeout(fetchFares, 8000);
        setTimeout(() => {
          fetchFares();
          setTriggerMsg(null);
        }, 15000);
      } else {
        await fetch(
          `${API}/api/v1/search/?origin=DEL&destination=BOM&travel_date=${dateStr}&trigger_live=true`
        );
        setTriggerMsg("Collection request sent. Observations updating...");
        setTimeout(() => {
          fetchFares();
          setTriggerMsg(null);
        }, 8000);
      }
    } catch {
      setTriggerMsg("Could not reach backend. Please ensure the backend server is running on port 8000.");
      setTimeout(() => setTriggerMsg(null), 5000);
    } finally {
      setTriggering(false);
    }
  };

  // Unique sources found in data
  const availableSources = Array.from(new Set(fares.map(f => f.source)));

  // Filtered fares
  const filtered = fares.filter(f => {
    const statusOk = filter === "all" || f.data_status === filter;
    const srcOk = sourceFilter === "all" || f.source === sourceFilter;
    return statusOk && srcOk;
  });

  const timeAgo = (ts: string) => {
    const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs font-bold text-green-600 uppercase tracking-wider">Live Feed</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Live Airfares</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Real-time observations from all booking sources · Refreshes every 30s
            {lastUpdate && ` · Last updated: ${lastUpdate.toLocaleTimeString()}`}
          </p>
        </div>
        <div className="flex gap-2">
          {/* Trigger collection button */}
          <button
            onClick={triggerCollection}
            disabled={triggering}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium transition disabled:opacity-50"
          >
            <Zap className={cn("h-4 w-4", triggering && "animate-pulse")} />
            {triggering ? "Triggering..." : "Trigger Collection"}
          </button>
          <button
            onClick={fetchFares}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-secondary transition disabled:opacity-50"
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      {/* Trigger message */}
      {triggerMsg && (
        <div className="rounded-lg border border-violet-200 bg-violet-50 dark:bg-violet-950/30 dark:border-violet-700 px-4 py-3 text-sm text-violet-700 dark:text-violet-300">
          <Zap className="inline h-4 w-4 mr-1.5" />
          {triggerMsg}
        </div>
      )}

      {/* Source filter chips */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSourceFilter("all")}
          className={cn("px-3 py-1.5 rounded-full text-xs font-medium transition",
            sourceFilter === "all" ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground hover:bg-secondary/80"
          )}>
          All Sources
        </button>
        {Object.entries(SOURCE_META).map(([key, meta]) => (
          <button
            key={key}
            onClick={() => setSourceFilter(sourceFilter === key ? "all" : key)}
            className={cn("px-3 py-1.5 rounded-full text-xs font-medium transition flex items-center gap-1.5",
              sourceFilter === key ? `${meta.badgeClass} ring-2 ring-offset-1` : "bg-secondary text-muted-foreground hover:bg-secondary/80"
            )}>
            <div className={cn("w-1.5 h-1.5 rounded-full", meta.color)} />
            {meta.label}
            <span className="opacity-60 text-[10px]">{meta.badge}</span>
          </button>
        ))}
      </div>

      {/* Status filters */}
      <div className="flex gap-2">
        {["all", "LIVE", "DEMO"].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={cn("px-3 py-1.5 rounded-lg text-xs font-medium transition",
              filter === f ? "bg-primary text-primary-foreground" : "border border-border text-muted-foreground hover:bg-secondary"
            )}>
            {f === "all" ? "All Status" : f}
          </button>
        ))}
      </div>

      {/* Fares table */}
      <div className="rounded-2xl border border-border bg-card overflow-hidden">
        {loading && fares.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-muted-foreground">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" /> Loading live fares...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-56 text-muted-foreground gap-3 p-6">
            <Radio className="h-10 w-10 opacity-30" />
            <div className="text-sm font-medium">
              {sourceFilter !== "all"
                ? `No observations for ${getSourceMeta(sourceFilter).label} in current view`
                : "No observations in feed yet"}
            </div>
            <div className="text-xs text-center max-w-sm text-muted-foreground">
              {sourceFilter !== "all" ? (
                <span>
                  Switch to{" "}
                  <button onClick={() => setSourceFilter("all")} className="font-semibold text-primary underline">
                    All Sources
                  </button>{" "}
                  to view available live & demo fares, or click{" "}
                  <span className="font-semibold text-violet-600">Trigger Collection</span> to run scrapers via scrape.do.
                </span>
              ) : (
                <span>
                  Click <span className="font-semibold text-violet-600">Trigger Collection</span> above to scrape
                  all booking sources via scrape.do.
                </span>
              )}
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted-foreground border-b border-border bg-secondary/30">
                  <th className="text-left px-4 py-3">Route</th>
                  <th className="text-left px-4 py-3">Airline</th>
                  <th className="text-right px-4 py-3">Fare (₹)</th>
                  <th className="text-center px-4 py-3">Stops</th>
                  <th className="text-center px-4 py-3">Advance</th>
                  <th className="text-center px-4 py-3">Source</th>
                  <th className="text-center px-4 py-3">Status</th>
                  <th className="text-right px-4 py-3">Observed</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((fare) => {
                  const meta = getSourceMeta(fare.source);
                  return (
                    <tr key={fare.id} className="border-b border-border/50 hover:bg-secondary/20 transition">
                      <td className="px-4 py-3 font-semibold text-foreground">
                        {fare.origin ?? fare.route?.split("-")[0]}
                        <span className="text-muted-foreground mx-1">→</span>
                        {fare.destination ?? fare.route?.split("-")[1]}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                          <Plane className="h-3.5 w-3.5 shrink-0" />
                          {fare.airline}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-foreground">
                        ₹{fare.total_fare?.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-center text-xs text-muted-foreground">
                        {fare.stops === 0 ? "Direct" : `${fare.stops} stop`}
                      </td>
                      <td className="px-4 py-3 text-center text-xs text-muted-foreground">
                        {fare.advance_purchase_days != null ? `T+${fare.advance_purchase_days}d` : "—"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full", meta.badgeClass)}>
                          {meta.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={cn(
                          "text-[10px] font-bold px-2 py-0.5 rounded-full",
                          fare.data_status === "LIVE" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                            : fare.data_status === "DEMO" ? "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                            : "bg-red-100 text-red-600"
                        )}>
                          {fare.data_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-xs text-muted-foreground">
                        {fare.observation_timestamp ? timeAgo(fare.observation_timestamp) : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="px-4 py-3 border-t border-border text-xs text-muted-foreground flex items-center justify-between">
              <span>Showing {filtered.length} of {fares.length} observations</span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                Auto-refreshes every 30 seconds
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Source legend */}
      <div className="rounded-2xl border border-border bg-card p-4">
        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">Source Type Legend</div>
        <div className="flex flex-wrap gap-3 text-xs">
          {[
            { badge: "OTA",    desc: "Online Travel Agency (MakeMyTrip, Cleartrip, Ixigo, Yatra, Goibibo, EaseMyTrip)" },
            { badge: "GOVT",   desc: "Government of India owned airline (Air India)" },
            { badge: "AIRLINE",desc: "Direct airline portal (IndiGo)" },
            { badge: "GDS",    desc: "Global Distribution System (Amadeus)" },
            { badge: "META",   desc: "Meta-search (Google Flights via Apify)" },
            { badge: "DEMO",   desc: "Synthetic demo data (when live sources unavailable)" },
          ].map(item => (
            <div key={item.badge} className="flex items-center gap-1.5">
              <span className="font-bold text-[10px] bg-secondary px-1.5 py-0.5 rounded">{item.badge}</span>
              <span className="text-muted-foreground">{item.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
