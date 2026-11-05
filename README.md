# MarketIQ — Marketplace Supply & Demand Analytics

## Business Problem

Short-term rental platforms like Airbnb operate as two-sided marketplaces: hosts supply listings, guests generate demand. Understanding where supply and demand are out of balance — and what drives pricing power — is the core problem this project addresses.

Using London Inside Airbnb data, the project answers four questions:

1. **Supply** — how concentrated is the market, who controls the listings, and where is supply growing?
2. **Demand** — how is occupancy distributed across boroughs, and what seasonal patterns drive booking behaviour?
3. **Pricing** — how price-elastic is demand, and what is the revenue-maximising price by market segment?
4. **Opportunity** — which boroughs are under-supplied relative to demand, and what should hosts do about it?

---

## Live Dashboard

*(Link added after Streamlit deployment)*

---

## Key Findings

| Area | Finding |
|------|---------|
| Market concentration | A small share of professional hosts (10+ listings) controls a disproportionate share of supply — Gini > 0.6 |
| Ghost supply | A material share of listings have `availability_365 = 0` — blocked capital that inflates the listing count without serving demand |
| Occupancy | Median occupancy ~50–60%; top-quartile listings achieve 70%+ driven by Superhost status and competitive pricing |
| Seasonality | Demand peaks in summer (~1.4× annual average); winter trough ~0.6× — a 2× swing across the year |
| Price elasticity | Demand is moderately elastic: a 10% price increase is associated with a ~5–8% occupancy reduction across room types |
| Revenue peak | Revenue-maximising price (across the full market) estimated at £80–120/night — premium above this hurts occupancy faster than it raises revenue |
| Top opportunity | Inner-London boroughs with high review density and constrained supply score highest on the opportunity index |

---

## Project Structure

```
MarketIQ/
├── data/
│   └── processed/                        # Outputs from all four notebooks
│       ├── listings_clean.csv
│       ├── listings_with_occupancy.csv
│       ├── borough_demand.csv
│       ├── borough_balance.csv
│       ├── borough_master.csv
│       ├── borough_pricing_summary.csv
│       ├── host_segments.csv
│       ├── seasonal_index.csv
│       ├── demand_by_dow.csv
│       ├── demand_by_month.csv
│       ├── demand_forecast.csv
│       ├── price_elasticity.csv
│       ├── pricing_analysis.csv
│       ├── market_opportunity.csv
│       └── dashboard_kpis.csv
├── notebooks/
│   ├── 01_supply_analysis.ipynb          # Host concentration, Gini, ghost supply
│   ├── 02_demand_analysis.ipynb          # Occupancy estimation, seasonality, borough demand
│   ├── 03_pricing_analytics.ipynb        # Price elasticity, revenue optimisation, competitive positioning
│   └── 04_recommendations_forecasting.ipynb  # Demand forecast, opportunity scoring, host recommendations
├── app.py                                # Streamlit dashboard (5 tabs)
├── outputs/figures/                      # Saved charts from notebooks
├── requirements.txt
└── README.md
```

---

## Methodology

### Notebook 01 — Supply Analysis

- **Price cleaning**: stripped `$` and `,` from the raw price string column using regex
- **Host classification**: four segments — Casual (1 listing), Small multi (2–3), Medium multi (4–9), Professional (10+)
- **Gini coefficient**: computed from scratch using the standard formula `G = (2Σ i*yi − (n+1)Σ yi) / (n Σ yi)` to quantify supply concentration
- **Lorenz curve**: cumulative host share vs cumulative listing share to visualise inequality
- **Ghost supply**: listings with `availability_365 = 0` identified as blocked capital — either long-term let, owner-occupied, or delisted in practice
- **Availability bands**: segmented listings into five bands (0–30, 31–90, 91–180, 181–270, 271–365 days) to distinguish casual from commercial operators

### Notebook 02 — Demand Analysis

**Occupancy estimation** — Airbnb does not publish booking data. The industry-standard proxy uses the calendar file:

```
available = 'f'  → date is blocked (booked or host-blocked)
available = 't'  → date is open to book
Occupancy rate = days_blocked / total_calendar_days
```

This slightly over-estimates true bookings (host-blocked days are included) but is the approach used by Inside Airbnb and AirDNA. A more refined version uses the San Francisco review-rate model: `estimated_nights = (reviews_per_month / review_rate) × avg_length_of_stay`.

**Demand-supply balance score**: normalised demand intensity (reviews per listing) and supply (listing count) each to 0–1 with min-max scaling, then computed the difference. Positive = under-supplied (demand pressure exceeds relative supply); negative = over-supplied.

**Seasonal decomposition**: monthly review volume used as a demand proxy; seasonal index computed as the average monthly deviation from the annual mean.

### Notebook 03 — Pricing Analytics

**Price elasticity** — log-log OLS regression:

```
log(occupancy) = β₀ + β₁ × log(price)
```

