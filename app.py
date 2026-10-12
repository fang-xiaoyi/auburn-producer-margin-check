"""Producer Margin Check

Run locally with:
    streamlit run app.py

The benchmark values in this prototype are transcribed from public Alabama
Extension and USDA ERS publications. They are reference scenarios, not a
claim that one representative farm describes every Alabama operation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Producer Margin Check",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { max-width: 1420px; padding-top: 2rem; }
    .hero { padding: 1.1rem 1.3rem; border: 1px solid #d9e2e7;
            border-left: 7px solid #841617; border-radius: 8px;
            background: linear-gradient(135deg, #fff8f5 0%, #f4f8fa 100%); }
    .hero .eyebrow { color: #841617; font-size: .78rem; font-weight: 700;
                     letter-spacing: .08em; }
    .hero h1 { margin: .25rem 0 .35rem 0; color: #1f2933; }
    .hero p { margin: 0; color: #4b5563; font-size: 1.03rem; }
    [data-testid="stMetricValue"] { color: #841617; }
    div[data-testid="stDataFrame"] { border: 1px solid #e2e8f0; }
    </style>
    """,
    unsafe_allow_html=True,
)


COST_LABELS = {
    "pasture": "Pasture / forage",
    "feed": "Purchased feed",
    "health": "Animal health",
    "replacements": "Replacement stock",
    "machinery": "Machinery and equipment",
    "labor": "Labor",
    "land": "Land, rent, and interest",
    "other": "Marketing, admin, and other",
}

COST_COLORS = {
    "pasture": "#F28E2B",
    "feed": "#E15759",
    "health": "#59A14F",
    "replacements": "#4E79A7",
    "machinery": "#B07AA1",
    "labor": "#76B7B2",
    "land": "#9C755F",
    "other": "#BAB0AC",
}


def money(value: Optional[float], decimals: int = 0) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.{decimals}f}"


def price(value: Optional[float]) -> str:
    return "—" if value is None else f"${value:,.2f}/lb"


