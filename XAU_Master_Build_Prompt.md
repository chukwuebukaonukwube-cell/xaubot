# MASTER BUILD PROMPT — XAU/USD Analysis Bot v2
# Drop this into your AI builder as the project system prompt or first message.
# This document governs the entire build. Nothing overrides it.

---

## YOUR FIRST ACTION — NON-NEGOTIABLE

Before writing a single line of code, you will read `XAU_Bot_Logic_v2.md`
**in full, from line 1 to the final line.** Not a skim. Not a summary pass.

When you have finished reading, you will output this exact block:

```
LOGIC FILE ABSORBED.
Sections confirmed:
  [1] Locked parameters — Edge 1, Edge 2, Overlap, Risk, Drift, Parity, Critic
  [2] State objects — RegimeState, Edge1Signal, Edge2Signal, BotState,
      DriftState, ParityState, CriticOutput
  [3] Indicator module — ema, atr, swing_low, swing_point,
      rolling_range, body_ratio, wick_ratio
  [4] Regime engine
  [5] Edge 1 detector — 6 gates, locked rejections
  [6] Edge 2 detector — compression + fakeout filter, locked rejections
  [7] Overlap engine — 4 Phase 11 rules
  [8] Risk engine
  [9] Regime drift detector — DriftSeverity, 5 flag types
  [10] Parity monitor — reference snapshots, 7 indicator checks
  [11] Claude critic layer — bounded prompt, validation, 4 output sections
  [12] Signal output format — TRADE, WATCH, NO TRADE
  [13] Logging schema — all v1 + v2 fields
  [14] Master execution flow — Steps 1–13
Critical rules confirmed: Rules 1–9
Data source: Twelvedata API (primary) — MT5 Python bridge (fallback)
```

If you cannot produce this block accurately, re-read the logic file.
Do not proceed to code until this block is output correctly.

---

## PROJECT OVERVIEW

You are building a **XAU/USD signal analysis bot** in Python.

- The system is a **deterministic signal engine**. It detects setups and outputs
  analysis. It does NOT execute trades. Manual execution in MetaTrader 5.
- Two edges: Edge 1 (1H trend pullback, LONG only) and Edge 2 (M15 compression
  breakout, bidirectional). Both are backtested and their parameters are locked.
- Three observation layers sit above the engine: regime drift detection, live vs
  backtest parity monitoring, and a bounded Claude critic layer.
- The Anthropic Claude API is used exclusively in the critic layer. It flags
  contradictions. It never generates signals or modifies any signal field.
- Dashboard: Streamlit.
- Data: Twelvedata API (primary). MT5 Python bridge (fallback).

The full specification lives in `XAU_Bot_Logic_v2.md`.
That file is the authority. If this prompt and the logic file conflict,
the logic file wins.

---

## BUILD RULES — THESE OVERRIDE YOUR DEFAULTS

```
BUILD RULE 1 — ONE MODULE AT A TIME
  Build each module completely before starting the next.
  Do not scaffold the whole project and fill in later.
  Incomplete modules create hidden bugs that are untraceable.

BUILD RULE 2 — NO IMPROVISATION
  If a parameter, threshold, function signature, or logic condition
  is specified in the logic file, use it exactly.
  Do not substitute with "common knowledge" equivalents.
  Do not add parameters that are not in the spec.
  Do not improve thresholds because they seem suboptimal.
  The values are locked by backtested research.

BUILD RULE 3 — ONE INDICATOR IMPLEMENTATION
  indicators/core.py is the ONLY place indicators are calculated.
  EMA, ATR, swing_low, swing_point, rolling_range, body_ratio,
  wick_ratio are implemented once here and imported everywhere.
  If you find yourself writing an indicator calculation outside
  this file, stop and refactor.

BUILD RULE 4 — STATE OBJECTS ARE THE CONTRACT
  Every module reads from typed dataclasses and writes to typed dataclasses.
  No loose dictionaries passed between modules.
  No global variables.
  No module-level state.

BUILD RULE 5 — CRITIC LAYER IS ISOLATED
  The critic/ folder has read access to signal context.
  It never imports from edges/, overlap/, risk/, or signals/.
  It never modifies any dataclass field.
  It only writes to CriticOutput.

BUILD RULE 6 — DRIFT AND PARITY NEVER GATE SIGNALS
  DriftState and ParityState are produced after the signal is formed.
  The decision engine (Steps 1–10 in the execution flow) never reads
  DriftState or ParityState. They are observation outputs only.

BUILD RULE 7 — LOG EVERY DECISION
  The logger writes an entry every cycle — TRADE, WATCH, and NO TRADE.
  Not just on signal fires. Every cycle.
  The log schema is in Section 13 of the logic file. Use it exactly.

BUILD RULE 8 — TEST EACH MODULE BEFORE MOVING ON
  Each module has a corresponding test file in tests/.
  Write the test alongside the module. Not after.
  At minimum: unit test with known input → known output.
  For indicators: verify against manually calculated reference values.
```

