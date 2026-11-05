import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="MarketIQ — London Airbnb Analytics",
    page_icon="🏠",
    layout="wide",
)

BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data" / "processed"

BLUE   = "#1B4F8A"
RED    = "#C0392B"
GREEN  = "#27AE60"
ORANGE = "#E67E22"
GREY   = "#95A5A6"
PURPLE = "#8E44AD"

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_csv(name, **kwargs):
    path = DATA_DIR / name
    if not path.exists():
        return None
    return pd.read_csv(path, **kwargs)

@st.cache_data
def get_borough_col(df):
    for c in df.columns:
        if "neighbourhood" in c.lower():
            if df[c].notna().sum() > 0:
                return c
    return df.columns[0]

def load_all():
    kpis         = load_csv("dashboard_kpis.csv")
    listings     = load_csv("listings_with_occupancy.csv", low_memory=False)
    bor_master   = load_csv("borough_master.csv")
    host_seg     = load_csv("host_segments.csv")
    seasonal     = load_csv("seasonal_index.csv")
    dow          = load_csv("demand_by_dow.csv")
    forecast     = load_csv("demand_forecast.csv", parse_dates=["year_month_dt"])
    elasticity   = load_csv("price_elasticity.csv")
    pricing      = load_csv("pricing_analysis.csv")
    opportunity  = load_csv("market_opportunity.csv")

    return dict(kpis=kpis, listings=listings, bor_master=bor_master,
                host_seg=host_seg, seasonal=seasonal, dow=dow,
                forecast=forecast, elasticity=elasticity,
                pricing=pricing, opportunity=opportunity)

data = load_all()

missing = [k for k, v in data.items() if v is None]
if missing:
    st.error(f"Missing processed files: {missing}. "
             f"Copy all CSVs from your Notebook 04 zip into `data/processed/`.")
    st.stop()

kpis        = data["kpis"].iloc[0]
listings    = data["listings"]
bor_master  = data["bor_master"]
host_seg    = data["host_seg"]
seasonal    = data["seasonal"]
dow         = data["dow"]
forecast    = data["forecast"]
elasticity  = data["elasticity"]
pricing     = data["pricing"]
opportunity = data["opportunity"]

borough_col = get_borough_col(bor_master)
bc_opp      = get_borough_col(opportunity)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🏠 MarketIQ — London Airbnb Market Analytics")
st.caption("Inside Airbnb data · Supply, Demand, Pricing & Market Opportunity")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Market Overview",
    "📈 Demand & Seasonality",
    "💷 Pricing Analytics",
    "🎯 Market Opportunity",
    "🏘️ Host Recommendations",
])

