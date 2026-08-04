from __future__ import annotations

import argparse
import json

from app.continual_learning import run_cp3_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the CP3 continual learning simulation.')
    parser.add_argument('--max-rows', type=int, default=None, help='Optional cap for faster local runs.')
    parser.add_argument('--batch-count', type=int, default=4, help='Number of temporal batches to simulate.')
    parser.add_argument('--drift-threshold', type=float, default=0.15, help='Relative MAE increase to flag drift.')
    parser.add_argument('--quality-gate', type=float, default=0.05, help='Minimum holdout improvement required to promote a checkpoint.')
    parser.add_argument('--no-persist', action='store_true', help='Run the simulation without writing model artifacts or version metadata.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_cp3_pipeline(
        max_rows=args.max_rows,
        batch_count=args.batch_count,
        drift_threshold=args.drift_threshold,
        quality_gate=args.quality_gate,
        persist=not args.no_persist,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()