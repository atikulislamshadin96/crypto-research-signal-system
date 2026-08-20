from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from collections import deque
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path
from typing import Iterator

from crypto_signal_system.phase4_protocol import load_verified_phase4_protocol

ROOT = Path('/home/ubuntu/crypto-signal-system')
FLOW_MANIFEST_ROOT = ROOT / 'data/flow/bybit_spot_trades/manifests'
L2_MANIFEST_ROOT = ROOT / 'data/l2/manifests'
OUT = ROOT / 'artifacts/phase4_order_flow_overlay/protocol_validation_v1.json'
EXPECTED_FINGERPRINT = '86a8608328a77a9d60cfc95570ac05cf178207995f9243906f7c081d38f47cfd'
START_MS = 1746057600000
END_MS = 1753833600000
WINDOW_MS = 1000
SYMBOLS = ('BTCUSDT', 'ETHUSDT')
START = date(2025, 5, 1)
END = date(2025, 7, 29)
CTS_RE = re.compile(rb'"cts"\s*:\s*(\d+)')


def day_strings() -> list[str]:
    return [(START + timedelta(days=i)).isoformat() for i in range((END - START).days + 1)]


def iter_flow(path: Path) -> Iterator[tuple[int, int, Decimal, Decimal, Decimal]]:
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ['id', 'timestamp', 'price', 'volume', 'side', 'rpi']:
            raise ValueError(f'flow_header_mismatch:{path}:{reader.fieldnames}')
        prior_id: int | None = None
        prior_ts: int | None = None
        for row in reader:
            trade_id = int(row['id'])
            timestamp = int(row['timestamp'])
            price = Decimal(row['price'])
            volume = Decimal(row['volume'])
            side = row['side']
            if prior_id is not None and trade_id != prior_id + 1:
                raise ValueError(f'trade_id_gap:{path}:{prior_id}:{trade_id}')
            if prior_ts is not None and timestamp < prior_ts:
                raise ValueError(f'flow_timestamp_out_of_order:{path}:{prior_ts}:{timestamp}')
            if side not in {'buy', 'sell'} or price <= 0 or volume < 0:
                raise ValueError(f'invalid_flow_value:{path}:{trade_id}')
            notional = price * volume
            signed = notional if side == 'buy' else -notional
            yield timestamp, trade_id, signed, (notional if side == 'buy' else Decimal(0)), (notional if side == 'sell' else Decimal(0))
            prior_id = trade_id
            prior_ts = timestamp


def iter_all_flow(symbol: str) -> Iterator[tuple[int, int, Decimal, Decimal, Decimal]]:
    for day in day_strings():
        manifest = json.loads((FLOW_MANIFEST_ROOT / symbol / f'{day}.json').read_text())
        if manifest.get('status') != 'PASS' or not manifest.get('research_usable'):
            raise ValueError(f'flow_manifest_not_pass:{symbol}:{day}')
        path = ROOT / manifest['archive_path']
        if not path.exists():
            raise ValueError(f'missing_flow_archive:{path}')
        yield from iter_flow(path)


def iter_l2_timestamps(symbol: str) -> Iterator[tuple[str, int, int]]:
    for day in day_strings():
        manifest = json.loads((L2_MANIFEST_ROOT / symbol / f'{day}.json').read_text())
        if manifest.get('status') != 'PASS' or not manifest.get('research_usable'):
            raise ValueError(f'l2_manifest_not_pass:{symbol}:{day}')
        path = ROOT / manifest['input_files'][0]['path']
        if not path.exists():
            raise ValueError(f'missing_l2_archive:{path}')
        with zipfile.ZipFile(path, 'r') as archive:
            members = [info for info in archive.infolist() if not info.is_dir()]
            if len(members) != 1:
                raise ValueError(f'l2_member_count:{path}:{len(members)}')
            with archive.open(members[0], 'r') as stream:
                for index, line in enumerate(stream, start=1):
                    match = CTS_RE.search(line)
                    if match is None:
                        raise ValueError(f'missing_cts:{path}:{index}')
                    yield day, index, int(match.group(1))


