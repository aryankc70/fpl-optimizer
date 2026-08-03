from fpl_optimizer.db.session import engine, Base
from fpl_optimizer.db import models  # noqa: F401 — ensures models are registered


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


if __name__ == "__main__":
    init_db()