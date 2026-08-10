# 🎵 Music Store Database Design

A production-oriented **PostgreSQL relational database design** for a digital music store platform.

The project models the core business entities and transactions required for managing customers, artists, albums, tracks, genres, playlists, orders, and payments.

It demonstrates practical database engineering concepts including:

- Relational data modelling
- Primary and foreign keys
- Many-to-many relationships
- Business-rule constraints
- PostgreSQL ENUM types
- Indexing
- Database triggers
- Views
- Analytical SQL queries
- Logical and physical ERD design
- Business requirements documentation
- Data dictionary documentation

---

## 📌 Project Overview

A digital music platform needs to manage several interconnected business areas:

- Customers
- Artists
- Albums
- Tracks
- Genres
- Media formats
- Playlists
- Orders
- Order items
- Payments

The objective of this project is to design a structured and normalized PostgreSQL database that maintains:

- Data integrity
- Referential integrity
- Business-rule validation
- Query performance
- Scalability for future analytics and data engineering
- Clear technical and business documentation

---

## 🏗️ High-Level Architecture

```text
                         MUSIC STORE
                              │
                              ▼
                   ┌─────────────────────┐
                   │     PostgreSQL      │
                   │       OLTP DB       │
                   └─────────┬───────────┘
                             │
        ┌────────────────────┼─────────────────────┐
        │                    │                     │
        ▼                    ▼                     ▼
   Customers             Catalogue              Sales
        │                    │                     │
        │             Artist / Album              │
        │             Track / Genre               │
        │             Media Type                  │
        │                                          │
        ▼                                          ▼
   Playlists                                  Orders
        │                                          │
        ▼                                          ▼
 Playlist Tracks                              Order Items
                                                   │
                                                   ▼
                                               Payments