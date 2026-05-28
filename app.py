"""
Nassau Candy Distributor — Streamlit Dashboard (Real Data)
Run: cd nassau_candy_shipping && streamlit run streamlit_app/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Nassau Candy — Route Efficiency",
    page_icon="🍬", layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg,#4361EE18,#4CC9F018);
    border:1px solid #4361EE44; border-radius:12px;
    padding:16px 20px; text-align:center;
}
.metric-value{font-size:1.9rem;font-weight:700;color:#4361EE}
.metric-label{font-size:0.82rem;color:#666;margin-top:4px}
.sec{font-size:1.1rem;font-weight:600;border-left:4px solid #4361EE;
     padding-left:10px;margin:14px 0 6px 0}
</style>
""", unsafe_allow_html=True)

PROD_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise":   "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows":           "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious":      "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate":          "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel":   "Wicked Choccy's",
    "Laffy Taffy":                         "Sugar Shack",
    "SweeTARTS":                           "Sugar Shack",
    "Nerds":                               "Secret Factory",
    "Everlasting Gobstopper":              "Secret Factory",
    "Fun Dip":                             "The Other Factory",
    "Fizzy Lifting Drinks":                "The Other Factory",
    "Hair Toffee":                         "The Other Factory",
    "Kazookles":                           "The Other Factory",
    "Lickable Wallpaper":                  "The Other Factory",
    "Wonka Gum":                           "The Other Factory",
}

FACTORY_COORDS = {
    "Lot's O' Nuts":     (32.881893, -111.768036),
    "Wicked Choccy's":  (32.076176, -81.088371),
    "Sugar Shack":       (48.11914,  -96.18115),
    "Secret Factory":    (41.446333, -90.565487),
    "The Other Factory": (35.1175,   -89.971107)
}

@st.cache_data
def load():
    import os
    BASE = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv("Nassau Candy Distributor.csv")
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True)
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  dayfirst=True)
    df["Lead Time"]  = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Factory"]    = df["Product Name"].map(PROD_FACTORY)
    df["Route"]      = df["Factory"] + " → " + df["Region"]
    df["Month"]      = df["Order Date"].dt.to_period("M").astype(str)
    df["Year"]       = df["Order Date"].dt.year
    thr = df.groupby("Ship Mode")["Lead Time"].transform(
            lambda x: x.mean() + 0.5*x.std())
    df["Is Delayed"] = (df["Lead Time"] > thr).astype(int)
    return df

df = load()

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("🍬 Nassau Candy")
st.sidebar.markdown("**Filter Panel**")
st.sidebar.divider()

factories  = st.sidebar.multiselect("Factory",   sorted(df["Factory"].unique()),  default=sorted(df["Factory"].unique()))
regions    = st.sidebar.multiselect("Region",    sorted(df["Region"].unique()),   default=sorted(df["Region"].unique()))
modes      = st.sidebar.multiselect("Ship Mode", sorted(df["Ship Mode"].unique()),default=sorted(df["Ship Mode"].unique()))
divisions  = st.sidebar.multiselect("Division",  sorted(df["Division"].unique()), default=sorted(df["Division"].unique()))
yr         = st.sidebar.slider("Year", int(df["Year"].min()), int(df["Year"].max()),
                                (int(df["Year"].min()), int(df["Year"].max())))

fd = df[
    df["Factory"].isin(factories) &
    df["Region"].isin(regions) &
    df["Ship Mode"].isin(modes) &
    df["Division"].isin(divisions) &
    df["Year"].between(*yr)
]

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🍬 Nassau Candy Distributor")
st.subheader("Factory-to-Customer Shipping Route Efficiency Analysis")
st.divider()

if fd.empty:
    st.warning("No data for selected filters.")
    st.stop()

# ── Route Stats ───────────────────────────────────────────────────────────────
rs = (fd.groupby("Route")
      .agg(Avg_Lead=("Lead Time","mean"),
           Orders=("Order ID","count"),
           Delay_Rate=("Is Delayed","mean"),
           Sales=("Sales","sum"),
           Profit=("Gross Profit","sum"))
      .round(2))
rng = rs["Avg_Lead"].max() - rs["Avg_Lead"].min() + 1e-9
rs["Efficiency"] = (
    (1-(rs["Avg_Lead"]-rs["Avg_Lead"].min())/rng)*0.6
    + (1-rs["Delay_Rate"])*0.4
).round(3)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
def kcard(col, val, label, color="#4361EE"):
    col.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{color}">{val}</div>'
                 f'<div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

kcard(c1, f"{len(fd):,}",                         "Total Orders")
kcard(c2, f"{fd['Lead Time'].mean():.0f}d",       "Avg Lead Time",     "#F72585")
kcard(c3, f"{fd['Is Delayed'].mean()*100:.1f}%",  "Delay Rate",        "#F3722C")
kcard(c4, f"${fd['Sales'].sum():,.0f}",            "Total Sales",       "#43AA8B")
kcard(c5, f"{rs['Efficiency'].mean():.3f}",        "Avg Efficiency",    "#7209B7")

st.divider()

