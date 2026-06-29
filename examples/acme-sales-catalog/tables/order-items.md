---
type: Table
title: Order Items
description: One row per line item within an order, linking products to the order that contains them.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=order_items
tags: [sales, table, line-items]
timestamp: 2026-05-28T14:30:00Z
---

# Summary

`acme.sales.order_items` records each product line within an order. Summing
`line_total` across an order reconciles to the parent order's `order_total`.

# Schema

| column | type | description |
|---|---|---|
| `order_item_id` | STRING | Globally unique line identifier. Primary key. |
| `order_id` | STRING | Foreign key to [orders](/tables/orders.md). |
| `product_id` | STRING | Catalog identifier for the product sold. |
| `quantity` | INT64 | Units sold on this line. |
| `line_total` | NUMERIC | Quantity times unit price, net of discounts, in USD. |

# Grain

One row per `order_item_id`. Many line items roll up to one
[order](/tables/orders.md).
