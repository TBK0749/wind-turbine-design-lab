"""Generate the Markdown model validation report."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    """Generate docs/model_validation_report.md from benchmark data."""

    from windlab.validation import load_benchmark_cases, render_validation_report

    cases = load_benchmark_cases(ROOT / "data/validation_benchmarks.json")
    report = render_validation_report(cases)
    (ROOT / "docs/model_validation_report.md").write_text(report)


if __name__ == "__main__":
    main()
