"use client";

import React from "react";
import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";

// Leaflet requires window object, so we disable SSR
const RouteExplorerMap = dynamic(
  () => import("@/components/maps/RouteExplorer"),
  { 
    ssr: false,
    loading: () => (
      <div className="h-[600px] w-full flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    )
  }
);

export default function ExplorerPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          India Route Network
        </h1>
        <p className="text-gray-500">
          Visualize air routes and average fares across the Indian domestic aviation network.
        </p>
      </div>

      <RouteExplorerMap />
    </div>
  );
}
