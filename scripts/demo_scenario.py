import time
import uuid
import httpx
from sqlalchemy import create_engine, text

# =============================
# CONFIG
# =============================

REGISTRY_DB_URL = "postgresql://ars:ars@localhost:5432/ars"
ARS_BASE_URL = "http://localhost:8000"

USER_OK = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_CONFLICT = uuid.UUID("22222222-2222-2222-2222-222222222222")

PERMISSION_GROUPS = [
    {"name": "ADMIN", "description": "Admin access"},
    {"name": "FINANCE", "description": "Finance access"},
    {"name": "SUPPORT", "description": "Support access"},
]

# ADMIN конфликтует с FINANCE
CONFLICTS = [
    ("ADMIN", "FINANCE"),
]

# =============================
# REGISTRY SEED
# =============================

def seed_registry():
    print("\n[DEMO] Seeding Registry DB")

    engine = create_engine(REGISTRY_DB_URL)

    with engine.begin() as conn:
        # Очистка
        conn.execute(text("DELETE FROM user_permission_groups"))
        conn.execute(text("DELETE FROM permission_group_conflicts"))
        conn.execute(text("DELETE FROM permission_groups"))

        # Создаём permission groups
        group_ids = {}
        for g in PERMISSION_GROUPS:
            result = conn.execute(
                text("""
                    INSERT INTO permission_groups (id, name, description, created_at)
                    VALUES (:id, :name, :description, now())
                    RETURNING id
                """),
                {
                    "id": uuid.uuid4(),
                    "name": g["name"],
                    "description": g["description"],
                },
            )
            group_id = result.scalar_one()
            group_ids[g["name"]] = group_id
            print(f"[DEMO] Created permission group: {g['name']}")

        # Конфликты
        for left, right in CONFLICTS:
            conn.execute(
                text("""
                    INSERT INTO permission_group_conflicts (
                        id, group_id, conflicts_with_id
                    )
                    VALUES (:id, :left_id, :right_id)
                """),
                {
                    "id": uuid.uuid4(),
                    "left_id": group_ids[left],
                    "right_id": group_ids[right],
                },
            )
            print(f"[DEMO] Conflict defined: {left} <-> {right}")

    print("[DEMO] Registry seeded successfully")
    return group_ids


# =============================
# ARS REQUESTS
# =============================

def send_access_request(
    user_id: uuid.UUID,
    group_id: uuid.UUID,
    action: str = "GRANT",
):
    print(
        f"[DEMO] Sending request: "
        f"user={user_id} action={action} group_id={group_id}"
    )

    response = httpx.post(
        f"{ARS_BASE_URL}/access-requests",
        json={
            "user_id": str(user_id),
            "permission_group_id": str(group_id),
            "action": action,
        },
        timeout=5,
    )

    response.raise_for_status()
    data = response.json()

    print(
        f"[DEMO] Request created: "
        f"id={data['id']} status={data['status']}"
    )

    return data["id"]


# =============================
# SCENARIO
# =============================

def run_scenario():
    print("\n========== DEMO SCENARIO START ==========\n")

    groups = seed_registry()
    time.sleep(1)

    # 1️⃣ Пользователь без конфликтов
    print("\n[SCENARIO] User without conflicts")
    send_access_request(
        user_id=USER_OK,
        group_id=groups["SUPPORT"],
    )

    time.sleep(1)

    # 2️⃣ Пользователь с конфликтом
    print("\n[SCENARIO] User with conflict")

    # Сначала ADMIN
    send_access_request(
        user_id=USER_CONFLICT,
        group_id=groups["ADMIN"],
    )

    time.sleep(1)

    # Потом FINANCE → конфликт
    send_access_request(
        user_id=USER_CONFLICT,
        group_id=groups["FINANCE"],
    )

    print("\n[DEMO] Waiting for workers to process requests...\n")
    time.sleep(6)

    print("\n========== DEMO SCENARIO END ==========\n")


if __name__ == "__main__":
    run_scenario()