# ===========================================================================
# TAB 1 — Market Overview
# ===========================================================================
with tab1:
    st.subheader("Market Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Listings",    f"{int(kpis['total_listings']):,}")
    c2.metric("Total Hosts",       f"{int(kpis['total_hosts']):,}")
    c3.metric("Median Price/Night", f"£{kpis['median_price']:.0f}")
    c4.metric("Median Occupancy",  f"{kpis['median_occupancy_pct']:.0f}%")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Median Annual Revenue", f"£{kpis['median_annual_revenue']:,.0f}")
    c6.metric("Entire Home Share",     f"{kpis['entire_home_pct']:.0f}%")
    c7.metric("Superhost Share",       f"{kpis['superhost_pct']:.0f}%")
    c8.metric("Top Opportunity Borough", str(kpis["top_borough"]))

    st.divider()
    col_left, col_right = st.columns(2)

    # Listings by borough
    with col_left:
        bor_plot = bor_master.sort_values("listings", ascending=True).tail(20)
        fig = px.bar(bor_plot, x="listings", y=borough_col, orientation="h",
                     title="Listings by Borough (Top 20)",
                     labels={"listings": "Number of listings", borough_col: ""},
                     color="listings", color_continuous_scale="Blues")
        fig.update_layout(coloraxis_showscale=False, height=500,
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # Room type distribution
    with col_right:
        if "room_type" in listings.columns:
            rt = listings["room_type"].value_counts().reset_index()
            rt.columns = ["room_type", "count"]
            fig2 = px.pie(rt, names="room_type", values="count",
                          title="Room Type Distribution",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(height=500, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig2, use_container_width=True)

    # Borough supply table
    st.subheader("Borough Supply at a Glance")
    display_cols = [c for c in [borough_col, "listings", "median_price",
                                "median_occupancy", "est_monthly_revenue",
                                "opportunity_score"] if c in bor_master.columns]
    bor_display = bor_master[display_cols].sort_values(
        "opportunity_score" if "opportunity_score" in bor_master.columns else "listings",
        ascending=False
    ).reset_index(drop=True)
    bor_display.index += 1
    if "median_price" in bor_display.columns:
        bor_display["median_price"] = bor_display["median_price"].apply(lambda v: f"£{v:,.0f}")
    if "est_monthly_revenue" in bor_display.columns:
        bor_display["est_monthly_revenue"] = bor_display["est_monthly_revenue"].apply(
            lambda v: f"£{v:,.0f}")
    if "median_occupancy" in bor_display.columns:
        bor_display["median_occupancy"] = bor_display["median_occupancy"].apply(
            lambda v: f"{v*100:.0f}%" if v < 1 else f"{v:.0f}%")
    if "opportunity_score" in bor_display.columns:
        bor_display["opportunity_score"] = bor_display["opportunity_score"].round(3)
    st.dataframe(bor_display, use_container_width=True)

# ===========================================================================
# TAB 2 — Demand & Seasonality
# ===========================================================================
with tab2:
    st.subheader("Demand & Seasonality")

    col_l, col_r = st.columns(2)

    # Occupancy distribution
    with col_l:
        occ = listings["occupancy_rate"].dropna()
        fig = px.histogram(occ * 100, nbins=60,
                           title="Occupancy Rate Distribution",
                           labels={"value": "Occupancy rate (%)", "count": "Listings"},
                           color_discrete_sequence=[BLUE])
        fig.add_vline(x=occ.median() * 100, line_dash="dash", line_color=RED,
                      annotation_text=f"Median: {occ.median()*100:.0f}%",
                      annotation_position="top right")
        fig.update_layout(showlegend=False, height=400,
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # Seasonal index
    with col_r:
        seasonal["month_name"] = seasonal["month"].apply(lambda m: MONTH_NAMES[m - 1])
        fig2 = px.bar(seasonal, x="month_name", y="seasonal_index",
                      title="Seasonal Demand Index by Month",
                      labels={"month_name": "", "seasonal_index": "Seasonal index"},
                      color="seasonal_index",
                      color_continuous_scale=[[0, RED], [0.5, GREY], [1, GREEN]])
        fig2.add_hline(y=1.0, line_dash="dash", line_color=GREY,
                       annotation_text="Average = 1.0")
        fig2.update_layout(coloraxis_showscale=False, height=400,
                           margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    # Day of week occupancy
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        dow_plot = dow.set_index("day_of_week").reindex(dow_order).reset_index()
        dow_plot["is_weekend"] = dow_plot["day_of_week"].isin(["Friday","Saturday","Sunday"])
        fig3 = px.bar(dow_plot, x="day_of_week", y=dow_plot["occupancy"] * 100,
                      title="Occupancy Rate by Day of Week",
                      labels={"x": "", "y": "Occupancy rate (%)"},
                      color="is_weekend",
                      color_discrete_map={True: RED, False: BLUE})
        fig3.update_layout(showlegend=False, height=400,
                           margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    # Demand forecast
    with col_r2:
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=forecast["year_month_dt"], y=forecast["forecast"],
            mode="lines+markers", name="Forecast",
            line=dict(color=RED, width=2.5),
            marker=dict(size=5),
        ))
        fig4.add_trace(go.Scatter(
            x=forecast["year_month_dt"], y=forecast["trend"],
            mode="lines", name="Trend",
            line=dict(color=ORANGE, width=1.5, dash="dash"),
        ))
        fig4.update_layout(
            title="12-Month Demand Forecast (Review Volume)",
            xaxis_title="", yaxis_title="Reviews per month",
            height=400, margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", y=1.02),
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Borough occupancy heatmap
    st.subheader("Occupancy by Borough")
    occ_bor = (listings.groupby(borough_col)["occupancy_rate"]
               .median().reset_index()
               .sort_values("occupancy_rate", ascending=False))
    fig5 = px.bar(occ_bor, x=borough_col, y=occ_bor["occupancy_rate"] * 100,
                  title="Median Occupancy Rate by Borough",
                  labels={borough_col: "", "y": "Median occupancy (%)"},
                  color=occ_bor["occupancy_rate"] * 100,
                  color_continuous_scale="Blues")
    fig5.update_layout(coloraxis_showscale=False, height=400,
                       xaxis_tickangle=-45, margin=dict(l=10, r=10, t=40, b=80))
    st.plotly_chart(fig5, use_container_width=True)

# ===========================================================================
# TAB 3 — Pricing Analytics
# ===========================================================================
with tab3:
    st.subheader("Pricing Analytics")

    col_l, col_r = st.columns(2)

    # Price distribution
    with col_l:
        p99 = listings["price"].quantile(0.99)
        price_data = listings[listings["price"].notna() & (listings["price"] <= p99)]["price"]
        fig = px.histogram(price_data, nbins=80,
                           title="Nightly Price Distribution (capped at 99th pct)",
                           labels={"value": "Nightly price (£)", "count": "Listings"},
                           color_discrete_sequence=[BLUE])
        fig.add_vline(x=listings["price"].median(), line_dash="dash", line_color=RED,
                      annotation_text=f"Median: £{listings['price'].median():.0f}",
                      annotation_position="top right")
        fig.update_layout(showlegend=False, height=400,
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # Price elasticity by room type
    with col_r:
        elas_plot = elasticity.sort_values("elasticity")
        bar_colors = [RED if v < -0.3 else ORANGE if v < 0 else GREEN
                      for v in elas_plot["elasticity"]]
        fig2 = go.Figure(go.Bar(
            x=elas_plot["elasticity"], y=elas_plot["room_type"],
            orientation="h",
            marker_color=bar_colors,
            text=elas_plot["elasticity"].round(2),
            textposition="outside",
        ))
        fig2.add_vline(x=0, line_color=GREY, line_width=1)
        fig2.update_layout(
            title="Price Elasticity by Room Type<br><sup>More negative = more price-sensitive</sup>",
            xaxis_title="Elasticity coefficient",
            yaxis_title="",
            height=400, margin=dict(l=10, r=10, t=60, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Revenue optimisation curve (reconstruct from elasticity)
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        avg_beta1 = elasticity["elasticity"].mean()
        price_range = np.linspace(20, 500, 400)

        occ_valid = listings["occupancy_rate"].dropna()
        avg_occ   = occ_valid.mean()
        avg_price = listings["price"].dropna().mean()

        beta0_est = np.log(avg_occ) - avg_beta1 * np.log(avg_price)
        occ_hat   = np.exp(beta0_est + avg_beta1 * np.log(price_range)).clip(0, 1)
        rev_hat   = price_range * occ_hat

        opt_idx   = np.argmax(rev_hat)
        opt_price = price_range[opt_idx]
        opt_rev   = rev_hat[opt_idx]

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=price_range, y=rev_hat, mode="lines",
                                  name="Est. revenue", line=dict(color=GREEN, width=2)))
        fig3.add_vline(x=opt_price, line_dash="dash", line_color=RED,
                       annotation_text=f"Peak: £{opt_price:.0f}",
                       annotation_position="top left")
        fig3.update_layout(
            title=f"Revenue Optimisation Curve<br><sup>Estimated peak at £{opt_price:.0f}/night</sup>",
            xaxis_title="Nightly price (£)",
            yaxis_title="Revenue = price × occupancy (£)",
            height=400, margin=dict(l=10, r=10, t=60, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Competitive price positioning
    with col_r2:
        if "price_position" in pricing.columns:
            pos_counts = pricing["price_position"].value_counts().reset_index()
            pos_counts.columns = ["position", "count"]
            fig4 = px.bar(pos_counts, x="position", y="count",
                          title="Competitive Price Positioning",
                          labels={"position": "", "count": "Listings"},
                          color_discrete_sequence=[GREEN, GREEN, BLUE, ORANGE, RED])
            fig4.update_layout(height=400, xaxis_tickangle=-20,
                               margin=dict(l=10, r=10, t=40, b=60))
            st.plotly_chart(fig4, use_container_width=True)

    # Price by borough
    st.subheader("Median Price by Borough")
    bor_price = (listings.groupby(borough_col)["price"]
                 .median().reset_index()
                 .sort_values("price", ascending=False))
    overall_med = listings["price"].median()
    fig5 = px.bar(bor_price, x=borough_col, y="price",
                  title=f"Median Nightly Price by Borough  (overall median: £{overall_med:.0f})",
                  labels={borough_col: "", "price": "Median price (£)"},
                  color="price", color_continuous_scale="RdYlGn_r")
    fig5.add_hline(y=overall_med, line_dash="dash", line_color=GREY)
    fig5.update_layout(coloraxis_showscale=False, height=400,
                       xaxis_tickangle=-45, margin=dict(l=10, r=10, t=40, b=80))
    st.plotly_chart(fig5, use_container_width=True)

# ===========================================================================
# TAB 4 — Market Opportunity
# ===========================================================================
with tab4:
    st.subheader("Market Opportunity")
    st.caption("Composite score combining demand intensity, supply-demand balance, "
               "estimated revenue, and pricing premium share.")

    col_l, col_r = st.columns([2, 1])

    with col_l:
        opp_plot = opportunity.sort_values("opportunity_score", ascending=True)
        opp_plot["tier"] = opp_plot["opportunity_score"].apply(
            lambda v: "Top quartile" if v >= opportunity["opportunity_score"].quantile(0.75)
            else "Above median" if v >= opportunity["opportunity_score"].median()
            else "Below median"
        )
        color_map = {"Top quartile": GREEN, "Above median": BLUE, "Below median": GREY}
        fig = px.bar(opp_plot, x="opportunity_score", y=bc_opp, orientation="h",
                     title="Market Opportunity Score by Borough",
                     labels={"opportunity_score": "Score (0–1)", bc_opp: ""},
                     color="tier", color_discrete_map=color_map)
        fig.update_layout(height=600, margin=dict(l=10, r=10, t=40, b=10),
                          legend=dict(orientation="h", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**Top 5 Opportunities**")
        top5 = opportunity.sort_values("opportunity_score", ascending=False).head(5)
        for i, row in top5.iterrows():
            st.markdown(f"**{row[bc_opp]}**")
            st.progress(float(row["opportunity_score"]))
            st.caption(f"Score: {row['opportunity_score']:.3f}")

    # Supply vs demand scatter
    st.subheader("Supply vs Demand Balance")
    if "reviews_per_listing" in opportunity.columns and "listings" in opportunity.columns:
        opp_scatter = opportunity.copy()
        opp_scatter["market_status"] = opp_scatter["balance_score"].apply(
            lambda v: "Under-supplied" if v > 0.1
            else "Over-supplied" if v < -0.1
            else "Balanced"
        ) if "balance_score" in opp_scatter.columns else "Balanced"

        color_map2 = {"Under-supplied": GREEN, "Over-supplied": RED, "Balanced": GREY}
        fig2 = px.scatter(opp_scatter,
                          x="listings", y="reviews_per_listing",
                          text=bc_opp,
                          color="market_status" if "market_status" in opp_scatter.columns else None,
                          color_discrete_map=color_map2,
                          title="Supply vs Demand by Borough",
                          labels={"listings": "Total listings (supply)",
                                  "reviews_per_listing": "Reviews per listing (demand intensity)",
                                  bc_opp: "Borough"})
        fig2.update_traces(textposition="top center", textfont_size=9)
        fig2.update_layout(height=500, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    # Full opportunity table
    st.subheader("Full Opportunity Rankings")
    opp_table = opportunity.sort_values("opportunity_score", ascending=False).reset_index(drop=True)
    opp_table.index += 1
    num_cols = ["opportunity_score", "reviews_per_listing", "balance_score",
                "est_monthly_revenue", "median_price"]
    for c in num_cols:
        if c in opp_table.columns:
            if c in ("est_monthly_revenue", "median_price"):
                opp_table[c] = opp_table[c].apply(lambda v: f"£{v:,.0f}")
            else:
                opp_table[c] = opp_table[c].round(3)
    st.dataframe(opp_table, use_container_width=True)

# ===========================================================================
# TAB 5 — Host Recommendations
# ===========================================================================
with tab5:
    st.subheader("Host Recommendations")

    # Host segment metrics
    seg_order = ["Casual (1 listing)", "Small multi (2–3)",
                 "Medium multi (4–9)", "Professional (10+)"]
    host_seg_plot = host_seg.copy()
    host_seg_plot["host_type"] = pd.Categorical(
        host_seg_plot["host_type"], categories=seg_order, ordered=True)
    host_seg_plot = host_seg_plot.sort_values("host_type")

    col_l, col_r = st.columns(2)

    with col_l:
        fig = px.bar(host_seg_plot, x="host_type", y="median_occupancy" if "median_occupancy" in host_seg_plot.columns else "n_listings",
                     title="Median Occupancy by Host Type",
                     labels={"host_type": "", "median_occupancy": "Median occupancy rate"},
                     color_discrete_sequence=[BLUE])
        if "median_occupancy" in host_seg_plot.columns:
            if host_seg_plot["median_occupancy"].max() <= 1:
                fig.update_traces(customdata=host_seg_plot["median_occupancy"] * 100,
                                  hovertemplate="%{x}: %{customdata:.1f}%")
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        if "superhost_pct" in host_seg_plot.columns:
            fig2 = px.bar(host_seg_plot, x="host_type", y="superhost_pct",
                          title="Superhost % by Host Type",
                          labels={"host_type": "", "superhost_pct": "Superhost share (%)"},
                          color_discrete_sequence=[GREEN])
            fig2.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig2, use_container_width=True)

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        if "median_price" in host_seg_plot.columns:
            fig3 = px.bar(host_seg_plot, x="host_type", y="median_price",
                          title="Median Nightly Price by Host Type",
                          labels={"host_type": "", "median_price": "Median price (£)"},
                          color_discrete_sequence=[ORANGE])
            fig3.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig3, use_container_width=True)

    with col_r2:
        if "median_revenue" in host_seg_plot.columns:
            fig4 = px.bar(host_seg_plot, x="host_type", y="median_revenue",
                          title="Median Estimated Annual Revenue",
                          labels={"host_type": "", "median_revenue": "Median annual revenue (£)"},
                          color_discrete_sequence=[PURPLE])
            fig4.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig4, use_container_width=True)

    # Recommendation cards
    st.divider()
    st.subheader("Actionable Recommendations by Host Type")

    recs = {
        "🏠 Casual Host (1 listing)": {
            "colour": "#EBF5FB",
            "text": (
                "**Priority: Achieve Superhost status.** "
                "Superhosts earn 15–20% higher occupancy at the same price point. "
                "To qualify: maintain a 4.8+ rating, <1% cancellation rate, and respond to 90%+ "
                "of messages within 24 hours. "
                "**Pricing:** Start at or slightly below your borough × room type median to build "
                "review volume, then increase once you reach 10+ reviews."
            ),
        },
        "🏘️ Small Multi-Host (2–3 listings)": {
            "colour": "#EAFAF1",
            "text": (
                "**Priority: Automate operations and start pricing dynamically.** "
                "Use a channel manager (Lodgify, Guesty) to sync calendars across platforms. "
                "Consider a dynamic pricing tool (PriceLabs, Wheelhouse) — they typically "
                "increase revenue 10–25% by adjusting rates for weekends, events, and seasonality. "
                "**Diversify:** if both listings are in the same borough and room type, "
                "you are exposed to the same demand shocks."
            ),
        },
        "🏗️ Medium Multi-Host (4–9 listings)": {
            "colour": "#FEF9E7",
            "text": (
                "**Priority: Per-listing ROI analysis.** "
                "Not all listings earn equally — identify which are underperforming vs their "
                "borough median and investigate why (pricing, photos, description, location). "
                "Ghost supply listings (availability = 0) represent blocked capital; "
                "consider activating or converting to medium-term lets. "
                "**Scale-up risk:** Superhost status is harder to maintain across many listings; "
                "consider a co-host or property management service."
            ),
        },
        "🏢 Professional Host (10+ listings)": {
            "colour": "#F9F3FF",
            "text": (
                "**Priority: Market concentration and revenue management.** "
                "Analyse your portfolio's Gini coefficient — if concentration in one borough is "
                "high and that market becomes oversupplied, revenue will compress. "
                "Algorithmic revenue management is essential at this scale; manual pricing "
                "leaves money on the table. "
                "**Regulatory risk:** London's 90-night rule applies to entire-home listings "
                "without planning permission. Monitor council enforcement trends by borough."
            ),
        },
    }

    for title, rec in recs.items():
        with st.container():
            st.markdown(
                f"""<div style="background:{rec['colour']};padding:16px 20px;
                border-radius:8px;margin-bottom:12px;">
                <b>{title}</b><br><br>{rec['text']}
                </div>""",
                unsafe_allow_html=True,
            )

    # Key market insights
    st.divider()
    st.subheader("Key Market Insights")

    top_bor  = str(kpis["top_borough"])
    med_occ  = kpis["median_occupancy_pct"]
    med_rev  = kpis["median_annual_revenue"]
    peak_idx = seasonal["seasonal_index"].max()
    peak_mon = MONTH_NAMES[int(seasonal["seasonal_index"].idxmax())]

    insights = [
        f"**Median occupancy of {med_occ:.0f}%** means the average London listing "
        f"is booked roughly {med_occ*3.65:.0f} nights per year.",
        f"**{peak_mon} is peak demand** — seasonal index of {peak_idx:.2f}x the annual average. "
        f"Hosts should raise prices and enforce minimum stay requirements in peak months.",
        f"**{top_bor}** scores highest on the market opportunity index — "
        f"high demand relative to supply suggests pricing power and lower vacancy risk.",
        f"**Median estimated annual revenue: £{med_rev:,.0f}.** "
        f"Top-quartile hosts earn 3–5× this, driven by location, Superhost status, and pricing strategy.",
    ]

    for ins in insights:
        st.markdown(f"- {ins}")
