# 演示用例

以下是系统的真实运行效果，所有结果均由 Qwen3 自动生成 SQL 并查询业务数据库得出。

---

## 案例 1：空结果处理

**提问**
> 2027 年的销售数据是怎样的？

**系统行为**
- 自动生成 SQL，JOIN sales / products / customers / employees 四张表
- 执行查询，返回 0 条结果
- 以自然语言告知用户数据库中无该年份记录，不报错、不崩溃

**生成 SQL**
```sql
SELECT s.id, s.order_date, p.name AS product_name,
       c.name AS customer_name, e.name AS employee_name
FROM sales s
JOIN products p ON s.product_id = p.id
JOIN customers c ON s.customer_id = c.id
JOIN employees e ON s.employee_id = e.id
WHERE strftime('%Y', s.order_date) = '2027'
ORDER BY s.order_date
LIMIT 200;
```

**回答**
> 2027 年的销售数据为空，数据库中暂无任何发生在 2027 年的销售记录。

---

## 案例 2：员工销售额排名

**提问**
> 每个销售员工在 2024 年的销售额排名

**系统行为**
- 识别出需要对员工维度聚合销售数据
- 生成带 ROW_NUMBER 窗口函数的复杂 SQL
- 自动在右侧生成柱状图，以销售额降序排列

**生成 SQL**
```sql
SELECT
    e.name AS employee_name,
    SUM(s.amount) AS total_sales_2024,
    ROW_NUMBER() OVER (ORDER BY SUM(s.amount) DESC) AS rank
FROM sales s
JOIN employees e ON s.employee_id = e.id
WHERE strftime('%Y', s.order_date) = '2024'
GROUP BY e.id, e.name
ORDER BY total_sales_2024 DESC
LIMIT 200;
```

**回答**
> 2024 年销售额排名前 5 的销售员工依次是：郑华（284.2 万元）、徐磊（258.0 万元）、宋阳（253.4 万元）、冯丽（237.5 万元）和王强（231.9 万元），数据已按销售额降序排列。

**图表**：柱状图，X 轴为员工姓名，Y 轴为销售额（元）

---

## 案例 3：多轮对话 — 上下文追问

**提问（接上一轮）**
> 其中销售额最高的那个人，他卖的什么产品最多？

**系统行为**
- 读取会话历史，自动理解"销售额最高的那个人"指郑华
- 使用子查询先找到郑华的 employee_id，再统计其各产品销售数量
- 无需用户重新描述背景

**生成 SQL**
```sql
SELECT
    p.name AS product_name,
    SUM(s.quantity) AS total_quantity
FROM sales s
JOIN products p ON s.product_id = p.id
WHERE s.employee_id = (
    SELECT e.id
    FROM sales s2
    JOIN employees e ON s2.employee_id = e.id
    WHERE strftime('%Y', s2.order_date) = '2024'
    GROUP BY e.id
    ORDER BY SUM(s2.amount) DESC
    LIMIT 1
)
GROUP BY p.id, p.name
ORDER BY total_quantity DESC
LIMIT 1;
```

**回答**
> 销售额最高的员工销售最多的产品是"笔记本电脑"，共售出 203 台。

**图表**：柱状图，展示该员工各产品销售量

---

## 案例 4：开放式探索

**提问**
> 给我随便看点有趣的

**系统行为**
- 没有明确问题，系统自主选择分析角度
- 主动关联库存与销售数据，找出"低库存但高销售额"的商品
- 生成包含两个系列（总销售额 + 当前库存）的复合柱状图

**生成 SQL**
```sql
SELECT
    p.name AS product_name,
    p.category AS category,
    SUM(s.amount) AS total_sales,
    p.stock AS current_stock
FROM sales s
JOIN products p ON s.product_id = p.id
GROUP BY p.id, p.name, p.category, p.stock
HAVING p.stock < 50
ORDER BY total_sales DESC
LIMIT 5;
```

**回答**
> 我们发现库存低于 50 台的"投影仪"（电子产品类）销售额高达 269 万元，是当前低库存商品中销售表现最强的单品。

**图表**：柱状图，X 轴为商品名，双系列展示总销售额与当前库存

---

## 功能覆盖总结

| 案例 | 验证能力 |
|------|---------|
| 案例 1 | 空结果兜底处理，不报错 |
| 案例 2 | 多表 JOIN + 窗口函数 + 图表生成 |
| 案例 3 | 多轮上下文记忆，追问不需要重复背景 |
| 案例 4 | 开放式提问，系统主动选择分析视角 |
