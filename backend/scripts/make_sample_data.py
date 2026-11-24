"""Generate demo CSVs in data/ with dates relative to --today (default: actual today).

    python backend/scripts/make_sample_data.py            # dates relative to today
    python backend/scripts/make_sample_data.py --today 2026-11-24
"""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"

# name, return_window_days, discount_allowed, max_discount_pct
COMPANIES = [
    ("Square Pharma", 90, True, 10),
    ("Beximco Pharma", 60, True, 15),
    ("Incepta", 90, False, ""),
    ("Renata", "no return", True, 20),
    ("ACI Ltd", 60, False, ""),
    ("Local Herbal Co", "no return", False, ""),
]

# name, company, batch, qty, days_to_expiry, cost, price, avg_daily_sales
MEDICINES = [
    # --- 3 demo cases from the problem statement ---
    ("Napa Extra 500mg", "Beximco Pharma", "B-101", 500, 120, 1.2, 1.5, 20),    # fast seller -> NO alert
    ("Seclo 20mg", "Square Pharma", "S-220", 300, 98, 5.0, 7.0, 1.5),           # -> RETURN (deadline +8d)
    ("Cough Syrup 100ml", "Local Herbal Co", "C-310", 80, 60, 45, 60, 0.3),     # -> OTHER
    # --- more variety ---
    ("Ace 500mg", "Square Pharma", "S-101", 800, 200, 0.9, 1.2, 25),
    ("Maxpro 20mg", "Renata", "R-330", 250, 75, 6.0, 8.0, 0.8),                 # DISCOUNT
    ("Ciprocin 500mg", "Square Pharma", "S-415", 200, 105, 11, 14, 0.5),        # RETURN soon
    ("Fexo 120mg", "Incepta", "I-210", 400, 90, 7.5, 10, 2),                    # RETURN
    ("Alatrol 10mg", "Square Pharma", "S-512", 150, 45, 2.5, 3.5, 0.2),
    ("Zimax 500mg", "Beximco Pharma", "B-205", 120, 150, 38, 50, 1),
    ("Rivotril 0.5mg", "Incepta", "I-330", 60, 300, 4, 6, 0.1),
    ("Orsaline-N", "Renata", "R-118", 1000, 20, 1.5, 2, 12),                    # sells fast but near expiry
    ("Napa Syrup 60ml", "Beximco Pharma", "B-107", 90, 180, 20, 28, 1.2),
    ("Monas 10mg", "Square Pharma", "S-620", 300, 130, 8, 11, 3),
    ("Neotack 40mg", "ACI Ltd", "A-410", 180, 85, 3.2, 4.5, 0.4),               # RETURN-ish
    ("Tofen 1mg", "ACI Ltd", "A-111", 220, 400, 3, 4, 1.5),
    ("Losectil 20mg", "Incepta", "I-510", 340, 70, 5.5, 7.5, 0.9),
    ("Vitamin C 500mg", "Local Herbal Co", "L-001", 700, 55, 2, 3, 0.7),        # OTHER
    ("Calbo-D", "Renata", "R-402", 280, 140, 6, 8, 2),
    ("Cef-3 200mg", "Square Pharma", "S-731", 160, 110, 22, 30, 1.4),
    ("Filmet 400mg", "Beximco Pharma", "B-308", 500, 95, 2.5, 3.5, 4),
    ("Ranitidine 150mg", "ACI Ltd", "A-212", 600, 30, 1.8, 2.5, 6),
    ("Dexpoten 25mg", "Renata", "R-505", 140, 160, 7, 9, 0.6),
    ("Omidon 10mg", "Incepta", "I-611", 260, 60, 2.8, 4, 0.5),
    ("Amodis 400mg", "Square Pharma", "S-808", 320, 210, 3.4, 5, 2.5),
    ("Moxacil 500mg", "Beximco Pharma", "B-419", 90, 40, 9, 12, 0.3),
    ("Herbal Tonic 200ml", "Local Herbal Co", "L-014", 45, 90, 80, 110, 0.15),  # OTHER
    ("Hexisol Gargle", "Renata", "R-077", 70, 120, 55, 75, 0.2),
    ("Zinc Syrup", "ACI Ltd", "A-330", 110, 100, 30, 42, 0.6),
    ("Insulin 70/30", "Incepta", "I-901", 40, 65, 650, 780, 0.5),
    ("ORS Powder", "Local Herbal Co", "L-020", 900, 300, 1.2, 2, 5),
    ("Paracetamol 500mg", "Square Pharma", "S-005", 1200, 220, 0.5, 0.8, 30),
    ("Antacid Plus", "Beximco Pharma", "B-512", 200, 50, 2.2, 3, 0.4),
    ("Eye Drops", "Renata", "R-250", 60, 35, 40, 55, 0.2),
    ("Bisoprolol 5mg", "Square Pharma", "S-915", 180, 140, 4.5, 6, 1),
    ("Cetirizine 10mg", "ACI Ltd", "A-099", 420, 110, 1.1, 1.6, 3),
    ("Expired Sample Cream", "Local Herbal Co", "L-777", 12, -10, 60, 90, 0.1),  # already expired
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=None, help="YYYY-MM-DD")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()
    rng = random.Random(42)
    DATA.mkdir(exist_ok=True)

    with open(DATA / "sample_companies.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "return_window_days", "discount_allowed", "max_discount_pct"])
        for name, window, disc, pct in COMPANIES:
            w.writerow([name, window, "yes" if disc else "no", pct])

    with open(DATA / "sample_medicines.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "batch", "quantity", "expiry_date", "company", "cost_price", "selling_price"])
        for name, comp, batch, qty, dte, cost, price, _ in MEDICINES:
            w.writerow([name, batch, qty, (today + timedelta(days=dte)).isoformat(), comp, cost, price])

    with open(DATA / "sample_sales.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["medicine", "batch", "sale_date", "quantity_sold"])
        for name, _, batch, _, _, _, _, avg in MEDICINES:
            for d in range(1, 31):
                sold = max(0, round(rng.gauss(avg, avg * 0.3)))
                if avg < 1:  # slow movers: sell 1 unit on some days
                    sold = 1 if rng.random() < avg else 0
                if sold:
                    w.writerow([name, batch, (today - timedelta(days=d)).isoformat(), sold])
    print(f"Wrote 3 CSVs to {DATA} (today={today}, {len(MEDICINES)} medicines)")


if __name__ == "__main__":
    main()
