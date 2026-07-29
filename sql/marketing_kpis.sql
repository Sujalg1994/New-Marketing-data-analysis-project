-- PostgreSQL marketing KPI queries
-- Table expected: marketing_campaigns

-- 1. Overall executive KPIs
SELECT
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    ROUND(SUM(spend_gbp)::numeric, 2) AS spend_gbp,
    ROUND(SUM(revenue_gbp)::numeric, 2) AS revenue_gbp,
    ROUND(SUM(clicks)::numeric / NULLIF(SUM(impressions), 0), 4) AS ctr,
    ROUND(SUM(conversions)::numeric / NULLIF(SUM(clicks), 0), 4) AS conversion_rate,
    ROUND(SUM(spend_gbp)::numeric / NULLIF(SUM(conversions), 0), 2) AS cpa_gbp,
    ROUND(SUM(revenue_gbp)::numeric / NULLIF(SUM(spend_gbp), 0), 2) AS roas
FROM marketing_campaigns;

-- 2. Channel performance: aggregate totals before calculating rates
SELECT
    channel,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    ROUND(SUM(spend_gbp)::numeric, 2) AS spend_gbp,
    ROUND(SUM(revenue_gbp)::numeric, 2) AS revenue_gbp,
    ROUND(SUM(clicks)::numeric / NULLIF(SUM(impressions), 0), 4) AS ctr,
    ROUND(SUM(conversions)::numeric / NULLIF(SUM(clicks), 0), 4) AS conversion_rate,
    ROUND(SUM(spend_gbp)::numeric / NULLIF(SUM(conversions), 0), 2) AS cpa_gbp,
    ROUND(SUM(revenue_gbp)::numeric / NULLIF(SUM(spend_gbp), 0), 2) AS roas
FROM marketing_campaigns
GROUP BY channel
ORDER BY roas DESC;

-- 3. Monthly trend
SELECT
    DATE_TRUNC('month', date)::date AS month,
    ROUND(SUM(spend_gbp)::numeric, 2) AS spend_gbp,
    ROUND(SUM(revenue_gbp)::numeric, 2) AS revenue_gbp,
    SUM(conversions) AS conversions,
    ROUND(SUM(revenue_gbp)::numeric / NULLIF(SUM(spend_gbp), 0), 2) AS roas
FROM marketing_campaigns
GROUP BY 1
ORDER BY 1;

-- 4. Customer segment value
SELECT
    customer_segment,
    SUM(conversions) AS conversions,
    ROUND(SUM(revenue_gbp)::numeric, 2) AS revenue_gbp,
    ROUND(SUM(spend_gbp)::numeric / NULLIF(SUM(conversions), 0), 2) AS cpa_gbp,
    ROUND(SUM(revenue_gbp)::numeric / NULLIF(SUM(spend_gbp), 0), 2) AS roas
FROM marketing_campaigns
GROUP BY customer_segment
ORDER BY revenue_gbp DESC;

-- 5. A/B test descriptive performance
SELECT
    ab_variant,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    ROUND(SUM(conversions)::numeric / NULLIF(SUM(clicks), 0), 4) AS conversion_rate,
    ROUND(SUM(revenue_gbp)::numeric, 2) AS revenue_gbp
FROM marketing_campaigns
GROUP BY ab_variant
ORDER BY ab_variant;

-- 6. Campaigns that spend heavily but underperform account average ROAS
WITH campaign_performance AS (
    SELECT
        campaign,
        SUM(spend_gbp) AS spend_gbp,
        SUM(revenue_gbp) AS revenue_gbp,
        SUM(revenue_gbp) / NULLIF(SUM(spend_gbp), 0) AS roas
    FROM marketing_campaigns
    GROUP BY campaign
),
benchmark AS (
    SELECT SUM(revenue_gbp) / NULLIF(SUM(spend_gbp), 0) AS portfolio_roas
    FROM marketing_campaigns
)
SELECT
    campaign,
    ROUND(spend_gbp::numeric, 2) AS spend_gbp,
    ROUND(revenue_gbp::numeric, 2) AS revenue_gbp,
    ROUND(roas::numeric, 2) AS roas
FROM campaign_performance
CROSS JOIN benchmark
WHERE roas < portfolio_roas
ORDER BY spend_gbp DESC;
