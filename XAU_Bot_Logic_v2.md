# XAU/USD Analysis Bot — Complete Logic Specification
## Version 2.0 — Hardened Build Document

**Instrument:** XAU/USD only  
**Account:** Exness $10 | 0.01 lot fixed | $1 per $1 gold move  
**Bot role:** Analysis and signal output only — manual execution in MetaTrader 5  
**Architecture:** Deterministic Python engine. Claude explains outputs and flags contradictions. Claude never generates signals.  
**Authority source:** Edge 1 Phases 1–5 + Edge 2 Phases 1–11 backtested on 38,808 1H candles  
**v2 additions:** Regime Drift Detection | Live vs Backtest Parity Monitor | Claude Critic Layer  

---

## WHAT CHANGED IN v2 (read this first)

v1 was a correct and disciplined system. Three structural gaps were identified during review:

**Gap 1 — No mechanism to detect when the market regime shifts away from the backtested era.**  
The edges were validated on 2020–2026 XAU/USD data. That era includes COVID volatility, the 2022 rate shock, and the 2024–2025 geopolitical gold spike. The market personality encoded in the thresholds (0.4 body ratio, EMA structure, session windows) may not persist indefinitely. The system had no way to know if it was degrading silently.

**Gap 2 — No mechanism to verify that live indicator calculations match backtest calculations candle-by-candle.**  
Rule 2 stated "byte-for-byte identical." But EMA drift from missing candles, ATR drift from feed gaps, and session misalignment from broker-side timing differences accumulate silently. There was no enforcement — only an intention.

**Gap 3 — Claude's role was passive (narrator only).**  
The critic identified that the overlap engine was compensating for a deeper correlation: both edges reading the same volatility structure through different lenses. A passive Claude cannot flag when technically valid signals contradict each other in context. A bounded critic layer — read access only, never modifying the signal — closes this gap without violating Rule 3.

**What did NOT change:**  
All locked parameters. Both edge detection logics. The overlap engine. The risk engine. The signal format. The logging schema. The deterministic engine is untouched. v2 adds three layers above and beside the engine. It does not alter the engine.

---

## CRITICAL ENGINEERING RULES (updated for v2)

These are not preferences. Violating any of these rules silently destroys the edge.

```
RULE 1 — ONE IMPLEMENTATION PER INDICATOR
  There is exactly one EMA function, one ATR function, one session parser,
  one candle classifier. Everything imports from indicators/core.py.
  Never calculate the same indicator two ways in two places.
  If two modules produce different values for the same input, the live
  bot is no longer running the backtested system.

RULE 2 — BACKTEST PARITY
  Every calculation in the live engine must be byte-for-byte identical
  to the corresponding calculation in the research engine.
  If they differ, performance divergence is guaranteed and untraceable.
  v2 addition: the Parity Monitor enforces this at runtime. It is not
  an aspiration. It is a verified constraint checked every N candles.

RULE 3 — NO AI IN THE DECISION LAYER
  Claude (or any LLM) sits above the engine. It explains outputs and
  flags contradictions. It never generates signals. It never overrides
  rules. It never adds confidence scores. It never modifies signal
  parameters. The decision layer is deterministic Python only.
  The Critic Layer has READ ACCESS ONLY. It writes to a separate
  critic_output field. It does not touch any signal field.

RULE 4 — STATE IS EXPLICIT
  All system state lives in typed dataclasses. No loose variables.
  No global state. No hidden flags. Every module reads from state objects
  and writes to state objects. Nothing else.
  v2 addition: DriftState and ParityState are new state objects.
  They are read-only to the decision engine. The engine never branches
  on DriftState or ParityState. Those objects are for the human and
  the Critic Layer only.

RULE 5 — EVERY DECISION IS LOGGED
  Every signal pass, every signal reject, every no-trade condition —
  all logged with full context. Without this, live and backtest
  performance cannot be compared.
  v2 addition: DriftState and ParityState are logged alongside every
  signal entry. The full context is always preserved.

RULE 6 — EDGES ARE SEPARATE
  Edge 1 logic never bleeds into Edge 2 logic. They share state objects
  and the conflict engine, but their detection and validation modules
  are entirely independent. They live in separate folders.

RULE 7 — NOTHING IS ADDED THAT WAS NOT IN THE RESEARCH
  RSI was rejected. MACD was rejected. All entry refinements were rejected.
  These rejections are permanent unless a new research phase re-tests them.
  No indicator is added because it sounds smart. No filter is added because
  it feels safer. v2 additions (drift detection, parity monitor, critic
  layer) are OBSERVATION AND FLAGGING systems only. They are not indicators.
  They do not gate trades. They inform the human.

RULE 8 — THE CRITIC LAYER IS BOUNDED (new in v2)
  Claude's critic output is appended to the signal report as a separate
  block. It uses the words FLAG, CONFIRM, CONTRADICT, MONITOR.
  It does not use the words TAKE, SKIP, AVOID, RECOMMEND, or any synonym.
  If Claude produces output that implies a trade decision, that output
  is malformed and must be discarded. The Critic Layer prompt must be
  written and tested to prevent this.

RULE 9 — DRIFT IS MONITORED, NOT ACTED UPON (new in v2)
  When the Regime Drift Detector flags degradation, the bot does NOT
  change its behavior. It logs the flag. It includes the flag in the
  Critic Layer output. The human decides whether to pause trading.
  The engine never gates on drift state. If it did, it would be
  second-guessing the backtested system with live noise. The flags
  exist to alert the human, not to modify the system.
```

---

## FOLDER STRUCTURE (v2)

```
bot/
│
├── data/
│   ├── candles/            # Parquet files: 1H and M15 XAU/USD candles
│   ├── cache/              # In-memory or file-backed candle cache
│   └── backtest_ref/       # Reference indicator outputs from research engine
│                           # Used by parity monitor for comparison
│
├── indicators/
│   └── core.py             # THE ONLY place indicators are calculated
│
├── regimes/
│   └── engine.py           # Market state classification
│
├── edges/
│   ├── edge1/
│   │   ├── detector.py     # Edge 1 setup detection
│   │   └── validator.py    # Edge 1 condition validation
│   └── edge2/
│       ├── detector.py     # Edge 2 setup detection
│       └── validator.py    # Edge 2 condition validation
│
├── overlap/
│   └── engine.py           # Conflict resolution + co-activation rules
│
├── risk/
│   └── engine.py           # Position sizing + dollar risk management
│
├── signals/
│   └── output.py           # Signal formatting and emission
│
├── analytics/
│   └── logger.py           # Structured decision logging
│
├── config/
│   └── settings.py         # All locked parameters in one place
│
├── dashboard/
│   └── app.py              # Streamlit dashboard
│
├── state/
│   └── models.py           # All dataclasses defined here (incl. v2 state)
│
├── drift/                  # NEW in v2
│   ├── detector.py         # Regime drift detection engine
│   └── models.py           # DriftState dataclass
│
├── parity/                 # NEW in v2
│   ├── monitor.py          # Live vs backtest parity checker
│   └── models.py           # ParityState dataclass
│
├── critic/                 # NEW in v2
│   ├── layer.py            # Claude Critic Layer — read only, flags only
│   └── prompt.py           # Critic system prompt (hardened, bounded)
│
└── tests/
    ├── test_indicators.py
    ├── test_edge1.py
    ├── test_edge2.py
    ├── test_overlap.py
    ├── test_drift.py       # NEW in v2
    ├── test_parity.py      # NEW in v2
    └── test_critic.py      # NEW in v2 — validates critic output is bounded
```

---

## SECTION 1 — LOCKED PARAMETERS

**These values were set by the research. They are never modified without a new research phase.**  
**v2 adds new parameter blocks for drift detection and parity monitoring. Edges are untouched.**

