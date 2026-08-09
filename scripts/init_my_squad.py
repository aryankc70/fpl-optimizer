# scripts/init_my_squad.py
from fpl_optimizer.db.session import SessionLocal
from fpl_optimizer.db.models import UserSquad
from fpl_optimizer.optimization.squad_selector import load_candidates, solve_squad

def init_my_squad():
    candidates = load_candidates()
    squad = solve_squad(candidates)

    player_ids = ",".join(str(p.player_id) for p in squad)
    total_cost = sum(p.cost_tenths for p in squad) / 10
    bank = round(100.0 - total_cost, 1)

    db = SessionLocal()
    try:
        existing = db.get(UserSquad, 1)
        if existing:
            db.delete(existing)
            db.commit()

        db.add(UserSquad(id=1, player_ids=player_ids, free_transfers=1, bank=bank, last_updated_gameweek=1))
        db.commit()
        print(f"Initialized My Squad with {len(squad)} players, bank: £{bank}m")
    finally:
        db.close()

if __name__ == "__main__":
    init_my_squad()