---

## DATA SOURCE — TWELVEDATA API

**Primary data source: Twelvedata REST API**

```python
# Required candles:
#   XAU/USD  1H  — minimum 250 bars for EMA200 warmup
#   XAU/USD  M15 — minimum 500 bars for compression zone history
#
# Twelvedata endpoint:
#   GET https://api.twelvedata.com/time_series
#   params: symbol=XAU/USD, interval=1h or 15min,
#           outputsize=500, apikey=YOUR_KEY
#
# Response schema (use this exactly — do not rename columns):
#   datetime, open, high, low, close, volume
#
# Store as Parquet in data/candles/:
#   xauusd_1h.parquet
#   xauusd_m15.parquet
#
# Refresh strategy:
#   On each cycle, fetch only the latest N bars needed to update
#   the existing Parquet. Do not re-fetch full history every cycle.
#   Append new completed candles only. Never include the current
#   incomplete (live) candle in calculations.
#
# Column naming after fetch — normalise immediately:
#   df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
#   df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
#   df = df.sort_values('timestamp').reset_index(drop=True)
#
# API key: load from environment variable TWELVEDATA_API_KEY
#   Never hardcode the key.

# Fallback: MT5 Python bridge
#   import MetaTrader5 as mt5
#   mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_H1, 0, 250)
#   Activate fallback only if Twelvedata returns error or rate limit.
#   Log: "DATA SOURCE: Twelvedata failed — switched to MT5 bridge."
```

---

## BUILD ORDER — FOLLOW THIS EXACTLY

Work through modules in this order. Complete each before starting the next.
After each module, output a completion checkpoint (format below).

```
MODULE 1  → config/settings.py
MODULE 2  → state/models.py
MODULE 3  → indicators/core.py         + tests/test_indicators.py
MODULE 4  → data/fetcher.py            (Twelvedata + MT5 fallback)
MODULE 5  → regimes/engine.py          + tests/test_regime.py
MODULE 6  → edges/edge1/detector.py    + tests/test_edge1.py
MODULE 7  → edges/edge2/detector.py    + tests/test_edge2.py
MODULE 8  → overlap/engine.py          + tests/test_overlap.py
MODULE 9  → risk/engine.py
MODULE 10 → signals/output.py
MODULE 11 → analytics/logger.py
MODULE 12 → drift/detector.py          + tests/test_drift.py
MODULE 13 → parity/monitor.py          + tests/test_parity.py
MODULE 14 → critic/prompt.py
           critic/layer.py             + tests/test_critic.py
MODULE 15 → main.py                    (orchestrates Steps 1–13)
MODULE 16 → dashboard/app.py           (Streamlit)
```

**Completion checkpoint format — output after each module:**

```
MODULE [N] COMPLETE: [module name]
Files written: [list]
Tests passing: [yes / no — if no, state what is failing]
Logic file section referenced: [section number(s)]
Deviations from spec: [NONE — or describe exactly what and why]
Ready for next module: YES
```

If you have any deviation from spec, it must be explicitly stated
in the checkpoint. "Deviations: NONE" must be true before moving on.

---

## MODULE-BY-MODULE INSTRUCTIONS

### MODULE 1 — config/settings.py

Source: Logic file Section 1 (entire section).