```python
# config/settings.py

# ============================================================
# ACCOUNT CONSTANTS (never change)
# ============================================================
ACCOUNT_BALANCE       = 10.00
LOT_SIZE              = 0.01
USD_PER_POINT         = 1.00

# ============================================================
# EDGE 1 — TREND PULLBACK (locked from Phase 5)
# ============================================================
E1_TIMEFRAME          = '1H'
E1_DIRECTION          = 'LONG'
E1_VALID_WEEKDAYS     = [1, 2, 3]
E1_VALID_SESSIONS     = ['London_Open', 'London_Main', 'NY_Main']
E1_RR                 = 1.5
E1_TIMEOUT_BARS       = 72
E1_SL_SWING_LOOKBACK  = 10
E1_SL_ATR_BUFFER      = 0.5
E1_EMA_FAST           = 20
E1_EMA_MID            = 50
E1_EMA_SLOW           = 200

# ============================================================
# EDGE 2 — BREAKOUT SYSTEM (locked from Phase 10)
# ============================================================
E2_TIMEFRAME          = 'M15'
E2_DIRECTION          = 'BOTH'
E2_VALID_WEEKDAYS     = [0,1,2,3,4]
E2_VALID_SESSIONS     = 'ALL'
E2_RR                 = 1.5
E2_TIMEOUT_BARS       = 72
E2_SL_SWING_LOOKBACK  = 10
E2_SL_ATR_BUFFER      = 0.5
E2_COMPRESSION_MULT   = 3.5
E2_RANGE_MIN_ATR_MULT = 0.3
E2_RANGE_MAX_ATR_MULT = 3.0
E2_FAKEOUT_BODY_MIN   = 0.4
E2_FAKEOUT_WICK_RATIO = 0.3
E2_CLASS_A_CLOSE_MULT = 0.7
E2_CLASS_B_CLOSE_MULT = 0.4

# ============================================================
# OVERLAP / CONFLICT ENGINE (locked from Phase 11)
# ============================================================
OVERLAP_SIZING_REDUCTION  = 0.30
E2_SHORT_SUPPRESSION      = True
E2_MIN_OOS_TRADES_FOR_LOCK = 20

# ============================================================
# ACCOUNT RISK LIMITS
# ============================================================
MAX_SINGLE_TRADE_RISK_USD   = 5.00
MAX_COMBINED_RISK_USD       = 8.00
MAX_DAILY_TRADES_E1         = 1
MAX_DAILY_TRADES_E2         = 2


# ============================================================
# REGIME DRIFT DETECTION (new in v2)
# ============================================================
# These parameters define what "drift" means relative to
# the backtested performance baseline. They are NOT edge
# parameters. They do not gate trades. They trigger flags.

DRIFT_EV_WINDOW_TRADES      = 20
# Rolling window size in trades. Drift is measured over
# the last N completed trades per edge. Minimum 20 before
# any drift signal is meaningful.

DRIFT_EV_THRESHOLD_E1       = 0.10
# If rolling EV for Edge 1 drops below +0.10R (vs research
# baseline of +0.29R), drift flag is raised.
# Rationale: halfway between zero and the research EV.
# Below this level, the edge may be operating in noise.

DRIFT_EV_THRESHOLD_E2       = 0.30
# If rolling EV for Edge 2 drops below +0.30R (vs research
# baseline of +0.65R), drift flag is raised.

DRIFT_WR_THRESHOLD_E1       = 0.35
# If rolling win rate for Edge 1 drops below 35% (vs
# research baseline of ~50%), drift flag is raised.

DRIFT_WR_THRESHOLD_E2       = 0.40
# If rolling win rate for Edge 2 drops below 40% (vs
# research baseline of ~56%), drift flag is raised.

DRIFT_CONSECUTIVE_LOSS_E1   = 5
# If Edge 1 records 5 consecutive losses, drift flag is raised.
# This is separate from EV drift — fast-moving warning.

DRIFT_CONSECUTIVE_LOSS_E2   = 4
# If Edge 2 records 4 consecutive losses, drift flag is raised.

DRIFT_ATR_MULTIPLIER_HIGH   = 2.0
# If current ATR_1H > 2.0 * ATR_1H_mean_90d, the market
# is operating in an abnormal volatility regime.
# Flag: "Current volatility is outside the distribution
# this edge was validated on."

DRIFT_ATR_MULTIPLIER_LOW    = 0.4
# If current ATR_1H < 0.4 * ATR_1H_mean_90d, the market
# is in abnormally compressed volatility.

DRIFT_SESSION_EV_LOOKBACK   = 30
# Rolling window in trades for per-session EV breakdown.
# Used to detect if session leadership has rotated in a
# way that suggests regime change.

DRIFT_REGIME_FLIP_WINDOW    = 14
# If the 1H trend state has flipped between BULL/BEAR/MIXED
# more than 4 times in the last 14 days, flag raised.
# Choppy regime flipping degrades trend-following edges.

DRIFT_REGIME_FLIP_THRESHOLD = 4


# ============================================================
# LIVE VS BACKTEST PARITY MONITOR (new in v2)
# ============================================================
PARITY_CHECK_FREQUENCY      = 10
# Run parity check every N completed candles (1H timeframe).
# Runs separately on M15 candles for Edge 2 calculations.

PARITY_EMA_TOLERANCE        = 0.05
# Allowed absolute difference between live EMA and reference
# EMA in USD. Gold price means EMA values are in the 2000–3000
# range. A 0.05 USD tolerance is tight but realistic.
# If divergence exceeds this: parity flag raised.

PARITY_ATR_TOLERANCE_PCT    = 0.5
# Allowed percentage difference between live ATR and reference
# ATR. Expressed as percent of reference ATR value.
# If |live_atr - ref_atr| / ref_atr > 0.005: parity flag raised.

PARITY_SESSION_TOLERANCE_MIN = 1
# Allowed session classification mismatch in minutes.
# If live session classification and reference session differ
# by more than 1 minute at session boundaries: flag raised.
# This catches broker-side UTC offset issues.

PARITY_SWING_TOLERANCE      = 0.10
# Allowed absolute difference in swing_low / swing_high
# values between live and reference engines.

PARITY_MAX_GAP_CANDLES      = 2
# Maximum number of missing candles in the live feed before
# parity flag is raised and a data-quality warning is issued.
# Missing candles corrupt EMA and ATR calculations silently.


# ============================================================
# CRITIC LAYER CONFIGURATION (new in v2)
# ============================================================
CRITIC_MODEL                = 'claude-sonnet-4-20250514'
CRITIC_MAX_TOKENS           = 600
# Hard cap on critic output tokens. Forces concision.
# A critic that writes 2000 tokens is speculating, not flagging.

CRITIC_TEMPERATURE          = 0.1
# Near-zero temperature. The critic is not creative.
# It is analytical. Consistency is required.

CRITIC_ENABLED              = True
# Can be toggled off for performance or debugging.
# When off: critic_output field is populated with "CRITIC DISABLED."

CRITIC_CALL_ON_NO_TRADE     = False
# Whether to call Claude when no signal fires.
# Default False — saves API cost and noise on quiet cycles.
# Set True during active monitoring phases.

CRITIC_CALL_ON_WATCH        = True
# Call critic when compression zone is active (WATCH state).
# Useful for detecting contradiction between E1 and E2 context
# before the breakout fires.

CRITIC_CALL_ON_DRIFT_FLAG   = True
# Always call critic when any drift flag is active,
# regardless of signal type.
```

---

## SECTION 2 — STATE OBJECTS (v2)

**All system state is explicit and typed. v2 adds DriftState and ParityState.**  
**These new objects are read-only to the decision engine.**

