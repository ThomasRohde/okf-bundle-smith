---
type: Table
title: Customers
description: One row per customer, with acquisition channel and the date of first completed order.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=customers
tags: [sales, table, customers]
timestamp: 2026-05-28T14:30:00Z
---

# Summary

`acme.sales.customers` holds one record per customer. It is a slowly changing
dimension; the current row reflects the latest known attributes.

# Schema

| column | type | description |
|---|---|---|
| `customer_id` | STRING | Globally unique customer identifier. Primary key. |
| `acquisition_channel` | STRING | Channel that produced the first order. |
| `first_order_date` | DATE | Date of the customer's first completed order. |
| `country` | STRING | ISO 3166-1 alpha-2 country code. |

# Grain

One row per `customer_id`.

# Relationships

A customer places zero or more [orders](/tables/orders.md).
