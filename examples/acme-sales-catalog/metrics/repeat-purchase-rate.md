---
type: Metric
title: Repeat Purchase Rate
description: Share of customers with more than one completed order within their first 90 days.
tags: [sales, metric, retention]
timestamp: 2026-06-18T11:00:00Z
---

# Definition

The repeat purchase rate is the fraction of customers who place a second
completed order within 90 days of their first order.

# Formula

```sql
SELECT
  COUNTIF(orders_in_90d > 1) / COUNT(*) AS repeat_purchase_rate
FROM (
  SELECT customer_id, COUNT(*) AS orders_in_90d
  FROM acme.sales.orders o
  JOIN acme.sales.customers c USING (customer_id)
  WHERE o.order_date <= DATE_ADD(c.first_order_date, INTERVAL 90 DAY)
  GROUP BY customer_id
);
```

# Source

Joins [orders](/tables/orders.md) with [customers](/tables/customers.md) on
`customer_id`.

# Caveats

Customers acquired in the last 90 days have an incomplete window and should be
excluded from trend lines.
