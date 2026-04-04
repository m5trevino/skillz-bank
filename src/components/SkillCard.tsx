import { motion } from "motion/react";
import { Skill } from "../types";

interface SkillCardProps {
  skill: Skill;
  index: number;
  key?: string;
}

const tagColors: Record<string, string> = {
  SECURE: "bg-primary/10 text-primary border-primary/20",
  ACTIVE: "bg-secondary/10 text-secondary border-secondary/20",
  STEALTH: "bg-primary/10 text-primary border-primary/20",
  LOCKED: "bg-tertiary/10 text-tertiary border-tertiary/20",
  CRITICAL: "bg-error/10 text-error border-error/20",
  STABLE: "bg-secondary/10 text-secondary border-secondary/20",
  SYNCED: "bg-primary/10 text-primary border-primary/20",
  UNSTABLE: "bg-error/10 text-error border-error/20",
  COMMS: "bg-primary/10 text-primary border-primary/20",
  ADMIN: "bg-primary/10 text-primary border-primary/20",
  ASSET: "bg-primary/10 text-primary border-primary/20",
  PHYS: "bg-primary/10 text-primary border-primary/20",
  MASTER: "bg-primary/10 text-primary border-primary/20",
  NETWORK: "bg-primary/10 text-primary border-primary/20",
  DESTRUCT: "bg-error/10 text-error border-error/20",
  PRIMED: "bg-tertiary/10 text-tertiary border-tertiary/20",
};

export default function SkillCard({ skill, index }: SkillCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ 
        scale: 1.02, 
        boxShadow: "0 0 20px rgba(57, 255, 20, 0.15)",
        zIndex: 30
      }}
      transition={{ 
        delay: index * 0.05,
        scale: { duration: 0.2 },
        boxShadow: { duration: 0.2 }
      }}
      className="bg-surface-container group hover:bg-surface-highest transition-all duration-300 relative border-l border-t border-white/5 cursor-pointer"
    >
      <div className="absolute -left-[1px] top-0 h-full w-[2px] bg-primary opacity-50 group-hover:opacity-100 group-hover:shadow-[0_0_12px_#39FF14]"></div>
      
      <div className="p-5 flex flex-col h-full">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-black text-on-surface leading-tight uppercase">
            {skill.name}
          </h3>
          <div className="flex flex-col items-end gap-1">
            <div className="flex flex-wrap justify-end gap-1">
              {skill.status.map(tag => (
                <span key={tag} className={`px-1.5 py-0.5 text-[0.5rem] font-bold uppercase border ${tagColors[tag] || "border-white/10 text-white/50"}`}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        <p className="text-xs text-on-surface-variant font-medium leading-relaxed flex-grow opacity-80 mb-6">
          {skill.description}
        </p>
      </div>
    </motion.div>
  );
}