```python
# state/models.py

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

# ============================================================
# EXISTING ENUMS (unchanged from v1)
# ============================================================

class TrendState(Enum):
    BULL    = "BULL"
    BEAR    = "BEAR"
    MIXED   = "MIXED"

class VolatilityState(Enum):
    LOW     = "LOW"
    NORMAL  = "NORMAL"
    HIGH    = "HIGH"

class SessionName(Enum):
    ASIAN        = "Asian"
    LONDON_OPEN  = "London_Open"
    LONDON_MAIN  = "London_Main"
    NY_MAIN      = "NY_Main"
    OFF          = "Off"

class WeekdayName(Enum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4

class SignalType(Enum):
    TRADE    = "TRADE"
    WATCH    = "WATCH"
    NO_TRADE = "NO_TRADE"

class BreakoutClass(Enum):
    A       = "A"
    B       = "B"
    FAKEOUT = "FAKEOUT"


# ============================================================
# NEW IN v2 — DRIFT SEVERITY
# ============================================================

class DriftSeverity(Enum):
    NONE     = "NONE"     # All metrics within expected range
    WATCH    = "WATCH"    # One metric degraded — monitor
    CAUTION  = "CAUTION"  # Two or more metrics degraded
    ALERT    = "ALERT"    # EV has crossed below threshold
                          # AND one structural flag active


# ============================================================
# NEW IN v2 — PARITY STATUS
# ============================================================

class ParityStatus(Enum):
    OK       = "OK"       # All indicators within tolerance
    WARNING  = "WARNING"  # One indicator outside tolerance
    BREACH   = "BREACH"   # Critical divergence detected
                          # — human must inspect feed


# ============================================================
# EXISTING DATACLASSES (unchanged from v1)
# ============================================================

@dataclass
class RegimeState:
    timestamp:        datetime
    trend_1h:         TrendState
    ema20_1h:         float
    ema50_1h:         float
    ema200_1h:        float
    atr_1h:           float
    volatility:       VolatilityState
    session:          SessionName
    weekday:          WeekdayName
    hour_utc:         int

    @property
    def is_e1_eligible_weekday(self) -> bool:
        return self.weekday.value in [1, 2, 3]

    @property
    def is_e1_eligible_session(self) -> bool:
        return self.session in [
            SessionName.LONDON_OPEN,
            SessionName.LONDON_MAIN,
            SessionName.NY_MAIN
        ]

    @property
    def is_bull_trend(self) -> bool:
        return self.trend_1h == TrendState.BULL


@dataclass
class Edge1Signal:
    timestamp:        datetime
    direction:        str
    entry_price:      float
    stop_loss:        float
    take_profit:      float
    stop_distance:    float
    dollar_risk:      float
    timeout_bar:      int
    ema20:            float
    ema50:            float
    ema200:           float
    atr:              float
    session:          str
    weekday:          str
    regime:           RegimeState
    sizing_factor:    float = 1.0
    adjusted_risk:    float = 0.0
    overlap_active:   bool  = False


@dataclass
class CompressionZone:
    start_bar:        int
    end_bar:          int
    range_high:       float
    range_low:        float
    range_height:     float
    atr_at_detection: float


@dataclass
class Edge2Signal:
    timestamp:           datetime
    direction:           str
    breakout_class:      BreakoutClass
    entry_price:         float
    stop_loss:           float
    take_profit:         float
    stop_distance:       float
    dollar_risk:         float
    timeout_bar:         int
    compression_high:    float
    compression_low:     float
    atr:                 float
    session:             str
    sizing_factor:       float = 1.0
    adjusted_risk:       float = 0.0
    overlap_active:      bool  = False
    e2_short_suppressed: bool  = False


@dataclass
class BotState:
    timestamp:           datetime
    regime:              Optional[RegimeState] = None
    e1_active:           bool = False
    e1_signal:           Optional[Edge1Signal] = None
    e1_open_since:       Optional[datetime] = None
    e1_trades_today:     int = 0
    e2_active:           bool = False
    e2_signal:           Optional[Edge2Signal] = None
    e2_open_since:       Optional[datetime] = None
    e2_trades_today:     int = 0
    e1_pending:          Optional[Edge1Signal] = None
    e2_pending:          Optional[Edge2Signal] = None
    both_active:         bool = False
    combined_risk:       float = 0.0
    last_reset_date:     Optional[str] = None


# ============================================================
# NEW IN v2 — DRIFT STATE
# ============================================================

@dataclass
class DriftFlag:
    """
    A single flagged drift condition. Multiple flags can be
    active simultaneously. Each is logged independently.
    """
    flag_type:        str       # e.g. 'EV_BELOW_THRESHOLD_E1'
    description:      str       # human-readable explanation
    current_value:    float     # the metric value that triggered
    threshold:        float     # the threshold it crossed
    trades_in_window: int       # sample size at time of flag
    timestamp:        datetime


@dataclass
class DriftState:
    """
    Output of the Regime Drift Detector.
    Produced every cycle. Always logged.
    Read-only to the decision engine.
    The engine never branches on this object.
    """
    timestamp:              datetime
    severity:               DriftSeverity

    # Per-edge rolling metrics
    e1_rolling_ev:          Optional[float]  # None if < 20 trades
    e1_rolling_wr:          Optional[float]
    e1_consecutive_losses:  int
    e1_trade_count:         int              # total live trades so far

    e2_rolling_ev:          Optional[float]
    e2_rolling_wr:          Optional[float]
    e2_consecutive_losses:  int
    e2_trade_count:         int

    # Volatility context
    atr_1h_current:         float
    atr_1h_mean_90d:        float
    atr_ratio:              float            # current / mean_90d
    volatility_outside_backtest: bool        # True if ratio > 2.0 or < 0.4

    # Regime choppiness
    regime_flip_count_14d:  int
    regime_choppy:          bool             # True if flips > threshold

    # Session leadership
    e1_session_ev:          Dict[str, float] # {'London_Open': ev, ...}
    session_rotation_flag:  bool             # True if dominant session shifted

    # Active flags list
    active_flags:           List[DriftFlag] = field(default_factory=list)

    # Baseline reference (from research)
    e1_baseline_ev:         float = 0.29
    e1_baseline_wr:         float = 0.50
    e2_baseline_ev:         float = 0.65
    e2_baseline_wr:         float = 0.56


# ============================================================
# NEW IN v2 — PARITY STATE
# ============================================================

@dataclass
class ParityCheck:
    """
    Result of comparing one indicator between live and reference.
    """
    indicator_name:   str
    live_value:       float
    reference_value:  float
    difference:       float
    difference_pct:   float
    tolerance:        float
    passed:           bool
    timestamp:        datetime


@dataclass
class ParityState:
    """
    Output of the Live vs Backtest Parity Monitor.
    Produced every PARITY_CHECK_FREQUENCY candles.
    Read-only to the decision engine.
    """
    timestamp:              datetime
    status:                 ParityStatus

    # Individual checks
    ema20_check:            ParityCheck
    ema50_check:            ParityCheck
    ema200_check:           ParityCheck
    atr_1h_check:           ParityCheck
    atr_m15_check:          ParityCheck
    swing_low_check:        ParityCheck
    session_check:          ParityCheck     # Boolean pass/fail only

    # Data quality
    candles_checked:        int
    missing_candles_1h:     int
    missing_candles_m15:    int
    data_quality_ok:        bool

    # Cumulative drift tracking
    cumulative_ema20_drift: float           # sum of abs differences over time
    cumulative_atr_drift:   float
    parity_check_count:     int             # how many checks run so far

    failed_checks:          List[str] = field(default_factory=list)


# ============================================================
# NEW IN v2 — CRITIC OUTPUT
# ============================================================

@dataclass
class CriticOutput:
    """
    Output of the Claude Critic Layer.
    Appended to signal report. Never modifies signal fields.
    Contains only FLAGS, CONFIRMATIONS, and CONTRADICTIONS.
    """
    timestamp:              datetime
    critic_called:          bool            # False if CRITIC_ENABLED=False
    signal_type:            str             # TRADE / WATCH / NO_TRADE
    edge_source:            str             # EDGE1 / EDGE2 / BOTH / NONE

    # Structured flags (extracted from Claude response)
    contradictions:         List[str]       # Conditions that contradict each other
    confirmations:          List[str]       # Conditions that reinforce the signal
    drift_flags_in_context: List[str]       # Active drift flags explained in plain lang
    parity_flags_in_context: List[str]      # Active parity issues explained in plain lang
    context_notes:          List[str]       # Observations with no implied action

    # Raw response
    raw_critic_text:        str
    tokens_used:            int

    # Validation
    output_bounded:         bool            # True if no decision words found
    decision_words_found:   List[str]       # Should always be empty
```

---

## SECTION 3 — INDICATOR MODULE (unchanged from v1)

**Single source of truth for all calculations. Never duplicated.**

```python
# indicators/core.py

import pandas as pd
import numpy as np

def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Standard EMA using pandas ewm.
    span=period, adjust=False.
    This is the ONLY EMA implementation in the system.
    """
    return series.ewm(span=period, adjust=False).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Wilder's smoothing (alpha = 1/period).
    df must have columns: high, low, close
    This is the ONLY ATR implementation in the system.
    """
    high  = df['high']
    low   = df['low']
    prev  = df['close'].shift(1)
    tr    = pd.concat([
        (high - low),
        (high - prev).abs(),
        (low  - prev).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()


def swing_low(df: pd.DataFrame, lookback: int) -> pd.Series:
    """Rolling minimum of 'low' over lookback bars."""
    return df['low'].rolling(lookback).min()


def swing_point(df: pd.DataFrame, lookback: int, direction: str) -> pd.Series:
    """
    direction='long':  rolling min of 'low'  over lookback
    direction='short': rolling max of 'high' over lookback
    """
    if direction == 'long':
        return df['low'].rolling(lookback).min()
    elif direction == 'short':
        return df['high'].rolling(lookback).max()
    else:
        raise ValueError(f"Invalid direction: {direction}")


def rolling_range(df: pd.DataFrame, period: int) -> pd.Series:
    """
    Rolling (high_max - low_min) over period bars.
    Used by Edge 2 compression detection.
    """
    return df['high'].rolling(period).max() - df['low'].rolling(period).min()


def body_ratio(row) -> float:
    """
    Absolute body size / total candle range.
    Used by Edge 2 fakeout filter.
    """
    total_range = row['high'] - row['low']
    if total_range == 0:
        return 0.0
    return abs(row['close'] - row['open']) / total_range


def wick_ratio(row, direction: str) -> float:
    """
    Rejection wick / total candle range.
    direction='long':  upper wick (high - max(open, close))
    direction='short': lower wick (min(open, close) - low)
    Used by Edge 2 fakeout filter.
    """
    total_range = row['high'] - row['low']
    if total_range == 0:
        return 0.0
    if direction == 'long':
        wick = row['high'] - max(row['open'], row['close'])
    else:
        wick = min(row['open'], row['close']) - row['low']
    return wick / total_range


def classify_volatility(atr_current: float, atr_mean_20: float) -> VolatilityState:
    """
    LOW:    atr_current < 0.7 * atr_mean_20
    HIGH:   atr_current > 1.5 * atr_mean_20
    NORMAL: everything else
    """
    ratio = atr_current / atr_mean_20 if atr_mean_20 > 0 else 1.0
    if ratio < 0.7:
        return VolatilityState.LOW
    elif ratio > 1.5:
        return VolatilityState.HIGH
    else:
        return VolatilityState.NORMAL


def classify_session(hour_utc: int, minute: int = 0) -> SessionName:
    """
    Asian:       00:00 – 06:59 UTC
    London_Open: 07:00 – 08:59 UTC
    London_Main: 09:00 – 12:59 UTC
    NY_Main:     13:00 – 17:30 UTC
    Off:         17:31 – 23:59 UTC
    """
    if 0 <= hour_utc <= 6:
        return SessionName.ASIAN
    elif 7 <= hour_utc <= 8:
        return SessionName.LONDON_OPEN
    elif 9 <= hour_utc <= 12:
        return SessionName.LONDON_MAIN
    elif 13 <= hour_utc <= 16:
        return SessionName.NY_MAIN
    elif hour_utc == 17 and minute <= 30:
        return SessionName.NY_MAIN
    else:
        return SessionName.OFF
```

---

## SECTION 4 — REGIME ENGINE (unchanged from v1)

```python
# regimes/engine.py

def classify_regime(df_1h, current_bar, current_datetime) -> RegimeState:
    """
    1. EMA State (1H)
       ema20  = ema(close, 20) at current_bar
       ema50  = ema(close, 50) at current_bar
       ema200 = ema(close, 200) at current_bar

       IF ema20 > ema50 > ema200  → BULL
       IF ema20 < ema50 < ema200  → BEAR
       ELSE                       → MIXED

    2. ATR (1H)
       atr_current = atr(df_1h, 14) at current_bar
       atr_mean_20 = atr_current.rolling(20).mean()
       volatility  = classify_volatility(atr_current, atr_mean_20)

    3. Session + Weekday
       session = classify_session(hour_utc, minute)
       weekday = WeekdayName(current_datetime.weekday())

    4. Return RegimeState
    """
    ...
```

**What the Regime Engine does NOT do:**
- Does not make trade decisions
- Does not check edge conditions
- Does not know about Edge 1 or Edge 2
- Does not know about DriftState or ParityState

---

## SECTION 5 — EDGE 1: TREND PULLBACK LOGIC (unchanged from v1)