def dec(value: Decimal) -> str:
    if value == 0:
        return '0'
    return format(value, 'f')


def validate_symbol(symbol: str) -> dict[str, object]:
    flow = iter_all_flow(symbol)
    next_flow = next(flow, None)
    window: deque[tuple[int, int, Decimal, Decimal, Decimal]] = deque()
    signed = Decimal(0)
    buy = Decimal(0)
    sell = Decimal(0)
    prior_l2: int | None = None
    l2_count = 0
    valid_count = 0
    empty_count = 0
    boundary_count = 0
    digest = hashlib.sha256()
    first_valid: tuple[str, int, int] | None = None
    last_valid: tuple[str, int, int] | None = None
    flow_count = 0
    with localcontext() as context:
        context.prec = 50
        context.rounding = ROUND_HALF_EVEN
        for day, index, timestamp in iter_l2_timestamps(symbol):
            l2_count += 1
            if prior_l2 is not None and timestamp < prior_l2:
                raise ValueError(f'l2_timestamp_out_of_order:{symbol}:{prior_l2}:{timestamp}')
            prior_l2 = timestamp
            while next_flow is not None and next_flow[0] < timestamp:
                window.append(next_flow)
                signed += next_flow[2]
                buy += next_flow[3]
                sell += next_flow[4]
                flow_count += 1
                next_flow = next(flow, None)
            cutoff = timestamp - WINDOW_MS
            while window and window[0][0] < cutoff:
                old = window.popleft()
                signed -= old[2]
                buy -= old[3]
                sell -= old[4]
            if timestamp < START_MS + WINDOW_MS or timestamp > END_MS:
                status = 'UNAVAILABLE_BOUNDARY'
                boundary_count += 1
                value = 'null'
                buy_value = 'null'
                sell_value = 'null'
                trade_count = 0
            elif not window:
                status = 'EMPTY'
                empty_count += 1
                value = 'null'
                buy_value = 'null'
                sell_value = 'null'
                trade_count = 0
            else:
                status = 'VALID'
                valid_count += 1
                value = dec(signed)
                buy_value = dec(buy)
                sell_value = dec(sell)
                trade_count = len(window)
                if first_valid is None:
                    first_valid = (day, index, timestamp)
                last_valid = (day, index, timestamp)
            record = f'{symbol}|{day}|{index}|{timestamp}|{status}|{value}|{buy_value}|{sell_value}|{trade_count}\n'.encode()
            digest.update(record)
    if next_flow is not None:
        # Remaining trades are outside the final L2 timestamp range but were still read only as needed.
        pass
    return {
        'symbol': symbol,
        'flow_trade_count_consumed_through_last_l2': flow_count,
        'l2_timestamp_count': l2_count,
        'valid_flow_alignment_count': valid_count,
        'empty_flow_window_count': empty_count,
        'boundary_unavailable_count': boundary_count,
        'first_valid_alignment': first_valid,
        'last_valid_alignment': last_valid,
        'alignment_record_sha256': digest.hexdigest(),
    }


def main() -> None:
    protocol = load_verified_phase4_protocol(expected_fingerprint=EXPECTED_FINGERPRINT)
    results = [validate_symbol(symbol) for symbol in SYMBOLS]
    result = {
        'validation_version': 'phase4_flow_protocol_validation_v1',
        'protocol_version': protocol['protocol_version'],
        'protocol_fingerprint_sha256': EXPECTED_FINGERPRINT,
        'validation_scope': 'protocol generation and timestamp alignment only; no Phase 4 outcome statistics',
        'source': 'Bybit official public spot trade archives and accepted Bybit historical L2 archives',
        'window': {'start': '2025-05-01T00:00:00.000Z', 'end_exclusive': '2025-07-30T00:00:00.000Z', 'aggregation_window_ms': WINDOW_MS},
        'symbols': results,
        'phase4_outcome_statistics_computed': False,
        'bootstrap_computed': False,
        'fdr_computed': False,
        'bonferroni_computed': False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
