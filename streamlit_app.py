import streamlit as st
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


df = pd.read_excel("3_with_dividends_groups.xlsx")
df_max_index_in_dividends_group = (
    df.groupby(["Ticker", "Dividends_group_from_Dividends_flag_shifted"])[
        "index_in_dividends_group"
    ]
    .max()
    .reset_index()
)
df_max_index_in_dividends_group = df_max_index_in_dividends_group.merge(df, how="left",)


ticker = st.selectbox("Ticker", df["Ticker"].drop_duplicates().tolist())
st.write("You selected Ticker:", ticker)

df_ticker = df[df["Ticker"] == ticker]

window = st.slider("MA window", 1, 7, 4)
st.write("You selected MA window:", window)

period = st.slider(
    "Dividends period",
    int(df_ticker["Dividends_group_from_Dividends_flag_shifted"].min()),
    int(df_ticker["Dividends_group_from_Dividends_flag_shifted"].max()),
    1,
)
st.write("You selected Dividens period:", period)


# generic computations for al tickers
df_ma_in_dividends_group = (
    df.groupby(["Ticker", "Dividends_group_from_Dividends_flag_shifted"])["Close"]
    .rolling(window=window)
    .mean()
    .reset_index()
)
df_ma_in_dividends_group_no_nulls = df_ma_in_dividends_group[
    ~df_ma_in_dividends_group["Close"].isnull()
]

# computations all periods
df_ma_min_value_in_dividends_group = (
    df_ma_in_dividends_group_no_nulls.groupby(
        ["Ticker", "Dividends_group_from_Dividends_flag_shifted"]
    )["Close"]
    .min()
    .reset_index()
)

df_scenario_1_ma_min_value_compare = pd.merge(
    df_max_index_in_dividends_group,
    df_ma_min_value_in_dividends_group,
    on=["Ticker", "Dividends_group_from_Dividends_flag_shifted"],
    suffixes=("_max", "_ma_min_value"),
)
df_scenario_1_ma_min_value_compare["Close_diff"] = (
    df_scenario_1_ma_min_value_compare["Close_max"]
    - df_scenario_1_ma_min_value_compare["Close_ma_min_value"]
)

df_ma_argmin_value_in_dividends_group = (
    df_ma_in_dividends_group_no_nulls.groupby(
        ["Ticker", "Dividends_group_from_Dividends_flag_shifted"]
    )["Close"]
    .apply(lambda x: x.argmin())
    .reset_index()
)
df_ma_argmin_value_in_dividends_group.rename(columns={"Close":"Close_argmin_value"}, inplace=True)

df_scenario_1_min_value_compare = pd.merge(
    df_scenario_1_ma_min_value_compare,
    df_ma_argmin_value_in_dividends_group,
    on=["Ticker", "Dividends_group_from_Dividends_flag_shifted"],
)

df_scenario_1_min_value_compare_example = df_scenario_1_min_value_compare[
    df_scenario_1_min_value_compare["Ticker"] == ticker
]
df_scenario_1_min_value_compare_example.reset_index(drop=True, inplace=True)

period_ma_argmin_index = df_scenario_1_min_value_compare_example["Close_argmin_value"].iloc[period-1]

# computations dividens period
df_ma_with_regular_close = df.copy()
df_ma_with_regular_close[f"Close_MA_{window}"] = df_ma_in_dividends_group["Close"]
df_ma_with_regular_close = df_ma_with_regular_close[
    ~df_ma_with_regular_close[f"Close_MA_{window}"].isnull()
]

df_example = df_ma_with_regular_close[
    (df_ma_with_regular_close["Ticker"] == ticker)
    & (
        df_ma_with_regular_close["Dividends_group_from_Dividends_flag_shifted"]
        == period
    )
]
df_example.reset_index(drop=True, inplace=True)

st.write("Period start:", df_example["Datetime"].min())
st.write("Period end:", df_example["Datetime"].max())

st.markdown("""---""")

smooth_d1 = np.gradient(df_example[f"Close_MA_{window}"])
smooth_d2 = np.gradient(np.gradient(df_example[f"Close_MA_{window}"]))
infls = np.where(np.diff(np.sign(smooth_d2)))[0]

# plot results: 1 dividends
plt.rcParams["figure.figsize"] = (12, 5)
fig, ax = plt.subplots(constrained_layout=True)


ax.plot(df_example["Close"], label="Close")
ax.plot(df_example[f"Close_MA_{window}"], label=f"Close_MA_{window}")
ax.scatter(df_example.index[period_ma_argmin_index], df_example[f"Close_MA_{window}"].iloc[period_ma_argmin_index], color="red")

ax.set_xlabel("Day")
ax.set_ylabel("Close")

# derivs
ax2 = ax.twinx()
ax2.plot(
    smooth_d1, label=f"First Derivative from Close_MA_{window}", color="purple", ls="--"
)
ax2.plot(
    smooth_d2, label=f"Second Derivative from Close_MA_{window}", color="red", ls="--"
)

ax2.set_ylabel("Derivative")

lines = ax.get_lines() + ax2.get_lines()
ax.legend(lines, [line.get_label() for line in lines], loc="upper left")

for i, infl in enumerate(infls, 1):
    ax2.axvline(x=infl + 1, color="k", label=f"Inflection Point")

st.write("Dividends Period trend - supports detailed investigation on which measure to use to find inflections")
st.write("Currently used measure: minimum MA (red dot)")
st.pyplot(fig)

# all periods
fig2, ax_fig_2 = plt.subplots(constrained_layout=True)
ax_fig_2.scatter(
        df_scenario_1_min_value_compare_example["Close_argmin_value"],
        df_scenario_1_min_value_compare_example["Close_diff"]
)
ax_fig_2.scatter(
        df_scenario_1_min_value_compare_example["Close_argmin_value"].iloc[period-1],
        df_scenario_1_min_value_compare_example["Close_diff"].iloc[period-1],
        color="red"
)
ax_fig_2.set_ylabel(f"Close diff")
ax_fig_2.set_xlabel(f"Day with minimum Close_MA_{window}")

st.markdown("""---""")

st.write("All periods summary - supports analysis at Ticker level to find consistent inflection patterns before Dividends")
st.write("If points are concentrated in top left corner, that means there is long increasing trend before Dividends")
st.pyplot(fig2)

st.write("Close diff (OY) refers to difference: Close at Dividends day - Close at minimum MA")

st.write("Based on All periods summary we can decide if for given Ticker we can observe increasing trend before Dividends in majority of periods")
