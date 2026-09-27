"""
Lebanon's tourism infrastructure - an interactive drill-down.

Dataset: Tourism - Lebanon 2023 (town-level), AUB LINKED / Impact Open Data.
Run locally with:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page setup and palette
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Lebanon's tourism infrastructure",
    page_icon="📊",
    layout="wide",
)

BG = "#121417"
TERRACOTTA = "#E2725B"
SLATE = "#5FA8B8"
SAGE = "#8FBBA9"
GOLD = "#E3B23C"
INK = "#F2F4F3"
MUTED = "#9AA3A8"
GRID = "#262B30"
FAINT = "#3F4A52"

FACILITIES = [
    "Total number of hotels",
    "Total number of guest houses",
    "Total number of cafes",
    "Total number of restaurants",
]
SHORT = {
    "Total number of hotels": "Hotels",
    "Total number of guest houses": "Guest houses",
    "Total number of cafes": "Cafés",
    "Total number of restaurants": "Restaurants",
}
COLOURS = {"Restaurants": TERRACOTTA, "Cafés": SLATE,
           "Guest houses": SAGE, "Hotels": GOLD}


def style(fig: go.Figure, height: int = 430) -> go.Figure:
    """One look for every chart on the page."""
    fig.update_layout(
        height=height,
        font=dict(family="Arial, sans-serif", size=14, color=INK),
        title=dict(font=dict(size=18, color=INK), x=0.0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED)),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color=MUTED)),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(title="", orientation="h", y=1.02, yanchor="bottom", x=0),
    )
    return fig


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    """Load the published CSV and repair two problems in it."""
    df = pd.read_csv(Path(__file__).parent / "tourism_lebanon_2023.csv")

    def fix_encoding(text: str) -> str:
        # the published file is double UTF-8 encoded: "Zahlé" arrives as "ZahlÃ©"
        for _ in range(2):
            try:
                text = text.encode("latin1").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                break
        return text

    # refArea holds DBpedia URIs, not readable names
    df["Area"] = (df["refArea"].str.split("/").str[-1]
                  .str.replace("_", " ").map(fix_encoding)
                  .str.replace(", Lebanon", "", regex=False))
    df["Town"] = df["Town"].str.strip().map(fix_encoding)
    df["Total establishments"] = df[FACILITIES].sum(axis=1)

    return df[["Town", "Area", "Tourism Index", "Total establishments"] + FACILITIES]


df = load_data()
NATIONAL_TOTAL = int(df["Total establishments"].sum())

# --------------------------------------------------------------------------
# Header and context
# --------------------------------------------------------------------------
st.title("Lebanon's tourism infrastructure")
st.markdown(
    "Every one of Lebanon's **1,137 towns**, scored on the tourism it actually has: "
    "hotels, guest houses, cafés and restaurants, plus a composite **Tourism Index** from 0 to 10. "
    "Data from the [AUB LINKED portal](https://linked.aub.edu.lb:8502/), 2023."
)

with st.expander("How the Tourism Index works, and why it has gaps"):
    st.markdown(
        """
The index is not a rating anyone gave a town — it is built from four yes/no questions:

| Does the town have… | Points |
|---|---|
| a hotel? | 3 |
| a café? | 3 |
| a restaurant? | 3 |
| a guest house? | 1 |

