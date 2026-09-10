"use client";

import { Bell, Search, User } from "lucide-react";

export default function Topbar() {

  return (
    <header className="flex items-center justify-between h-16 px-6 border-b border-border bg-card/80 backdrop-blur-md sticky top-0 z-10">
      <div className="flex items-center flex-1">
        <div className="relative w-full max-w-md">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <Search className="w-4 h-4 text-muted-foreground" />
          </div>
          <input 
            type="text" 
            className="w-full py-2 pl-10 pr-4 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all" 
            placeholder="Search routes, airlines, or dates..." 
          />
        </div>
      </div>
      
      <div className="flex items-center space-x-3">
        <div className="flex items-center px-3 py-1.5 text-xs font-semibold text-success bg-success/10 rounded-full border border-success/20">
          <span className="w-2 h-2 mr-2 rounded-full bg-success animate-pulse"></span>
          LIVE DATA
        </div>
        
        <button className="p-2 text-muted-foreground hover:text-foreground transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full border border-card"></span>
        </button>
        
        <div className="flex items-center gap-2 pl-4 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary border border-primary/30">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden md:block">
            <p className="text-sm font-medium leading-none">Admin User</p>
            <p className="text-xs text-muted-foreground mt-1">SIH Presenter</p>
          </div>
        </div>
      </div>
    </header>
  );
}
