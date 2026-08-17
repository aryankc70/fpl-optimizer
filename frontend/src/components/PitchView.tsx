import type { Lineup, SquadPlayer } from '../types/api';
import { PitchPlayer } from './PitchPlayer';

interface PitchViewProps {
  lineup: Lineup;
}

// Row order from bottom (GKP) to top (FWD) — matches real FPL orientation
const ROWS: { position: SquadPlayer['position']; topPercent: number }[] = [
  { position: 'FWD', topPercent: 12 },
  { position: 'MID', topPercent: 38 },
  { position: 'DEF', topPercent: 64 },
  { position: 'GKP', topPercent: 88 },
];

function rowPlayers(lineup: Lineup, position: string): SquadPlayer[] {
  return lineup.starting_xi
    .filter((p) => p.position === position)
    .sort((a, b) => b.predicted_points - a.predicted_points);
}

export function PitchView({ lineup }: PitchViewProps) {
  return (
    <div className="relative w-full max-w-xl mx-auto aspect-[3/4] rounded-3xl overflow-hidden glass-panel glow-purple">
      {/* Pitch background: alternating green stripes + markings */}
      <div
        className="absolute inset-0"
        style={{
          background: `repeating-linear-gradient(
            to bottom,
            #0d5c2e 0%, #0d5c2e 12.5%,
            #0a4d26 12.5%, #0a4d26 25%
          )`,
        }}
      />
      {/* Center circle */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-28 h-28 rounded-full border-2 border-white/25" />
      {/* Halfway line */}
      <div className="absolute left-0 right-0 top-1/2 border-t-2 border-white/25" />
      {/* Penalty box (bottom, near GKP) */}
      <div className="absolute left-1/2 -translate-x-1/2 bottom-0 w-2/3 h-[15%] border-2 border-b-0 border-white/20 rounded-t-lg" />

      {/* Player rows */}
      {ROWS.map(({ position, topPercent }) => {
        const players = rowPlayers(lineup, position);
        return (
          <div
            key={position}
            className="absolute left-0 right-0 flex justify-center gap-4 sm:gap-8 px-4"
            style={{ top: `${topPercent}%`, transform: 'translateY(-50%)' }}
          >
            {players.map((p) => (
              <PitchPlayer
                key={p.player_id}
                webName={p.web_name}
                predictedPoints={p.predicted_points}
                badge={
                  p.player_id === lineup.captain.player_id ? 'C'
                  : p.player_id === lineup.vice_captain.player_id ? 'VC'
                  : undefined
                }
              />
            ))}
          </div>
        );
      })}
    </div>
  );
}