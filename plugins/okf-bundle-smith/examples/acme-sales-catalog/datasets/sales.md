---
type: Dataset
title: Sales Dataset
description: Curated BigQuery dataset holding completed orders, order line items, and customer records for analytics.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales
tags: [sales, dataset, bigquery]
timestamp: 2026-05-28T14:30:00Z
---

# Summary

The `acme.sales` dataset is the governed source of truth for completed-order
analytics. It is refreshed daily and is safe for cross-team reporting.

# Tables

* [orders](/tables/orders.md) - one row per completed order.
* [order_items](/tables/order-items.md) - one row per line item.
* [customers](/tables/customers.md) - one row per customer.

# Access

Read access is granted through the `analytics-readers` group. Partition pruning
on `order_date` is required for any query scanning more than 90 days, per
BigQuery [cost controls](https://cloud.google.com/bigquery/docs/best-practices-costs).

# Citations

[1] [BigQuery: controlling costs](https://cloud.google.com/bigquery/docs/best-practices-costs)
