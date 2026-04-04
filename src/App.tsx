/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from "react";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import AsciiBanner from "./components/AsciiBanner";
import SkillCard from "./components/SkillCard";
import SkillListItem from "./components/SkillListItem";
import Footer from "./components/Footer";
import { SKILLS_DATA } from "./types";

export default function App() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');

  return (
    <div className="min-h-screen bg-background selection:bg-primary selection:text-black flex">
      <Sidebar />
      
      <main className="flex-1 ml-64 flex flex-col relative min-h-screen">
        {/* Background Effects */}
        <div className="fixed inset-0 pointer-events-none opacity-[0.03] z-[100] bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]" />
        <div className="fixed top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent z-[101]" />
        
        <TopBar viewMode={viewMode} onToggleView={() => setViewMode(prev => prev === 'grid' ? 'list' : 'grid')} />
        
        <div className="flex-1 p-8 flex flex-col h-[calc(100vh-64px)] overflow-hidden">
          {/* Background Grid Pattern */}
          <div 
            className="absolute inset-0 opacity-5 pointer-events-none" 
            style={{ 
              backgroundImage: 'radial-gradient(#39FF14 1px, transparent 1px)', 
              backgroundSize: '24px 24px' 
            }} 
          />
          
          {/* Scanlines Overlay */}
          <div className="scanlines fixed inset-0 z-10 pointer-events-none" />

          {/* Content Section */}
          <div className="relative z-20 flex flex-col h-full">
            <section className="mb-6">
              <AsciiBanner />
              
              <div className="flex justify-between items-end">
                <div>
                  <h1 className="font-black text-2xl text-on-surface tracking-tighter uppercase">
                    SKILL_TERMINAL_v9.2
                  </h1>
                  <p className="text-on-surface-variant font-mono text-[10px] uppercase tracking-[0.2em] mt-1 opacity-50">
                    STATUS: UPLINK_ESTABLISHED // ENCRYPTION: POLY-GLOW-128
                  </p>
                </div>
                
                <div className="text-right">
                  <span className="text-primary text-2xl font-black italic">14 / 128</span>
                  <p className="text-[9px] font-bold tracking-widest text-on-surface-variant uppercase opacity-60">LOADED_SLOTS</p>
                </div>
              </div>
            </section>

            {viewMode === 'grid' ? (
              <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pb-12 overflow-y-auto pr-2">
                {SKILLS_DATA.map((skill, index) => (
                  <SkillCard key={skill.id} skill={skill} index={index} />
                ))}
              </section>
            ) : (
              <section className="flex-1 bg-surface-highest/20 backdrop-blur-xl rounded-xl border border-white/5 overflow-hidden flex flex-col">
                <div className="flex-1 overflow-y-auto">
                  <div className="grid grid-cols-1">
                    {SKILLS_DATA.map((skill, index) => (
                      <SkillListItem key={skill.id} skill={skill} index={index} />
                    ))}
                  </div>
                </div>
              </section>
            )}

            <Footer />
          </div>
        </div>
      </main>
    </div>
  );
}
