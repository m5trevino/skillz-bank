import { Search, Bell, Terminal, Settings, LayoutGrid, List } from "lucide-react";

interface TopBarProps {
  viewMode: 'grid' | 'list';
  onToggleView: () => void;
}

export default function TopBar({ viewMode, onToggleView }: TopBarProps) {
  return (
    <header className="w-[calc(100%-16rem)] fixed top-0 right-0 sticky z-40 bg-background/40 backdrop-blur-xl border-b border-white/5 flex justify-between items-center px-8 h-16">
      <div className="flex items-center flex-1">
        <div className="flex bg-surface-highest/40 border border-white/5 rounded-full px-4 py-1.5 items-center gap-3 w-full max-w-md">
          <Search className="w-4 h-4 text-on-surface-variant" />
          <input 
            type="text" 
            className="bg-transparent border-none p-0 text-on-surface-variant text-xs font-label focus:ring-0 w-full placeholder:text-on-surface-variant/40"
            placeholder="QUERY_SYSTEM_REGISTRY..."
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-4">
          <button 
            onClick={onToggleView}
            className="text-primary hover:text-secondary transition-all"
            title={viewMode === 'grid' ? "Switch to List View" : "Switch to Grid View"}
          >
            {viewMode === 'grid' ? <List className="w-5 h-5" /> : <LayoutGrid className="w-5 h-5" />}
          </button>
          <Bell className="w-5 h-5 text-primary cursor-pointer hover:text-secondary transition-all" />
          <Terminal className="w-5 h-5 text-primary cursor-pointer hover:text-secondary transition-all" />
          <Settings className="w-5 h-5 text-primary cursor-pointer hover:text-secondary transition-all" />
        </div>
        <div className="h-8 w-px bg-white/5"></div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-[10px] font-bold text-primary">SESSION_ACTIVE</p>
            <p className="text-[9px] text-on-surface-variant opacity-50">0x4F2...E81</p>
          </div>
        </div>
      </div>
    </header>
  );
}