Copy all constants exactly as written. Every constant. Every comment.
Do not reorganise into classes or enums at this stage.
The file is imported by every other module. Stability is critical.

After writing: visually verify every constant against the logic file.
This is the only module where you do a manual double-check pass.
If a constant differs from the logic file by even one decimal place,
the backtested edge is no longer what is running live.

---

### MODULE 2 — state/models.py

Source: Logic file Section 2 (entire section).

Implement all dataclasses and enums in this order:
  TrendState, VolatilityState, SessionName, WeekdayName,
  SignalType, BreakoutClass, DriftSeverity, ParityStatus,
  RegimeState (with @property methods),
  Edge1Signal, CompressionZone, Edge2Signal, BotState,
  DriftFlag, DriftState, ParityCheck, ParityState,
  CriticOutput

Every field, every type annotation, every default value — from the spec.
Do not add fields. Do not remove fields. Do not rename fields.
Other modules will import these. Field name changes break everything silently.

---

### MODULE 3 — indicators/core.py

Source: Logic file Section 3 (entire section).

Implement: ema, atr, swing_low, swing_point, rolling_range,
           body_ratio, wick_ratio, classify_volatility, classify_session

Critical implementation details:
  ema:            ewm(span=period, adjust=False)
  atr:            ewm(alpha=1/period, adjust=False) — Wilder's smoothing
  swing_low:      rolling(lookback).min() on 'low'
  swing_point:    rolling min on 'low' for long, rolling max on 'high' for short
  rolling_range:  rolling max of high minus rolling min of low over period
  body_ratio:     abs(close - open) / (high - low) — return 0.0 if range == 0
  wick_ratio:     directional wick / (high - low) — return 0.0 if range == 0
  classify_session: exact UTC hour boundaries from the spec — 17:30 cutoff included

Test file must include:
  - EMA: feed 5-period EMA a known series, verify last value against manual calc
  - ATR: verify Wilder's smoothing is used (not simple rolling mean)
  - body_ratio: test zero-range candle returns 0.0 (no division by zero)
  - classify_session: test all session boundaries including 17:29 vs 17:31

---

### MODULE 4 — data/fetcher.py

Source: Data Source section of this prompt + Logic file Step 1 of execution flow.

Implement:
  fetch_candles_twelvedata(symbol, interval, n_bars) -> pd.DataFrame
  fetch_candles_mt5(symbol, timeframe, n_bars) -> pd.DataFrame
  get_candles(symbol, interval, n_bars) -> pd.DataFrame  # tries TD, falls back to MT5
  load_parquet(path) -> pd.DataFrame
  save_parquet(df, path) -> None
  validate_candles(df) -> bool  # checks: no NaN, sorted ascending, no gaps > 2

Column normalisation happens inside fetch functions. Output always has:
  ['timestamp', 'open', 'high', 'low', 'close', 'volume']
  timestamp is UTC-aware datetime.

Twelvedata base URL: https://api.twelvedata.com/time_series
API key from: os.environ['TWELVEDATA_API_KEY']
Rate limit: Twelvedata free tier = 800 requests/day. Log every API call.

validate_candles returns False and logs the reason if:
  - Any OHLCV column has NaN
  - Timestamps are not sorted ascending
  - More than PARITY_MAX_GAP_CANDLES consecutive missing bars
  - High < Low on any row

---

### MODULE 5 — regimes/engine.py

Source: Logic file Section 4.

Function signature:
  classify_regime(df_1h, current_bar, current_datetime) -> RegimeState

Uses only: indicators/core.py functions
Reads: df_1h DataFrame, current_bar index, current_datetime (UTC)
Writes: RegimeState object only — nothing else

EMA values are taken at index current_bar of the full EMA series.
ATR mean_20 = atr_series.rolling(20).mean() at current_bar.
Session uses classify_session with hour AND minute (17:30 cutoff is minute-sensitive).

The regime engine does not know about edges, drift, or parity.
It classifies. That is all.

---

### MODULE 6 — edges/edge1/detector.py

Source: Logic file Section 5 (entire section including "NOT CHECKED" block).

Function signature:
  detect_edge1(df_1h, current_bar, regime, bot_state) -> Optional[Edge1Signal]

