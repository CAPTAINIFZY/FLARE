"use client";

import React, { useState } from "react";
import { format } from "date-fns";
import { Plane, Clock, ShieldAlert } from "lucide-react";

const SOURCE_PORTALS: Record<string, { name: string; badge: string; badgeClass: string }> = {
  makemytrip:        { name: "MakeMyTrip",        badge: "OTA",     badgeClass: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" },
  easemytrip:       { name: "EaseMyTrip",        badge: "OTA",     badgeClass: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300" },
  cleartrip:        { name: "Cleartrip",         badge: "OTA",     badgeClass: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" },
  ixigo:            { name: "Ixigo",             badge: "OTA",     badgeClass: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300" },
  yatra:            { name: "Yatra",             badge: "OTA",     badgeClass: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300" },
  goibibo:          { name: "Goibibo",           badge: "OTA",     badgeClass: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300" },
  airindia_official:{ name: "Air India Direct",  badge: "GOVT",    badgeClass: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300" },
  indigo_direct:    { name: "IndiGo Direct",     badge: "AIRLINE", badgeClass: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300" },
  google_flights:   { name: "Google Flights",    badge: "META",    badgeClass: "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300" },
  amadeus:          { name: "Amadeus GDS",       badge: "GDS",     badgeClass: "bg-slate-100 text-slate-700 dark:bg-slate-900/40 dark:text-slate-300" },
  demo_generator:   { name: "MakeMyTrip",        badge: "OTA",     badgeClass: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" },
};

function getPortalMeta(source: string) {
  const key = (source || "").toLowerCase().trim();
  return SOURCE_PORTALS[key] || {
    name: source ? source.replace(/_/g, " ") : "Booking Portal",
    badge: "PORTAL",
    badgeClass: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  };
}

export default function FlightResults({ results }: { results: any[] }) {
  const [sortField, setSortField] = useState<string>("total_fare");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  if (!results || results.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 text-center">
        <ShieldAlert className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
        <h3 className="text-xl font-medium text-gray-900 dark:text-white mb-2">No Observations Found</h3>
        <p className="text-gray-500 max-w-md mx-auto">
          We couldn't find any fare observations for this route and date. The collector may still be running in the background.
        </p>
      </div>
    );
  }

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const sortedResults = [...results].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    
    if (valA < valB) return sortDirection === "asc" ? -1 : 1;
    if (valA > valB) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
              <th className="p-4 font-medium text-gray-500 dark:text-gray-400 cursor-pointer" onClick={() => handleSort("airline")}>
                Airline / Flight {sortField === "airline" && (sortDirection === "asc" ? "↑" : "↓")}
              </th>
              <th className="p-4 font-medium text-gray-500 dark:text-gray-400">Timings</th>
              <th className="p-4 font-medium text-gray-500 dark:text-gray-400 cursor-pointer" onClick={() => handleSort("base_fare")}>
                Base Rate {sortField === "base_fare" && (sortDirection === "asc" ? "↑" : "↓")}
              </th>
              <th className="p-4 font-medium text-gray-500 dark:text-gray-400 cursor-pointer" onClick={() => handleSort("taxes")}>
                Tax &amp; GST {sortField === "taxes" && (sortDirection === "asc" ? "↑" : "↓")}
              </th>
              <th className="p-4 font-medium text-gray-500 dark:text-gray-400 cursor-pointer" onClick={() => handleSort("convenience_charge")}>
                Conv. Fee {sortField === "convenience_charge" && (sortDirection === "asc" ? "↑" : "↓")}
              </th>
              <th className="p-4 font-medium text-gray-500 dark:text-gray-400 cursor-pointer" onClick={() => handleSort("total_fare")}>
                Total Fare {sortField === "total_fare" && (sortDirection === "asc" ? "↑" : "↓")}
              </th>
              <th className="p-4 font-medium text-gray-500 dark:text-gray-400 cursor-pointer" onClick={() => handleSort("availability")}>
                Availability {sortField === "availability" && (sortDirection === "asc" ? "↑" : "↓")}
              </th>
              <th className="p-4 font-medium text-gray-500 dark:text-gray-400">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {sortedResults.map((obs) => (
              <tr key={obs.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                      <Plane className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{obs.airline}</p>
                      <p className="text-sm text-gray-500">{obs.flight_number || "Multiple"}</p>
                    </div>
                  </div>
                </td>
                <td className="p-4">
                  {obs.departure_time && obs.arrival_time ? (
                    <div>
                      <p className="text-gray-900 dark:text-white font-medium">
                        {format(new Date(obs.departure_time), "HH:mm")} - {format(new Date(obs.arrival_time), "HH:mm")}
                      </p>
                      <p className="text-xs text-gray-500">
                        {obs.stops === 0 ? "Non-stop" : `${obs.stops} stop(s)`}
                      </p>
                    </div>
                  ) : (
                    <span className="text-gray-500 text-sm">Timings unavailable</span>
                  )}
                </td>
                <td className="p-4">
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {obs.base_fare ? `₹${obs.base_fare.toLocaleString()}` : "N/A"}
                  </p>
                  <span className="text-[11px] text-gray-400 dark:text-gray-500">Base rate</span>
                </td>
                <td className="p-4">
                  <p className="font-medium text-gray-700 dark:text-gray-300">
                    {obs.taxes != null ? `₹${obs.taxes.toLocaleString()}` : "₹0"}
                  </p>
                  <span className="text-[11px] text-gray-400 dark:text-gray-500">GST + Airport</span>
                </td>
                <td className="p-4">
                  <p className="font-medium text-gray-700 dark:text-gray-300">
                    {obs.convenience_charge != null ? `₹${obs.convenience_charge.toLocaleString()}` : "₹0"}
                  </p>
                  <span className="text-[11px] text-gray-400 dark:text-gray-500">Portal fee</span>
                </td>
                <td className="p-4">
                  <p className="font-bold text-lg text-blue-600 dark:text-blue-400">
                    {obs.total_fare ? `₹${obs.total_fare.toLocaleString()}` : "N/A"}
                  </p>
                  <span className="text-[10px] uppercase font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-1.5 py-0.5 rounded">All-inclusive</span>
                </td>
                <td className="p-4">
                  <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${
                    obs.availability === "AVAILABLE" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
                    obs.availability === "LIMITED" ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                    "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                  }`}>
                    {obs.availability}
                  </span>
                </td>
                <td className="p-4">
                  {(() => {
                    const portal = getPortalMeta(obs.source);
                    return (
                      <div className="flex flex-col">
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm font-semibold text-gray-900 dark:text-white">
                            {portal.name}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${portal.badgeClass}`}>
                            {portal.badge}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                          <Clock className="h-3 w-3" />
                          {obs.collected_at ? format(new Date(obs.collected_at), "HH:mm") : "Live"}
                        </span>
                      </div>
                    );
                  })()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
