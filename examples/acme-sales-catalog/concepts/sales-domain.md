---
type: Reference
title: Sales Domain
description: Entry point for the Acme sales analytics knowledge bundle and how its datasets, tables, and metrics fit together.
tags: [sales, domain, overview]
timestamp: 2026-06-20T09:00:00Z
---

# Summary

The sales domain covers how Acme records and analyzes completed customer
orders. It is the recommended starting point for an agent answering questions
about revenue, customers, or order behavior.

# Scope

This domain includes the curated [sales dataset](/datasets/sales.md), the core
[orders](/tables/orders.md) and [customers](/tables/customers.md) tables, and
the governed metrics built on top of them.

# Key facts

* Orders are immutable once completed; corrections are issued as new rows.
* Every order belongs to exactly one customer.
* Revenue reporting is owned by the Finance Analytics team.

# Relationships

* Curated data lives in the [sales dataset](/datasets/sales.md).
* The headline metric is [gross revenue](/metrics/gross-revenue.md).
* Daily freshness is maintained by the
  [daily revenue refresh](/processes/daily-revenue-refresh.md) runbook.
