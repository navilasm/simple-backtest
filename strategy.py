import backtrader as bt

class StrategyRSI(bt.Strategy):
    params = (('rsi_period', 14), ('rsi_lower', 30), ('rsi_upper', 70),)

    def __init__(self):
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)
        self.indicator_values = []
        self.indicator_headers = None

    def next(self):
        try:
            rsi_val = self.rsi[0]
        except:
            rsi_val = None

        local_vars = locals()
        if self.indicator_headers is None:
            var_names = [name for name in local_vars if name not in ('self', 'local_vars')]
            self.indicator_headers = ['datetime'] + var_names
            self.indicator_values.append(self.indicator_headers)
        
        self.indicator_values.append([self.data.datetime.datetime(0), rsi_val])

        if not self.position:  # Not in the market
            if rsi_val is not None and rsi_val < self.params.rsi_lower:
                self.buy()
        else:  # In the market
            if rsi_val is not None and rsi_val > self.params.rsi_upper:
                self.sell()


class StrategyMACross(bt.Strategy):
    params = (('fast_ma', 10), ('slow_ma', 20))

    def __init__(self):
        # Indicators
        self.fast = bt.indicators.SMA(self.data.close, period=self.params.fast_ma)
        self.slow = bt.indicators.SMA(self.data.close, period=self.params.slow_ma)
        self.crossover = bt.indicators.CrossOver(self.fast, self.slow)

        # For logging indicator values
        self.indicator_values = []
        self.indicator_headers = None

    def next(self):
        try:
            fast_val = self.fast[0]
            slow_val = self.slow[0]
            cross_val = self.crossover[0]
        except:
            fast_val = slow_val = cross_val = None

        # Header row
        local_vars = locals()
        if self.indicator_headers is None:
            var_names = [name for name in local_vars if name not in ('self', 'local_vars')]
            self.indicator_headers = ['datetime'] + var_names
            self.indicator_values.append(self.indicator_headers)

        # Log values
        self.indicator_values.append([
            self.data.datetime.datetime(0),
            fast_val,
            slow_val,
            cross_val
        ])

        # --- Trading Logic ---
        if not self.position:
            # Buy when fast MA crosses above slow MA
            if cross_val is not None and cross_val > 0:
                self.buy()
        else:
            # Sell when fast MA crosses back below slow MA
            if cross_val is not None and cross_val < 0:
                self.sell()


class StrategySAR(bt.Strategy):
    params = (
        ('af', 0.02),    # Acceleration Factor
        ('afmax', 0.1),  # Maximum AF
    )

    def __init__(self):
        # Parabolic SAR indicator
        self.psar = bt.indicators.ParabolicSAR(
            af=self.params.af,
            afmax=self.params.afmax
        )

        # For logging indicator values
        self.indicator_values = []
        self.indicator_headers = None

    def next(self):
        try:
            psar_val = self.psar[0]
            close_val = self.data.close[0]
        except:
            psar_val = None
            close_val = None

        # Create header row once
        local_vars = locals()
        if self.indicator_headers is None:
            var_names = [name for name in local_vars if name not in ('self', 'local_vars')]
            self.indicator_headers = ['datetime'] + var_names
            self.indicator_values.append(self.indicator_headers)

        # Log indicator values
        self.indicator_values.append([
            self.data.datetime.datetime(0),
            psar_val,
            close_val
        ])

        # --- Trading Logic (Simple SAR Trend-Following) ---

        # Enter long when price moves above SAR
        if not self.position:
            if psar_val is not None and close_val is not None:
                if close_val > psar_val:
                    self.buy()

        # Exit long when price moves below SAR
        else:
            if psar_val is not None and close_val is not None:
                if close_val < psar_val:
                    self.sell()


