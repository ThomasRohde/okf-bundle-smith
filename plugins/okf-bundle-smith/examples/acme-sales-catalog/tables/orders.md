---
type: Table
title: Orders
description: One row per completed customer order, including order total and the customer who placed it.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, table, orders]
timestamp: 2026-05-28T14:30:00Z
---

# Summary

`acme.sales.orders` records every completed order. Rows are immutable; refunds
and corrections are appended as new rows with a negative `order_total`.

# Schema

| column | type | description |
|---|---|---|
| `order_id` | STRING | Globally unique order identifier. Primary key. |
| `customer_id` | STRING | Foreign key to [customers](/tables/customers.md). |
| `order_date` | DATE | Partition column. Date the order completed. |
| `order_total` | NUMERIC | Order total in USD, net of discounts. |
| `status` | STRING | Always `completed` in this table. |

# Grain

One row per `order_id`. Line-level detail lives in
[order_items](/tables/order-items.md).

# Relationships

* Each order belongs to one [customer](/tables/customers.md).
* Each order has one or more [order items](/tables/order-items.md).
