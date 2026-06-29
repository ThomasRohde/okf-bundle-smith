---
type: Metric
title: Gross Revenue
description: Total completed-order value in USD over a period, before refunds and tax adjustments.
tags: [sales, metric, revenue]
timestamp: 2026-06-18T11:00:00Z
---

# Definition

Gross revenue is the sum of `order_total` across all completed orders in the
reporting period.

# Formula

```sql
SELECT SUM(order_total) AS gross_revenue
FROM acme.sales.orders
WHERE order_date BETWEEN @start AND @end;
```

# Source

Derived from [orders](/tables/orders.md). Line-level reconciliation uses
[order_items](/tables/order-items.md).

# Caveats

* Refund rows carry a negative `order_total`, so gross revenue is already net of
  refunds that fall inside the same period.
* Tax and shipping are excluded.