```python
# edges/edge1/detector.py

def detect_edge1(df_1h, current_bar, regime, bot_state) -> Optional[Edge1Signal]:
    """
    GATE 1 — DAILY LIMIT
      IF bot_state.e1_trades_today >= MAX_DAILY_TRADES_E1: RETURN None

    GATE 2 — WEEKDAY FILTER
      IF regime.weekday not in [TUE, WED, THU]: RETURN None

    GATE 3 — SESSION FILTER
      IF regime.session not in [LONDON_OPEN, LONDON_MAIN, NY_MAIN]: RETURN None

    GATE 4 — TREND CONFIRMATION
      IF regime.trend_1h != TrendState.BULL: RETURN None
      Required: EMA20 > EMA50 > EMA200 on 1H.

    GATE 5 — PULLBACK INTO EMA ZONE
      pullback_valid = (current_low <= ema20) and (current_low >= ema50 * 0.998)
      IF not pullback_valid: RETURN None
      Note: 0.998 is a 0.2% tolerance below EMA50.
      Phase 5 confirmed that tight EMA distance constraints overfit.

    GATE 6 — CONTINUATION CONFIRMATION
      continuation_valid = current_close > current_open (bullish candle)
      IF not continuation_valid: RETURN None

    ALL GATES PASSED — BUILD SIGNAL
      entry_price   = current_close
      swing_sl      = swing_low(last 10 bars)
      stop_loss     = swing_sl - (0.5 * atr)
      stop_distance = entry_price - stop_loss
      IF stop_distance <= 0: RETURN None
      dollar_risk   = stop_distance * 1.0
      IF dollar_risk > MAX_SINGLE_TRADE_RISK_USD: RETURN None
      take_profit   = entry_price + (1.5 * stop_distance)
      timeout_bar   = current_bar + 72

    RETURN Edge1Signal(...)
    """
    ...
```

**NOT CHECKED (rejected in research — permanent):**
- RSI: Phase 5 — no OOS improvement
- MACD: Phase 5 — no OOS improvement
- Candle body strength filters: Phase 5 Mode C — overfitting
- EMA distance constraints: Phase 5 Mode C — overfitting
- Volume: not in research
- Volatility gates: not justified by research findings

---

## SECTION 6 — EDGE 2: BREAKOUT LOGIC (unchanged from v1)

```python
# edges/edge2/detector.py

def detect_compression_zones(df_m15) -> List[CompressionZone]:
    """
    COMPRESSION CONDITION:
      rolling_range(20) / atr(14) <= 3.5
      Note: threshold (3.5) is NOT the discriminator.
      ANY threshold between 1.5 and 5.0 produces identical trade sets.
      The fakeout filter is the real gate.

    RANGE VALIDATION:
      range_height >= 0.3 * atr_at_detection
      range_height <= 3.0 * atr_at_detection
    """
    ...


def classify_breakout(row, compression_zone, direction) -> BreakoutClass:
    """
    THE REAL QUALITY GATE.

    FAKEOUT if:
      body_ratio < 0.4  OR  wick_ratio > 0.3

    CLASS A if:
      long:  (close - low) / (high - low) >= 0.70
      short: (high - close) / (high - low) >= 0.70

    CLASS B if:
      not FAKEOUT and not Class A
    """
    ...


def detect_edge2(df_m15, current_bar, regime, bot_state,
                 compression_zones) -> Optional[Edge2Signal]:
    """
    GATE 1 — DAILY LIMIT
      IF bot_state.e2_trades_today >= MAX_DAILY_TRADES_E2: RETURN None

    GATE 2 — NO SESSION FILTER (Phase 7: all sessions positive)

    GATE 3 — NO WEEKDAY FILTER

    GATE 4 — COMPRESSION ZONE EXISTS
      Find most recent valid CompressionZone that ended before current_bar
      and has not already produced a signal.

    GATE 5 — BREAKOUT DETECTED
      long_break  = current_close > zone.range_high
      short_break = current_close < zone.range_low

    GATE 6 — FAKEOUT FILTER
      breakout_class = classify_breakout(row, zone, direction)
      IF FAKEOUT: RETURN None

    ALL GATES PASSED — BUILD SIGNAL
      entry_price = current_close
      SL = swing_point(10) ± 0.5 ATR
      TP = 1.5R from entry
      timeout_bar = current_bar + 72

    RETURN Edge2Signal(...)
    """
    ...
```

**NOT APPLIED (rejected in research — permanent):**
- Session filter: Phase 7 — all sessions positive
- Trailing stop: Phase 10 — EV collapsed from +0.635R to +0.119R
- Partial exit at +1R: Phase 10 — reduced winner value
- Breakeven move: Phase 10 — same mechanism as trailing

---

## SECTION 7 — OVERLAP ENGINE (unchanged from v1)

```python
# overlap/engine.py

def apply_overlap_rules(e1_signal, e2_signal, bot_state):
    """
    RULE 1 — BOTH EDGES ALLOWED SIMULTANEOUSLY
      Correlation -0.323 OOS → genuine diversification.

    RULE 2 — CO-ACTIVATION SIZING REDUCTION (30%)
      IF both edges active (any combination of pending + open):
        sizing_factor = 0.70 for both signals
        At 0.01 fixed lot: take only higher-priority signal.
        Priority: E1 BULL + valid session > E2 Class A BULL > E2 Class B > E2 BEAR/MIXED

    RULE 3 — E2 SHORT SUPPRESSION
      IF E1 LONG active AND E2 direction == SHORT:
        e2_signal.e2_short_suppressed = True
        Log: "OOS E2 SHORT during E1 active = -1.02R (n=1)"
        Log: "Strong prior — not hard-locked until E2 OOS count = 20"

    RULE 4 — COMBINED RISK CAP
      IF combined adjusted risk > $8.00:
        Drop lower-priority signal.

    MANDATORY LOG EVERY CYCLE:
      "Phase 11 caveat: E2 OOS sample = N. Rule locks at 20."
    """
    ...
```

---

## SECTION 8 — RISK ENGINE (unchanged from v1)

```python
# risk/engine.py

def assess_risk(signal, bot_state) -> dict:
    """
    dollar_risk_raw   = stop_distance * USD_PER_POINT
    dollar_risk_adj   = adjusted_risk (after sizing factor)
    account_risk_pct  = dollar_risk_adj / ACCOUNT_BALANCE * 100
    dollar_target     = stop_distance * RR * USD_PER_POINT

    risk_flag:
      <= $2.00  → ACCEPTABLE
      <= $3.50  → ELEVATED
      <= $5.00  → HIGH
      >  $5.00  → REJECTED (caught upstream, should never reach here)

    Always include:
      "At $10 with 0.01 lot fixed: a $3 stop = 30% of account.
       This is the reality. The bot states it, not hides it."
    """
    ...
```

---

## SECTION 9 — REGIME DRIFT DETECTION (new in v2)

**This module observes live edge performance and flags when it diverges from the backtested baseline. It does not modify the engine. It produces a DriftState object that is logged and passed to the Critic Layer.**

### 9.1 What Drift Detection Is

The backtested edges were validated on a specific historical regime of XAU/USD behavior. Market regimes change. If the live edge begins performing materially differently from the research baseline, the human needs to know before the account is damaged. The drift detector is the early warning system.

**What it is NOT:**
- It is not a circuit breaker
- It does not stop the bot from issuing signals
- It does not modify any signal parameter
- It does not know better than the research

**What it IS:**
- A set of rolling performance metrics compared against research baselines
- A set of structural market observations (volatility, regime choppiness)
- A flag producer that writes to DriftState and to the log
- Context that the human and the Critic Layer receive

### 9.2 Drift Detection Logic