Implement exactly 6 gates in the exact order specified.
Each gate must log its rejection reason if it rejects.
Log format: "E1 rejected — [reason with actual values]"

Gate 5 pullback condition:
  pullback_valid = (current_low <= ema20) AND (current_low >= ema50 * 0.998)
  The 0.998 multiplier is in the spec. Do not change it.

Stop loss calculation:
  swing_sl uses the last E1_SL_SWING_LOOKBACK (10) bars.
  stop_loss = swing_sl - (E1_SL_ATR_BUFFER * atr_value)
  If stop_distance <= 0: reject with log.
  If dollar_risk > MAX_SINGLE_TRADE_RISK_USD: reject with log.

Return: fully populated Edge1Signal with sizing_factor=1.0 (overlap engine sets this).

DO NOT add any gate, filter, or check not in the spec.
RSI is rejected. MACD is rejected. Volume is not in the research.
If you add any of these, the build is incorrect.

---

### MODULE 7 — edges/edge2/detector.py

Source: Logic file Section 6 (entire section including "NOT APPLIED" block).

Two functions:
  detect_compression_zones(df_m15) -> List[CompressionZone]
  classify_breakout(row, compression_zone, direction) -> BreakoutClass
  detect_edge2(df_m15, current_bar, regime, bot_state,
               compression_zones) -> Optional[Edge2Signal]

Compression detection:
  Condition: rolling_range(20) / atr(14) <= E2_COMPRESSION_MULT (3.5)
  Note from spec: the threshold is NOT the real gate. Do not over-engineer it.
  Range validation: height >= 0.3 * ATR AND height <= 3.0 * ATR

Fakeout filter (the real quality gate):
  FAKEOUT if body_ratio < 0.4 OR wick_ratio > 0.3
  CLASS A: close in top/bottom 70% of candle range
  CLASS B: not fakeout, close in 40–70% range
  This classification must be direction-aware (long vs short logic differs).

detect_edge2 gates:
  Gate 4: most recent valid zone that (a) ended before current_bar
           and (b) has not already produced a signal.
           Mark used zones to prevent duplicate signals.

DO NOT add session filter, weekday filter, trailing stop logic,
partial exit logic, or breakeven logic. All permanently rejected.

---

### MODULE 8 — overlap/engine.py

Source: Logic file Section 7 (entire section including Phase 11 caveat note).

Function signature:
  apply_overlap_rules(e1_signal, e2_signal, bot_state) -> Tuple[Optional[Edge1Signal], Optional[Edge2Signal]]

Implement exactly 4 rules in order.
Rule 2 note: at 0.01 fixed lot, "sizing down 30%" means recommending
the human take only the higher-priority signal. The sizing_factor field
is still set to 0.70 on both signals for logging purposes. The signal
output module will translate this into the co-activation recommendation.

Rule 3: e2_short_suppressed flag is set on the signal object.
The signal output module formats suppressed signals as WARNING, not TRADE.
The human makes the final call. The bot flags clearly.

Mandatory log every cycle (even if no signals):
  "Phase 11 caveat: E2 OOS trade count = [N]. Locks at 20."

---

### MODULE 9 — risk/engine.py

Source: Logic file Section 8.

Function signature:
  assess_risk(signal, bot_state) -> dict

Returns dict with exactly these keys:
  dollar_risk_raw, dollar_risk_adj, dollar_target,
  account_risk_pct, rr, risk_flag, sizing_factor,
  overlap_active, timeout_hours

risk_flag thresholds: <= 2.00 ACCEPTABLE | <= 3.50 ELEVATED |
                      <= 5.00 HIGH | > 5.00 REJECTED

Always include account reality note in log output:
  "At $10 with 0.01 lot fixed: ${stop_distance} stop = ${dollar_risk} risk = {pct}% of account."

---

### MODULE 10 — signals/output.py

Source: Logic file Section 12 (all three signal formats).

Function signature:
  format_signal(signal_type, e1_signal, e2_signal, risk_assessment,
                bot_state, drift_state, parity_state,
                critic_output) -> str

Produces the exact formatted text blocks from the spec.
The box-drawing characters (╔ ╠ ╚ ═) must be used exactly as shown.
All three formats: TRADE, WATCH, NO TRADE.

