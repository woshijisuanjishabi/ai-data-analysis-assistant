"""快速抽查 business.db 的数据合理性。"""
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from config import settings

db_path = (BASE_DIR / settings.BUSINESS_DB_PATH).resolve()
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("【各部门销售额】")
rows = cur.execute("""
    SELECT d.name, COUNT(s.id), ROUND(SUM(s.amount), 2)
    FROM departments d
    JOIN employees  e ON e.department_id = d.id
    JOIN sales      s ON s.employee_id  = e.id
    GROUP BY d.name
    ORDER BY 3 DESC
""").fetchall()
for r in rows:
    print(f"  {r[0]:<8}  订单数 {r[1]:>4}  销售额 {r[2]:>12,.2f}")

print("\n【各品类销售 TOP3】")
rows = cur.execute("""
    SELECT p.category, COUNT(s.id), ROUND(SUM(s.amount), 2)
    FROM products p JOIN sales s ON s.product_id = p.id
    GROUP BY p.category
    ORDER BY 3 DESC
""").fetchall()
for r in rows:
    print(f"  {r[0]:<10}  订单数 {r[1]:>4}  销售额 {r[2]:>12,.2f}")

print("\n【2024 各月销售趋势】")
rows = cur.execute("""
    SELECT strftime('%Y-%m', order_date) AS ym,
           COUNT(*) AS orders,
           ROUND(SUM(amount), 2) AS total
    FROM sales
    WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
    GROUP BY ym
    ORDER BY ym
""").fetchall()
for r in rows:
    print(f"  {r[0]}  订单数 {r[1]:>3}  销售额 {r[2]:>12,.2f}")

conn.close()
