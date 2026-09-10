"use client";

import React, { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from "recharts";

export default function AnalyticsTabs({ results }: { results: any[] }) {
  const [activeTab, setActiveTab] = useState<"comparison" | "breakdown" | "distribution">("comparison");

  if (!results || results.length === 0) return null;

  // Process data for charts
  const airlineData: Record<string, { airline: string; minFare: number; count: number; totalFare: number }> = {};
  
  results.forEach(obs => {
    if (!obs.total_fare || obs.availability === "UNAVAILABLE") return;
    
    if (!airlineData[obs.airline]) {
      airlineData[obs.airline] = { airline: obs.airline, minFare: obs.total_fare, count: 1, totalFare: obs.total_fare };
    } else {
      airlineData[obs.airline].count++;
      airlineData[obs.airline].totalFare += obs.total_fare;
      if (obs.total_fare < airlineData[obs.airline].minFare) {
        airlineData[obs.airline].minFare = obs.total_fare;
      }
    }
  });

  const chartData = Object.values(airlineData).map(d => ({
    ...d,
    avgFare: Math.round(d.totalFare / d.count)
  })).sort((a, b) => a.avgFare - b.avgFare);

  const breakdownData = Object.values(
    results.reduce((acc, obs) => {
      if (!obs.total_fare || obs.availability === "UNAVAILABLE") return acc;
      const airline = obs.airline;
      if (!acc[airline]) {
        acc[airline] = { airline, baseFare: 0, taxes: 0, convFee: 0, count: 0 };
      }
      acc[airline].baseFare += obs.base_fare || Math.round(obs.total_fare * 0.82);
      acc[airline].taxes += obs.taxes || Math.round(obs.total_fare * 0.15);
      acc[airline].convFee += obs.convenience_charge != null ? obs.convenience_charge : 300;
      acc[airline].count++;
      return acc;
    }, {} as Record<string, any>)
  ).map((d: any) => ({
    airline: d.airline,
    "Base Rate": Math.round(d.baseFare / d.count),
    "Taxes & GST": Math.round(d.taxes / d.count),
    "Convenience Fee": Math.round(d.convFee / d.count),
  }));

  const colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#ec4899"];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
      <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
        <button
          className={`pb-3 px-4 font-medium text-sm transition-colors relative ${
            activeTab === "comparison" ? "text-blue-600 dark:text-blue-400" : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          }`}
          onClick={() => setActiveTab("comparison")}
        >
          Airline Comparison
          {activeTab === "comparison" && (
            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 dark:bg-blue-400 rounded-t-full"></span>
          )}
        </button>
        <button
          className={`pb-3 px-4 font-medium text-sm transition-colors relative ${
            activeTab === "breakdown" ? "text-blue-600 dark:text-blue-400" : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          }`}
          onClick={() => setActiveTab("breakdown")}
        >
          Fare Component Breakdown
          {activeTab === "breakdown" && (
            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 dark:bg-blue-400 rounded-t-full"></span>
          )}
        </button>
        <button
          className={`pb-3 px-4 font-medium text-sm transition-colors relative ${
            activeTab === "distribution" ? "text-blue-600 dark:text-blue-400" : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          }`}
          onClick={() => setActiveTab("distribution")}
        >
          Data Provenance
          {activeTab === "distribution" && (
            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 dark:bg-blue-400 rounded-t-full"></span>
          )}
        </button>
      </div>

      {activeTab === "comparison" && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Average vs Minimum Fare by Airline</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" opacity={0.2} />
                <XAxis dataKey="airline" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} tickFormatter={(val) => `₹${val}`} />
                <RechartsTooltip 
                  formatter={(value: any) => [`₹${value}`, "Fare"]}
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="avgFare" name="Average Fare" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Bar>
                <Bar dataKey="minFare" name="Minimum Fare" fill="#9ca3af" opacity={0.5} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === "breakdown" && (
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Fare Component Breakdown</h3>
              <p className="text-xs text-gray-500">Average Base Rate, Taxes &amp; GST, and Convenience Fees per airline</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium text-gray-600 dark:text-gray-300">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-blue-500"></span> Base Rate</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-emerald-500"></span> Taxes &amp; GST</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded bg-amber-500"></span> Conv. Fee</span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdownData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" opacity={0.2} />
                <XAxis dataKey="airline" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} tickFormatter={(val) => `₹${val}`} />
                <RechartsTooltip 
                  formatter={(value: any, name: any) => [`₹${Number(value).toLocaleString()}`, name]}
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="Base Rate" stackId="a" fill="#3b82f6" />
                <Bar dataKey="Taxes & GST" stackId="a" fill="#10b981" />
                <Bar dataKey="Convenience Fee" stackId="a" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      
      {activeTab === "distribution" && (
        <div className="flex flex-col md:flex-row gap-6">
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Observation Sources</h3>
            <div className="space-y-4">
              {Object.entries(
                results.reduce((acc, curr) => {
                  acc[curr.source] = (acc[curr.source] || 0) + 1;
                  return acc;
                }, {} as Record<string, number>)
              ).map(([source, count], idx) => (
                <div key={source} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <span className="capitalize font-medium text-gray-700 dark:text-gray-300">{source}</span>
                  <span className="bg-white dark:bg-gray-800 px-3 py-1 rounded text-sm font-semibold">{count as React.ReactNode}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Availability Status</h3>
            <div className="space-y-4">
              {Object.entries(
                results.reduce((acc, curr) => {
                  acc[curr.availability] = (acc[curr.availability] || 0) + 1;
                  return acc;
                }, {} as Record<string, number>)
              ).map(([status, count], idx) => (
                <div key={status} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <span className={`font-medium ${
                    status === 'AVAILABLE' ? 'text-green-600 dark:text-green-400' :
                    status === 'LIMITED' ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {status}
                  </span>
                  <span className="bg-white dark:bg-gray-800 px-3 py-1 rounded text-sm font-semibold">{count as React.ReactNode}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
