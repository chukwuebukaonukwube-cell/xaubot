import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
from state.models import BotState

LOG_FILE = Path(os.getcwd()) / 'logs' / 'decisions.jsonl'


def load_logs() -> List[Dict]:
    if not LOG_FILE.exists():
        return []
    entries = []
    with open(LOG_FILE, 'r', encoding='utf-8') as handle:
        for line in handle:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def filter_logs(logs: List[Dict], signal_type: Optional[str], edge_source: Optional[str]) -> List[Dict]:
    filtered = logs
    if signal_type:
        filtered = [entry for entry in filtered if entry.get('signal_type') == signal_type]
    if edge_source:
        filtered = [entry for entry in filtered if entry.get('edge_source') == edge_source]
    return filtered


def _build_performance_frame(logs: List[Dict]) -> Dict[str, List]:
    return {
        'e1_rolling_ev': [entry.get('e1_rolling_ev') for entry in logs if entry.get('e1_rolling_ev') is not None],
        'e1_rolling_wr': [entry.get('e1_rolling_wr') for entry in logs if entry.get('e1_rolling_wr') is not None],
        'e2_rolling_ev': [entry.get('e2_rolling_ev') for entry in logs if entry.get('e2_rolling_ev') is not None],
        'e2_rolling_wr': [entry.get('e2_rolling_wr') for entry in logs if entry.get('e2_rolling_wr') is not None],
    }


def _ensure_session_state() -> None:
    if 'bot_state' not in st.session_state:
        st.session_state['bot_state'] = BotState(timestamp=datetime.now(timezone.utc))
    if 'trade_log' not in st.session_state:
        st.session_state['trade_log'] = []
    if 'analysis_result' not in st.session_state:
        st.session_state['analysis_result'] = {}


def run_analysis() -> None:
    from main import run_cycle

    bot_state: BotState = st.session_state['bot_state']
    trade_log: List[dict] = st.session_state['trade_log']

    try:
        signal_text, metadata = run_cycle(bot_state, trade_log, return_metadata=True)
        st.session_state['analysis_result'] = {
            'signal_text': signal_text,
            'metadata': metadata,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        st.success('Analysis cycle completed successfully.')
    except Exception as exc:
        st.session_state['analysis_result'] = {
            'error': str(exc),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        st.error(f'Analysis failed: {exc}')


def main():
    st.set_page_config(page_title='XAU/USD Signal Monitor', layout='wide')
    st.title('XAU/USD Analysis Dashboard')
    st.markdown('Cloud-friendly analysis dashboard. Runs live analysis cycles and displays detailed signal output. No MetaTrader5 dependency required.')

    _ensure_session_state()

    with st.sidebar:
        st.header('Dashboard Controls')
        st.write('Trigger a live analysis cycle and inspect full output details.')
        if st.button('Run analysis now'):
            run_analysis()

        st.markdown('---')
        st.write('Streamlit Cloud deployment requires:')
        st.write('- `TWELVEDATA_API_KEY` for live candle data')
        st.write('- internet access to Twelvedata API')
        st.write('- optional cached candles in `data/candles/` for offline replay')

        st.markdown('---')
        signal_type = st.selectbox('Signal type', ['ALL', 'TRADE', 'WATCH', 'NO_TRADE'])
        edge_source = st.selectbox('Edge source', ['ALL', 'EDGE1', 'EDGE2', 'NONE'])
        if st.button('Refresh logs'):
            st.experimental_rerun()

        st.markdown('---')
        st.write('Auto-refresh will keep the latest logs visible.')
        st_autorefresh = getattr(st, 'autorefresh', None)
        if callable(st_autorefresh):
            st_autorefresh(interval=60000, limit=None, key='dashboard_refresh')

    analysis_result = st.session_state['analysis_result']
    if analysis_result.get('error'):
        st.error(analysis_result['error'])

    if analysis_result.get('signal_text'):
        st.subheader('Latest triggered analysis')
        st.code(analysis_result['signal_text'])
        with st.expander('Show full analysis metadata'):
            st.json(analysis_result['metadata'])
        st.markdown(f"**Last analysis run:** {analysis_result['timestamp']}")

    st.markdown('---')
    st.subheader('Current live logs')
    logs = load_logs()
    filtered_logs = logs
    if signal_type != 'ALL':
        filtered_logs = filter_logs(filtered_logs, signal_type, None)
    if edge_source != 'ALL':
        filtered_logs = filter_logs(filtered_logs, None, edge_source)

    if filtered_logs:
        latest = filtered_logs[-1]
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown('#### Current signal from logs')
            st.code(latest.get('formatted_signal_text') or latest.get('critic_raw_text') or 'No signal text available.')
            st.markdown('#### System health snapshot')
            st.markdown(f"- **Drift severity:** {latest.get('drift_severity', 'N/A')}")
            st.markdown(f"- **Parity status:** {latest.get('parity_status', 'N/A')}")
            st.markdown(f"- **Active drift flags:** {latest.get('drift_flag_types', [])}")
            st.markdown(f"- **E2 OOS count:** {latest.get('e2_oos_trade_count', 0)} / 20")
            st.markdown(f"- **Phase 11 caveat active:** {latest.get('phase11_caveat_active', False)}")
        with col2:
            st.markdown('#### Performance charts')
            perf = _build_performance_frame(filtered_logs[-50:])
            if perf['e1_rolling_ev']:
                st.line_chart({'Edge 1 EV': perf['e1_rolling_ev']})
            if perf['e1_rolling_wr']:
                st.line_chart({'Edge 1 WR': perf['e1_rolling_wr']})
            if perf['e2_rolling_ev']:
                st.line_chart({'Edge 2 EV': perf['e2_rolling_ev']})
            if perf['e2_rolling_wr']:
                st.line_chart({'Edge 2 WR': perf['e2_rolling_wr']})

        st.markdown('---')
        st.subheader('Log viewer')
        display_logs = filtered_logs[-50:][::-1]
        st.dataframe(display_logs)
    else:
        st.info('No logs available yet. Trigger analysis to generate the first signal.')


if __name__ == '__main__':
    main()
