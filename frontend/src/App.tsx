import { ChipCalendarView } from './components/ChipCalendarView';
import { HitAdvisor } from './components/HitAdvisor';
import { LineupView } from './components/LineupView';
import { PredictionsTable } from './components/PredictionsTable';
import { SquadView } from './components/SquadView';
import { MySquadView } from './components/MySquadView';


function App() {
  return (
    <div style={{ fontFamily: 'var(--font-display)' }}>
      <header className="text-center pt-20 pb-8">
        <h1 className="text-5xl font-black text-white tracking-tight">
          FPL <span className="text-[var(--color-mu-red)]">Optimizer</span>
        </h1>
        <p className="text-white/40 mt-3">Season-long squad intelligence, powered by ML and ILP</p>
      </header>

      <PredictionsTable />
      <MySquadView />
      <SquadView />
      <LineupView />
      <HitAdvisor />
      <ChipCalendarView />
    </div>
  );
}

export default App;