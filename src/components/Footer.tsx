import { motion } from "motion/react";

export default function Footer() {
  return (
    <footer className="mt-4 flex items-center justify-between text-[9px] font-bold uppercase tracking-[0.2em] text-on-surface-variant/60">
      <div className="flex gap-8">
        <span className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_4px_rgba(57,255,20,0.8)]"></span> 
          CPU_LOAD: 12%
        </span>
        <span className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_4px_rgba(57,255,20,0.8)]"></span> 
          MEM_BUFFER: 4.2TB
        </span>
        <span className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-error shadow-[0_0_4px_rgba(255,113,108,0.8)]"></span> 
          FIREWALL_HITS: 0
        </span>
      </div>
      <div>
        © 2024 FLINTX_SKILLZ_MANAGEMENT_TERMINAL // READY
      </div>
    </footer>
  );
}