Every score is therefore some number of 3s plus an optional 1, which is why **no town scores
2, 5 or 8** — those totals are impossible. It also means the index measures *what kinds* of
facility a town has, not how many: a town with one café scores the same as a town with a hundred.
That is exactly why the charts below show counts alongside the index rather than the index alone.
        """
    )

# --------------------------------------------------------------------------
# The two linked controls
# --------------------------------------------------------------------------
st.sidebar.header("Drill down")

regions = ["All of Lebanon"] + sorted(df["Area"].unique())
region = st.sidebar.selectbox(
    "1 · Region",
    regions,
    help="Pick a governorate or district. This also sets what the slider below can offer.",
)

# CONTROL 1 narrows the data...
scope = df if region == "All of Lebanon" else df[df["Area"] == region]

# ...and CONTROL 2's options are built from whatever CONTROL 1 left behind.
available_levels = sorted(scope["Tourism Index"].unique())

if len(available_levels) == 1:
    only = available_levels[0]
    st.sidebar.info(f"Every town in {region} scores {only}, so there is nothing to filter.")
    min_index = only
else:
    min_index = st.sidebar.select_slider(
        "2 · Minimum Tourism Index",
        options=available_levels,
        value=available_levels[0],
        help="Only the scores that actually occur in the region above are offered.",
    )

st.sidebar.caption(
    f"Scores available in **{region}**: "
    + ", ".join(str(int(v)) for v in available_levels)
)

view = scope[scope["Tourism Index"] >= min_index]

# --------------------------------------------------------------------------
# Headline numbers for the current selection
# --------------------------------------------------------------------------
supply = int(view["Total establishments"].sum())
share_of_scope = supply / scope["Total establishments"].sum() if scope["Total establishments"].sum() else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Towns shown", f"{len(view):,}", f"of {len(scope):,} in scope")
c2.metric("Establishments", f"{supply:,}", f"{supply / NATIONAL_TOTAL:.0%} of Lebanon")
c3.metric("Share of this region's supply", f"{share_of_scope:.0%}")
c4.metric(
    "Hotels among them",
    f"{int(view['Total number of hotels'].sum()):,}",
    f"{(view['Total number of hotels'].sum() / supply if supply else 0):.0%} of the mix",
)

if view.empty:
    st.warning("No towns clear that score in this region. Lower the slider to bring some back.")
    st.stop()

st.divider()

# --------------------------------------------------------------------------
# Visualisation 1 - the mix
# --------------------------------------------------------------------------
left, right = st.columns([3, 2])

with left:
    if region == "All of Lebanon":
        grouped = view.groupby("Area")[FACILITIES].sum()
        grouped = grouped.loc[grouped.sum(axis=1).nlargest(12).index]
        label, axis_title = "Area", "Region"
    else:
        grouped = view.set_index("Town")[FACILITIES]
        grouped = grouped.loc[grouped.sum(axis=1).nlargest(12).index]
        label, axis_title = "Town", "Town"

    tidy = (grouped.rename(columns=SHORT).reset_index()
            .melt(id_vars=grouped.index.name or label,
                  var_name="Facility type", value_name="Count")
            .rename(columns={grouped.index.name or label: label}))

    fig1 = px.bar(
        tidy, x="Count", y=label, color="Facility type", orientation="h",
        color_discrete_map=COLOURS,
        category_orders={
            label: list(grouped.sum(axis=1).nlargest(12).index[::-1]),
            "Facility type": ["Restaurants", "Cafés", "Guest houses", "Hotels"],
        },
        title=f"What the supply is made of — top {min(12, len(grouped))} by size",
        labels={"Count": "Establishments", label: ""},
    )
    fig1.update_layout(barmode="stack")
    st.plotly_chart(style(fig1, 470), width="stretch")

with right:
    mix = view[FACILITIES].sum().rename(index=SHORT)
    fig2 = px.pie(
        names=mix.index, values=mix.values, hole=0.5,
        color=mix.index, color_discrete_map=COLOURS,
        title="Food versus beds in this selection",
    )
    fig2.update_traces(
        textinfo="label+percent", texttemplate="%{label}<br>%{percent:.0%}",
        marker=dict(line=dict(color=BG, width=2)), sort=False,
    )
    fig2.update_layout(showlegend=False)
    fig2.add_annotation(text=f"{supply:,}", x=0.5, y=0.5, showarrow=False,
                        font=dict(size=24, color=INK))
    st.plotly_chart(style(fig2, 470), width="stretch")

# insight that updates with the selection
food = view["Total number of cafes"].sum() + view["Total number of restaurants"].sum()
beds = view["Total number of hotels"].sum() + view["Total number of guest houses"].sum()
st.info(
    f"**Insight.** In this selection, food and drink make up **{food / supply:.0%}** of the supply "
    f"and lodging **{beds / supply:.0%}**. Nationally the split is 83% food to 17% lodging — "
    "Lebanon's tourism infrastructure is built for day visitors rather than overnight stays."
)

st.divider()

# --------------------------------------------------------------------------
# Visualisation 2 - the relationship, with the rest of the country as context
# --------------------------------------------------------------------------
st.subheader("Do the categories grow together?")

context = df[(df["Total establishments"] > 0) & (~df.index.isin(view.index))]
selected = view[view["Total establishments"] > 0].copy()
selected["Lodging"] = (selected["Total number of hotels"]
                       + selected["Total number of guest houses"])

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=context["Total number of cafes"], y=context["Total number of restaurants"],
    mode="markers", name="Rest of Lebanon",
    marker=dict(size=6, color=FAINT, opacity=0.55),
    hovertext=context["Town"], hoverinfo="text",
))
fig3.add_trace(go.Scatter(
    x=selected["Total number of cafes"], y=selected["Total number of restaurants"],
    mode="markers", name="Current selection",
    marker=dict(
        size=selected["Lodging"], sizemode="area",
        sizeref=2.0 * max(selected["Lodging"].max(), 1) / (38 ** 2), sizemin=7,
        color=selected["Tourism Index"], cmin=0, cmax=10,
        colorscale=[[0, "#3B4348"], [0.5, SAGE], [1, TERRACOTTA]],
        line=dict(width=0.5, color=BG),
        colorbar=dict(title="Index", tickfont=dict(color=MUTED)),
    ),
    customdata=selected[["Town", "Area", "Lodging", "Tourism Index"]],
    hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                  "Cafés %{x} · Restaurants %{y}<br>"
                  "Lodging %{customdata[2]} · Index %{customdata[3]}<extra></extra>",
))
fig3.update_layout(
    title="Cafés against restaurants, one dot per town — bubble size is lodging",
    xaxis_title="Cafés per town", yaxis_title="Restaurants per town",
)
st.plotly_chart(style(fig3, 480), width="stretch")

if len(selected) > 2:
    r = selected["Total number of cafes"].corr(selected["Total number of restaurants"])
    odd = selected.assign(gap=selected["Lodging"] - selected["Total number of restaurants"]).nlargest(1, "gap")
    town = odd["Town"].iloc[0]
    st.info(
        f"**Insight.** Cafés and restaurants correlate at **r = {r:.2f}** here — food service arrives "
        f"as a package. Lodging does not follow the same rule: **{town}** has "
        f"{int(odd['Lodging'].iloc[0])} places to stay against {int(odd['Total number of restaurants'].iloc[0])} "
        "restaurants, a rural lodging profile rather than an urban dining one."
    )

with st.expander("See the towns behind this view"):
    st.dataframe(
        view.sort_values("Total establishments", ascending=False)
        .rename(columns=SHORT)
        .reset_index(drop=True),
        width="stretch", hide_index=True,
    )

# --------------------------------------------------------------------------
# Design justifications
# --------------------------------------------------------------------------
st.divider()
st.subheader("Why these two controls")

j1, j2 = st.columns(2)

with j1:
    with st.expander("Control 1 · Region (dropdown)", expanded=False):
        st.markdown(
            """
