"""
Seed script to create a realistic demo store and live drop for Indian Thrift Sellers.
Run: .venv\Scripts\python scripts\seed_demo_drop.py
"""

from backend.app.database.connection import SessionLocal, init_db
from backend.app.database.models import Store, Drop, DropItem, Order, utcnow

def seed_demo():
    init_db()
    db = SessionLocal()

    # 1. Create or get Demo Store
    store = db.query(Store).filter(Store.slug == "vintage-curations").first()
    if not store:
        store = Store(
            name="Vintage Curations Delhi",
            slug="vintage-curations",
            instagram_handle="vintagecurations.in",
            upi_id="vintagecurations@okhdfcbank",
            phone="9876543210",
            fulfillment_type="self",
            flat_shipping_fee=70.0,
            created_at=utcnow(),
        )
        db.add(store)
        db.commit()
        db.refresh(store)
        print(f"Created Store: {store.name}")
    else:
        print(f"Store already exists: {store.name}")

    # 2. Create or get Demo Drop
    drop = db.query(Drop).filter(Drop.slug == "winter-vintage-drop").first()
    if not drop:
        drop = Drop(
            store_id=store.id,
            title="Winter Archive Drop Vol. 1",
            slug="winter-vintage-drop",
            status="live",
            created_at=utcnow(),
        )
        db.add(drop)
        db.commit()
        db.refresh(drop)
        print(f"Created Drop: {drop.title}")
    else:
        print(f"Drop already exists: {drop.title}")

    # 3. Add 4 Demo Items if drop is empty
    if len(drop.items) == 0:
        demo_items = [
            {
                "title": "Vintage 90s Carhartt Heavyweight Duck Jacket - Tan",
                "aesthetic": "Gorpcore / Workwear",
                "category": "Outerwear",
                "size_label": "L (Relaxed)",
                "chest_inches": 44.0,
                "length_inches": 28.5,
                "price_inr": 1899.0,
                "condition_score": "9/10 Mint",
                "status": "available",
            },
            {
                "title": "90s Nirvana In Utero Faded Graphic Tee - Single Stitch",
                "aesthetic": "90s Grunge",
                "category": "Tops",
                "size_label": "M (Boxy)",
                "chest_inches": 40.0,
                "length_inches": 27.0,
                "price_inr": 899.0,
                "condition_score": "8/10 Faded Vintage",
                "status": "available",
            },
            {
                "title": "Y2K Diesel Low-Rise Flared Cargo Pants - Washed Olive",
                "aesthetic": "Y2K / Cyberpunk",
                "category": "Bottoms",
                "size_label": "32x30",
                "chest_inches": None,
                "length_inches": 39.0,
                "price_inr": 1199.0,
                "condition_score": "10/10 Mint",
                "status": "available",
            },
            {
                "title": "Vintage Ralph Lauren Cable Knit V-Neck Sweater - Cream",
                "aesthetic": "Old Money / Preppy",
                "category": "Tops",
                "size_label": "XL",
                "chest_inches": 46.0,
                "length_inches": 29.0,
                "price_inr": 1299.0,
                "condition_score": "9.5/10 Flawless",
                "status": "available",
            },
        ]

        for item_data in demo_items:
            item = DropItem(
                drop_id=drop.id,
                title=item_data["title"],
                aesthetic=item_data["aesthetic"],
                category=item_data["category"],
                size_label=item_data["size_label"],
                chest_inches=item_data["chest_inches"],
                length_inches=item_data["length_inches"],
                price_inr=item_data["price_inr"],
                condition_score=item_data["condition_score"],
                status=item_data["status"],
                created_at=utcnow(),
            )
            db.add(item)

        db.commit()
        print(f"Added {len(demo_items)} demo vintage pieces to drop!")

    db.close()
    print("Seed complete! Ready for testing.")

if __name__ == "__main__":
    seed_demo()
