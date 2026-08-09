const POSITION_STYLES: Record<string, string> = {
  GKP: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  DEF: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  MID: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  FWD: 'bg-[var(--color-mu-red)]/20 text-red-300 border-[var(--color-mu-red)]/30',
};

export function PositionBadge({ position }: { position: string }) {
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${POSITION_STYLES[position] ?? ''}`}>
      {position}
    </span>
  );
}