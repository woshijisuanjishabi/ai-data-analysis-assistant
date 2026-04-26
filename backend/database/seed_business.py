"""
初始化业务数据库 business.db：创建表结构并插入示例数据。
可反复执行（每次会先 DROP 再 CREATE）。

运行方式：
    python -m database.seed_business
或
    python database/seed_business.py
"""

import os
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

# 允许从 backend/ 目录直接运行
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import settings


def get_db_path() -> Path:
    p = (BASE_DIR / settings.BUSINESS_DB_PATH).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def create_schema(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        DROP TABLE IF EXISTS sales;
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS departments;

        CREATE TABLE departments (
            id           INTEGER PRIMARY KEY,
            name         TEXT    NOT NULL UNIQUE,
            manager_name TEXT,
            created_at   DATE    NOT NULL
        );

        CREATE TABLE employees (
            id             INTEGER PRIMARY KEY,
            name           TEXT    NOT NULL,
            department_id  INTEGER NOT NULL,
            position       TEXT    NOT NULL,
            hire_date      DATE    NOT NULL,
            salary         REAL    NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );

        CREATE TABLE products (
            id        INTEGER PRIMARY KEY,
            name      TEXT    NOT NULL,
            category  TEXT    NOT NULL,
            price     REAL    NOT NULL,
            stock     INTEGER NOT NULL
        );

        CREATE TABLE customers (
            id         INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            region     TEXT    NOT NULL,
            level      TEXT    NOT NULL,
            created_at DATE    NOT NULL
        );

        CREATE TABLE sales (
            id             INTEGER PRIMARY KEY,
            order_date     DATE    NOT NULL,
            product_id     INTEGER NOT NULL,
            customer_id    INTEGER NOT NULL,
            employee_id    INTEGER NOT NULL,
            quantity       INTEGER NOT NULL,
            unit_price     REAL    NOT NULL,
            amount         REAL    NOT NULL,
            FOREIGN KEY (product_id)  REFERENCES products(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );

        CREATE INDEX idx_sales_date     ON sales(order_date);
        CREATE INDEX idx_sales_product  ON sales(product_id);
        CREATE INDEX idx_sales_customer ON sales(customer_id);
        CREATE INDEX idx_sales_employee ON sales(employee_id);
        CREATE INDEX idx_emp_dept       ON employees(department_id);
        """
    )


DEPARTMENTS = [
    (1, "技术部",  "张伟",  "2020-01-15"),
    (2, "市场部",  "李娜",  "2020-01-15"),
    (3, "销售部",  "王强",  "2020-01-15"),
    (4, "财务部",  "赵敏",  "2020-01-15"),
    (5, "人事部",  "孙丽",  "2020-01-15"),
]

EMPLOYEES = [
    # (name, dept_id, position, hire_date, salary)
    ("张伟", 1, "技术总监", "2020-01-15", 35000),
    ("陈涛", 1, "高级工程师", "2021-03-01", 25000),
    ("林洋", 1, "工程师",    "2022-06-10", 18000),
    ("黄磊", 1, "工程师",    "2023-02-20", 16000),
    ("李娜", 2, "市场总监",   "2020-02-01", 30000),
    ("周婷", 2, "市场专员",   "2021-09-15", 15000),
    ("吴迪", 2, "市场专员",   "2022-11-01", 14000),
    ("王强", 3, "销售总监",   "2020-01-20", 32000),
    ("徐磊", 3, "销售经理",   "2021-05-10", 22000),
    ("郑华", 3, "销售代表",   "2022-08-01", 12000),
    ("冯丽", 3, "销售代表",   "2023-01-15", 12000),
    ("宋阳", 3, "销售代表",   "2023-07-01", 11000),
    ("赵敏", 4, "财务总监",   "2020-03-01", 28000),
    ("钱晨", 4, "会计",       "2022-04-10", 13000),
    ("孙丽", 5, "人事经理",   "2020-05-15", 20000),
]

PRODUCTS = [
    ("笔记本电脑",   "电子产品", 6500.00, 120),
    ("台式机",       "电子产品", 4800.00,  80),
    ("显示器",       "电子产品", 1800.00, 200),
    ("机械键盘",     "电子产品",  450.00, 350),
    ("无线鼠标",     "电子产品",  180.00, 500),
    ("办公椅",       "办公家具", 1200.00, 150),
    ("升降办公桌",   "办公家具", 2500.00,  60),
    ("文件柜",       "办公家具",  800.00,  90),
    ("A4复印纸",     "办公耗材",   28.00,2000),
    ("中性笔",       "办公耗材",    3.50,5000),
    ("订书机",       "办公耗材",   35.00, 800),
    ("投影仪",       "电子产品", 3800.00,  30),
]

CUSTOMERS = [
    ("华东贸易有限公司",   "华东", "A级", "2022-03-10"),
    ("北方科技集团",       "华北", "A级", "2021-08-20"),
    ("南方实业股份",       "华南", "A级", "2020-11-05"),
    ("西部建设工程",       "西北", "B级", "2023-02-14"),
    ("东方商务咨询",       "华东", "B级", "2022-09-01"),
    ("中原机械制造",       "华中", "B级", "2021-12-12"),
    ("沿海进出口公司",     "华南", "A级", "2020-06-18"),
    ("西南物流集团",       "西南", "B级", "2023-05-22"),
    ("北辰新能源",         "华北", "C级", "2023-10-30"),
    ("金海餐饮连锁",       "华东", "C级", "2024-01-15"),
    ("星辰教育科技",       "华北", "B级", "2023-04-08"),
    ("蓝海金融服务",       "华南", "A级", "2021-07-25"),
]


def seed_data(cur: sqlite3.Cursor) -> None:
    # departments
    cur.executemany(
        "INSERT INTO departments(id, name, manager_name, created_at) VALUES (?,?,?,?)",
        DEPARTMENTS,
    )

    # employees
    cur.executemany(
        "INSERT INTO employees(name, department_id, position, hire_date, salary) VALUES (?,?,?,?,?)",
        EMPLOYEES,
    )

    # products
    cur.executemany(
        "INSERT INTO products(name, category, price, stock) VALUES (?,?,?,?)",
        PRODUCTS,
    )

    # customers
    cur.executemany(
        "INSERT INTO customers(name, region, level, created_at) VALUES (?,?,?,?)",
        CUSTOMERS,
    )

    # sales — 生成 2024 全年 + 2025 前几个月的订单
    rng = random.Random(42)
    product_rows  = cur.execute("SELECT id, price FROM products").fetchall()
    customer_ids  = [r[0] for r in cur.execute("SELECT id FROM customers").fetchall()]
    sales_emp_ids = [
        r[0] for r in cur.execute(
            "SELECT id FROM employees WHERE department_id = 3"
        ).fetchall()
    ]

    sales_rows = []
    start = date(2024, 1, 1)
    end   = date(2025, 3, 31)
    days  = (end - start).days

    for _ in range(800):
        d = start + timedelta(days=rng.randint(0, days))
        pid, price = rng.choice(product_rows)
        cid = rng.choice(customer_ids)
        eid = rng.choice(sales_emp_ids)
        qty = rng.randint(1, 20)
        # 价格偶尔折扣
        unit = round(price * rng.choice([1.0, 1.0, 1.0, 0.95, 0.9]), 2)
        amount = round(unit * qty, 2)
        sales_rows.append((d.isoformat(), pid, cid, eid, qty, unit, amount))

    cur.executemany(
        """
        INSERT INTO sales(order_date, product_id, customer_id, employee_id,
                          quantity, unit_price, amount)
        VALUES (?,?,?,?,?,?,?)
        """,
        sales_rows,
    )


def main() -> None:
    db_path = get_db_path()
    print(f"[seed] 目标数据库: {db_path}")
    if db_path.exists():
        os.remove(db_path)
        print(f"[seed] 已删除旧数据库")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        create_schema(cur)
        seed_data(cur)
        conn.commit()

        # 打印统计
        print("\n[seed] 数据写入完成，当前统计：")
        for tbl in ["departments", "employees", "products", "customers", "sales"]:
            n = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  - {tbl:<12}  {n} 行")
    finally:
        conn.close()

    print(f"\n[OK] 完成：{db_path}")


if __name__ == "__main__":
    main()