def price_gap(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{'-' if value < 0 else ''}${abs(value):,.2f}/lb"


def pct(value: Optional[float]) -> str:
    return "—" if value is None else f"{value:,.1f}%"


def number(value: Optional[float], decimals: int = 1) -> str:
    return "—" if value is None else f"{value:,.{decimals}f}"


def benchmark(
    key: str,
    name: str,
    geography: str,
    year: str,
    scope: str,
    total_cost: float,
    gross_revenue: Optional[float],
    variable_cost: Optional[float],
    costs: Optional[Dict[str, float]] = None,
    cost_groups: Optional[Dict[str, float]] = None,
    herd_size: Optional[int] = None,
    production: Optional[Dict[str, float]] = None,
    source: str = "",
    note: str = "",
) -> Dict:
    return {
        "key": key,
        "name": name,
        "geography": geography,
        "year": year,
        "scope": scope,
        "total_cost": total_cost,
        "gross_revenue": gross_revenue,
        "variable_cost": variable_cost,
        "costs": costs or {},
        "cost_groups": cost_groups or {},
        "herd_size": herd_size,
        "production": production or {},
        "source": source,
        "note": note,
    }


BENCHMARKS: List[Dict] = [
    benchmark(
        "aces-2022",
        "Alabama Extension 2022 cow-calf budget",
        "Alabama",
        "2022",
        "Representative enterprise budget",
        1156.67,
        977.00,
        929.72,
        costs={
            "pasture": 474.70,
            "feed": 156.37,
            "health": 38.72,
            "replacements": 150.00,
            "machinery": 89.60,
            "labor": 0.00,
            "land": 114.35,
            "other": 132.93,
        },
        production={"weaning_rate": 90.0, "weaning_weight": 625.0, "calf_price": 1.60, "cull_revenue": 77.0},
        source="https://www.aces.edu/blog/topics/farm-management/south-alabama-cow-calf-enterprise-cost-study/",
        note="Extension enterprise budget. Use as a public Alabama reference, not as a farm-specific average.",
    ),
    benchmark(
        "southwest-small",
        "Southwest Alabama small farm model",
        "Southwest Alabama",
        "Fall 2022",
        "40 brood cows + 1 bull",
        854.99,
        541.05,
        736.09,
        costs={
            "pasture": 230.58,
            "feed": 219.00,
            "health": 2.50,
            "replacements": 113.70,
            "machinery": 125.00,
            "labor": 0.00,
            "land": 17.81,
            "other": 27.50,
        },
        herd_size=40,
        production={"weaning_rate": 85.0},
        source="https://www.aces.edu/blog/topics/farm-management/south-alabama-cow-calf-enterprise-cost-study/",
        note="Representative farm model. Labor is excluded in the published model.",
    ),
    benchmark(
        "southwest-large",
        "Southwest Alabama large farm model",
        "Southwest Alabama",
        "Fall 2022",
        "150 brood cows + 6 bulls",
        1294.85,
        821.26,
        1130.47,
        costs={
            "pasture": 387.03,
            "feed": 278.65,
            "health": 2.50,
            "replacements": 175.00,
            "machinery": 166.67,
            "labor": 0.00,
            "land": 54.05,
            "other": 66.57,
        },
        herd_size=150,
        production={"weaning_rate": 85.0},
        source="https://www.aces.edu/blog/topics/farm-management/south-alabama-cow-calf-enterprise-cost-study/",
        note="Representative farm model. It includes excess hay sales in gross returns and excludes labor.",
    ),
    benchmark(
        "southeast-small",
        "Southeast Alabama small farm model",
        "Southeast Alabama",
        "Fall 2022",
        "38 brood cows + 1 bull",
        780.74,
        660.01,
        654.94,
        costs={
            "pasture": 101.45,
            "feed": 271.49,
            "health": 8.69,
            "replacements": 124.74,
            "machinery": 52.64,
            "labor": 0.00,
            "land": 13.05,
            "other": 82.88,
        },
        herd_size=38,
        production={"weaning_rate": 84.0},
        source="https://www.aces.edu/blog/topics/farm-management/south-alabama-cow-calf-enterprise-cost-study/",
        note="Representative farm model. Labor is excluded in the published model.",
    ),
    benchmark(
        "southeast-large",
        "Southeast Alabama large farm model",
        "Southeast Alabama",
        "Fall 2022",
        "250 brood cows + 10 bulls",
        1106.18,
        952.58,
        948.77,
        costs={
            "pasture": 280.58,
            "feed": 221.50,
            "health": 40.29,
            "replacements": 222.50,
            "machinery": 124.00,
            "labor": 0.00,
            "land": 51.90,
            "other": 8.00,
        },
        herd_size=250,
        production={"weaning_rate": 90.0},
        source="https://www.aces.edu/blog/topics/farm-management/south-alabama-cow-calf-enterprise-cost-study/",
        note="Representative farm model. Labor is excluded in the published model.",
    ),
]


for size_label, low, high, operating, ownership, overhead in [
    ("20–49 cows", 20, 49, 563, 407, 1129),
    ("50–99 cows", 50, 99, 552, 351, 640),
    ("100–249 cows", 100, 249, 586, 278, 390),
    ("250–499 cows", 250, 499, 615, 245, 252),
    ("500+ cows", 500, 10000, 584, 218, 108),
]:
    BENCHMARKS.append(
        benchmark(
            f"usda-ers-{low}",
            f"USDA ERS national size benchmark: {size_label}",
            "United States",
            "2018",
            size_label,
            operating + ownership + overhead,
            None,
            operating,
            cost_groups={
                "Operating costs": operating,
                "Ownership costs": ownership,
                "Opportunity and overhead": overhead,
            },
            herd_size=(low + high) // 2 if high < 10000 else 500,
            source="https://ers.usda.gov/publications/107012",
            note="National economic cost benchmark by herd-size category. Cost definitions differ from the Alabama representative farm models.",
        )
    )


def get_benchmark(key: str) -> Dict:
    return next(item for item in BENCHMARKS if item["key"] == key)


def closest_benchmark(herd_size: int) -> Dict:
    candidates = [item for item in BENCHMARKS if item["herd_size"]]
    return min(candidates, key=lambda item: abs(item["herd_size"] - herd_size))


def calculate(inputs: Dict) -> Dict:
    pounds = inputs["weaning_rate"] / 100 * inputs["weaning_weight"]
    calf_revenue = pounds * inputs["calf_price"]
    gross_revenue = calf_revenue + inputs["cull_revenue"]
    total_cost = sum(inputs["costs"].values())
    margin = gross_revenue - total_cost
    break_even = (total_cost - inputs["cull_revenue"]) / pounds if pounds else None
    return {
        "pounds": pounds,
        "calf_revenue": calf_revenue,
        "gross_revenue": gross_revenue,
        "total_cost": total_cost,
        "margin": margin,
        "break_even": break_even,
        "annual_margin": margin * inputs["herd_size"],
        "cost_per_pound": total_cost / pounds if pounds else None,
        "acres_per_cow": inputs["acres"] / inputs["herd_size"] if inputs["herd_size"] else None,
    }


def benchmark_metrics(item: Dict) -> Dict:
    production = item["production"]
    pounds = None
    if production.get("weaning_rate") is not None and production.get("weaning_weight") is not None:
        pounds = production["weaning_rate"] / 100 * production["weaning_weight"]
    margin = None
    if item["gross_revenue"] is not None:
        margin = item["gross_revenue"] - item["total_cost"]
    return {
        "pounds": pounds,
        "margin": margin,
        "break_even": ((item["total_cost"] - production.get("cull_revenue", 0)) / pounds) if pounds else None,
    }


def read_inputs() -> Dict:
    st.sidebar.header("Your operation")
    st.sidebar.caption("Enter annual values per cow-unit. The calculation updates as you type.")

    herd_size = st.sidebar.number_input("Brood cows / cow-units", min_value=1, value=50, step=1, key="herd_size")
    acres = st.sidebar.number_input("Grazing acres", min_value=0.0, value=350.0, step=10.0, key="acres")
    weaning_rate = st.sidebar.number_input("Weaning rate (%)", min_value=0.0, max_value=100.0, value=90.0, step=1.0, key="weaning_rate")
    weaning_weight = st.sidebar.number_input("Average weaning weight (lb)", min_value=0.0, value=625.0, step=5.0, key="weaning_weight")
    calf_price = st.sidebar.number_input("Expected calf price ($/lb)", min_value=0.0, value=1.60, step=0.01, format="%.2f", key="calf_price")
    cull_revenue = st.sidebar.number_input("Cull and other revenue ($/cow)", min_value=0.0, value=77.0, step=5.0, key="cull_revenue")

    st.sidebar.subheader("Annual costs per cow")
    costs = {}
    defaults = {
        "pasture": 474.70,
        "feed": 156.37,
        "health": 38.72,
        "replacements": 150.00,
        "machinery": 89.60,
        "labor": 0.00,
        "land": 114.35,
        "other": 132.93,
    }
    for key, label in COST_LABELS.items():
        costs[key] = st.sidebar.number_input(label, min_value=0.0, value=defaults[key], step=5.0, format="%.2f", key=f"cost_{key}")

    st.sidebar.subheader("Your history")
    st.sidebar.caption("Optional. Enter total cost per cow from your records.")
    history = {
        "previous": st.sidebar.number_input("Previous year total cost", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="history_previous"),
        "three_year": st.sidebar.number_input("3-year average total cost", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="history_three_year"),
        "five_year": st.sidebar.number_input("5-year average total cost", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="history_five_year"),
    }
    return {
        "herd_size": herd_size,
        "acres": acres,
        "weaning_rate": weaning_rate,
        "weaning_weight": weaning_weight,
        "calf_price": calf_price,
        "cull_revenue": cull_revenue,
        "costs": costs,
        "history": history,
    }


def load_example() -> None:
    values = {
        "herd_size": 50,
        "acres": 350.0,
        "weaning_rate": 90.0,
        "weaning_weight": 625.0,
        "calf_price": 1.60,
        "cull_revenue": 77.0,
        "cost_pasture": 474.70,
        "cost_feed": 156.37,
        "cost_health": 38.72,
        "cost_replacements": 150.0,
        "cost_machinery": 89.60,
        "cost_labor": 0.0,
        "cost_land": 114.35,
        "cost_other": 132.93,
        "history_previous": 0.0,
        "history_three_year": 0.0,
        "history_five_year": 0.0,
    }
    for key, value in values.items():
        st.session_state[key] = value


def make_report(inputs: Dict, current: Dict, selected: Dict) -> Dict:
    """Create a portable report that can be downloaded and reloaded later."""
    return {
        "tool": "Auburn Producer Margin Check",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "selected_benchmark": selected["key"],
        "inputs": {
            "herd_size": inputs["herd_size"],
            "acres": inputs["acres"],
            "weaning_rate": inputs["weaning_rate"],
            "weaning_weight": inputs["weaning_weight"],
            "calf_price": inputs["calf_price"],
            "cull_revenue": inputs["cull_revenue"],
            "costs": inputs["costs"],
            "history": inputs["history"],
        },
        "calculated": current,
    }


def apply_imported_inputs(payload: Dict) -> bool:
    """Load only recognized numeric fields from a previously exported report."""
    values = payload.get("inputs", {}) if isinstance(payload, dict) else {}
    for key in [
        "herd_size", "acres", "weaning_rate", "weaning_weight",
        "calf_price", "cull_revenue",
    ]:
        if key in values:
            st.session_state[key] = values[key]
    for key, value in values.get("costs", {}).items():
        if key in COST_LABELS:
            st.session_state[f"cost_{key}"] = value
    for key, value in values.get("history", {}).items():
        if key in {"previous", "three_year", "five_year"}:
            st.session_state[f"history_{key}"] = value
    benchmark_key = payload.get("selected_benchmark")
    if benchmark_key in {item["key"] for item in BENCHMARKS}:
        st.session_state["benchmark_key"] = benchmark_key
    return True


def status_text(gap: Optional[float], favorable_when_lower: bool = True) -> str:
    if gap is None:
        return "No public value"
    favorable = gap <= 0 if favorable_when_lower else gap >= 0
    return "Favorable" if favorable else "Watch"


def render_bar(label: str, value: float, benchmark_value: Optional[float], max_value: float) -> None:
    ratio = min(max(value / max_value if max_value else 0, 0), 1)
    benchmark_ratio = min(max(benchmark_value / max_value if benchmark_value is not None and max_value else 0, 0), 1)
    st.markdown(
        f"""
        <div class="bar-label"><span>{label}</span><span>{money(value)}</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:{ratio * 100:.1f}%"></div><span class="benchmark-marker" style="left:{benchmark_ratio * 100:.1f}%"></span></div>
        """,
        unsafe_allow_html=True,
    )


def render_sources() -> None:
    st.markdown("### Sources and definitions")
    st.markdown(
        "The Alabama values come from public representative enterprise budgets and farm models. "
        "The USDA ERS values are national economic costs by herd-size category. "
        "The tool keeps the source year and scope visible because these are different types of benchmark."
    )
    st.markdown(
        "- [Alabama Extension South Alabama Cow-Calf Enterprise Cost Study](https://www.aces.edu/blog/topics/farm-management/south-alabama-cow-calf-enterprise-cost-study/)  \n"
        "- [Alabama Extension Enterprise Budgets for Livestock](https://www.aces.edu/blog/topics/beef/enterprise-budgets-for-livestock/)  \n"
        "- [USDA ERS Structure, Management Practices, and Production Costs of U.S. Beef Cow-Calf Farms](https://ers.usda.gov/publications/107012)  \n"
        "- [CattleFax Cow-Calf Breakeven Evaluator](https://www.cattlefax.com/ccbe/)"
    )
    st.info("A future Auburn version could connect secure producer records, annual benchmark updates, and Extension follow-up reports. The public benchmark layer should be reviewed and refreshed before any production deployment.")


def main() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">AUBURN UNIVERSITY | FARM MANAGEMENT DECISION SUPPORT</div>
          <h1>Producer Margin Check</h1>
          <p>Enter a few farm numbers. The tool calculates the margin, finds the largest gaps against a relevant benchmark, and suggests the next management question.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "benchmark_key" not in st.session_state:
        st.session_state["benchmark_key"] = "aces-2022"
    if st.sidebar.button("Load ACES example", use_container_width=True):
        load_example()
        st.rerun()

    inputs = read_inputs()
    current = calculate(inputs)

    if st.sidebar.button("Find closest public benchmark", use_container_width=True):
        st.session_state["benchmark_key"] = closest_benchmark(int(inputs["herd_size"]))["key"]
        st.rerun()

    benchmark_options = {item["name"]: item["key"] for item in BENCHMARKS}
    selected_name = next(item["name"] for item in BENCHMARKS if item["key"] == st.session_state["benchmark_key"])
    selected_name = st.selectbox("Selected benchmark", list(benchmark_options.keys()), index=list(benchmark_options.keys()).index(selected_name))
    st.session_state["benchmark_key"] = benchmark_options[selected_name]
    selected = get_benchmark(st.session_state["benchmark_key"])

    tab_dashboard, tab_scenario, tab_data, tab_sources = st.tabs(
        ["Dashboard", "Scenario lab", "Data management", "Sources and definitions"]
    )

    with tab_dashboard:
        st.subheader("Your margin screen")
        status = "Positive margin" if current["margin"] >= 0 else "Margin below zero"
        status_color = "normal" if current["margin"] >= 0 else "inverse"
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pounds weaned / exposed cow", f"{current['pounds']:,.0f} lb")
        c2.metric("Gross revenue / cow", money(current["gross_revenue"]))
        c3.metric("Break-even calf price", price(current["break_even"]))
        c4.metric("Margin / cow", money(current["margin"]), delta=status, delta_color=status_color)

        a1, a2, a3 = st.columns(3)
        a1.metric("Estimated annual margin", money(current["annual_margin"]))
        a2.metric("Cost per pound weaned", price(current["cost_per_pound"]))
        a3.metric("Acres per cow", number(current["acres_per_cow"], 1))

        st.markdown("### Selected benchmark")
        meta_cols = st.columns(4)
        meta_cols[0].metric("Reference", selected["geography"])
        meta_cols[1].metric("Source year", selected["year"])
        meta_cols[2].metric("Scope", selected["scope"])
        meta_cols[3].metric("Benchmark total cost", money(selected["total_cost"]))
        st.caption(selected["note"])

        benchmark_data = benchmark_metrics(selected)
        perf_rows = [
            ["Gross revenue / cow", money(current["gross_revenue"]), money(selected["gross_revenue"]), money(current["gross_revenue"] - selected["gross_revenue"]) if selected["gross_revenue"] is not None else "—", "Higher is favorable" if selected["gross_revenue"] is not None else "No public value"],
            ["Total cost / cow", money(current["total_cost"]), money(selected["total_cost"]), money(current["total_cost"] - selected["total_cost"]), "Lower is favorable"],
            ["Margin / cow", money(current["margin"]), money(benchmark_data["margin"]), money(current["margin"] - benchmark_data["margin"]) if benchmark_data["margin"] is not None else "—", "Higher is favorable" if benchmark_data["margin"] is not None else "No public value"],
            ["Weaning rate", pct(inputs["weaning_rate"]), pct(selected["production"].get("weaning_rate")), pct(inputs["weaning_rate"] - selected["production"].get("weaning_rate")) if selected["production"].get("weaning_rate") is not None else "—", "Higher is favorable" if selected["production"].get("weaning_rate") is not None else "No public value"],
            ["Weaning weight", f"{inputs['weaning_weight']:,.0f} lb", f"{selected['production'].get('weaning_weight'):,.0f} lb" if selected["production"].get("weaning_weight") is not None else "—", f"{inputs['weaning_weight'] - selected['production'].get('weaning_weight'):,.0f} lb" if selected["production"].get("weaning_weight") is not None else "—", "Higher is favorable" if selected["production"].get("weaning_weight") is not None else "No public value"],
            ["Break-even price", price(current["break_even"]), price(benchmark_data["break_even"]), price_gap(current["break_even"] - benchmark_data["break_even"]) if benchmark_data["break_even"] is not None else "—", "Lower is favorable" if benchmark_data["break_even"] is not None else "No public value"],
        ]
        st.dataframe(pd.DataFrame(perf_rows, columns=["Metric", "Your operation", "Benchmark", "Gap", "Read"]), use_container_width=True, hide_index=True)

        st.markdown("### Cost breakdown")
        cost_rows = []
        category_gaps = []
        for key, label in COST_LABELS.items():
            own = inputs["costs"][key]
            ref = selected["costs"].get(key)
            gap = own - ref if ref is not None else None
            if gap is not None:
                category_gaps.append((key, label, own, ref, gap))
            cost_rows.append([label, money(own), money(ref), money(gap) if gap is not None else "—", status_text(gap, True) if gap is not None else "Different classification"])
        st.dataframe(pd.DataFrame(cost_rows, columns=["Cost category", "Your operation", "Benchmark", "Gap", "Read"]), use_container_width=True, hide_index=True)
        if selected["cost_groups"]:
            st.caption("This national reference uses broader economic cost groups, so it is shown separately from the Alabama line-item comparison.")
            group_rows = [[label, money(value)] for label, value in selected["cost_groups"].items()]
            st.dataframe(pd.DataFrame(group_rows, columns=["National cost group", "Benchmark / cow"]), use_container_width=True, hide_index=True)
        st.caption("Acreage is calculated for your operation. The public reference models do not report comparable acreage, so acreage matching is reserved for a future Auburn producer-data layer.")

        st.markdown("### Benchmark scan")
        scan_rows = []
        for item in BENCHMARKS:
            cost_gap = current["total_cost"] - item["total_cost"]
            margin_gap = current["margin"] - item["gross_revenue"] + item["total_cost"] if item["gross_revenue"] is not None else None
            scan_rows.append({
                "Reference": item["name"],
                "Scope": item["scope"],
                "Year": item["year"],
                "Cost / cow": item["total_cost"],
                "Your cost gap": cost_gap,
                "Cost signal": "Below reference" if cost_gap < -25 else "Above reference" if cost_gap > 25 else "Close",
                "Margin signal": "Higher than reference" if margin_gap is not None and margin_gap > 25 else "Lower than reference" if margin_gap is not None and margin_gap < -25 else "Not comparable / close",
            })
        st.dataframe(pd.DataFrame(scan_rows), use_container_width=True, hide_index=True, column_config={"Cost / cow": st.column_config.NumberColumn(format="$%d"), "Your cost gap": st.column_config.NumberColumn(format="$%d")})

        history_rows = []
        for label, key in [("Previous year", "previous"), ("3-year average", "three_year"), ("5-year average", "five_year")]:
            if inputs["history"][key] > 0:
                gap = current["total_cost"] - inputs["history"][key]
                history_rows.append([label, money(inputs["history"][key]), money(gap), "Higher current cost" if gap > 25 else "Lower current cost" if gap < -25 else "Close"])
        if history_rows:
            st.markdown("### Your history")
            st.dataframe(pd.DataFrame(history_rows, columns=["Reference", "Historical total cost", "Current minus reference", "Read"]), use_container_width=True, hide_index=True)

        st.markdown("### What the tool sees")
        if category_gaps:
            largest_cost_gap = max(category_gaps, key=lambda row: row[4])
            largest_saving = min(category_gaps, key=lambda row: row[4])
        else:
            largest_cost_gap = largest_saving = None

        diagnosis = []
        suggestions = []
        if current["total_cost"] > selected["total_cost"] + 25:
            diagnosis.append(f"Total cost is {money(current['total_cost'] - selected['total_cost'])} per cow above the selected reference.")
        elif current["total_cost"] < selected["total_cost"] - 25:
            diagnosis.append(f"Total cost is {money(selected['total_cost'] - current['total_cost'])} per cow below the selected reference.")
        else:
            diagnosis.append("Total cost is close to the selected reference; the next question is likely production or marketing performance.")

        if largest_cost_gap and largest_cost_gap[4] > 25:
            diagnosis.append(f"The largest visible cost gap is {largest_cost_gap[1].lower()}, at {money(largest_cost_gap[4])} per cow above the reference.")
            suggestions.append(f"Review {largest_cost_gap[1].lower()} first. Separate necessary productive spending from spending that does not raise pounds sold or preserve the herd.")
        if largest_saving and largest_saving[4] < -25:
            diagnosis.append(f"The strongest cost position is {largest_saving[1].lower()}, at {money(abs(largest_saving[4]))} per cow below the reference.")
            suggestions.append(f"Protect the advantage in {largest_saving[1].lower()} while checking that the lower cost is not reducing production or animal performance.")

        reference_pounds = benchmark_data["pounds"]
        if reference_pounds is not None and current["pounds"] < reference_pounds - 10:
            gap = reference_pounds - current["pounds"]
            diagnosis.append(f"Output is {gap:,.0f} pounds per exposed cow below the selected reference.")
            suggestions.append("Check reproductive performance, death loss, calving distribution, and weaning weight before changing herd size.")
        elif reference_pounds is not None and current["pounds"] > reference_pounds + 10:
            diagnosis.append(f"Output is {current['pounds'] - reference_pounds:,.0f} pounds per exposed cow above the selected reference.")
            suggestions.append("The production result is a strength. Test whether the higher output is also producing an adequate margin after all costs.")

        if selected["gross_revenue"] is not None and current["gross_revenue"] < selected["gross_revenue"] - 25:
            suggestions.append("Review sale weights, sale timing, calf price, and cull revenue together. A price-only response may miss a production or marketing gap.")
        if not suggestions:
            suggestions.append("Use the scenario lab to change one lever at a time and discuss which response fits the operation’s resources and goals.")

        for item in diagnosis:
            st.info(item)
        st.markdown("#### Suggested next steps")
        for item in suggestions:
            st.markdown(f"- {item}")

    with tab_scenario:
        st.subheader("Scenario lab")
        st.caption("Change one or two assumptions and see how much the annual margin moves. This is a planning screen, not a forecast.")
        s1, s2, s3 = st.columns(3)
        scenario_rate = s1.slider("Scenario weaning rate (%)", 50, 100, int(inputs["weaning_rate"]), 1)
        scenario_weight = s2.slider("Scenario weaning weight (lb)", 350, 850, int(inputs["weaning_weight"]), 5)
        scenario_price = s3.number_input("Scenario calf price ($/lb)", min_value=0.0, value=float(inputs["calf_price"]), step=0.01, format="%.2f")
        scenario_cost_multiplier = st.slider("Scenario cost multiplier", 0.75, 1.25, 1.00, 0.01)
        scenario_inputs = deepcopy(inputs)
        scenario_inputs["weaning_rate"] = scenario_rate
        scenario_inputs["weaning_weight"] = scenario_weight
        scenario_inputs["calf_price"] = scenario_price
        scenario_inputs["costs"] = {key: value * scenario_cost_multiplier for key, value in inputs["costs"].items()}
        scenario = calculate(scenario_inputs)
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Scenario pounds", f"{scenario['pounds']:,.0f} lb", f"{scenario['pounds'] - current['pounds']:,.0f} lb")
        sc2.metric("Scenario break-even", price(scenario["break_even"]), f"{scenario['break_even'] - current['break_even']:+.2f}/lb" if current["break_even"] else None)
        sc3.metric("Scenario margin / cow", money(scenario["margin"]), money(scenario["margin"] - current["margin"]))
        sc4.metric("Annual margin change", money(scenario["annual_margin"] - current["annual_margin"]))
        st.markdown("#### The decision question")
        if scenario["margin"] > current["margin"]:
            st.success("This scenario improves the margin. Discuss whether the improvement comes from a realistic production gain, price assumption, or cost change.")
        elif scenario["margin"] < current["margin"]:
            st.warning("This scenario reduces the margin. Use it as a stress test and identify which assumption creates the pressure.")
        else:
            st.info("This scenario leaves the margin unchanged.")

    with tab_data:
        st.subheader("Save, reload, and share the analysis")
        st.caption("The app keeps the calculation in the current browser session. Export a JSON report if you want to save the inputs, calculated results, and selected benchmark for later discussion.")
        report = make_report(inputs, current, selected)
        st.download_button(
            "Export report",
            data=json.dumps(report, indent=2),
            file_name="producer_margin_check_report.json",
            mime="application/json",
            use_container_width=True,
        )

        st.markdown("#### Import a saved report")
        uploaded = st.file_uploader("Choose a JSON report created by this tool", type=["json"])
        if uploaded is not None and st.button("Load imported inputs", use_container_width=True):
            try:
                payload = json.loads(uploaded.getvalue().decode("utf-8"))
                apply_imported_inputs(payload)
                st.success("Inputs loaded. The dashboard will update after this message.")
                st.rerun()
            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, TypeError, ValueError) as exc:
                st.error(f"The file could not be loaded: {exc}")

        st.markdown("#### What is saved")
        st.markdown(
            "The report contains the entered production and cost assumptions, optional history, "
            "the selected public benchmark, and the calculated results. It does not contain a name, "
            "location, or identifying information unless a user writes that information into a field."
        )

    with tab_sources:
        render_sources()

    st.divider()
    st.caption("Prototype for Auburn farm-management and Extension discussion. Public benchmark data should be refreshed and reviewed before deployment with producers.")


if __name__ == "__main__":
    main()
