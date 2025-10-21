from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, CategoricalParameter
import talib.abstract as ta
import numpy as np
import pandas as pd



class AdaptiveFractalGridScalping(IStrategy):

    can_short = True
    # --- Параметры ---
    atr_length = IntParameter(10, 30, default=14, space="buy")
    sma_length = IntParameter(20, 100, default=50, space="buy")
    grid_multiplier_high = DecimalParameter(1.0, 3.0, default=1.0, space="buy")
    grid_multiplier_low = DecimalParameter(0.2, 1.5, default=0.8, space="buy")
    trail_stop_multiplier = DecimalParameter(0.2, 2.0, default=1.1, space="sell")
    volatility_threshold = DecimalParameter(0.5, 3.0, default=0.5, space="buy")
    
    # Динамическое плечо
    use_dynamic_leverage = CategoricalParameter([True, False], default=True, space="buy")
    base_leverage = IntParameter(1, 20, default=5, space="buy")
    max_leverage = IntParameter(1, 20, default=15, space="buy")
    leverage_atr_period = IntParameter(10, 30, default=14, space="buy")
    leverage_multiplier = DecimalParameter(0.5, 2.0, default=1.0, space="buy")

    timeframe = '5m'
    minimal_roi = {}
    stoploss = -0.99
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True
    use_custom_stoploss = False
    
    startup_candle_count = 400
    max_pending_bars = 10  # через сколько свечей снимать лимитный ордер

    def informative_pairs(self):
        # Здесь можно реализовать фильтр по топ-80 капитализации через внешний список
        # Для примера: просто возвращаем все пары из whitelist
        pairs = self.dp.current_whitelist()
        return [(pair, self.timeframe) for pair in pairs]

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=self.atr_length.value)
        dataframe['sma'] = ta.SMA(dataframe, timeperiod=self.sma_length.value)
        dataframe['fractal_high'] = dataframe['high'].rolling(5, center=True).apply(
            lambda x: x[2] if x[2] == max(x) else np.nan, raw=True)
        dataframe['fractal_low'] = dataframe['low'].rolling(5, center=True).apply(
            lambda x: x[2] if x[2] == min(x) else np.nan, raw=True)
        dataframe['grid_level_high'] = dataframe['fractal_high'] + dataframe['atr'] * self.grid_multiplier_high.value
        dataframe['grid_level_low'] = dataframe['fractal_low'] - dataframe['atr'] * self.grid_multiplier_low.value
        dataframe['pending_entry_price'] = np.nan
        dataframe['pending_entry_bars'] = 0
        # Для виртуальных шортовых ордеров
        dataframe['pending_entry_price_short'] = np.nan
        dataframe['pending_entry_bars_short'] = 0

        # --- Добавляем нормализацию волатильности (z-score ATR/close) ---
        window = 100
        dataframe['rel_volatility'] = dataframe['atr'] / dataframe['close']
        dataframe['rel_volatility_mean'] = dataframe['rel_volatility'].rolling(window).mean()
        dataframe['rel_volatility_std'] = dataframe['rel_volatility'].rolling(window).std()
        dataframe['norm_volatility'] = (
            (dataframe['rel_volatility'] - dataframe['rel_volatility_mean']) / dataframe['rel_volatility_std']
        )

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['enter_long'] = 0
        dataframe['enter_short'] = 0

        # Фильтр по нормализованной волатильности с параметром
        cond_vol = dataframe['norm_volatility'] > self.volatility_threshold.value

        # Лонг-сигнал
        cond_long = (
            cond_vol &
            (dataframe['close'] > dataframe['sma']) &
            dataframe['fractal_low'].notna()
        )

        # Шорт-сигнал
        cond_short = (
            cond_vol &
            (dataframe['close'] < dataframe['sma']) &
            dataframe['fractal_high'].notna()
        )

        dataframe.loc[cond_long, 'pending_entry_price'] = dataframe.loc[cond_long, 'grid_level_low']
        dataframe.loc[cond_long, 'pending_entry_bars'] = 1

        dataframe.loc[cond_short, 'pending_entry_price_short'] = dataframe.loc[cond_short, 'grid_level_high']
        dataframe.loc[cond_short, 'pending_entry_bars_short'] = 1

        # Переносим цену и счетчик вперёд, если ещё не было входа (лонг)
        for i in range(1, len(dataframe)):
            if pd.isna(dataframe.at[dataframe.index[i], 'pending_entry_price']):
                dataframe.at[dataframe.index[i], 'pending_entry_price'] = dataframe.at[dataframe.index[i-1], 'pending_entry_price']
                dataframe.at[dataframe.index[i], 'pending_entry_bars'] = dataframe.at[dataframe.index[i-1], 'pending_entry_bars'] + 1

            # Если цена дошла до лимитного уровня — выставляем сигнал на вход по рынку (лонг)
            if not pd.isna(dataframe.at[dataframe.index[i], 'pending_entry_price']):
                entry_price = dataframe.at[dataframe.index[i], 'pending_entry_price']
                if dataframe.at[dataframe.index[i], 'low'] <= entry_price <= dataframe.at[dataframe.index[i], 'high']:
                    dataframe.at[dataframe.index[i], 'enter_long'] = 1
                    dataframe.at[dataframe.index[i], 'pending_entry_price'] = np.nan
                    dataframe.at[dataframe.index[i], 'pending_entry_bars'] = 0
                # Если лимит не сработал за max_pending_bars — снимаем заявку
                elif dataframe.at[dataframe.index[i], 'pending_entry_bars'] > self.max_pending_bars:
                    dataframe.at[dataframe.index[i], 'pending_entry_price'] = np.nan
                    dataframe.at[dataframe.index[i], 'pending_entry_bars'] = 0

        # Переносим цену и счетчик вперёд, если ещё не было входа (шорт)
        for i in range(1, len(dataframe)):
            if pd.isna(dataframe.at[dataframe.index[i], 'pending_entry_price_short']):
                dataframe.at[dataframe.index[i], 'pending_entry_price_short'] = dataframe.at[dataframe.index[i-1], 'pending_entry_price_short']
                dataframe.at[dataframe.index[i], 'pending_entry_bars_short'] = dataframe.at[dataframe.index[i-1], 'pending_entry_bars_short'] + 1

            # Если цена дошла до лимитного уровня — выставляем сигнал на вход по рынку (шорт)
            if not pd.isna(dataframe.at[dataframe.index[i], 'pending_entry_price_short']):
                entry_price = dataframe.at[dataframe.index[i], 'pending_entry_price_short']
                if dataframe.at[dataframe.index[i], 'low'] <= entry_price <= dataframe.at[dataframe.index[i], 'high']:
                    dataframe.at[dataframe.index[i], 'enter_short'] = 1
                    dataframe.at[dataframe.index[i], 'pending_entry_price_short'] = np.nan
                    dataframe.at[dataframe.index[i], 'pending_entry_bars_short'] = 0
                # Если лимит не сработал за max_pending_bars — снимаем заявку
                elif dataframe.at[dataframe.index[i], 'pending_entry_bars_short'] > self.max_pending_bars:
                    dataframe.at[dataframe.index[i], 'pending_entry_price_short'] = np.nan
                    dataframe.at[dataframe.index[i], 'pending_entry_bars_short'] = 0

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe['pending_exit_price_tp_long'] = np.nan
        dataframe['pending_exit_price_sl_long'] = np.nan
        dataframe['pending_exit_price_tp_short'] = np.nan
        dataframe['pending_exit_price_sl_short'] = np.nan
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0

        for i in range(1, len(dataframe)):
            # --- LONG ---
            # Если был вход в long — фиксируем уровни TP и SL
            if dataframe.at[dataframe.index[i-1], 'enter_long'] == 1:
                dataframe.at[dataframe.index[i], 'pending_exit_price_tp_long'] = dataframe.at[dataframe.index[i], 'grid_level_high']
                dataframe.at[dataframe.index[i], 'pending_exit_price_sl_long'] = dataframe.at[dataframe.index[i], 'fractal_low'] - dataframe.at[dataframe.index[i], 'atr'] * self.trail_stop_multiplier.value
            else:
                dataframe.at[dataframe.index[i], 'pending_exit_price_tp_long'] = dataframe.at[dataframe.index[i-1], 'pending_exit_price_tp_long']
                dataframe.at[dataframe.index[i], 'pending_exit_price_sl_long'] = dataframe.at[dataframe.index[i-1], 'pending_exit_price_sl_long']

            # Если цена дошла до TP или SL — закрываем long и сбрасываем уровни
            if not pd.isna(dataframe.at[dataframe.index[i], 'pending_exit_price_tp_long']):
                if dataframe.at[dataframe.index[i], 'high'] >= dataframe.at[dataframe.index[i], 'pending_exit_price_tp_long']:
                    dataframe.at[dataframe.index[i], 'exit_long'] = 1
                    dataframe.at[dataframe.index[i], 'pending_exit_price_tp_long'] = np.nan
                    dataframe.at[dataframe.index[i], 'pending_exit_price_sl_long'] = np.nan
                elif dataframe.at[dataframe.index[i], 'low'] <= dataframe.at[dataframe.index[i], 'pending_exit_price_sl_long']:
                    dataframe.at[dataframe.index[i], 'exit_long'] = 1
                    dataframe.at[dataframe.index[i], 'pending_exit_price_tp_long'] = np.nan
                    dataframe.at[dataframe.index[i], 'pending_exit_price_sl_long'] = np.nan

            # --- SHORT ---
            # Если был вход в short — фиксируем уровни TP и SL
            if dataframe.at[dataframe.index[i-1], 'enter_short'] == 1:
                dataframe.at[dataframe.index[i], 'pending_exit_price_tp_short'] = dataframe.at[dataframe.index[i], 'grid_level_low']
                dataframe.at[dataframe.index[i], 'pending_exit_price_sl_short'] = dataframe.at[dataframe.index[i], 'fractal_high'] + dataframe.at[dataframe.index[i], 'atr'] * self.trail_stop_multiplier.value
            else:
                dataframe.at[dataframe.index[i], 'pending_exit_price_tp_short'] = dataframe.at[dataframe.index[i-1], 'pending_exit_price_tp_short']
                dataframe.at[dataframe.index[i], 'pending_exit_price_sl_short'] = dataframe.at[dataframe.index[i-1], 'pending_exit_price_sl_short']

            # Если цена дошла до TP или SL — закрываем short и сбрасываем уровни
            if not pd.isna(dataframe.at[dataframe.index[i], 'pending_exit_price_tp_short']):
                if dataframe.at[dataframe.index[i], 'low'] <= dataframe.at[dataframe.index[i], 'pending_exit_price_tp_short']:
                    dataframe.at[dataframe.index[i], 'exit_short'] = 1
                    dataframe.at[dataframe.index[i], 'pending_exit_price_tp_short'] = np.nan
                    dataframe.at[dataframe.index[i], 'pending_exit_price_sl_short'] = np.nan
                elif dataframe.at[dataframe.index[i], 'high'] >= dataframe.at[dataframe.index[i], 'pending_exit_price_sl_short']:
                    dataframe.at[dataframe.index[i], 'exit_short'] = 1
                    dataframe.at[dataframe.index[i], 'pending_exit_price_tp_short'] = np.nan
                    dataframe.at[dataframe.index[i], 'pending_exit_price_sl_short'] = np.nan

        return dataframe

    def leverage(self, pair: str, current_time, current_rate, proposed_leverage, max_leverage, side, **kwargs) -> float:
        if not self.use_dynamic_leverage.value:
            return float(self.base_leverage.value)
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        atr = ta.ATR(dataframe['high'], dataframe['low'], dataframe['close'], timeperiod=self.leverage_atr_period.value)
        current_atr = atr.iloc[-1] if len(atr) > 0 else 0.0
        # Чем выше волатильность, тем меньше плечо
        vol_factor = max(0.5, 2.0 - current_atr * self.leverage_multiplier.value)
        lev = float(self.base_leverage.value) * vol_factor
        lev = min(lev, float(self.max_leverage.value), max_leverage)
        lev = max(1.0, lev)
        return lev 

    plot_config = {
        'main_plot': {
            'sma': {'color': 'blue'},
            'fractal_high': {'color': 'red', 'marker': 'triangle-down', 'markersize': 6},
            'fractal_low': {'color': 'green', 'marker': 'triangle-up', 'markersize': 6},
            'grid_level_high': {'color': 'orange', 'linestyle': 'dashed'},
            'grid_level_low': {'color': 'purple', 'linestyle': 'dashed'},
            'pending_entry_price': {'color': 'yellow', 'linestyle': 'dotted'},
            'pending_entry_price_long': {'color': 'yellow', 'linestyle': 'dotted'},
            'pending_entry_price_short': {'color': 'yellow', 'linestyle': 'dotted'},
            'pending_exit_price_tp': {'color': 'lime', 'linestyle': 'dotted'},
            'pending_exit_price_sl': {'color': 'red', 'linestyle': 'dotted'},
            'pending_exit_price_tp_long': {'color': 'lime', 'linestyle': 'dotted'},
            'pending_exit_price_sl_long': {'color': 'red', 'linestyle': 'dotted'},
            'pending_exit_price_tp_short': {'color': 'orange', 'linestyle': 'dotted'},
            'pending_exit_price_sl_short': {'color': 'magenta', 'linestyle': 'dotted'},
        },
        'subplots': {
            "ATR": {
                'atr': {'color': 'black'},
            },
            "SIGNALS": {
                'enter_long': {'color': 'green', 'marker': '^', 'markersize': 8},
                'enter_short': {'color': 'red', 'marker': 'v', 'markersize': 8},
                'exit_long': {'color': 'orange', 'marker': 's', 'markersize': 6},
                'exit_short': {'color': 'purple', 'marker': 's', 'markersize': 6},
            }
        }
    }