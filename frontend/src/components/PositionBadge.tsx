const POSITION_STYLES: Record<string, string> = {
  GKP: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  DEF: 'bg-sky-500/20 text-sky-300 border-sky-500/30',
  MID: 'bg-[var(--color-fpl-green)]/15 text-[var(--color-fpl-green)] border-[var(--color-fpl-green)]/30',
  FWD: 'bg-fuchsia-500/20 text-fuchsia-300 border-fuchsia-500/30',
};

export function PositionBadge({ position }: { position: string }) {
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${POSITION_STYLES[position] ?? ''}`}>
      {position}
    </span>
  );
}