`β₁` is the price elasticity of demand. The log-log specification assumes constant elasticity across the price range — standard for demand curve estimation. It also handles the right-skewed price distribution without transformation. Limitation: this is a correlational estimate, not causal. Better-quality listings command higher prices *and* higher occupancy simultaneously, which biases `β₁` upward.

**Revenue optimisation**: revenue = price × occupancy(price). The optimal price is estimated by substituting the fitted elasticity into the first-order condition. The full revenue curve is plotted so stakeholders can see that the peak is flat — small price deviations cost little revenue.

**Competitive positioning**: each listing's price is benchmarked against the median price in its borough × room type segment. Listings are classified as Very cheap (<70%), Cheap (70–90%), At market (90–110%), Premium (110–130%), or Luxury (>130%) of the segment median.

### Notebook 04 — Recommendations & Forecasting

**Demand forecast** — manual trend + seasonal decomposition:
1. Fit a linear trend to the monthly review series, excluding the COVID trough (Mar 2020 – Jun 2021)
2. Compute average deviations from that trend by calendar month as seasonal factors
3. Extrapolate the trend and add seasonal factors to produce a 12-month forward estimate

This is equivalent to a Holt-Winters additive model. A production version would use Prophet or STL decomposition to handle structural breaks and time-varying seasonality.

**Market opportunity score** — composite index combining four normalised signals:

| Signal | Weight | Rationale |
|--------|--------|-----------|
| Reviews per listing (demand intensity) | 30% | Captures relative demand vs supply |
| Supply-demand balance score | 25% | Directly measures under/over-supply |
| Estimated monthly revenue | 30% | Captures absolute earnings potential |
| % listings priced at premium | 15% | Proxy for pricing power in the market |

Weights are explicit and adjustable — a PCA approach would let the data determine them, but explicit weights are more interpretable for stakeholders.

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| Market Overview | 8 KPI cards, listings by borough bar chart, room type pie chart, full borough table |
| Demand & Seasonality | Occupancy distribution, seasonal index, day-of-week occupancy, 12-month demand forecast |
| Pricing Analytics | Price distribution, elasticity by room type, revenue optimisation curve, competitive positioning |
| Market Opportunity | Opportunity score rankings, supply vs demand scatter, full opportunity table |
| Host Recommendations | Segment metrics (occupancy, price, revenue, Superhost %), recommendation cards by host type |

---

## Technical Stack

| Layer | Tools |
|-------|-------|
| Data source | Inside Airbnb — London (`listings.csv.gz`, `reviews.csv.gz`, `calendar.csv.gz`) |
| Data processing | pandas, numpy |
| Statistical analysis | scipy (OLS, z-scores), scikit-learn (MinMaxScaler, LinearRegression) |
| Visualisation | matplotlib, seaborn (notebooks), plotly (dashboard) |
| Dashboard | Streamlit |
| Environment | Google Colab |

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run notebooks in order in Google Colab
#    01 → 02 → 03 → 04
#    Each notebook uploads raw data and saves processed CSVs

# 3. Copy processed CSVs to data/processed/

# 4. Launch dashboard
streamlit run app.py
```

---

## Data Source

[Inside Airbnb](http://insideairbnb.com/get-the-data/) — London dataset. Inside Airbnb scrapes publicly visible Airbnb listing data and makes it available for research. The dataset includes listings, reviews, and calendar availability for all London boroughs. It is a snapshot, not a live feed — occupancy and pricing patterns reflect the scrape date.

**Key limitation**: calendar data marks a date as unavailable without distinguishing between *booked* and *host-blocked*. All occupancy figures in this project are proxies, not actuals.

---

## Interview Talking Points

**On marketplace analytics:**
A two-sided marketplace has supply-side and demand-side dynamics that interact. Analysing them separately and then looking at the balance — which side is growing faster, which boroughs are constrained — is more actionable than looking at either alone. The supply-demand balance score is a lightweight way to operationalise this for non-technical stakeholders.

**On price elasticity:**
The log-log OLS estimate is a quick, interpretable proxy. Its main limitation is omitted variable bias — listing quality, photos, and location all affect both price and occupancy simultaneously. A proper causal estimate would require a natural experiment (e.g. Airbnb changing its search ranking algorithm) or an instrumental variable that shifts price without directly affecting occupancy. I would use this estimate for directional guidance, not for precise revenue forecasting.

**On the Gini coefficient:**
The Gini measures inequality in a distribution. A value of 0 means every host has the same number of listings; a value of 1 means one host owns everything. In short-term rental markets, Gini > 0.6 is common because professional operators are economically incentivised to scale — each additional listing has near-zero marginal research cost once the management infrastructure is in place.

**On occupancy estimation:**
The calendar proxy conflates booked nights with host-blocked nights. A better estimate uses the San Francisco model: divide reviews per month by an estimated review rate (typically 0.5–0.72 based on Airbnb's own published data) to get estimated stays per month, then multiply by average length of stay. I used the calendar proxy because it is simpler and the Inside Airbnb data already provides it — but I would flag the limitation in any client-facing report.