**The question it answers.** "Forget the national totals — what does tourism look like *where I
live*, or in the region I am deciding a budget for?" The national picture is dominated by a handful
of towns, so a reader from Hasbaya learns almost nothing from it.

**Why a dropdown.** There are 25 regions. A multiselect would let a reader stack several regions
into one blurred total, and radio buttons would need 25 always-visible options taking over the
sidebar. A single-choice dropdown costs one line of space, makes the current scope unambiguous, and
guarantees every chart on the page describes one place.

**Course concept — reducing clutter, and context before detail.** The page opens on all of Lebanon
so the reader gets the overview first, then chooses a region to zoom into: overview, zoom and filter,
details on demand. The scatter plot keeps the rest of the country in faint grey underneath the
selection, so zooming in never costs the reader the context of where their region sits nationally.
            """
        )

with j2:
    with st.expander("Control 2 · Minimum Tourism Index (slider)", expanded=False):
        st.markdown(
            """
**The question it answers.** "Within this region, how much of what I am looking at is real tourism
infrastructure rather than a single café?" Raising the bar strips out the weakest towns and shows
how much of the region's supply survives.

**Why a select-slider, and how it is linked.** Its options are not fixed — they are read from the
region chosen above, so a region whose towns only ever score 0, 3 or 6 offers exactly those three
steps. This matters because the index skips 2, 5 and 8 entirely: a normal numeric slider would
invite readers to stop on values that no town can hold and show them an unchanged chart, which reads
like a broken app. A select-slider over the real values makes every step change something.

**Course concept — focusing attention.** The slider does not merely hide rows; it answers a question
by degree. Each step drops the towns that fail the bar and the headline metrics recompute, so the
reader watches a region's supply concentrate into fewer and fewer towns instead of reading a static
claim that it does.
            """
        )

st.caption(
    "Source: Tourism – Lebanon 2023, AUB LINKED / Impact Open Data · "
    "built with Streamlit and Plotly"
)