# ── Row 1 ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="sec">Avg Lead Time by Route (Top 15)</div>', unsafe_allow_html=True)
    top15 = rs.sort_values("Avg_Lead").head(15).reset_index()
    fig = px.bar(top15, x="Avg_Lead", y="Route", orientation="h",
                 color="Efficiency", color_continuous_scale="RdYlGn",
                 labels={"Avg_Lead":"Days","Route":""})
    fig.update_layout(height=400, margin=dict(l=5,r=5,t=5,b=5), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown('<div class="sec">Delay Rate by Factory</div>', unsafe_allow_html=True)
    fac_d = fd.groupby("Factory")["Is Delayed"].mean().reset_index()
    fac_d["Delay %"] = (fac_d["Is Delayed"]*100).round(1)
    fig = px.bar(fac_d.sort_values("Delay %"), x="Delay %", y="Factory",
                 orientation="h", color="Delay %",
                 color_continuous_scale="OrRd", text="Delay %")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=400, margin=dict(l=5,r=5,t=5,b=5),
                      coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2 ─────────────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="sec">Lead Time Heatmap (Factory × Region)</div>', unsafe_allow_html=True)
    pivot = fd.pivot_table("Lead Time","Factory","Region","mean").round(0)
    fig = px.imshow(pivot, text_auto=True, color_continuous_scale="YlOrRd",
                    aspect="auto", labels=dict(color="Days"))
    fig.update_layout(height=360, margin=dict(l=5,r=5,t=5,b=5))
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.markdown('<div class="sec">Lead Time Distribution by Ship Mode</div>', unsafe_allow_html=True)
    fig = px.box(fd, x="Ship Mode", y="Lead Time", color="Ship Mode",
                 category_orders={"Ship Mode":["Same Day","First Class","Second Class","Standard Class"]},
                 color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_layout(height=360, margin=dict(l=5,r=5,t=5,b=5),
                      showlegend=False, xaxis_title="", yaxis_title="Days")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 3 ─────────────────────────────────────────────────────────────────────
col5, col6 = st.columns([1.3, 0.7])

with col5:
    st.markdown('<div class="sec">📦 Orders & Delay % by Factory</div>', unsafe_allow_html=True)
    fac_summary = fd.groupby("Factory").agg(
        Orders=("Order ID","count"),
        Delay_Pct=("Is Delayed","mean")
    ).reset_index()
    fac_summary["Delay %"] = (fac_summary["Delay_Pct"]*100).round(1)
    fig = px.scatter(fac_summary, x="Orders", y="Delay %",
                     text="Factory", size="Orders",
                     color="Delay %", color_continuous_scale="RdYlGn_r",
                     labels={"Orders":"Total Orders","Delay %":"Delay Rate %"})
    fig.update_traces(textposition="top center")
    fig.update_layout(height=380, margin=dict(l=5,r=5,t=5,b=5), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col6:
    st.markdown('<div class="sec">🏆 Route Leaderboard</div>', unsafe_allow_html=True)
    lb = rs.sort_values("Efficiency", ascending=False).head(10)
    lb_show = lb[["Orders","Avg_Lead","Delay_Rate","Efficiency"]].copy()
    lb_show["Delay_Rate"] = (lb_show["Delay_Rate"]*100).round(1)
    lb_show.columns = ["Orders","Avg Days","Delay %","Score"]
    lb_show = lb_show.reset_index()
    lb_show.index = range(1, len(lb_show)+1)
    st.dataframe(lb_show, use_container_width=True, height=360)

# ── Row 4 : Trend ─────────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="sec">📈 Monthly Avg Lead Time by Ship Mode</div>', unsafe_allow_html=True)
monthly = (fd.groupby(["Month","Ship Mode"])["Lead Time"].mean().reset_index())
fig = px.line(monthly, x="Month", y="Lead Time", color="Ship Mode",
              markers=True, labels={"Lead Time":"Avg Days","Month":""},
              color_discrete_sequence=px.colors.qualitative.Bold)
fig.update_layout(height=300, margin=dict(l=5,r=5,t=5,b=5))
st.plotly_chart(fig, use_container_width=True)

# ── Row 5 : Product Sales ─────────────────────────────────────────────────────
col7, col8 = st.columns(2)
with col7:
    st.markdown('<div class="sec">Top Products by Sales</div>', unsafe_allow_html=True)
    ps = fd.groupby("Product Name")["Sales"].sum().sort_values(ascending=False).head(10)
    fig = px.bar(ps.reset_index(), x="Sales", y="Product Name", orientation="h",
                 color="Sales", color_continuous_scale="Blues_r")
    fig.update_layout(height=340, margin=dict(l=5,r=5,t=5,b=5),
                      coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

with col8:
    st.markdown('<div class="sec">Profit by Division & Region</div>', unsafe_allow_html=True)
    dr = fd.groupby(["Division","Region"])["Gross Profit"].sum().reset_index()
    fig = px.bar(dr, x="Region", y="Gross Profit", color="Division",
                 barmode="group",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=340, margin=dict(l=5,r=5,t=5,b=5))
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("🍬 Nassau Candy Distributor | Unified Mentor Project | Real Dataset")
