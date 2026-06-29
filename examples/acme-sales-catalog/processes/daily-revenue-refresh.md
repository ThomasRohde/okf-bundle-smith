---
type: Runbook
title: Daily Revenue Refresh
description: Scheduled job that rebuilds the sales tables and validates gross revenue before publishing.
tags: [sales, runbook, operations]
timestamp: 2026-06-22T07:30:00Z
---

# Trigger

Runs at 06:00 UTC daily via the `sales-refresh` scheduled query, after upstream
ingestion completes.

# Preconditions

* Upstream `raw.orders` load for the prior day has succeeded.
* No active schema migration on [orders](/tables/orders.md).

# Steps

1. Rebuild [orders](/tables/orders.md) and `order_items` for the prior day.
2. Recompute [gross revenue](/metrics/gross-revenue.md) for the prior day.
3. Compare against the line-item reconciliation total.

# Validation

The day passes if gross revenue and the summed line totals agree within 0.5%.

# Rollback

If validation fails, restore the previous partition snapshot and page the
Finance Analytics on-call. Do not publish a failed partition.
