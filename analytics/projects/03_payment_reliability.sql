-- Project 3: Payment Reliability and Operations Analytics

-- Payment-mode success rate
SELECT payment_mode,
       SUM(payment_attempts) AS attempts,
       SUM(successful_payments) AS successes,
       SUM(failed_payments) AS failures,
       ROUND(100.0 * SUM(successful_payments) / NULLIF(SUM(payment_attempts),0),2)
           AS success_rate_pct
FROM marts.payment_performance
GROUP BY payment_mode
ORDER BY success_rate_pct;

-- Daily failure-rate spikes
SELECT full_date,
       SUM(payment_attempts) AS attempts,
       SUM(failed_payments) AS failures,
       ROUND(100.0 * SUM(failed_payments) / NULLIF(SUM(payment_attempts),0),2)
           AS failure_rate_pct
FROM marts.payment_performance
GROUP BY full_date
HAVING SUM(payment_attempts) >= 5
ORDER BY failure_rate_pct DESC, full_date DESC
LIMIT 30;
