import { motion } from "motion/react";
import { 
  Terminal, 
  Lock, 
  Network, 
  ShoppingCart,
  Settings, 
  LogOut
} from "lucide-react";

const menuItems = [
  { id: 'terminal', label: 'Terminal', icon: Terminal, active: true },
  { id: 'vault', label: 'Vault', icon: Lock },
  { id: 'nodes', label: 'Nodes', icon: Network },
  { id: 'market', label: 'Market', icon: ShoppingCart },
];

export default function Sidebar() {
  return (
    <aside className="h-screen w-64 fixed left-0 top-0 bg-slate-950/80 backdrop-blur-2xl border-r border-white/5 flex flex-col py-8 z-50">
      <div className="px-6 mb-10">
        <h1 className="font-black text-primary italic tracking-tighter text-xl uppercase">SKILLZ_BNK</h1>
        
        <div className="mt-8 flex flex-col items-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-secondary p-[2px]">
            <div className="w-full h-full rounded-full bg-slate-900 overflow-hidden border-2 border-slate-950 flex items-center justify-center">
              <img 
                alt="User profile" 
                className="w-full h-full object-cover" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCyyly2ubvPwNhzVvlQtTuwmLJ1pJzi516StMl37bBS3xuQkGNmuWfP_Nl2d6irjL03qBF3cX8KIINVufyx0YegE_F-oEqhO1dU7MqCB9BWZ_EMAnBECWW3aEFmDqLofPXCeJ0efFN81UHfGkwEEWMRLkNQTPDi9j_lpk7oNp-u3rpa9npD-koyeDlhEIknAZNNgfN4oQM3l5iyyF_yOi7TuDvrmuMRj4S11xoiOJ-BKteGT5uN88jsOOWIV9920NV6oaTFslxkKng"
                referrerPolicy="no-referrer"
              />
            </div>
          </div>
          <div className="mt-4 text-center">
            <h3 className="text-on-surface font-bold text-sm tracking-widest uppercase">OPERATOR_01</h3>
            <p className="text-primary text-[10px] uppercase tracking-[0.2em] mt-1">Level 4 Access</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        {menuItems.map((item) => (
          <a
            key={item.id}
            href="#"
            className={`flex items-center gap-4 px-6 py-4 transition-all text-xs font-bold tracking-widest uppercase ${
              item.active 
                ? "text-primary bg-primary/5 border-r-4 border-primary" 
                : "text-on-surface-variant hover:text-primary hover:bg-primary/5"
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </a>
        ))}
      </nav>

      <div className="px-6 mt-auto">
        <motion.button 
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 py-3 rounded-lg text-[10px] font-extrabold uppercase tracking-widest mb-8 transition-all"
        >
          FORCE_REBOOT
        </motion.button>
        
        <div className="flex flex-col gap-2 border-t border-white/5 pt-4 mb-4">
          <a href="#" className="flex items-center gap-2 text-on-surface-variant hover:text-on-surface text-[10px] font-bold tracking-widest uppercase">
            <Settings className="w-4 h-4" /> Settings
          </a>
          <a href="#" className="flex items-center gap-2 text-on-surface-variant hover:text-error text-[10px] font-bold tracking-widest uppercase">
            <LogOut className="w-4 h-4" /> Disconnect
          </a>
        </div>
      </div>
    </aside>
  );
}
