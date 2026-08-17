function App() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8" style={{ fontFamily: 'var(--font-display)' }}>
      <div className="glass-panel glow-green rounded-3xl p-8 max-w-sm w-full">
        <div className="flex items-center justify-between mb-6">
          <span className="text-xs uppercase tracking-widest text-white/50">Gameweek 1</span>
          <span className="bg-[var(--color-fpl-green)] text-[var(--color-fpl-purple)] text-xs font-black px-3 py-1 rounded-full">
            LIVE
          </span>
        </div>
        <h1 className="text-4xl font-extrabold text-white mb-1">Erling Haaland</h1>
        <p className="text-white/50 text-sm mb-6">Manchester City · FWD</p>
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-black text-[var(--color-fpl-green)]">6.2</span>
          <span className="text-white/40 text-sm">predicted pts</span>
        </div>
      </div>
    </div>
  )
}

export default App