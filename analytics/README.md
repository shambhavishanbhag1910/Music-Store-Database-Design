# Analytics Project

The analytics layer is deliberately built on warehouse marts rather than the transactional database.

## Business questions answered

- How much completed revenue is generated daily/monthly?
- Which artists and genres drive revenue?
- What is average order value?
- Which customers have the highest lifetime value?
- What is the repeat purchase rate?
- Which customer RFM segments need retention or upsell actions?
- Which payment modes have the highest failure rate?
- Which products are bought together?
- Which playlist genres/artists have the strongest engagement?
- Are ETL pipelines meeting freshness and reliability expectations?

## KPI definitions

| KPI | Definition |
|---|---|
| Completed revenue | Sum of line-level net amount for completed orders |
| Completed orders | Distinct completed order IDs |
| Average order value | Completed revenue / completed orders |
| Lifetime value | Sum of completed line net amount per customer |
| Payment success rate | Successful payment attempts / all payment attempts |
| Repeat purchase rate | Customers with >1 completed order / purchasing customers |
| Playlist adds | Count of playlist-track relationships |

See `interview_grade_queries.sql` for advanced SQL examples.


## Portfolio analytics mini-projects

The `analytics/projects/` folder contains four focused analytics projects:

1. `01_sales_performance.sql` — revenue growth, genre mix and product contribution
2. `02_customer_360.sql` — RFM segmentation, retention and repeat purchase
3. `03_payment_reliability.sql` — payment-mode success and failure spikes
4. `04_playlist_engagement.sql` — engagement signals useful for recommendation analysis
