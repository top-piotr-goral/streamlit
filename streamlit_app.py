import streamlit as st
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


df = pd.read_excel("3_with_dividends_groups.xlsx")

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


df_ma_in_dividends_group = (
    df.groupby(["Ticker", "Dividends_group_from_Dividends_flag_shifted"])["Close"]
    .rolling(window=window)
    .mean()
    .reset_index()
)
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

smooth_d1 = np.gradient(df_example[f"Close_MA_{window}"])
smooth_d2 = np.gradient(np.gradient(df_example[f"Close_MA_{window}"]))
infls = np.where(np.diff(np.sign(smooth_d2)))[0]

# plot results
plt.rcParams["figure.figsize"] = (12, 5)
fig, ax = plt.subplots(constrained_layout=True)


ax.plot(df_example["Close"], label="Close")
ax.plot(df_example[f"Close_MA_{window}"], label=f"Close_MA_{window}")

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

st.pyplot(fig)