```python
# drift/detector.py

def detect_drift(trade_log: List[dict],
                 regime: RegimeState,
                 df_1h: pd.DataFrame,
                 current_bar: int) -> DriftState:
    """
    Runs every cycle. Uses completed trade log only.
    Never uses pending or open trades in EV/WR calculations.

    ──────────────────────────────────────────────────────
    STEP 1 — COLLECT COMPLETED TRADES PER EDGE
    ──────────────────────────────────────────────────────
    e1_completed = [t for t in trade_log
                    if t['edge_source'] == 'EDGE1'
                    and t['outcome'] in ['WIN','LOSS','TIMEOUT']]

    e2_completed = [t for t in trade_log
                    if t['edge_source'] == 'EDGE2'
                    and t['outcome'] in ['WIN','LOSS','TIMEOUT']]

    ──────────────────────────────────────────────────────
    STEP 2 — ROLLING METRICS (last N trades per edge)
    ──────────────────────────────────────────────────────
    WINDOW = DRIFT_EV_WINDOW_TRADES  # 20

    IF len(e1_completed) >= WINDOW:
        window_e1 = e1_completed[-WINDOW:]
        e1_rolling_ev = mean([t['result_r'] for t in window_e1])
        e1_rolling_wr = mean([1 if t['outcome']=='WIN' else 0
                               for t in window_e1])
    ELSE:
        e1_rolling_ev = None  # Insufficient sample — no drift signal yet
        e1_rolling_wr = None

    # Same for e2

    ──────────────────────────────────────────────────────
    STEP 3 — CONSECUTIVE LOSS COUNT
    ──────────────────────────────────────────────────────
    # Walk backwards through completed trades until a WIN
    e1_consecutive_losses = count_consecutive_losses(e1_completed)
    e2_consecutive_losses = count_consecutive_losses(e2_completed)

    ──────────────────────────────────────────────────────
    STEP 4 — VOLATILITY CONTEXT
    ──────────────────────────────────────────────────────
    atr_1h_current  = regime.atr_1h
    atr_mean_90d    = compute_90d_atr_mean(df_1h, current_bar)
    atr_ratio       = atr_1h_current / atr_mean_90d

    volatility_outside_backtest = (
        atr_ratio > DRIFT_ATR_MULTIPLIER_HIGH or
        atr_ratio < DRIFT_ATR_MULTIPLIER_LOW
    )

    ──────────────────────────────────────────────────────
    STEP 5 — REGIME CHOPPINESS
    ──────────────────────────────────────────────────────
    # Count trend state flips in last 14 calendar days
    recent_regimes = get_regimes_last_n_days(regime_log, 14)
    flip_count = count_trend_flips(recent_regimes)
    regime_choppy = flip_count > DRIFT_REGIME_FLIP_THRESHOLD

    ──────────────────────────────────────────────────────
    STEP 6 — SESSION EV BREAKDOWN (Edge 1 only)
    ──────────────────────────────────────────────────────
    # Compute rolling EV per session using last 30 E1 trades
    e1_session_ev = {
        'London_Open': compute_session_ev(e1_completed, 'London_Open', 30),
        'London_Main': compute_session_ev(e1_completed, 'London_Main', 30),
        'NY_Main':     compute_session_ev(e1_completed, 'NY_Main',     30),
    }
    # Session rotation flag: if the session that was historically
    # strongest now has the lowest EV over last 30 trades
    session_rotation_flag = detect_session_leadership_change(e1_session_ev)

    ──────────────────────────────────────────────────────
    STEP 7 — BUILD ACTIVE FLAGS LIST
    ──────────────────────────────────────────────────────
    flags = []

    IF e1_rolling_ev is not None and e1_rolling_ev < DRIFT_EV_THRESHOLD_E1:
        flags.append(DriftFlag(
            flag_type    = 'EV_BELOW_THRESHOLD_E1',
            description  = f"Edge 1 rolling EV = {e1_rolling_ev:.3f}R over last "
                           f"{WINDOW} trades. Research baseline: +0.29R. "
                           f"Threshold: +{DRIFT_EV_THRESHOLD_E1}R. "
                           f"This may indicate regime shift or edge decay.",
            current_value = e1_rolling_ev,
            threshold     = DRIFT_EV_THRESHOLD_E1,
            trades_in_window = len(e1_completed[-WINDOW:]),
            timestamp    = regime.timestamp
        ))

    IF e1_rolling_wr is not None and e1_rolling_wr < DRIFT_WR_THRESHOLD_E1:
        flags.append(DriftFlag(
            flag_type    = 'WR_BELOW_THRESHOLD_E1',
            description  = f"Edge 1 rolling win rate = {e1_rolling_wr:.1%} "
                           f"over last {WINDOW} trades. Baseline: ~50%.",
            current_value = e1_rolling_wr,
            threshold     = DRIFT_WR_THRESHOLD_E1,
            ...
        ))

    IF e1_consecutive_losses >= DRIFT_CONSECUTIVE_LOSS_E1:
        flags.append(DriftFlag(
            flag_type    = 'CONSECUTIVE_LOSSES_E1',
            description  = f"Edge 1 has recorded {e1_consecutive_losses} "
                           f"consecutive losses. Fast-decay warning.",
            ...
        ))

    # Same pattern for e2 metrics

    IF volatility_outside_backtest:
        direction = 'HIGH' if atr_ratio > 2.0 else 'LOW'
        flags.append(DriftFlag(
            flag_type    = f'VOLATILITY_OUTSIDE_BACKTEST_{direction}',
            description  = f"Current ATR = {atr_1h_current:.2f}. "
                           f"90d mean ATR = {atr_mean_90d:.2f}. "
                           f"Ratio = {atr_ratio:.2f}. "
                           f"Market volatility is outside the distribution "
                           f"this edge was validated on.",
            ...
        ))

    IF regime_choppy:
        flags.append(DriftFlag(
            flag_type    = 'REGIME_CHOPPY',
            description  = f"Trend state has flipped {flip_count} times "
                           f"in the last 14 days (threshold: "
                           f"{DRIFT_REGIME_FLIP_THRESHOLD}). "
                           f"Edge 1 is a trend-following system. "
                           f"Choppy regimes reduce its validity.",
            ...
        ))

    IF session_rotation_flag:
        flags.append(DriftFlag(
            flag_type    = 'SESSION_LEADERSHIP_SHIFT',
            description  = f"The session producing the highest Edge 1 EV "
                           f"in the last 30 trades differs from the backtested "
                           f"leadership distribution. Monitor.",
            ...
        ))

    ──────────────────────────────────────────────────────
    STEP 8 — DETERMINE SEVERITY
    ──────────────────────────────────────────────────────
    ev_flags = [f for f in flags if 'EV_BELOW' in f.flag_type]
    total_flags = len(flags)

    IF total_flags == 0:
        severity = DriftSeverity.NONE
    ELIF total_flags == 1 and len(ev_flags) == 0:
        severity = DriftSeverity.WATCH
    ELIF total_flags >= 2 or (total_flags == 1 and len(ev_flags) == 1):
        severity = DriftSeverity.CAUTION
    IF len(ev_flags) >= 1 and total_flags >= 2:
        severity = DriftSeverity.ALERT

    RETURN DriftState(
        severity    = severity,
        active_flags = flags,
        ...
    )
```

### 9.3 What Happens When Drift is Flagged

```
DriftSeverity.NONE:
  → Normal operation. Logged. Passed to Critic (no specific flag to raise).

DriftSeverity.WATCH:
  → Logged with full DriftState. Critic Layer receives it.
  → Signal output appends: "DRIFT MONITOR: 1 metric outside expected range."
  → NO change to signal. NO change to engine behavior.

DriftSeverity.CAUTION:
  → Logged. Critic Layer receives it with CAUTION priority.
  → Signal output appends: "DRIFT CAUTION: Multiple metrics degraded.
    Review performance log before next trade."
  → NO change to signal. NO change to engine behavior.

DriftSeverity.ALERT:
  → Logged. Critic Layer always called regardless of CRITIC_CALL settings.
  → Signal output appends: "DRIFT ALERT: Edge EV below threshold with
    structural flag active. Human review required."
  → NO change to signal. NO change to engine behavior.

The engine never stops on drift. The human stops the engine if they choose to.
The bot's job is to surface the information, not to make that decision.
```

---

## SECTION 10 — LIVE VS BACKTEST PARITY MONITOR (new in v2)

**This module verifies that live indicator values match the reference calculations from the research engine. It is the enforcement mechanism for Rule 2.**

### 10.1 What Parity Monitoring Is

The research engine produced specific indicator values on specific bars. Those values are the source of truth for edge detection. If the live engine produces different values for the same bars, it is not running the same system.

The parity monitor stores reference snapshots from the research engine and compares them against live calculations at regular intervals. Any divergence is flagged and logged.

### 10.2 Reference Snapshot System

```python
# data/backtest_ref/
#
# The research engine must export reference snapshots at build time.
# Format: Parquet file with columns:
#   timestamp, ema20_1h, ema50_1h, ema200_1h, atr_1h, atr_m15,
#   swing_low_10, swing_high_10, session, weekday
#
# These are the exact values the research engine used.
# The parity monitor compares live calculations against these.
#
# Snapshot coverage: at minimum the most recent 500 1H bars
# and 2000 M15 bars stored and updated as the reference engine
# processes new candles.
#
# The reference engine is the backtest codebase, run on the same
# live data feed, and its outputs are written to backtest_ref/.
# This shadow engine never trades. It only produces reference output.

def load_reference_snapshot(timestamp: datetime) -> dict:
    """
    Load reference indicator values for a specific bar timestamp.
    Returns None if timestamp not found in reference data.
    """
    ...
```

### 10.3 Parity Check Logic

```python
# parity/monitor.py

def run_parity_check(df_1h, df_m15, current_bar_1h,
                     current_bar_m15, regime) -> ParityState:
    """
    Runs every PARITY_CHECK_FREQUENCY candles (default: every 10).

    ──────────────────────────────────────────────────────
    STEP 1 — LOAD REFERENCE SNAPSHOT
    ──────────────────────────────────────────────────────
    current_ts = df_1h.iloc[current_bar_1h]['timestamp']
    ref = load_reference_snapshot(current_ts)

    IF ref is None:
        LOG: "PARITY: No reference snapshot for {current_ts}."
             "Cannot verify. Snapshot coverage may be insufficient."
        RETURN ParityState(status=ParityStatus.WARNING, ...)

    ──────────────────────────────────────────────────────
    STEP 2 — COMPUTE LIVE VALUES
    ──────────────────────────────────────────────────────
    live_ema20   = ema(df_1h['close'], 20).iloc[current_bar_1h]
    live_ema50   = ema(df_1h['close'], 50).iloc[current_bar_1h]
    live_ema200  = ema(df_1h['close'], 200).iloc[current_bar_1h]
    live_atr_1h  = atr(df_1h, 14).iloc[current_bar_1h]
    live_atr_m15 = atr(df_m15, 14).iloc[current_bar_m15]
    live_swing_l = swing_low(df_1h.iloc[current_bar_1h-10:current_bar_1h+1],
                             10).iloc[-1]

    ──────────────────────────────────────────────────────
    STEP 3 — RUN INDIVIDUAL CHECKS
    ──────────────────────────────────────────────────────
    checks = {
        'ema20':  check_absolute(live_ema20,   ref['ema20_1h'],
                                 PARITY_EMA_TOLERANCE),
        'ema50':  check_absolute(live_ema50,   ref['ema50_1h'],
                                 PARITY_EMA_TOLERANCE),
        'ema200': check_absolute(live_ema200,  ref['ema200_1h'],
                                 PARITY_EMA_TOLERANCE),
        'atr_1h': check_percent (live_atr_1h,  ref['atr_1h'],
                                 PARITY_ATR_TOLERANCE_PCT),
        'atr_m15':check_percent (live_atr_m15, ref['atr_m15'],
                                 PARITY_ATR_TOLERANCE_PCT),
        'swing_l':check_absolute(live_swing_l, ref['swing_low_10'],
                                 PARITY_SWING_TOLERANCE),
        'session':check_session (regime.session.value, ref['session'],
                                 PARITY_SESSION_TOLERANCE_MIN),
    }

    ──────────────────────────────────────────────────────
    STEP 4 — DATA GAP CHECK
    ──────────────────────────────────────────────────────
    missing_1h  = count_missing_candles(df_1h, '1H',  lookback=48)
    missing_m15 = count_missing_candles(df_m15,'M15', lookback=192)

    IF missing_1h > PARITY_MAX_GAP_CANDLES or missing_m15 > PARITY_MAX_GAP_CANDLES:
        LOG: "PARITY WARNING: {missing_1h} 1H gaps and "
             "{missing_m15} M15 gaps detected in recent feed."
             "EMA and ATR drift likely. Verify data source."

    ──────────────────────────────────────────────────────
    STEP 5 — DETERMINE PARITY STATUS
    ──────────────────────────────────────────────────────
    failed = [name for name, check in checks.items() if not check.passed]

    IF len(failed) == 0 and missing_1h == 0 and missing_m15 == 0:
        status = ParityStatus.OK
    ELIF len(failed) == 1 or missing_1h <= PARITY_MAX_GAP_CANDLES:
        status = ParityStatus.WARNING
    ELSE:
        status = ParityStatus.BREACH

    ──────────────────────────────────────────────────────
    STEP 6 — LOG AND RETURN
    ──────────────────────────────────────────────────────
    IF status == ParityStatus.BREACH:
        LOG: "PARITY BREACH: {len(failed)} indicators diverged from reference."
             "Failed: {failed}"
             "Live engine may not be running the backtested system."
             "Human review of data feed required before next trade."

    RETURN ParityState(status=status, failed_checks=failed, ...)
```

