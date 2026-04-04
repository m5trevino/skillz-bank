import { motion } from "motion/react";
import { Skill } from "../types";

interface SkillListItemProps {
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

export default function SkillListItem({ skill, index }: SkillListItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      whileHover={{ backgroundColor: "rgba(255, 255, 255, 0.05)" }}
      className="px-6 py-4 transition-all group cursor-pointer border-b border-white/5"
    >
      <div className="flex items-center gap-3">
        <span className="font-bold text-xs tracking-widest text-on-surface group-hover:text-primary transition-colors uppercase">
          {skill.name}
        </span>
        <div className="flex gap-1.5">
          {skill.status.map((tag) => (
            <span 
              key={tag}
              className={`${
                tag.startsWith('LEVEL') 
                  ? "bg-surface-highest/60 text-on-surface-variant border border-white/5" 
                  : (tagColors[tag] || "bg-surface-highest/60 text-on-surface-variant border border-white/5")
              } text-[8px] font-bold px-1.5 py-0.5 rounded uppercase tracking-tighter`}
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
      <p className="text-on-surface-variant/70 text-[11px] mt-1 leading-relaxed">
        {skill.description}
      </p>
    </motion.div>
  );
}
