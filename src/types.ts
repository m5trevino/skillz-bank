export interface Skill {
  id: string;
  name: string;
  status: string[];
  description: string;
  category?: string;
  level?: string;
  hexId?: string;
}

export const SKILLS_DATA: Skill[] = [
  {
    id: '1',
    name: 'NEURAL_INTERFACE_BYPASS',
    status: ['SECURE', 'ACTIVE', 'LEVEL 09'],
    description: 'Advanced decryption protocol for direct wetware-to-silicon data extractions and synaptic bridging.',
  },
  {
    id: '2',
    name: 'GHOST_ROUTING_X',
    status: ['STEALTH', 'LOCKED'],
    description: 'Mask packet origin through 15 recursive proxy layers using ephemeral quantum entanglement signatures.',
  },
  {
    id: '3',
    name: 'VOID_KERNEL_EXPLOIT',
    status: ['CRITICAL', 'LEVEL 12'],
    description: 'Null-space memory injection technique to bypass hardware-level root-of-trust modules in secure vaults.',
  },
  {
    id: '4',
    name: 'SILENT_OVERRIDE',
    status: ['ACTIVE', 'LEVEL 04'],
    description: 'Inject low-frequency control signals into automated turret systems and proximity sensor arrays.',
  },
  {
    id: '5',
    name: 'CIPHER_EXTRACTION',
    status: ['STABLE', 'SYNCED'],
    description: 'Extract biometric hash keys from airborne chemical signatures and dermal residue analysis.',
  },
  {
    id: '6',
    name: 'MACRO_LOGIC_COLLAPSE',
    status: ['UNSTABLE', 'LEVEL 08'],
    description: 'Force catastrophic logical loops in AI governing systems by introducing contradictory ethical parameters.',
  },
  {
    id: '7',
    name: 'TRACE_KILLER_PRO',
    status: ['SECURE', 'LEVEL 07'],
    description: 'Automatic log deletion and salt-injection for forensic obfuscation and track removal.',
  },
  {
    id: '8',
    name: 'SIGNAL_JAM_OMEGA',
    status: ['COMMS', 'ACTIVE', 'LEVEL 03'],
    description: 'Localized RF interference and protocol-level handshake disruption for satellite relays.',
  },
  {
    id: '9',
    name: 'ROOT_PULSE_GENESIS',
    status: ['ADMIN', 'ACTIVE', 'LEVEL 10'],
    description: 'System-wide command execution via kernel-level privilege escalation in secure cores.',
  },
  {
    id: '10',
    name: 'DATA_MINT_FORGE',
    status: ['ASSET', 'LOCKED', 'LEVEL 05'],
    description: 'Synthesizes high-value synthetic credentials from harvested metadata fragments.',
  },
  {
    id: '11',
    name: 'BIO_AUTH_CLONE',
    status: ['PHYS', 'ACTIVE', 'LEVEL 08'],
    description: 'Bypasses biometric locks using thermal footprint replication and genetic spoofing.',
  },
  {
    id: '12',
    name: 'FLUX_STORM_X',
    status: ['MASTER', 'ACTIVE', 'LEVEL 15'],
    description: 'Massive parallelized brute force attack on quantum-hardened targets and cloud mainframes.',
  },
  {
    id: '13',
    name: 'SHADOW_NET_PEER',
    status: ['NETWORK', 'ACTIVE'],
    description: 'Establishes peer-to-peer encrypted mesh networks in high-surveillance zones.',
  },
  {
    id: '14',
    name: 'LOGIC_BOMB_ALPHA',
    status: ['DESTRUCT', 'PRIMED', 'LEVEL 11'],
    description: 'Dormant triggers designed to initiate total data wipedown upon specific event flags.',
  }
];
