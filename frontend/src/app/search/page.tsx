"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import { format, addDays } from "date-fns";
import FlightResults from "@/components/search/FlightResults";
import AnalyticsTabs from "@/components/search/AnalyticsTabs";
import { Search, Loader2, Calendar, ArrowLeftRight, RefreshCw } from "lucide-react";

const API_BASE = "http://localhost:8000";

interface Airport {
  iata_code: string;
  name: string;
  city: string;
  state: string;
}

function AirportInput({
  label,
  value,
  onChange,
  placeholder,
  id,
}: {
  label: string;
  value: string;
  onChange: (val: string) => void;
  placeholder: string;
  id: string;
}) {
  const [suggestions, setSuggestions] = useState<Airport[]>([]);
  const [open, setOpen] = useState(false);
  const [fetching, setFetching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSuggestions([]);
      setOpen(false);
      return;
    }
    setFetching(true);
    try {
      const res = await axios.get(`${API_BASE}/api/v1/airports/search`, { params: { q } });
      const results: Airport[] = res.data.results || [];
      setSuggestions(results);
      setOpen(results.length > 0);
    } catch {
      setSuggestions([]);
    } finally {
      setFetching(false);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    onChange(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(v), 300);
  };

  const handleSelect = (airport: Airport) => {
    onChange(airport.iata_code);
    setSuggestions([]);
    setOpen(false);
  };

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div className="flex-1 w-full relative" ref={containerRef}>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type="text"
          value={value}
          onChange={handleChange}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-transparent text-gray-900 dark:text-white transition-all uppercase"
          placeholder={placeholder}
          required
          autoComplete="off"
          maxLength={3}
        />
        {fetching && (
          <Loader2 className="absolute right-3 top-3.5 h-5 w-5 animate-spin text-gray-400" />
        )}
      </div>
      {open && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden">
          {suggestions.map((a) => (
            <li
              key={a.iata_code}
              className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
              onMouseDown={() => handleSelect(a)}
            >
              <span className="font-bold text-blue-600 dark:text-blue-400 w-10 shrink-0 text-sm">
                {a.iata_code}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{a.city}</p>
                <p className="text-xs text-gray-500 truncate max-w-[200px]">{a.name}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function SearchContent() {
  const searchParams = useSearchParams();
  const queryOrigin = searchParams.get("origin") || searchParams.get("from");
  const queryDestination = searchParams.get("destination") || searchParams.get("to");
  const queryDate = searchParams.get("date") || searchParams.get("travel_date");

  const [origin, setOrigin] = useState(queryOrigin ? queryOrigin.toUpperCase() : "DEL");
  const [destination, setDestination] = useState(queryDestination ? queryDestination.toUpperCase() : "BOM");
  const [travelDate, setTravelDate] = useState(queryDate || format(addDays(new Date(), 7), "yyyy-MM-dd"));

  const [loading, setLoading] = useState(false);
  const [resultsData, setResultsData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollingCount, setPollingCount] = useState(0);
  const autoSearchedRef = useRef(false);

  const executeSearch = useCallback(async (orig: string, dest: string, date: string, triggerLive = true) => {
    if (triggerLive) {
      setLoading(true);
      setError(null);
      setResultsData(null);
      setPollingCount(0);
    }

    try {
      const params = {
        origin: orig.toUpperCase(),
        destination: dest.toUpperCase(),
        travel_date: date,
        trigger_live: triggerLive,
      };

      const res = await axios.get(`${API_BASE}/api/v1/search/`, { params });
      setResultsData(res.data);
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail || err.message || "Failed to fetch search results. Is the backend running?";
      setError(detail);
    } finally {
      if (triggerLive) setLoading(false);
    }
  }, []);

  const handleSearch = async (e?: React.FormEvent, triggerLive = true) => {
    if (e) e.preventDefault();
    await executeSearch(origin, destination, travelDate, triggerLive);
  };

  // Auto-search if origin or destination were passed in URL parameters
  useEffect(() => {
    if ((queryOrigin || queryDestination) && !autoSearchedRef.current) {
      autoSearchedRef.current = true;
      const targetOrig = (queryOrigin || origin).toUpperCase();
      const targetDest = (queryDestination || destination).toUpperCase();
      const targetDate = queryDate || travelDate;
      setOrigin(targetOrig);
      setDestination(targetDest);
      if (queryDate) setTravelDate(queryDate);
      executeSearch(targetOrig, targetDest, targetDate, true);
    }
  }, [queryOrigin, queryDestination, queryDate, origin, destination, travelDate, executeSearch]);

  // Poll every 4s when background collection is running (max 6 polls = 24s)
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    const isCollecting =
      resultsData?.data_provenance === "LIVE_COLLECTION_STARTED" ||
      resultsData?.data_provenance === "COLLECTION_IN_PROGRESS";

    if (isCollecting && pollingCount < 6) {
      interval = setInterval(() => {
        setPollingCount((c) => c + 1);
        handleSearch(undefined, false);
      }, 4000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resultsData, pollingCount]);

  const swap = () => {
    setOrigin(destination);
    setDestination(origin);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Airfare Intelligence Search
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Search live &amp; historical fares across all Indian routes
        </p>
      </div>

      {/* ── Search Form ── */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700 mb-8">
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4 items-end">
          <AirportInput
            id="origin-input"
            label="From"
            value={origin}
            onChange={setOrigin}
            placeholder="e.g. DEL"
          />

          {/* Swap button */}
          <button
            type="button"
            onClick={swap}
            title="Swap airports"
            className="self-end mb-1 h-10 w-10 shrink-0 rounded-full border border-gray-200 dark:border-gray-600 flex items-center justify-center text-gray-400 hover:text-blue-600 hover:border-blue-400 transition-colors"
          >
            <ArrowLeftRight className="h-4 w-4" />
          </button>

          <AirportInput
            id="destination-input"
            label="To"
            value={destination}
            onChange={setDestination}
            placeholder="e.g. BOM"
          />

          {/* Date picker */}
          <div className="flex-1 w-full">
            <label
              htmlFor="travel-date"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
            >
              Travel Date
            </label>
            <div className="relative">
              <input
                id="travel-date"
                type="date"
                value={travelDate}
                min={format(new Date(), "yyyy-MM-dd")}
                onChange={(e) => setTravelDate(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-transparent text-gray-900 dark:text-white transition-all"
                required
              />
              <Calendar className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          <button
            type="submit"
            id="search-submit-btn"
            disabled={loading}
            className="w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="animate-spin h-5 w-5" />
            ) : (
              <Search className="h-5 w-5" />
            )}
            {loading ? "Searching..." : "Search Fares"}
          </button>
        </form>
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-xl mb-8 border border-red-200 dark:border-red-800 flex items-start gap-3">
          <div className="flex-1 text-sm">{error}</div>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-600 font-bold text-lg leading-none"
          >
            ×
          </button>
        </div>
      )}

      {/* ── Loading ── */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <Loader2 className="animate-spin h-10 w-10 mb-4 text-blue-600" />
          <p className="text-lg font-medium">Searching permitted sources…</p>
          <p className="text-sm text-gray-400 mt-1">Triggering live data collection in the background</p>
        </div>
      )}

      {/* ── Results ── */}
      {!loading && resultsData && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Summary row */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-gray-50 dark:bg-gray-800/50 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 gap-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {resultsData.search.origin} → {resultsData.search.destination}
              </h2>
              <p className="text-gray-500 mt-1 text-sm">
                {format(new Date(resultsData.search.travel_date + "T00:00:00"), "dd MMM yyyy")}
                {" "}•{" "}
                {resultsData.results_count} observation
                {resultsData.results_count !== 1 ? "s" : ""}
              </p>
            </div>

            <div className="flex flex-wrap gap-2 items-center">
              {/* Live collection spinner */}
              {(resultsData.data_provenance === "LIVE_COLLECTION_STARTED" ||
                resultsData.data_provenance === "COLLECTION_IN_PROGRESS") && (
                <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 animate-pulse">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  Collecting live data…
                </span>
              )}

              <span
                className={`px-4 py-1.5 rounded-full text-sm font-medium ${
                  resultsData.data_provenance === "LIVE"
                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                    : resultsData.data_provenance === "HISTORICAL"
                    ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                    : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                }`}
              >
                {resultsData.data_provenance.replace(/_/g, " ")}
              </span>

              <span
                className={`px-4 py-1.5 rounded-full text-sm font-medium ${
                  resultsData.availability_pressure === "LOW"
                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                    : resultsData.availability_pressure === "HIGH"
                    ? "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
                    : resultsData.availability_pressure === "SEVERE"
                    ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                    : "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                }`}
              >
                Pressure: {resultsData.availability_pressure}
              </span>
            </div>
          </div>

          <AnalyticsTabs results={resultsData.results} />
          <FlightResults results={resultsData.results} />
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center py-24 text-gray-500">
        <Loader2 className="animate-spin h-10 w-10 mb-4 text-blue-600" />
        <p className="text-lg font-medium">Loading search parameters…</p>
      </div>
    }>
      <SearchContent />
    </Suspense>
  );
}
