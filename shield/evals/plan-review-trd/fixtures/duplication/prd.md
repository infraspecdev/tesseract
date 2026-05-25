# Order Refund PRD

## Problem

Bytebite cannot currently refund a partially-fulfilled order without manual SQL intervention. The Orders database carries idempotent order_status transitions but the Payments side records refunds against the original capture only, so customer-care agents have to file a ticket against Payments and wait. The Q1 incident postmortem tracked 41 such tickets with median resolution time 38h.

## Users

Customer-care agents.

## Goals

Refunds should issue in seconds, not hours.