class StrategyMACD(bt.Strategy):
    params = (
        ('fast', 12),
        ('slow', 26),
        ('signal', 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast,
            period_me2=self.params.slow,
            period_signal=self.params.signal
        )

        self.macd_line = self.macd.macd
        self.signal_line = self.macd.signal

        # Backtrader MACD has no .histo — compute manually
        self.hist = self.macd.macd - self.macd.signal

        self.indicator_values = []
        self.indicator_headers = None

    def next(self):
        try:
            macd_val = self.macd_line[0]
            signal_val = self.signal_line[0]
            hist_val = self.hist[0]
        except:
            macd_val = signal_val = hist_val = None

        local_vars = locals()
        if self.indicator_headers is None:
            var_names = [v for v in local_vars if v not in ('self', 'local_vars')]
            self.indicator_headers = ['datetime'] + var_names
            self.indicator_values.append(self.indicator_headers)

        self.indicator_values.append([
            self.data.datetime.datetime(0),
            macd_val,
            signal_val,
            hist_val
        ])

        # --- Simple MACD Trading Logic ---
        if not self.position:
            if hist_val is not None and hist_val > 0:
                self.buy()
        else:
            if hist_val is not None and hist_val < 0:
                self.sell()


class StrategyBollinger(bt.Strategy):
    params = (('period', 20), ('devfactor', 2.0),)

    def __init__(self):
        self.bb = bt.indicators.BollingerBands(
            period=self.params.period, devfactor=self.params.devfactor
        )

        self.mid = self.bb.mid
        self.top = self.bb.top
        self.bot = self.bb.bot

        self.indicator_values = []
        self.indicator_headers = None

    def next(self):
        try:
            mid = float(self.mid[0])
            top = float(self.top[0])
            bot = float(self.bot[0])
            close = float(self.data.close[0])
        except:
            mid = top = bot = close = None

        # Store indicator values
        local_vars = locals()
        if self.indicator_headers is None:
            var_names = [n for n in local_vars if n not in ('self','local_vars')]
            self.indicator_headers = ['datetime'] + var_names
            self.indicator_values.append(self.indicator_headers)

        self.indicator_values.append([
            self.data.datetime.datetime(0),
            mid, top, bot, close,
        ])

        # --- Logic ---
        if not self.position:
            if close is not None and close < bot:
                self.buy()
        else:
            if close is not None and close > top:
                self.sell()


class StrategyWilliamsR(bt.Strategy):
    params = (('period', 14),)

    def __init__(self):
        self.wr = bt.indicators.WilliamsR(period=self.params.period)

        self.indicator_values = []
        self.indicator_headers = None

    def next(self):
        try:
            wr_val = float(self.wr[0])
        except:
            wr_val = None

        local_vars = locals()
        if self.indicator_headers is None:
            var_names = [n for n in local_vars if n not in ('self','local_vars')]
            self.indicator_headers = ['datetime'] + var_names
            self.indicator_values.append(self.indicator_headers)

        self.indicator_values.append([
            self.data.datetime.datetime(0),
            wr_val
        ])

        # --- Logic ---
        if not self.position:
            if wr_val is not None and wr_val < -80:
                self.buy()
        else:
            if wr_val is not None and wr_val > -20:
                self.sell()


class StrategyHarami(bt.Strategy):
    def __init__(self):
        # Returns +100 (bullish), -100 (bearish), 0 (none)
        self.harami = bt.talib.CDLHARAMI(
            self.data.open,
            self.data.high,
            self.data.low,
            self.data.close
        )

        self.indicator_values = []
        self.indicator_headers = None

    def next(self):
        try:
            harami_val = int(self.harami[0])
        except:
            harami_val = None

        local_vars = locals()
        if self.indicator_headers is None:
            var_names = [n for n in local_vars if n not in ('self','local_vars')]
            self.indicator_headers = ['datetime'] + var_names
            self.indicator_values.append(self.indicator_headers)

        self.indicator_values.append([
            self.data.datetime.datetime(0),
            harami_val
        ])

        # --- Logic ---
        if not self.position:
            if harami_val == 100:   # Bullish Harami
                self.buy()
        else:
            if harami_val == -100:  # Bearish Harami
                self.sell()
