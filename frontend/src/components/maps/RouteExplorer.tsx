"use client";

import React, { useState, useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Plane, Navigation, ArrowRight, ArrowLeftRight, Search, MapPin, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

// Major Indian Airports with accurate coordinates
export interface AirportData {
  id: string;
  name: string;
  city: string;
  lat: number;
  lng: number;
}

const AIRPORTS: AirportData[] = [
  { id: "DEL", name: "Indira Gandhi International Airport", city: "Delhi", lat: 28.5562, lng: 77.1000 },
  { id: "TRV", name: "Trivandrum International Airport", city: "Thiruvananthapuram (Trivandrum)", lat: 8.4821, lng: 76.9200 },
  { id: "BOM", name: "Chhatrapati Shivaji Maharaj Int", city: "Mumbai", lat: 19.0896, lng: 72.8656 },
  { id: "BLR", name: "Kempegowda International Airport", city: "Bengaluru", lat: 13.1986, lng: 77.7066 },
  { id: "MAA", name: "Chennai International Airport", city: "Chennai", lat: 12.9941, lng: 80.1709 },
  { id: "CCU", name: "Netaji Subhas Chandra Bose Int", city: "Kolkata", lat: 22.6520, lng: 88.4463 },
  { id: "HYD", name: "Rajiv Gandhi International Airport", city: "Hyderabad", lat: 17.2403, lng: 78.4294 },
  { id: "COK", name: "Cochin International Airport", city: "Kochi", lat: 10.1518, lng: 76.3930 },
  { id: "AMD", name: "Sardar Vallabhbhai Patel Int", city: "Ahmedabad", lat: 23.0772, lng: 72.6347 },
  { id: "PNQ", name: "Pune Airport", city: "Pune", lat: 18.5822, lng: 73.9197 },
  { id: "GOI", name: "Manohar / Dabolim International", city: "Goa", lat: 15.3808, lng: 73.8314 },
  { id: "JAI", name: "Jaipur International Airport", city: "Jaipur", lat: 26.8242, lng: 75.8122 },
  { id: "GAU", name: "Lokpriya Gopinath Bordoloi Int", city: "Guwahati", lat: 26.1061, lng: 91.5859 },
];

// Helper to calculate great-circle distance (Haversine formula)
function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

// Estimate flight duration
function estimateFlightTime(distKm: number): string {
  const totalMinutes = Math.round((distKm / 680) * 60) + 30; // avg cruise speed + taxi/approach
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;
  return `${hours}h ${mins}m`;
}

// Estimate representative fare breakdown
function estimateFarePreview(distKm: number) {
  const basePricePerKm = 2.6 + (distKm / 1000) * 0.25;
  const baseRate = Math.round((distKm * basePricePerKm) / 50) * 50;
  const taxes = Math.round(baseRate * 0.18);
  const convFee = 250;
  const totalFare = baseRate + taxes + convFee;
  return { baseRate, taxes, convFee, totalFare };
}

// Function to create modern custom HTML DivIcons for Leaflet
function createAirportIcon(id: string, isOrigin: boolean, isDest: boolean) {
  let bgClass = "bg-slate-700 text-white border-white";
  let badgeClass = "bg-slate-800 text-slate-200 border-slate-600";
  let pulse = "";

  if (isOrigin) {
    bgClass = "bg-blue-600 text-white border-blue-200 shadow-blue-500/50";
    badgeClass = "bg-blue-700 text-white border-blue-400 font-bold";
    pulse = '<span class="absolute -inset-1 rounded-full bg-blue-400 opacity-60 animate-ping"></span>';
  } else if (isDest) {
    bgClass = "bg-emerald-600 text-white border-emerald-200 shadow-emerald-500/50";
    badgeClass = "bg-emerald-700 text-white border-emerald-400 font-bold";
    pulse = '<span class="absolute -inset-1 rounded-full bg-emerald-400 opacity-60 animate-ping"></span>';
  }

  const html = `
    <div class="relative flex items-center justify-center cursor-pointer group">
      ${pulse}
      <div class="relative w-8 h-8 rounded-full border-2 flex items-center justify-center shadow-lg transition-transform transform hover:scale-125 ${bgClass}">
        <span class="text-[10px] font-black tracking-tighter">${id}</span>
      </div>
    </div>
  `;

  return L.divIcon({
    html,
    className: "custom-leaflet-marker",
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
}

export default function RouteExplorer() {
  const router = useRouter();
  const [originId, setOriginId] = useState<string>("DEL");
  const [destinationId, setDestinationId] = useState<string>("TRV");

  const origin = useMemo(() => AIRPORTS.find((a) => a.id === originId) || AIRPORTS[0], [originId]);
  const destination = useMemo(() => AIRPORTS.find((a) => a.id === destinationId) || AIRPORTS[1], [destinationId]);

  const routeDistance = useMemo(() => {
    if (!origin || !destination || origin.id === destination.id) return 0;
    return calculateDistance(origin.lat, origin.lng, destination.lat, destination.lng);
  }, [origin, destination]);

  const fareEstimate = useMemo(() => {
    return estimateFarePreview(routeDistance);
  }, [routeDistance]);

  const swapAirports = () => {
    setOriginId(destinationId);
    setDestinationId(originId);
  };

  const handleAirportClick = (airport: AirportData) => {
    if (airport.id === originId) return;
    setDestinationId(airport.id);
  };

  const handleSearchRedirect = (orig = originId, dest = destinationId) => {
    router.push(`/search?origin=${orig}&destination=${dest}`);
  };

  // Other available destinations from origin for subtle background polyline mesh
  const secondaryRoutes = useMemo(() => {
    return AIRPORTS.filter((a) => a.id !== originId && a.id !== destinationId);
  }, [originId, destinationId]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-lg flex flex-col lg:flex-row h-[720px] relative z-0">
      {/* ── Left Sidebar Control Panel ── */}
      <div className="w-full lg:w-96 bg-gray-50/70 dark:bg-gray-900/60 p-5 border-r border-gray-200 dark:border-gray-700 flex flex-col h-full overflow-y-auto z-10">
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400">
            <Navigation className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">Route Network</h2>
            <p className="text-xs text-gray-500">Interactive corridor &amp; fare locator</p>
          </div>
        </div>

        {/* Airport Selectors */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm space-y-3 mb-4">
          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400 flex items-center gap-1.5 mb-1">
              <span className="w-2 h-2 rounded-full bg-blue-600"></span> Origin Airport
            </label>
            <select
              value={originId}
              onChange={(e) => setOriginId(e.target.value)}
              className="w-full p-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-medium focus:ring-2 focus:ring-blue-500 outline-none"
            >
              {AIRPORTS.map((a) => (
                <option key={`orig-${a.id}`} value={a.id}>
                  {a.city} ({a.id})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-center -my-1">
            <button
              onClick={swapAirports}
              title="Swap origin and destination"
              className="p-1.5 rounded-full border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-blue-900/30 text-gray-500 hover:text-blue-600 transition-colors"
            >
              <ArrowLeftRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 mb-1">
              <span className="w-2 h-2 rounded-full bg-emerald-600"></span> Destination Airport
            </label>
            <select
              value={destinationId}
              onChange={(e) => setDestinationId(e.target.value)}
              className="w-full p-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-medium focus:ring-2 focus:ring-emerald-500 outline-none"
            >
              {AIRPORTS.map((a) => (
                <option key={`dest-${a.id}`} value={a.id} disabled={a.id === originId}>
                  {a.city} ({a.id})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Selected Route Corridor Card */}
        {origin && destination && origin.id !== destination.id && (
          <div className="bg-gradient-to-br from-blue-50/70 via-white to-emerald-50/70 dark:from-gray-800 dark:via-gray-800 dark:to-gray-800/80 p-4 rounded-xl border border-blue-100 dark:border-blue-900/40 shadow-sm mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
                ACTIVE FLIGHT CORRIDOR
              </span>
              <span className="text-xs text-gray-500 font-medium">{estimateFlightTime(routeDistance)}</span>
            </div>

            <div className="flex items-center justify-between my-2">
              <div>
                <span className="text-2xl font-black text-gray-900 dark:text-white">{origin.id}</span>
                <p className="text-[11px] text-gray-500 truncate max-w-[100px]">{origin.city}</p>
              </div>
              <div className="flex-1 flex flex-col items-center px-2">
                <Plane className="h-4 w-4 text-blue-600 dark:text-blue-400 rotate-90" />
                <span className="text-[10px] text-gray-400 font-semibold">{routeDistance.toLocaleString()} km</span>
              </div>
              <div className="text-right">
                <span className="text-2xl font-black text-gray-900 dark:text-white">{destination.id}</span>
                <p className="text-[11px] text-gray-500 truncate max-w-[100px]">{destination.city}</p>
              </div>
            </div>

            {/* Estimated Fare Breakdown Preview */}
            <div className="mt-3 pt-3 border-t border-gray-200/70 dark:border-gray-700/60">
              <div className="flex justify-between items-baseline mb-1">
                <span className="text-xs text-gray-500">Typical All-Inclusive Fare:</span>
                <span className="text-base font-bold text-blue-600 dark:text-blue-400">
                  ₹{fareEstimate.totalFare.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400 bg-white/60 dark:bg-gray-900/40 px-2 py-1.5 rounded border border-gray-100 dark:border-gray-700">
                <span>Base: ₹{fareEstimate.baseRate.toLocaleString()}</span>
                <span>•</span>
                <span>Tax: ₹{fareEstimate.taxes.toLocaleString()}</span>
                <span>•</span>
                <span>Fee: ₹{fareEstimate.convFee}</span>
              </div>
            </div>

            {/* Action CTA Button */}
            <button
              onClick={() => handleSearchRedirect(origin.id, destination.id)}
              className="mt-3 w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-md hover:shadow-lg transition-all transform active:scale-95"
            >
              <Search className="h-4 w-4" />
              <span>Search Airfare ({origin.id} → {destination.id})</span>
            </button>
          </div>
        )}

        {/* Quick Pick Routes */}
        <div className="mt-auto">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-amber-500" /> Popular Routes
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {[
              { from: "DEL", to: "TRV", label: "Delhi ➔ Trivandrum" },
              { from: "DEL", to: "BOM", label: "Delhi ➔ Mumbai" },
              { from: "DEL", to: "BLR", label: "Delhi ➔ Bengaluru" },
              { from: "DEL", to: "COK", label: "Delhi ➔ Kochi" },
              { from: "BOM", to: "DEL", label: "Mumbai ➔ Delhi" },
              { from: "BLR", to: "TRV", label: "Bengaluru ➔ Trivandrum" },
            ].map((r) => (
              <button
                key={`${r.from}-${r.to}`}
                onClick={() => {
                  setOriginId(r.from);
                  setDestinationId(r.to);
                }}
                className={`p-2 text-left rounded-lg border text-xs transition-all ${
                  originId === r.from && destinationId === r.to
                    ? "bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300 font-bold"
                    : "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-blue-300"
                }`}
              >
                <div className="font-semibold">{r.from} ➔ {r.to}</div>
                <div className="text-[10px] opacity-70 truncate">{r.label}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right Map Canvas ── */}
      <div className="w-full lg:w-2/3 h-full relative z-0">
        <MapContainer
          center={[20.5937, 78.9629]}
          zoom={5}
          style={{ height: "100%", width: "100%", zIndex: 0 }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />

          {/* Render markers for all airports */}
          {AIRPORTS.map((airport) => {
            const isOrigin = airport.id === originId;
            const isDest = airport.id === destinationId;
            const icon = createAirportIcon(airport.id, isOrigin, isDest);

            const distFromOrigin =
              origin && airport.id !== origin.id
                ? calculateDistance(origin.lat, origin.lng, airport.lat, airport.lng)
                : 0;
            const est = estimateFarePreview(distFromOrigin);

            return (
              <Marker
                key={airport.id}
                position={[airport.lat, airport.lng]}
                icon={icon}
                eventHandlers={{
                  click: () => handleAirportClick(airport),
                }}
              >
                <Popup>
                  <div className="p-1 min-w-[200px]">
                    <div className="flex items-center justify-between gap-2 border-b border-gray-100 pb-1.5 mb-2">
                      <span className="font-bold text-gray-900 text-sm">
                        {airport.city} ({airport.id})
                      </span>
                      {isOrigin && (
                        <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-[10px] font-bold rounded">
                          ORIGIN
                        </span>
                      )}
                      {isDest && (
                        <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-bold rounded">
                          DESTINATION
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mb-2">{airport.name}</p>

                    {airport.id !== originId && (
                      <div className="space-y-2">
                        <div className="text-[11px] text-gray-600 bg-gray-50 p-2 rounded">
                          <div>Distance from {originId}: <strong>{distFromOrigin.toLocaleString()} km</strong></div>
                          <div>Duration: <strong>{estimateFlightTime(distFromOrigin)}</strong></div>
                          <div className="mt-1 pt-1 border-t border-gray-200">
                            Est. Base: <strong>₹{est.baseRate.toLocaleString()}</strong> + Tax: <strong>₹{est.taxes.toLocaleString()}</strong> + Fee: <strong>₹{est.convFee}</strong>
                          </div>
                        </div>

                        <div className="flex gap-1.5">
                          <button
                            onClick={() => handleSearchRedirect(originId, airport.id)}
                            className="flex-1 py-1.5 px-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold flex items-center justify-center gap-1 shadow transition-colors"
                          >
                            <Search className="h-3 w-3" />
                            Search Airfares
                          </button>
                          <button
                            onClick={() => setOriginId(airport.id)}
                            className="py-1.5 px-2 border border-gray-300 hover:border-gray-400 text-gray-700 rounded text-xs transition-colors"
                            title="Set as Origin"
                          >
                            Set Origin
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {/* Active Highlighted Polyline for Selected Corridor */}
          {origin && destination && origin.id !== destination.id && (
            <>
              {/* Glowing Outer Polyline */}
              <Polyline
                positions={[
                  [origin.lat, origin.lng],
                  [destination.lat, destination.lng],
                ]}
                color="#3b82f6"
                weight={5}
                opacity={0.8}
              />
              {/* Inner Dashed Animation Line */}
              <Polyline
                positions={[
                  [origin.lat, origin.lng],
                  [destination.lat, destination.lng],
                ]}
                color="#10b981"
                weight={2}
                dashArray="6, 12"
                opacity={1}
              />
            </>
          )}

          {/* Secondary Subdued Network Flight Lines from Current Origin */}
          {origin &&
            secondaryRoutes.map((dest) => (
              <Polyline
                key={`mesh-${origin.id}-${dest.id}`}
                positions={[
                  [origin.lat, origin.lng],
                  [dest.lat, dest.lng],
                ]}
                color="#94a3b8"
                weight={1}
                opacity={0.3}
                dashArray="4, 8"
              />
            ))}
        </MapContainer>
      </div>
    </div>
  );
}
