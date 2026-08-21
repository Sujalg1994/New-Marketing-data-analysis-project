# Marketing Campaign Performance Analytics

An end-to-end **marketing data analyst portfolio project** for a UK retail business. It demonstrates how campaign data can be transformed into executive KPIs, channel and customer-segment insights, A/B-test evidence, and a practical budget recommendation.

> **Data note:** the dataset is synthetic and reproducibly generated. It is suitable for portfolio demonstration but should not be presented as real company data.

## Business problem

Marketing leaders need to know:

- Which channels produce profitable growth?
- Which customer segments generate the most revenue?
- Did creative variant B outperform variant A?
- How should the next £100,000 budget be allocated?
- Which campaigns require optimisation before further investment?

## Project results

Running the seeded analysis produces the following portfolio baseline:

| KPI | Result |
|---|---:|
| Revenue | £2.15m |
| Marketing spend | £630.4k |
| Conversions | 23,200 |
| ROAS | 3.41x |
| CPA | £27.17 |
| Best channel by ROAS | Email — 7.76x |
| Highest-revenue segment | Returning Customers — £739.5k |
| A/B test | Variant B significant, +5.37% relative conversion lift |

### Recommended action

Scale Email carefully because it has the strongest observed ROAS and lowest CPA. Maintain Paid Search and Paid Social as acquisition channels, but optimise targeting and creative before aggressive expansion. Display has the weakest ROAS and should be treated as a controlled test-and-learn channel rather than automatically receiving more budget.

## Repository structure

```text
.
├── dashboard/
│   └── app.py                     # Interactive Streamlit dashboard
├── sql/
│   └── marketing_kpis.sql         # PostgreSQL KPI and diagnostic queries
├── src/
│   ├── generate_data.py           # Seeded synthetic data generator
│   └── marketing_analysis.py      # KPI, A/B test and budget workflow
├── tests/
│   └── test_kpis.py               # Formula and significance tests
├── pyproject.toml                 # Pytest configuration
├── requirements.txt
└── README.md
```

The generated `data/` and `outputs/` folders are intentionally ignored by Git because they can be recreated from code.

## Analytical methods

- Marketing funnel KPIs: CTR, conversion rate, CPC, CPA, ROAS, profit and ROMI
- Correct weighted aggregation: totals are aggregated before non-additive rates are calculated
- Channel, campaign, segment and monthly performance analysis
- Two-proportion z-test for A/B conversion-rate comparison
- Guardrailed budget-allocation model using ROAS and conversion evidence
- Interactive filtering by date, region, channel and customer segment
- Unit tests for KPI formulas and statistical-test behaviour

## Run locally

```bash
git clone https://github.com/SanketCSakhare/New-Marketing-data-analysis-project.git
cd New-Marketing-data-analysis-project
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Generate the dataset and analysis outputs:

```bash
python src/generate_data.py
python src/marketing_analysis.py --budget 100000
```

Launch the dashboard:

```bash
streamlit run dashboard/app.py
```

Run tests:

```bash
python -m pytest -q
```

## SQL usage

Load the generated CSV into a PostgreSQL table named `marketing_campaigns`, then run `sql/marketing_kpis.sql`. The SQL file includes executive KPIs, channel performance, monthly trends, segment value, A/B descriptive results and underperforming-campaign diagnostics.

## Skills demonstrated

`Python` · `Pandas` · `NumPy` · `SQL` · `Streamlit` · `A/B testing` · `Marketing attribution KPIs` · `Budget optimisation` · `Data storytelling` · `Testing`

## Limitations

This is a portfolio simulation. The analysis does not claim causal attribution across channels, customer lifetime value, incrementality, marketing-mix modelling or multi-touch attribution. A real deployment would require validated source systems, agreed attribution rules, margin data and experiment governance.
