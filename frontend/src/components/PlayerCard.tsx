import { PositionBadge } from './PositionBadge';

interface PlayerCardProps {
  webName: string;
  position: string;
  cost: number;
  predictedPoints: number;
  badge?: 'C' | 'VC';
  subtitle?: string;
  dimmed?: boolean;
}

export function PlayerCard({ webName, position, cost, predictedPoints, badge, subtitle, dimmed }: PlayerCardProps) {
  return (
    <div className={`glass-panel rounded-2xl p-4 flex items-center justify-between transition-opacity ${dimmed ? 'opacity-50' : ''}`}>
      <div className="flex items-center gap-3">
        <PositionBadge position={position} />
        <div>
          <div className="flex items-center gap-2">
            <span className="text-white font-semibold">{webName}</span>
            {badge && (
              <span className="bg-[var(--color-mu-gold)] text-black text-[10px] font-black w-5 h-5 rounded-full flex items-center justify-center">
                {badge}
              </span>
            )}
          </div>
          <span className="text-white/40 text-xs">{subtitle ?? `£${cost.toFixed(1)}m`}</span>
        </div>
      </div>
      <div className="text-right">
        <span className="text-[var(--color-mu-red)] font-black text-lg">{predictedPoints.toFixed(1)}</span>
        <span className="text-white/30 text-xs block">pts</span>
      </div>
    </div>
  );
}