### 10.4 What Happens on Parity Failure

```
ParityStatus.OK:
  → Normal. Logged every check cycle. No signal modification.

ParityStatus.WARNING:
  → Logged. Critic Layer notes it in context.
  → Signal output appends: "PARITY WARNING: {indicator} diverged
    from reference by {diff}. Monitor data feed quality."
  → NO change to signal.

ParityStatus.BREACH:
  → Logged with full detail.
  → Signal output appends: "PARITY BREACH: Live indicators diverged
    significantly from backtested reference. The live engine may not
    be running the same system that was validated. Human must inspect
    data feed before taking this signal."
  → Critic Layer always called.
  → NO automatic signal cancellation — the human decides.
    This is the correct boundary: the bot surfaces the information.
    The human acts on it.
```

---

## SECTION 11 — CLAUDE CRITIC LAYER (new in v2)

**This is Claude's bounded role. Read access only. Flags only. Never decides.**

### 11.1 What the Critic Layer Is

The deterministic engine produces a signal. The Critic Layer receives the full context of that signal — the signal itself, the regime state, the drift state, the parity state, and the historical log — and produces a structured contradiction report.

The Critic Layer exists because deterministic rules cannot reason about contradictions between what they allow and what the full context suggests. A signal can be technically valid (all gates passed) while simultaneously being contextually contradictory (the two edges are reading opposite market direction). The rules cannot detect this. The Critic Layer can.

**The Critic Layer is a second pair of eyes, not a second decision-maker.**

### 11.2 What Claude Is Given (Read Access)

```python
# critic/layer.py

def build_critic_context(signal_type: str,
                         edge_source: str,
                         e1_signal: Optional[Edge1Signal],
                         e2_signal: Optional[Edge2Signal],
                         regime: RegimeState,
                         drift_state: DriftState,
                         parity_state: ParityState,
                         bot_state: BotState,
                         recent_log: List[dict]) -> dict:
    """
    Builds the read-only context package passed to Claude.
    Claude receives this context and nothing else.
    Claude cannot write to any of these objects.
    Claude cannot modify any signal field.
    """
    return {
        # What the engine decided
        'signal_type':    signal_type,       # TRADE / WATCH / NO_TRADE
        'edge_source':    edge_source,       # EDGE1 / EDGE2 / BOTH / NONE
        'e1_signal':      e1_signal,         # Full Edge1Signal or None
        'e2_signal':      e2_signal,         # Full Edge2Signal or None

        # Market context
        'regime': {
            'trend_1h':         regime.trend_1h.value,
            'volatility':       regime.volatility.value,
            'session':          regime.session.value,
            'weekday':          regime.weekday.name,
            'ema20':            regime.ema20_1h,
            'ema50':            regime.ema50_1h,
            'ema200':           regime.ema200_1h,
            'atr_1h':           regime.atr_1h,
        },

        # Live performance health
        'drift': {
            'severity':         drift_state.severity.value,
            'active_flags':     [f.description for f in drift_state.active_flags],
            'e1_rolling_ev':    drift_state.e1_rolling_ev,
            'e1_rolling_wr':    drift_state.e1_rolling_wr,
            'e2_rolling_ev':    drift_state.e2_rolling_ev,
            'e2_rolling_wr':    drift_state.e2_rolling_wr,
            'e1_consecutive_losses': drift_state.e1_consecutive_losses,
            'e2_consecutive_losses': drift_state.e2_consecutive_losses,
            'volatility_outside_backtest': drift_state.volatility_outside_backtest,
            'regime_choppy':    drift_state.regime_choppy,
        },

        # Indicator integrity
        'parity': {
            'status':           parity_state.status.value,
            'failed_checks':    parity_state.failed_checks,
            'missing_1h_gaps':  parity_state.missing_candles_1h,
            'missing_m15_gaps': parity_state.missing_candles_m15,
        },

        # Bot state context
        'bot_state': {
            'e1_active':        bot_state.e1_active,
            'e2_active':        bot_state.e2_active,
            'e1_trades_today':  bot_state.e1_trades_today,
            'e2_trades_today':  bot_state.e2_trades_today,
            'overlap_active':   bot_state.both_active,
        },

        # Recent performance (last 10 completed trades)
        'recent_trades': recent_log[-10:],
    }
```

### 11.3 The Critic System Prompt (hardened)

```python
# critic/prompt.py

CRITIC_SYSTEM_PROMPT = """
You are the Critic Layer of a deterministic XAU/USD trading signal engine.

YOUR ROLE:
You receive read-only context about a signal that the deterministic engine
has already produced. Your job is to identify contradictions, confirmations,
and context notes. You are a second pair of eyes, not a second decision-maker.

THE ENGINE'S DECISION IS FINAL.
You do not modify it. You do not override it. You do not improve it.
You flag what you see. The human decides what to do with your flags.

WHAT YOU MUST PRODUCE:
A structured analysis with exactly four sections:

CONTRADICTIONS:
  List any conditions that logically contradict each other in the current context.
  Each contradiction is one sentence. Be specific. Reference actual values.
  Example: "E2 LONG fired during a BEAR 1H regime. Edge 1 is in hard reject
  because trend is not BULL. Both edges are reading opposite market direction."
  If no contradictions exist, write: "None."

CONFIRMATIONS:
  List conditions that reinforce the signal's validity.
  Each confirmation is one sentence. Reference actual values.
  Example: "Session is London Main — historically the highest EV session for Edge 1."
  If no confirmations, write: "None."

DRIFT AND PARITY FLAGS:
  Summarize any active drift or parity issues in plain language.
  State what the flag means for the signal in context.
  Do not say what to do about it. State what exists.
  If none active, write: "None."

CONTEXT NOTES:
  Any other observations that are relevant but do not fit the above categories.
  These are neither contradictions nor confirmations.
  Example: "E2 OOS trade count is 8. The SHORT suppression rule is currently
  a strong prior, not a hard-locked rule. This suppression flag is logged
  as such."

WHAT YOU MUST NEVER DO:
- Never use the words: take, skip, avoid, recommend, suggest, should, don't,
  enter, wait, pass, hold off, reconsider, think twice, be careful.
- Never say what the human should do.
- Never assign a probability or confidence score.
- Never add an indicator that is not already in the context.
- Never compare the current setup to past setups you know about from training.
- Never say "this looks like" or "this reminds me of."
- Never produce output that implies a trade decision.
- If you find yourself writing a sentence that implies action, delete it and
  rewrite it as a pure observation.

YOUR OUTPUT IS BOUNDED.
If your output contains any decision language, it is malformed and will be
discarded by the system. Write only what you observe. Never what to do.

Keep your total response under 400 words. Precision over volume.
"""
```

### 11.4 Critic Output Validation

```python
# critic/layer.py

DECISION_WORDS = [
    'take', 'skip', 'avoid', 'recommend', 'suggest', 'should',
    "don't", 'dont', 'enter', 'wait', 'pass', 'hold off',
    'reconsider', 'think twice', 'be careful', 'caution advised',
    'i would', 'you might', 'consider', 'perhaps', 'maybe'
]

def validate_critic_output(raw_text: str) -> tuple[bool, List[str]]:
    """
    Scans critic output for decision language.
    Returns (is_bounded: bool, found_words: List[str])
    
    If is_bounded is False:
      - Log the malformed output
      - Do NOT append to signal report
      - Set CriticOutput.output_bounded = False
      - Human sees: "CRITIC OUTPUT INVALID — decision language detected.
        Critic response discarded. Review critic prompt."
    """
    found = []
    lower = raw_text.lower()
    for word in DECISION_WORDS:
        if word in lower:
            found.append(word)
    return (len(found) == 0, found)


def call_critic(context: dict) -> CriticOutput:
    """
    Makes the API call to Claude with the bounded system prompt.
    Validates the output. Returns CriticOutput.
    """
    if not CRITIC_ENABLED:
        return CriticOutput(critic_called=False,
                            raw_critic_text="CRITIC DISABLED.",
                            output_bounded=True, ...)

    response = anthropic_client.messages.create(
        model       = CRITIC_MODEL,
        max_tokens  = CRITIC_MAX_TOKENS,
        temperature = CRITIC_TEMPERATURE,
        system      = CRITIC_SYSTEM_PROMPT,
        messages    = [{'role': 'user',
                        'content': json.dumps(context, default=str)}]
    )

    raw_text = response.content[0].text
    is_bounded, found_words = validate_critic_output(raw_text)

    contradictions, confirmations, drift_flags, context_notes = \
        parse_critic_sections(raw_text)

    return CriticOutput(
        critic_called            = True,
        raw_critic_text          = raw_text,
        contradictions           = contradictions,
        confirmations            = confirmations,
        drift_flags_in_context   = drift_flags,
        parity_flags_in_context  = parity_flags_from_context(context),
        context_notes            = context_notes,
        output_bounded           = is_bounded,
        decision_words_found     = found_words,
        tokens_used              = response.usage.output_tokens
    )
```