The SYSTEM HEALTH block always appears (severity + parity status).
The CRITIC LAYER block appears when critic_output.critic_called is True.
If critic_output.output_bounded is False: show "CRITIC OUTPUT INVALID — discarded."

E2 SHORT suppressed signals: format as WARNING block, not TRADE block.
Include the Phase 11 caveat text in the suppression output.

---

### MODULE 11 — analytics/logger.py

Source: Logic file Section 13 (full LOG_SCHEMA).

Function signature:
  log_cycle(log_entry: dict) -> None
  update_performance_metrics(trade_log: List[dict]) -> dict  # called every 10 trades

log_cycle writes one JSON line per cycle to logs/decisions.jsonl
Every field in LOG_SCHEMA must be present in every log entry.
Use None for fields that are not applicable for this cycle (e.g., entry_price on NO_TRADE).
Do not omit fields. Omitting fields breaks performance analysis.

update_performance_metrics computes per-edge metrics from the spec:
  win_rate, ev_r, profit_factor, max_drawdown_r, avg_bars_held, timeout_rate
  Per-session breakdown for Edge 1.
  Per-class and per-direction breakdown for Edge 2.
  Overlap metrics.

---

### MODULE 12 — drift/detector.py

Source: Logic file Section 9 (entire section).

Function signature:
  detect_drift(trade_log, regime, df_1h, current_bar) -> DriftState

Steps in order:
  1. Collect completed trades per edge (outcome in WIN/LOSS/TIMEOUT only)
  2. Rolling EV and WR (last 20 trades) — return None if < 20 trades
  3. Consecutive loss count per edge (walk backward until WIN)
  4. ATR ratio vs 90-day mean (compute from df_1h history)
  5. Regime flip count last 14 days (from regime log — pass as parameter)
  6. Session EV breakdown for Edge 1 (last 30 trades)
  7. Build active DriftFlag list
  8. Determine DriftSeverity from flag count and EV flags

All 5 flag types from the spec must be implemented:
  EV_BELOW_THRESHOLD, WR_BELOW_THRESHOLD, CONSECUTIVE_LOSSES,
  VOLATILITY_OUTSIDE_BACKTEST, REGIME_CHOPPY, SESSION_LEADERSHIP_SHIFT

DriftState fields: all from the spec, including baseline references
  (e1_baseline_ev=0.29, e1_baseline_wr=0.50, etc.)

The drift detector never touches e1_signal, e2_signal, or BotState.
It reads from trade_log, regime, and df_1h only.

---

### MODULE 13 — parity/monitor.py

Source: Logic file Section 10 (entire section).

Two components:
  load_reference_snapshot(timestamp) -> Optional[dict]
  run_parity_check(df_1h, df_m15, current_bar_1h, current_bar_m15, regime) -> ParityState

Reference snapshots: stored as Parquet in data/backtest_ref/reference.parquet
Schema: timestamp, ema20_1h, ema50_1h, ema200_1h, atr_1h, atr_m15,
        swing_low_10, swing_high_10, session, weekday

For the initial build: generate reference snapshots by running the
indicators/core.py functions on the full historical dataset.
This is the bootstrap step — the research engine output approximation.

Parity check runs every PARITY_CHECK_FREQUENCY (10) candles.
Implement check_absolute and check_percent helper functions.
Build ParityCheck objects for each indicator.

ParityStatus determination:
  OK:      all checks pass, zero missing candles
  WARNING: 1 check fails OR <= PARITY_MAX_GAP_CANDLES missing
  BREACH:  2+ checks fail OR > PARITY_MAX_GAP_CANDLES missing

---

### MODULE 14 — critic/prompt.py and critic/layer.py

Source: Logic file Section 11 (entire section — read it carefully).

critic/prompt.py:
  CRITIC_SYSTEM_PROMPT — copy the exact prompt text from Section 11.3.
  DECISION_WORDS — copy the exact list from Section 11.4.
  Do not paraphrase the system prompt. Copy it.
  The wording of the bounded constraint is deliberate.

