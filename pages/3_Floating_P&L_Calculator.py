import streamlit as st
import pandas as pd
from millify import prettify

st.set_page_config(layout="wide")
st.title("Avg Price + Floating & Realized P/L Calculator")

LOT_SIZE = 100  # change here if your lot size is different

# -----------------------
# initialize session state
# -----------------------
if "trades" not in st.session_state:
    st.session_state.trades = pd.DataFrame(
        columns=[
            "Side", "Price", "Lot", "Qty (shares)", "Position Before", "Avg Price Before",
            "Realized P/L (this trade)", "Position After", "Avg Price After",
            "Floating P/L After", "Cum Realized P/L"
        ]
    )
if "position_qty" not in st.session_state:
    st.session_state.position_qty = 0  # signed shares: buy +, sell -
if "avg_price" not in st.session_state:
    st.session_state.avg_price = 0.0  # average cost of current open position
if "cum_realized" not in st.session_state:
    st.session_state.cum_realized = 0.0

# -----------------------
# input controls
# -----------------------
st.subheader("Enter Trade")
col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1.container(border=True):
    side = st.selectbox("Side", ["Buy", "Sell"])
with col2.container(border=True):
    price = st.number_input("Executed Price", value=0.0, min_value=0.0, step=0.01, format="%.2f")
with col3.container(border=True):
    lot = st.number_input("Lot", value=1, min_value=1, step=1)
with col4.container(border=True):
    current_price_for_check = st.number_input("Current Price (for floating P/L)", value=price, min_value=0.0, step=0.01, format="%.2f")

# -----------------------
# helper functions
# -----------------------
def add_trade(side: str, price: float, lot: int):
    qty = int(lot * LOT_SIZE)  # convert lots to shares
    signed_qty = qty if side.lower() == "buy" else -qty

    prev_qty = st.session_state.position_qty
    prev_avg = st.session_state.avg_price
    realized_this = 0.0

    # Case 1: no existing position
    if prev_qty == 0:
        # new position simply becomes the trade
        new_qty = signed_qty
        new_avg = price if signed_qty != 0 else 0.0
        # no realized P/L
        realized_this = 0.0

    else:
        # same direction? (both positive or both negative)
        if (prev_qty > 0 and signed_qty > 0) or (prev_qty < 0 and signed_qty < 0):
            # increase position -> weighted avg
            total_shares = abs(prev_qty) + abs(signed_qty)
            new_avg = (prev_avg * abs(prev_qty) + price * abs(signed_qty)) / total_shares
            new_qty = prev_qty + signed_qty
            realized_this = 0.0

        else:
            # opposite direction -> this trade closes or partially closes or reverses
            if abs(signed_qty) < abs(prev_qty):
                # partial close: closed_shares = abs(signed_qty)
                closed_shares = abs(signed_qty)
                if prev_qty > 0:
                    realized_this = (price - prev_avg) * closed_shares
                else:
                    realized_this = (prev_avg - price) * closed_shares

                new_qty = prev_qty + signed_qty  # still has remaining position
                new_avg = prev_avg  # avg unchanged for remaining open portion

            elif abs(signed_qty) == abs(prev_qty):
                # exact close -> realized for all prev_qty
                closed_shares = abs(signed_qty)
                if prev_qty > 0:
                    realized_this = (price - prev_avg) * closed_shares
                else:
                    realized_this = (prev_avg - price) * closed_shares

                new_qty = 0
                new_avg = 0.0

            else:
                # trade size larger than existing position -> close + open opposite
                closed_shares = abs(prev_qty)
                if prev_qty > 0:
                    realized_closed = (price - prev_avg) * closed_shares
                else:
                    realized_closed = (prev_avg - price) * closed_shares

                # remaining shares become new position in trade's direction
                leftover_shares = abs(signed_qty) - closed_shares
                # new average for the leftover position is the trade price
                new_avg = price
                new_qty = signed_qty + prev_qty  # will have sign of signed_qty

                realized_this = realized_closed

    # update session state
    st.session_state.position_qty = new_qty
    st.session_state.avg_price = round(new_avg, 4) if new_qty != 0 else 0.0
    st.session_state.cum_realized += realized_this

    # compute floating P/L after this trade (based on current price input field)
    floating_after = 0.0
    if st.session_state.position_qty != 0:
        floating_after = (current_price_for_check - st.session_state.avg_price) * st.session_state.position_qty
    else:
        floating_after = 0.0

    # append to trades dataframe
    new_row = {
        "Side": side,
        "Price": round(price, 4),
        "Lot": lot,
        "Qty (shares)": signed_qty,
        "Position Before": prev_qty,
        "Avg Price Before": round(prev_avg, 4),
        "Realized P/L (this trade)": round(realized_this, 2),
        "Position After": st.session_state.position_qty,
        "Avg Price After": st.session_state.avg_price,
        "Floating P/L After": round(floating_after, 2),
        "Cum Realized P/L": round(st.session_state.cum_realized, 2)
    }
    # st.session_state.trades = pd.concat([st.session_state.trades, pd.DataFrame([new_row])], ignore_index=True)
    new_df = pd.DataFrame([new_row])
    if st.session_state.trades.empty:
        st.session_state.trades = new_df
    else:
        st.session_state.trades = pd.concat(
            [st.session_state.trades, new_df],
            ignore_index=True
        )


# -----------------------
# Add button
# -----------------------
if st.button("Add Trade", type="primary"):
    if price <= 0 or lot <= 0:
        st.warning("Price and Lot must be > 0.")
    else:
        add_trade(side, float(price), int(lot))
        st.success("Trade added and position/avg recalculated.")

# -----------------------
# Display results
# -----------------------
with st.container(border=True):
    st.subheader("Position Summary")
    colA, colB, colC, colD = st.columns(4)
    with colA.container(border=True):
        st.metric("Position (shares)", value=prettify(int(st.session_state.position_qty)))
    with colB.container(border=True):
        st.metric("Available Lot", value=prettify(int(st.session_state.position_qty)/LOT_SIZE))
    with colC.container(border=True):
        st.metric("Average Price", value=f"{prettify(st.session_state.avg_price)}")
    with colD.container(border=True):
        # floating P/L computed using user-supplied current price field
        if st.session_state.position_qty != 0:
            floating = (current_price_for_check - st.session_state.avg_price) * st.session_state.position_qty
        else:
            floating = 0.0
        st.metric("Floating P/L (using input Current Price)", value=f"{prettify(floating)}")


    st.subheader("Trade Journal")
    st.dataframe(st.session_state.trades, use_container_width=True)

    st.write("### Notes")
    st.write(f"""
    - 1 lot = {LOT_SIZE} shares.
    - Position Qty is signed: buys add positive shares, sells subtract shares
    - Average Price updates only for the remaining open position (weighted average)
    - Realized P/L is calculated when a trade closes (fully or partially) existing position.""")