### 11.5 What Claude Does and Does Not Do (complete specification)

```
WHAT CLAUDE DOES:
  ✓ Identifies contradictions between simultaneously active signals
    (e.g., E2 LONG during BEAR regime while E1 is in hard reject)
  ✓ Confirms conditions that reinforce the signal in plain language
  ✓ Translates active drift flags into plain English with actual values
  ✓ Translates active parity flags into plain English
  ✓ Notes the Phase 11 caveat status every time E2 SHORT suppression is logged
  ✓ Flags when the two edges are reading opposite market direction
  ✓ Flags when current volatility is outside the backtested distribution
  ✓ Flags when session leadership has shifted relative to the research baseline
  ✓ Notes consecutive loss streaks in context
  ✓ Summarizes the full signal context as a coherent narrative

WHAT CLAUDE DOES NOT DO:
  ✗ Generate entry prices
  ✗ Override signal parameters
  ✗ Assign confidence scores
  ✗ Recommend taking or skipping a trade
  ✗ Add indicators not in the research
  ✗ Compare the current setup to past market events from training data
  ✗ Modify any field in Edge1Signal, Edge2Signal, or BotState
  ✗ Act as a gate — the critic is always optional context, never a blocker
  ✗ Speculate on future price movement
  ✗ Produce output that implies a trade decision in any form
```

---

## SECTION 12 — SIGNAL OUTPUT FORMAT (updated for v2)

**The same three states as v1 (TRADE, WATCH, NO TRADE) with two new appended blocks.**

### 12.1 TRADE Signal Format

```
╔══════════════════════════════════════════════════════════════╗
  SIGNAL: XAU/USD [EDGE 1 — TREND PULLBACK | EDGE 2 — BREAKOUT]
  Direction: LONG / SHORT
  Class: [E1 only | E2 Class A | E2 Class B]
  Generated: YYYY-MM-DD HH:MM UTC
╠══════════════════════════════════════════════════════════════╣
  ENTRY       : $[price]
  STOP LOSS   : $[price]     ← swing_low/high(10) ± 0.5 ATR
  TAKE PROFIT : $[price]     ← 1.5R from entry
  STOP DIST   : $[X.XX]
  RR          : 1:1.5 (fixed)
  TIMEOUT     : [72H / 18H] from entry bar
╠══════════════════════════════════════════════════════════════╣
  ACCOUNT RISK (0.01 lot, $10 account)
  Dollar risk : $[X.XX]  ([X]% of account)
  Risk flag   : [ACCEPTABLE / ELEVATED / HIGH]
  Overlap adj : [YES — sized down 30% | NO]
╠══════════════════════════════════════════════════════════════╣
  WHY THIS SIGNAL FIRED:
  [Gate-by-gate confirmation — same as v1]
╠══════════════════════════════════════════════════════════════╣
  REGIME STATE:
  Trend: [BULL/BEAR/MIXED]  |  ATR: [X.XX]
  Volatility: [LOW/NORMAL/HIGH]
  Session: [name]  |  Weekday: [name]
╠══════════════════════════════════════════════════════════════╣
  OVERLAP STATUS:
  [NONE / ACTIVE / E2 SHORT SUPPRESSED — with Phase 11 caveat]
╠══════════════════════════════════════════════════════════════╣
  SYSTEM HEALTH
  Drift severity : [NONE / WATCH / CAUTION / ALERT]
  Active flags   : [N flags — list flag types, not full text]
  Parity status  : [OK / WARNING / BREACH]
  Parity issues  : [list failed checks if any]
  E2 OOS count   : [N] / 20 for Phase 11 hard-lock
╠══════════════════════════════════════════════════════════════╣
  CRITIC LAYER OUTPUT
  ── CONTRADICTIONS ──────────────────────────────────────────
  [One sentence per contradiction, or "None."]
  ── CONFIRMATIONS ───────────────────────────────────────────
  [One sentence per confirmation, or "None."]
  ── DRIFT AND PARITY FLAGS ──────────────────────────────────
  [Plain-language summary of active flags, or "None."]
  ── CONTEXT NOTES ───────────────────────────────────────────
  [Observations with no implied action, or "None."]
  ── CRITIC OUTPUT BOUNDED: [YES / NO — DISCARDED IF NO] ─────
╠══════════════════════════════════════════════════════════════╣
  EXECUTE IN MT5:
  Symbol : XAUUSD
  Type   : Buy/Sell [Limit/Market]
  Lots   : 0.01
  SL     : [price]
  TP     : [price]
╚══════════════════════════════════════════════════════════════╝
```

### 12.2 NO TRADE Format

```
╔══════════════════════════════════════════════════════════════╗
  NO TRADE — XAU/USD
  Generated: YYYY-MM-DD HH:MM UTC
╠══════════════════════════════════════════════════════════════╣
  REASON:
  [Edge 1]: ✗ [specific gate that failed — same as v1]
  [Edge 2]: ✗ [specific gate that failed — same as v1]
╠══════════════════════════════════════════════════════════════╣
  SYSTEM HEALTH
  Drift: [severity + active flag count]
  Parity: [status]
╠══════════════════════════════════════════════════════════════╣
  CRITIC LAYER: [Disabled on NO_TRADE unless drift flag active
                 or CRITIC_CALL_ON_NO_TRADE = True]
╚══════════════════════════════════════════════════════════════╝
```

### 12.3 WATCH Format

```
╔══════════════════════════════════════════════════════════════╗
  WATCH — XAU/USD
  Generated: YYYY-MM-DD HH:MM UTC
╠══════════════════════════════════════════════════════════════╣
  STATUS: Edge 2 — Compression zone active, waiting for breakout
  Zone high: $[X.XX]  |  Zone low: $[X.XX]
  Zone width: $[X.XX] ([X]x ATR)  |  Zone age: [N] bars
  LONG trigger:  close above $[zone_high] + Class A/B confirmation
  SHORT trigger: close below $[zone_low]  + Class A/B confirmation
╠══════════════════════════════════════════════════════════════╣
  SYSTEM HEALTH: Drift [severity] | Parity [status]
╠══════════════════════════════════════════════════════════════╣
  CRITIC LAYER:
  [Active on WATCH when CRITIC_CALL_ON_WATCH = True]
  [Particularly useful here: identifies if E1 regime context
   contradicts the expected E2 breakout direction before it fires]
╠══════════════════════════════════════════════════════════════╣
  NOTE: This is not a signal. No entry until breakout confirmed.
╚══════════════════════════════════════════════════════════════╝
```

---

## SECTION 13 — LOGGING SPECIFICATION (updated for v2)

**v2 adds drift, parity, and critic fields to the log schema. All original fields unchanged.**

```python
# analytics/logger.py

LOG_SCHEMA = {
    # ── ORIGINAL v1 FIELDS (unchanged) ──────────────────
    'timestamp_utc':         str,
    'weekday':               str,
    'session':               str,
    'hour_utc':              int,
    'trend_1h':              str,
    'ema20':                 float,
    'ema50':                 float,
    'ema200':                float,
    'atr':                   float,
    'volatility':            str,
    'edge1_fired':           bool,
    'edge1_reject_reason':   str,
    'edge2_fired':           bool,
    'edge2_reject_reason':   str,
    'e2_breakout_class':     str,
    'e2_direction':          str,
    'overlap_active':        bool,
    'e2_short_suppressed':   bool,
    'sizing_factor':         float,
    'entry_price':           float,
    'stop_loss':             float,
    'take_profit':           float,
    'stop_distance':         float,
    'dollar_risk':           float,
    'dollar_risk_adj':       float,
    'rr':                    float,
    'timeout_bars':          int,
    'outcome':               str,
    'exit_price':            float,
    'pnl_usd':               float,
    'bars_held':             int,
    'exit_reason':           str,
    'signal_type':           str,
    'edge_source':           str,
    'e2_oos_trade_count':    int,
    'phase11_caveat_active': bool,

    # ── NEW v2 FIELDS — DRIFT ────────────────────────────
    'drift_severity':            str,    # NONE/WATCH/CAUTION/ALERT
    'drift_flag_count':          int,
    'drift_flag_types':          list,   # list of flag_type strings
    'e1_rolling_ev':             float,  # null if <20 trades
    'e1_rolling_wr':             float,
    'e2_rolling_ev':             float,
    'e2_rolling_wr':             float,
    'e1_consecutive_losses':     int,
    'e2_consecutive_losses':     int,
    'atr_ratio_90d':             float,  # current / 90d mean
    'volatility_outside_backtest': bool,
    'regime_flip_count_14d':     int,
    'regime_choppy':             bool,
    'session_rotation_flag':     bool,

    # ── NEW v2 FIELDS — PARITY ───────────────────────────
    'parity_status':             str,    # OK/WARNING/BREACH
    'parity_failed_checks':      list,   # list of failed indicator names
    'missing_candles_1h':        int,
    'missing_candles_m15':       int,
    'ema20_parity_diff':         float,
    'atr_1h_parity_diff_pct':    float,

    # ── NEW v2 FIELDS — CRITIC ───────────────────────────
    'critic_called':             bool,
    'critic_bounded':            bool,
    'critic_contradiction_count': int,
    'critic_confirmation_count': int,
    'critic_contradictions':     list,   # list of contradiction strings
    'critic_confirmations':      list,
    'critic_context_notes':      list,
    'critic_tokens_used':        int,
    'critic_raw_text':           str,    # Full response stored for review
}
```