critic/layer.py:
  build_critic_context(...)  -> dict
  validate_critic_output(raw_text) -> tuple[bool, List[str]]
  call_critic(context) -> CriticOutput

  Temperature: CRITIC_TEMPERATURE = 0.1
  Max tokens: CRITIC_MAX_TOKENS = 600
  Model: CRITIC_MODEL from settings.py

  validate_critic_output scans for all DECISION_WORDS (case-insensitive).
  If any found: output_bounded = False, decision_words_found = [found words].

  parse_critic_sections must extract the four sections:
    CONTRADICTIONS, CONFIRMATIONS, DRIFT AND PARITY FLAGS, CONTEXT NOTES
  Return each as a list of strings (one per bullet/sentence).

test_critic.py must include:
  - Test that output containing "you should take this trade" fails validation
  - Test that output containing "you should skip" fails validation
  - Test that clean contradictions-only output passes validation
  - Test that empty sections return ["None."]

---

### MODULE 15 — main.py

Source: Logic file Section 14 (Steps 1–13 in the master execution flow).

This is the orchestrator. It calls every module in sequence.
It does not contain any logic of its own.
Every function it calls is already built and tested.

Structure:
  run_edge1_cycle(df_1h, bot_state) -> None   # Steps 1–10, 11–13
  run_edge2_cycle(df_m15, bot_state) -> None  # Same flow for M15
  main_loop() -> None

Parity check: only runs if candle_count % PARITY_CHECK_FREQUENCY == 0.
Critic call: follows the conditional logic from settings.py
  (CRITIC_CALL_ON_DRIFT_FLAG, CRITIC_CALL_ON_WATCH, etc.)

Steps 1–10 produce the signal.
Steps 11–13 observe and annotate.
main.py assembles the final output and writes the log.

---

### MODULE 16 — dashboard/app.py

Source: Logic file — dashboard mentioned in folder structure.
Implement with Streamlit.

Four panels:
  1. CURRENT SIGNAL — latest signal output block (TRADE/WATCH/NO TRADE)
  2. SYSTEM HEALTH — DriftSeverity + ParityStatus + active flag list + E2 OOS count
  3. PERFORMANCE — rolling EV and WR per edge (charts), per-session breakdown
  4. LOG VIEWER — last 50 log entries, filterable by signal_type and edge_source

Auto-refresh: st.rerun() on a timer or manual refresh button.
Do not use real-time websocket streaming — polling every 60 seconds is sufficient.

---

## WHAT TO DO WHEN YOU HIT AN AMBIGUITY

If the logic file is silent on an implementation detail:

1. Use the simplest correct implementation.
2. Log it in the checkpoint as: "Ambiguity resolved: [what you chose and why]"
3. Do not invent features. Do not add complexity.

If you believe a spec value is wrong or suboptimal:

1. Build it as specified.
2. Add a comment: `# SPEC VALUE — do not change without new research phase`
3. Do not "improve" it. The values are locked by backtested research.

---

## FINAL VERIFICATION BEFORE HANDOFF

When all 16 modules are complete, run this checklist:

```
□ All constants in settings.py match the logic file exactly
□ indicators/core.py is the ONLY file containing indicator calculations
□ No global state exists outside BotState and its children
□ Every module has at least one passing test
□ The decision engine (Steps 1–10) never imports from drift/, parity/, or critic/
□ CriticOutput never modifies any field in Edge1Signal, Edge2Signal, or BotState
□ The log writes an entry on every cycle — TRADE, WATCH, and NO TRADE
□ All LOG_SCHEMA fields are present in every log entry (None where not applicable)
□ Twelvedata is the primary data source with MT5 as fallback
□ API key loaded from environment variable, never hardcoded
□ Critic system prompt matches Section 11.3 of the logic file exactly
□ Decision word validation runs on every critic response before display
□ Dashboard shows DriftSeverity and ParityStatus prominently
□ main.py orchestrates Steps 1–13 in the exact sequence from Section 14
```

If any checkbox is false: fix it before marking the build complete.

---

*This prompt governs the build of XAU_Bot_Logic_v2.*
*Logic file is the authority. This prompt is the implementation contract.*
*Do not deviate. Do not improve. Build what is specified.*
