"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { Volume2, VolumeX } from "lucide-react";
import { cn } from "@/lib/utils";

interface CinematicIntroProps {
  autoStart?: boolean;
}

export default function CinematicIntro({ autoStart = true }: CinematicIntroProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isMuted, setIsMuted] = useState(true);

  const videoRef = useRef<HTMLVideoElement>(null);

  // Play subtle cinematic audio chime on exit transition
  const playSciFiChime = useCallback(() => {
    try {
      const AudioContext = window.AudioContext || (window as unknown as { webkitAudioContext: typeof window.AudioContext }).webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = "sine";
      osc.frequency.setValueAtTime(320, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(640, ctx.currentTime + 0.5);
      
      gain.gain.setValueAtTime(0.05, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.8);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start();
      osc.stop(ctx.currentTime + 0.8);
    } catch {
      // Audio context may be restricted before interaction
    }
  }, []);

  // Smooth cinematic transition into the dashboard
  const handleExit = useCallback(() => {
    if (isTransitioning) return;
    setIsTransitioning(true);
    playSciFiChime();

    // Fade out video audio smoothly over 800ms
    if (videoRef.current && !isMuted) {
      try {
        const v = videoRef.current;
        const initialVol = v.volume;
        const fadeInterval = setInterval(() => {
          if (v.volume > 0.05) {
            v.volume = Math.max(0, v.volume - initialVol / 8);
          } else {
            v.volume = 0;
            clearInterval(fadeInterval);
          }
        }, 100);
      } catch {
        // Safe fallback
      }
    }

    // Wait for the 1000ms dissolve transition to complete before removing from DOM
    setTimeout(() => {
      setIsOpen(false);
      setIsTransitioning(false);
      if (videoRef.current) {
        videoRef.current.pause();
      }
    }, 1000);
  }, [isTransitioning, playSciFiChime, isMuted]);

  // Check initial launch condition
  useEffect(() => {
    const hasSeenIntro = sessionStorage.getItem("flare_intro_viewed");
    if (!hasSeenIntro && autoStart) {
      setIsOpen(true);
      sessionStorage.setItem("flare_intro_viewed", "true");
    }

    // Global listener so topbar or any button can open intro anytime
    const handleOpen = () => {
      setIsTransitioning(false);
      setIsOpen(true);
      if (videoRef.current) {
        videoRef.current.currentTime = 0;
        videoRef.current.play().catch(() => {});
      }
    };

    window.addEventListener("open-flare-intro", handleOpen);
    return () => window.removeEventListener("open-flare-intro", handleOpen);
  }, [autoStart]);

  // Keyboard shortcut: ESC to skip
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" || e.key === "Enter") {
        handleExit();
      } else if (e.key.toLowerCase() === "m") {
        toggleMute();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, handleExit]);

  // Toggle Audio
  const toggleMute = () => {
    if (!videoRef.current) return;
    const newMuted = !videoRef.current.muted;
    videoRef.current.muted = newMuted;
    setIsMuted(newMuted);
  };

  // Clicking anywhere on the video attempts to unmute if muted, or skip if already unmuted
  const handleVideoClick = () => {
    if (isMuted && videoRef.current) {
      videoRef.current.muted = false;
      setIsMuted(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className={cn(
        "fixed inset-0 z-[100] flex items-center justify-center bg-black select-none overflow-hidden will-change-[opacity,transform]",
        "transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)]",
        isTransitioning 
          ? "opacity-0 scale-[1.03] pointer-events-none" 
          : "opacity-100 scale-100"
      )}
      style={{ transform: "translate3d(0, 0, 0)" }}
    >
      {/* Pure Full-Screen 3D Intro Video */}
      <video
        ref={videoRef}
        src="/intro.mp4"
        preload="auto"
        playsInline
        autoPlay
        muted={isMuted}
        onClick={handleVideoClick}
        onTimeUpdate={(e) => {
          // As soon as 'FLARE' appears on screen (at ~4.8s), smoothly blend into the dashboard
          if (e.currentTarget.currentTime >= 4.8 && !isTransitioning) {
            handleExit();
          }
        }}
        onEnded={handleExit}
        className="w-full h-full object-cover cursor-pointer"
        style={{ transform: "translate3d(0, 0, 0)", backfaceVisibility: "hidden" }}
      />

      {/* Seamless Luminous Blend Overlay into Dashboard */}
      <div 
        className={cn(
          "absolute inset-0 pointer-events-none transition-opacity duration-1000 ease-out",
          isTransitioning 
            ? "opacity-100 bg-background" 
            : "opacity-0"
        )}
      />

      {/* Subtle cinematic vignette for screen edges */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,transparent_60%,rgba(0,0,0,0.6)_100%)]" />

      {/* Minimal Discreet Controls (Top-Right only) */}
      <div className="absolute top-6 right-6 z-20 flex items-center gap-2.5">
        {/* Sound Toggle */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            toggleMute();
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-black/40 hover:bg-black/70 text-white/80 hover:text-white backdrop-blur-md border border-white/15 transition-all text-xs shadow-lg"
          title={isMuted ? "Click to unmute sound" : "Sound is on (click to mute)"}
        >
          {isMuted ? (
            <>
              <VolumeX className="w-3.5 h-3.5 text-white/60" />
              <span className="text-[11px] font-medium">Unmute</span>
            </>
          ) : (
            <>
              <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[11px] font-medium text-emerald-400">Sound On</span>
            </>
          )}
        </button>

        {/* Minimal Skip Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleExit();
          }}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-black/40 hover:bg-black/70 text-white/80 hover:text-white backdrop-blur-md border border-white/15 transition-all text-xs font-medium shadow-lg hover:scale-105 active:scale-95"
          title="Skip intro and enter dashboard"
        >
          <span>Skip</span>
          <span className="text-[10px] px-1 py-0.2 rounded bg-white/15 text-white/70 font-mono">ESC</span>
        </button>
      </div>
    </div>
  );
}