---

## SECTION 14 — MASTER EXECUTION FLOW (updated for v2)

**Every cycle runs this exact sequence. Steps 1–10 are the original engine (unchanged). Steps 11–13 are new.**

```
Every completed 1H candle (Edge 1 cycle):
Every completed M15 candle (Edge 2 cycle):

[STEP 1] Fetch and validate data
  └─ Get latest candles from MT5 or data source
  └─ Verify no gaps, no NaN, correct sort order
  └─ IF data invalid → NO TRADE (data error) → STOP

[STEP 2] Update BotState daily counters
  └─ If new UTC day → reset e1_trades_today, e2_trades_today
  └─ If timeout reached → close trade, update state

[STEP 3] Calculate all indicators (indicators/core.py only)
  └─ EMA20, EMA50, EMA200 on 1H
  └─ ATR on 1H and M15
  └─ swing_low/high lookback values
  └─ rolling_range for compression detection

[STEP 4] Classify regime (regimes/engine.py)
  └─ Produce RegimeState object

[STEP 5] Run Edge 1 detector (edges/edge1/detector.py)
  └─ Check all 6 gates in order
  └─ Return Edge1Signal or None

[STEP 6] Run Edge 2 detector (edges/edge2/detector.py)
  └─ Update compression zone map
  └─ Check for breakout on current M15 bar
  └─ Apply fakeout filter
  └─ Return Edge2Signal or None

[STEP 7] Run overlap engine (overlap/engine.py)
  └─ Apply 4 Phase 11 rules
  └─ Apply sizing factors
  └─ Set suppression flags
  └─ Return modified signals

[STEP 8] Run risk engine (risk/engine.py)
  └─ Calculate dollar risk, account risk %
  └─ Apply final dollar risk cap check
  └─ Produce risk assessment block

[STEP 9] Format signal output (signals/output.py)
  └─ TRADE, WATCH, or NO TRADE
  └─ Full parameter block
  └─ Overlap status block
  └─ MT5 execution block

[STEP 10] Log core fields (analytics/logger.py)
  └─ Write base log entry — all v1 fields
  └─ Update performance metrics every 10 trades

  ── ABOVE THIS LINE: deterministic engine, unchanged ──
  ── BELOW THIS LINE: observation layers, new in v2 ────

[STEP 11] Run Regime Drift Detector (drift/detector.py)
  └─ Compute rolling EV and WR per edge from completed trades
  └─ Check consecutive losses per edge
  └─ Compute ATR ratio vs 90d mean
  └─ Check regime choppiness (flip count last 14d)
  └─ Check session leadership shift
  └─ Produce DriftState with severity and flag list
  └─ Append drift fields to log entry
  └─ NO MODIFICATION TO ANY SIGNAL OR STATE OBJECT

[STEP 12] Run Parity Monitor (parity/monitor.py) — every N candles
  └─ Load reference snapshot for current timestamp
  └─ Compare live vs reference for all indicators
  └─ Check for missing candles in feed
  └─ Produce ParityState with status and failed checks
  └─ Append parity fields to log entry
  └─ NO MODIFICATION TO ANY SIGNAL OR STATE OBJECT

[STEP 13] Run Claude Critic Layer (critic/layer.py)
  └─ Decision: should critic be called this cycle?
       → Always if DriftSeverity == ALERT
       → Always if ParityStatus == BREACH
       → If TRADE: yes (default)
       → If WATCH: yes if CRITIC_CALL_ON_WATCH = True
       → If NO_TRADE: yes if CRITIC_CALL_ON_NO_TRADE = True
  └─ Build read-only context package
  └─ Call Claude API with bounded system prompt
  └─ Validate output (scan for decision words)
  └─ Parse structured sections
  └─ Append critic fields to log entry
  └─ Append critic output block to signal report
  └─ CRITIC OUTPUT NEVER MODIFIES SIGNAL FIELDS
  └─ CRITIC OUTPUT IS FLAGGED AS INVALID IF DECISION LANGUAGE FOUND

[FINAL OUTPUT]
  └─ Complete signal report with all blocks
  └─ Complete log entry with all fields
  └─ Human reads report and executes in MT5
```

---

## SECTION 15 — WHAT IS LOCKED vs CONDITIONAL (updated for v2)

### Locked — never changed without a new research phase

```
Edge 1:
  ✓ Setup A only
  ✓ LONG only
  ✓ Tue/Wed/Thu only
  ✓ London_Open + London_Main + NY_Main
  ✓ EMA20 > EMA50 > EMA200 as the trend definition
  ✓ RR = 1.5
  ✓ Timeout = 72 bars
  ✓ SL = swing_low(10) - 0.5 ATR
  ✓ NO RSI | NO MACD | NO entry refinements

Edge 2:
  ✓ Entry at breakout candle close
  ✓ SL = swing_point(10) ± 0.5 ATR
  ✓ TP = fixed 1.5R
  ✓ Timeout = 72 bars
  ✓ Bidirectional (LONG + SHORT)
  ✓ No session filter | No weekday filter
  ✓ Classes A and B both active
  ✓ Fakeout filter is the quality gate
  ✓ NO trailing | NO partial exits | NO breakeven

Overlap:
  ✓ Both edges run simultaneously
  ✓ Co-activation sizing reduction (30%)
  ✓ E2 SHORT suppressed when E1 active (strong prior until n=20)

v2 Observation Layers:
  ✓ Drift detector thresholds are starting calibrations.
    After 100+ live trades, these thresholds may be revised
    based on the observed live distribution — with documentation.
  ✓ Parity tolerances are starting calibrations.
    After observing real feed quality, tolerances may be adjusted.
  ✓ Critic system prompt is locked for first 50 live signals.
    After that: prompt revision allowed if critic is producing
    decision language (Rule 8 violations) or is consistently
    unhelpful. Any revision must be documented and tested.
```

### Conditional — flagged for future research phases

```
Phase 10 flag (unchanged from v1):
  Partial exit / trail after +1R on the 1H system specifically.
  NOT active. OOS average winner MFE on 1H = 4.139R vs TP of 1.5R.

Phase 11 flag (unchanged from v1):
  E2 SHORT suppression becomes hard-locked at n=20 E2 OOS trades.
  Currently: strong prior. Bot logs running count every cycle.

Phase 13 flag (unchanged from v1):
  Risk-of-ruin and Kelly sizing analysis for $10 account.
  Not yet completed. Sizing remains fixed at 0.01 lot.

Phase 14 flag (NEW — v2):
  After 100+ live trades with drift detection active:
  Review drift threshold calibration against observed distribution.
  The current thresholds (EV < +0.10R for E1, etc.) are derived
  from research baselines. Live distribution may justify revision.
  This is NOT a license to change them early. It is a scheduled review.

Phase 15 flag (NEW — v2):
  If parity breaches are occurring regularly despite a clean data feed,
  investigate whether the reference snapshot system needs to account
  for broker-specific data adjustments (Exness data vs generic feed).
  Do not change tolerances until the breach source is identified.
```

---

## SECTION 16 — BOT IDENTITY (updated for v2)

```
THIS BOT IS:
  A regime-aware, selective signal analysis engine with two independently
  validated, partially overlapping edges — augmented with a drift monitor,
  a parity enforcer, and a bounded critic layer.

  It trades less, not more.
  It filters bad conditions first, then looks for good ones.
  The edge comes from avoiding bad trades, not from predicting good ones.
  (Phase 5 key finding — unchanged)

  The critic layer flags contradictions. It does not find trades.
  The drift monitor alerts to degradation. It does not stop the bot.
  The parity monitor enforces indicator integrity. It does not modify signals.
  All three observation layers serve the human. None of them serve themselves.

THIS BOT IS NOT:
  A "trade everything" system.
  An AI-powered signal generator.
  A system that improves by adding more indicators.
  A system where Claude's flags override deterministic rules.
  A system that knows when its own edge has failed — only when to raise a flag.

WHAT SUCCESS LOOKS LIKE:
  Edge 1 OOS target: WR ~50%, EV ~+0.29R per trade, MaxDD < 5R
  Edge 2 OOS target: WR ~56%, EV ~+0.65R per trade, MaxDD < 2R
  These are from the research. They are the performance benchmark.

  After 100 live trades:
    Rolling EV consistently above drift thresholds → engine validated in live
    Parity status consistently OK → indicator integrity confirmed
    Critic contradiction rate → baseline established for what is normal

  If live performance diverges significantly: investigate before continuing.
  If drift severity reaches ALERT consistently: pause and review.
  If parity breaches regularly: fix the data feed before any other action.

THE MOST IMPORTANT THING (unchanged):
  The research integrity must be preserved during implementation.
  If the live system calculates indicators differently from the research,
  the live system is not running the same edge that was validated.
  That is the primary engineering risk.
  The parity monitor exists to prevent that from happening silently.
  Everything else in this document is designed to prevent it knowingly.
```

---

*Document version: 2.0*  
*Built on: Edge 1 Phases 1–5 | Edge 2 Phases 1–11*  
*Data: 38,808 XAU/USD 1H candles | 2020-01-24 → 2026-05-07*  
*Account: Exness $10 | 0.01 lot | XAU/USD only*  
*Bot role: Analysis and signal output — manual execution in MT5*  
*v2 additions: Regime Drift Detection (Section 9) | Parity Monitor (Section 10) | Claude Critic Layer (Section 11)*  
*Next phases: E2 Phase 12 (paper trading) | E2 Phase 13 (risk-of-ruin) | Phase 14 (drift threshold calibration at 100 live trades) | Phase 15 (parity tolerance review)*  
*Phase 11 rule becomes hard-locked when E2 OOS trade count reaches 20*
