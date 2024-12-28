import os
import time
from pathlib import Path

import bt
import pandas as pd
from src.py_libs.algos.my_algos import (
    MeanReversionAlgo,
    MomentumInvestingAlgo,
    PriceFilterAlgo,
    StatDrawdown,
    StatInfoRatio,
    TrendFollowingAlgo,
)
from src.py_libs.data_process.load_utils import (
    get_historical_metadata,
    load_historical_data,
)
from src.py_libs.utils.tickers import sp500_tickers

tickers = {
    "A_G": ["AAPL", "GOOG"],
    "cash": ["SHY"],
    "sp500": sp500_tickers[:5],
    "my_select": ["MSFT", "AMZN", "NVDA", "META", "HSBC", "LLY", "TSLA"],
    "sp500_index": ["SPY"],
}
symbols = (
    tickers["my_select"]
    + tickers["cash"]
    + tickers["A_G"]
    + tickers["sp500"]
    + tickers["sp500_index"]
)


def main():
    from src.py_libs.data_process.load_manager import LocalDataManager
    from src.py_libs.data_process.yahoo_fin_loader import YahooDataLoader
    from src.py_libs.objects.enum import AssetType
    from src.py_libs.utils.hydra import setup_hydra

    yahoo_loader = YahooDataLoader()
    load_manager = LocalDataManager(yahoo_loader)

    config = setup_hydra()
    # from datetime import datetime, timedelta
    load_manager.init_data_files(
        symbols,
        datetime(2018, 12, 1),
        datetime(2023, 12, 10),
        interval=timedelta(minutes=config["env"]["interval_minutes"]),
        asset_type=AssetType.Stock,
    )
    
    load_manager.update_all_in_data_dir(asset_type=AssetType.Stock)

    data = load_historical_data(Path("output/historical_data"))
    meta_data = get_historical_metadata(Path("output/historical_data"))
    prices = pd.DataFrame.from_dict({k: v.adjclose for k, v in data.items()}).dropna()

    spy_eq_strategy = bt.Strategy(
        "SPY_BASE",
        algos=[
            bt.algos.RunQuarterly(),
            bt.algos.SelectAll(),
            bt.algos.SelectThese(tickers["sp500_index"]),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    ag_eq_strategy = bt.Strategy(
        "AAPL_GOOG",
        algos=[
            bt.algos.RunQuarterly(),
            bt.algos.SelectAll(),
            bt.algos.SelectThese(tickers["A_G"]),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    ag_algo_strategy_3 = bt.Strategy(
        "AAPL_GOOG_algo_3",
        algos=[
            bt.algos.RunWeekly(),
            bt.algos.SelectAll(),
            PriceFilterAlgo(),
            bt.algos.SelectN(3, sort_descending=False),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    ag_algo_strategy_6 = bt.Strategy(
        "AAPL_GOOG_algo_6",
        algos=[
            bt.algos.RunWeekly(),
            bt.algos.SelectAll(),
            PriceFilterAlgo(),
            bt.algos.SelectN(6, sort_descending=False),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )
    ag_algo_q_strategy_6 = bt.Strategy(
        "AAPL_GOOG_q_algo_6",
        algos=[
            bt.algos.RunQuarterly(),
            bt.algos.SelectAll(),
            PriceFilterAlgo(lookback=7, lag=1),
            bt.algos.SelectN(6, sort_descending=False),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    other_eq_strategy = bt.Strategy(
        "OTHER_EQ",
        algos=[
            bt.algos.RunQuarterly(),
            bt.algos.SelectAll(),
            # bt.algos.SelectThese(tickers["sp500"]),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    sphmv_strategy = bt.Strategy(
        "SPHMV",
        algos=[
            bt.algos.RunQuarterly(),
            bt.algos.SelectAll(),
            # bt.algos.SelectThese(tickers["sp500"]),
            StatDrawdown(lookback=3650),
            bt.algos.SelectN(5, sort_descending=False),
            StatInfoRatio(benchmark="AAPL", lookback=210, lag=30),
            bt.algos.SelectN(3, sort_descending=True),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    all_trend_strategy = bt.Strategy(
        "ALL_TREND",
        algos=[
            bt.algos.RunMonthly(),
            bt.algos.SelectAll(),
            TrendFollowingAlgo(10, 30),
            bt.algos.SelectN(6, sort_descending=False),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    all_momentum_strategy = bt.Strategy(
        "ALL_MOMENTUM",
        algos=[
            bt.algos.RunMonthly(),
            bt.algos.SelectAll(),
            # bt.algos.SelectThese(tickers["sp500"]),
            MomentumInvestingAlgo(10, 30),
            bt.algos.SelectN(6, sort_descending=True),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    all_meanrev_strategy = bt.Strategy(
        "ALL_MEANREV",
        algos=[
            bt.algos.RunQuarterly(),
            bt.algos.SelectAll(),
            # bt.algos.SelectThese(tickers["sp500"]),
            MeanReversionAlgo(10, 30),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance(),
        ],
    )

    backtest_spy_eq = bt.Backtest(spy_eq_strategy, prices)
    backtest_ag = bt.Backtest(ag_eq_strategy, prices)
    backtest_ag_3_algo = bt.Backtest(ag_algo_strategy_3, prices)
    backtest_ag_6_algo = bt.Backtest(ag_algo_strategy_6, prices)
    backtest_q_ag_6_algo = bt.Backtest(ag_algo_q_strategy_6, prices)
    backtest_sphmv = bt.Backtest(sphmv_strategy, prices)
    backtest_other_eq = bt.Backtest(other_eq_strategy, prices)
    backtest_all_trend = bt.Backtest(all_trend_strategy, prices)
    backtest_all_momentum = bt.Backtest(all_momentum_strategy, prices)
    backtest_all_meanrev = bt.Backtest(all_meanrev_strategy, prices)

    report = bt.run(
        backtest_spy_eq,
        # backtest_ag,
        # backtest_ag_3_algo,
        # backtest_ag_6_algo,
        backtest_q_ag_6_algo,
        # backtest_sphmv,
        backtest_other_eq,
        backtest_all_trend,
        backtest_all_momentum,
        backtest_all_meanrev,
    )
    # input()
    time.sleep(3)
    os.makedirs("plots", exist_ok=True)
    axes = report.plot()
    axes.figure.savefig("plots/equity_progression.png")

    # ok and what about some stats?
    report.display()

    # ok and how does the return distribution look like?
    report.plot_histogram()

    print("OK")


if __name__ == "__main__":
    main()
