from sqlalchemy import text
from fpl_optimizer.db.session import engine

VIEWS_PATH = "src/fpl_optimizer/db/views.sql"


def create_views():
    with open(VIEWS_PATH) as f:
        sql = f.read()

    with engine.begin() as conn:
        conn.execute(text(sql))

    print("Views created successfully.")


if __name__ == "__main__":
    create_views()