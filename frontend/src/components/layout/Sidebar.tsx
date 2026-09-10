"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  LineChart, 
  Activity, 
  Map, 
  TrendingUp,
  BarChart3,
  Radio,
  Settings
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Dashboard",           href: "/",           icon: LayoutDashboard },
  { name: "Search Airfares",     href: "/search",     icon: Activity },
  { name: "Live Airfares",       href: "/live-airfares", icon: Radio },
  { name: "Economic Dashboard",  href: "/economic",   icon: TrendingUp },
  { name: "Historical Analysis", href: "/historical", icon: LineChart },
  { name: "Route Explorer",      href: "/explorer",   icon: Map },
  { name: "Govt CPI Data",       href: "/cpi",        icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 h-screen border-r border-border bg-card">
      <div className="flex items-center justify-center h-16 border-b border-border">
        <h1 className="text-2xl font-bold tracking-wider text-primary">FLARE</h1>
      </div>
      <div className="flex flex-col flex-1 overflow-y-auto py-4">
        <nav className="flex-1 px-4 space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 group",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                    : "text-muted-foreground hover:bg-secondary hover:text-secondary-foreground"
                )}
              >
                <Icon 
                  className={cn(
                    "mr-3 h-5 w-5 transition-transform duration-200", 
                    isActive ? "scale-110" : "group-hover:scale-110"
                  )} 
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom area — Settings */}
      <div className="p-4 border-t border-border space-y-1">
        {/* Settings */}
        <div className="flex items-center px-4 py-2.5 text-sm text-muted-foreground rounded-lg hover:bg-secondary cursor-pointer transition-colors">
          <Settings className="mr-3 h-5 w-5" />
          Settings
        </div>
      </div>
    </div>
  );
}
