interface PitchPlayerProps {
  webName: string;
  predictedPoints: number;
  badge?: 'C' | 'VC';
}

export function PitchPlayer({ webName, predictedPoints, badge }: PitchPlayerProps) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative">
        <div className="w-16 h-16 rounded-full bg-[var(--color-fpl-purple)] border-[3px] border-white/90 shadow-xl" />
        {badge && (
          <span className="absolute -top-1.5 -right-1.5 bg-[var(--color-fpl-green)] text-[var(--color-fpl-purple)] text-xs font-black w-6 h-6 rounded-full flex items-center justify-center border-2 border-white">
            {badge}
          </span>
        )}
      </div>
      <div className="bg-black/70 backdrop-blur-sm rounded-lg px-3 py-1 text-center min-w-[80px]">
        <span className="text-white text-sm font-bold block leading-tight truncate max-w-[90px]">{webName}</span>
        <span className="text-[var(--color-fpl-green)] text-sm font-black block leading-tight">{predictedPoints.toFixed(1)}</span>
      </div>
    </div>
  );
}