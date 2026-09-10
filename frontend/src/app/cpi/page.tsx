"use client";

import { useEffect, useState } from "react";
import { ExternalLink, RefreshCw, ShieldCheck, Info } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CPIRecord {
  period: string;
  value: number;
  yoy_inflation_pct?: number | null;
  source?: string;
  source_url?: string;
  publication_date?: string;
  notes?: string;
}

interface WeightCategory {
  weight_percent: number;
  sub_categories?: Record<string, string>;
  source?: string;
  source_url?: string;
}

export default function CPIPage() {
  const [cpiData, setCpiData] = useState<{ latest: CPIRecord | null; records: CPIRecord[]; disclaimer?: string }>({ latest: null, records: [] });
  const [weights, setWeights] = useState<{ transport_weight_percent?: number; source?: string; note?: string }>({});
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [cpiRes, wRes] = await Promise.allSettled([
        fetch(`${API}/api/v1/cpi/government?limit=36`).then(r => r.json()),
        fetch(`${API}/api/v1/cpi/weights`).then(r => r.json()),
      ]);
      if (cpiRes.status === "fulfilled") setCpiData(cpiRes.value);
      if (wRes.status === "fulfilled") setWeights(wRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const allRecords = [...(cpiData.records || [])].reverse();

  return (
    <div className="space-y-8 p-6 max-w-5xl mx-auto">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="h-5 w-5 text-blue-600" />
            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">Official Government Data</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Government CPI Data</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Official Consumer Price Index data from the Ministry of Statistics &amp; Programme Implementation (MoSPI), Government of India
          </p>
        </div>
        <button onClick={fetchData} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-sm font-medium hover:bg-secondary transition disabled:opacity-50">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Official Source Info */}
      <div className="rounded-2xl border border-blue-200 bg-blue-50 dark:bg-blue-950/30 dark:border-blue-800 p-5">
        <div className="font-semibold text-blue-800 dark:text-blue-300 mb-2">Official Data Source</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          {[
            { label: "Publisher", value: "MoSPI / NSO, Government of India" },
            { label: "Dataset", value: "Consumer Price Index — Combined" },
            { label: "Base Year", value: "2012 = 100" },
            { label: "Coverage", value: "Rural + Urban (Combined)" },
          ].map(item => (
            <div key={item.label}>
              <div className="text-xs text-muted-foreground mb-0.5">{item.label}</div>
              <div className="font-medium text-blue-800 dark:text-blue-200">{item.value}</div>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center gap-3 text-sm">
          <a href="https://mospi.gov.in" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-blue-600 hover:underline">
            <ExternalLink className="h-4 w-4" />
            mospi.gov.in
          </a>
          <a href="https://data.gov.in" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-blue-600 hover:underline">
            <ExternalLink className="h-4 w-4" />
            data.gov.in
          </a>
        </div>
      </div>

      {/* Latest CPI Card */}
      {cpiData.latest && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="col-span-2 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-700 p-6 text-white">
            <div className="text-xs text-white/70 mb-1 uppercase">Latest Official CPI</div>
            <div className="text-5xl font-bold mb-1">{cpiData.latest.value.toFixed(1)}</div>
            <div className="text-sm text-white/80">Period: {cpiData.latest.period} · Base 2012=100</div>
            {cpiData.latest.yoy_inflation_pct != null && (
              <div className={`mt-2 text-lg font-semibold ${cpiData.latest.yoy_inflation_pct > 0 ? "text-orange-300" : "text-green-300"}`}>
                {cpiData.latest.yoy_inflation_pct > 0 ? "+" : ""}{cpiData.latest.yoy_inflation_pct.toFixed(2)}% YoY Inflation
              </div>
            )}
          </div>
          <div className="rounded-2xl bg-gradient-to-br from-teal-600 to-emerald-700 p-6 text-white">
            <div className="text-xs text-white/70 mb-1 uppercase">Transport Weight</div>
            <div className="text-4xl font-bold mb-1">{weights.transport_weight_percent?.toFixed(2) ?? "8.59"}%</div>
            <div className="text-xs text-white/60">In CPI basket</div>
          </div>
          <div className="rounded-2xl bg-gradient-to-br from-violet-600 to-purple-700 p-6 text-white">
            <div className="text-xs text-white/70 mb-1 uppercase">Data Points</div>
            <div className="text-4xl font-bold mb-1">{cpiData.records.length}</div>
            <div className="text-xs text-white/60">Official monthly records</div>
          </div>
        </div>
      )}

      {/* CPI Data Table */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="text-lg font-semibold mb-4">Monthly CPI Data</h2>
        {allRecords.length === 0 ? (
          <div className="flex items-center gap-2 text-muted-foreground py-8 justify-center">
            <Info className="h-5 w-5" />
            Government CPI data unavailable
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted-foreground border-b border-border">
                  <th className="text-left py-3 pr-4">Period</th>
                  <th className="text-right py-3 pr-4">CPI Value</th>
                  <th className="text-right py-3 pr-4">YoY Inflation</th>
                  <th className="text-right py-3 pr-4">Publication</th>
                  <th className="text-right py-3">Source</th>
                </tr>
              </thead>
              <tbody>
                {allRecords.map((rec) => (
                  <tr key={rec.period} className="border-b border-border/50 hover:bg-secondary/30 transition">
                    <td className="py-3 pr-4 font-medium">{rec.period}</td>
                    <td className="py-3 pr-4 text-right font-bold text-blue-600">{rec.value.toFixed(1)}</td>
                    <td className={`py-3 pr-4 text-right text-xs font-semibold ${
                      rec.yoy_inflation_pct == null ? "text-muted-foreground"
                        : rec.yoy_inflation_pct > 6 ? "text-red-600"
                        : rec.yoy_inflation_pct > 4 ? "text-orange-500"
                        : "text-emerald-600"
                    }`}>
                      {rec.yoy_inflation_pct != null
                        ? `${rec.yoy_inflation_pct > 0 ? "+" : ""}${rec.yoy_inflation_pct.toFixed(2)}%`
                        : "—"}
                    </td>
                    <td className="py-3 pr-4 text-right text-xs text-muted-foreground">
                      {rec.publication_date ?? "—"}
                    </td>
                    <td className="py-3 text-right">
                      {rec.source_url ? (
                        <a href={rec.source_url} target="_blank" rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-blue-500 hover:underline">
                          MoSPI <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <span className="text-xs text-muted-foreground">MoSPI/NSO</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="text-xs text-muted-foreground mt-4 pt-3 border-t border-border">
          {cpiData.disclaimer ?? "All values are from official MoSPI press releases. This data is NOT produced by the FLARE system."}
        </p>
      </div>

      {/* Transport Weight Card */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="text-lg font-semibold mb-2">CPI Transport &amp; Communication Weight</h2>
        <p className="text-sm text-muted-foreground mb-4">Used for estimated airfare contribution calculation (Mode A)</p>
        <div className="flex items-center gap-6 flex-wrap">
          <div>
            <div className="text-xs text-muted-foreground mb-1">Official Weight</div>
            <div className="text-3xl font-bold text-teal-600">8.59%</div>
          </div>
          <div className="flex-1 min-w-60">
            <div className="text-xs text-muted-foreground mb-1">Note</div>
            <div className="text-sm">{weights.note ?? "NSO CPI basket does not publish a separate national weight for domestic air transport. The 8.59% Transport & Communication weight is the closest official category."}</div>
          </div>
        </div>
        <a href="https://mospi.gov.in/sites/default/files/publication_reports/Technical_Note_CPI.pdf"
          target="_blank" rel="noopener noreferrer"
          className="mt-4 inline-flex items-center gap-1.5 text-sm text-blue-600 hover:underline">
          <ExternalLink className="h-4 w-4" />
          NSO CPI Technical Notes (official source)
        </a>
      </div>
    </div>
  );
}
