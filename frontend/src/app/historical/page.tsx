"use client";

import { useState } from "react";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Filter, Download } from "lucide-react";

// Mock Data for demonstration
const thirtyDayTrend = Array.from({ length: 30 }).map((_, i) => {
  const base = 4800 + Math.sin(i / 3) * 500;
  return {
    day: `Sep ${i + 1}`,
    IndiGo: Math.round(base * 0.95),
    "Air India": Math.round(base * 1.15),
    SpiceJet: Math.round(base * 0.9),
  };
});

const seasonalityData = [
  { name: 'Mon', avgFare: 4800 },
  { name: 'Tue', avgFare: 4500 },
  { name: 'Wed', avgFare: 4600 },
  { name: 'Thu', avgFare: 4900 },
  { name: 'Fri', avgFare: 5500 },
  { name: 'Sat', avgFare: 5800 },
  { name: 'Sun', avgFare: 5400 },
];

export default function HistoricalAnalysis() {
  const [route, setRoute] = useState("DEL-BOM");

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Historical Analysis</h1>
          <p className="text-muted-foreground mt-1">Analyze airfare trends over time for specific routes</p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-3">
          <button className="flex items-center px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </button>
          <button className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <select 
          className="bg-card border border-border rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary outline-none"
          value={route}
          onChange={(e) => setRoute(e.target.value)}
        >
          <option value="DEL-BOM">DEL-BOM (Delhi to Mumbai)</option>
          <option value="DEL-BLR">DEL-BLR (Delhi to Bangalore)</option>
          <option value="BOM-BLR">BOM-BLR (Mumbai to Bangalore)</option>
        </select>
        
        <select className="bg-card border border-border rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary outline-none">
          <option>Advance Purchase: 15 Days</option>
          <option>Advance Purchase: 30 Days</option>
          <option>Advance Purchase: 7 Days</option>
        </select>

        <select className="bg-card border border-border rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary outline-none">
          <option>Last 30 Days</option>
          <option>Last 3 Months</option>
          <option>Year to Date</option>
        </select>
      </div>

      {/* Main Historical Trend Chart */}
      <div className="glass-card rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-6">30-Day Airfare Trend ({route})</h2>
        <div className="h-96 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={thirtyDayTrend} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorIndiGo" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorAI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis dataKey="day" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} domain={['dataMin - 500', 'dataMax + 500']} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px' }}
                itemStyle={{ color: '#f8fafc' }}
              />
              <Legend />
              <Area type="monotone" dataKey="IndiGo" stroke="#3b82f6" fillOpacity={1} fill="url(#colorIndiGo)" />
              <Area type="monotone" dataKey="Air India" stroke="#ef4444" fillOpacity={1} fill="url(#colorAI)" />
              <Area type="monotone" dataKey="SpiceJet" stroke="#f59e0b" fillOpacity={0} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Seasonality and Volatility */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-6">Day of Week Seasonality</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={seasonalityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} domain={[3000, 7000]} />
                <Tooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Bar dataKey="avgFare" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Historical Insights</h2>
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
              <p className="font-medium text-primary">Highest Volatility Period</p>
              <p className="text-sm text-foreground mt-1">Historically, fares on {route} show the highest intraday volatility on Fridays between 14:00 and 18:00 IST.</p>
            </div>
            <div className="p-4 rounded-lg bg-warning/10 border border-warning/20">
              <p className="font-medium text-warning">Festival Anomaly</p>
              <p className="text-sm text-foreground mt-1">Fares spike by an average of 42% exactly 14 days prior to Diwali compared to the monthly median.</p>
            </div>
            <div className="p-4 rounded-lg bg-success/10 border border-success/20">
              <p className="font-medium text-success">Optimal Booking Window</p>
              <p className="text-sm text-foreground mt-1">For {route}, the historical price floor occurs consistently between T-21 and T-28 days before departure.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
