"""CLI: enter patient + context + VI / AHW / TOD (mm); print ``PatientMeasurementRecord`` as JSON."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from numic.api.schemas.measurement import ManualMeasurementRequest, PatientInfo, MeasurementContext
from numic.measurement.manual_entry import patient_measurement_record_from_manual


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Build a full patient measurement record from operator-entered calipers (mm)."
    )
    p.add_argument("--patient-ref", required=True, help="MRN / episode / patient external ref")
    p.add_argument(
        "--measured-at",
        required=True,
        help="ISO-8601 datetime (e.g. 2025-04-14T14:30:00 or 2025-04-14 14:30:00)",
    )
    p.add_argument("--given-name", default=None)
    p.add_argument("--family-name", default=None)
    p.add_argument("--dob", default=None, help="YYYY-MM-DD")
    p.add_argument("--ga-weeks", type=float, default=None, dest="ga_weeks")
    p.add_argument("--measured-by", default=None)
    p.add_argument("--clinical-notes", default=None)
    p.add_argument("--vi", type=float, required=True, help="VI (mm) per your protocol")
    p.add_argument("--ahw", type=float, required=True, help="AHW (mm)")
    p.add_argument("--tod", type=float, required=True, help="TOD (mm)")
    p.add_argument("--vi-percentile", type=float, default=None, dest="vi_percentile")
    p.add_argument("--vi-p97-ref-mm", type=float, default=None, dest="vi_p97_reference_mm")
    p.add_argument(
        "--source",
        choices=("gui", "cli", "other"),
        default="cli",
        dest="entry_source",
    )
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = p.parse_args(argv)

    t = args.measured_at.strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    if " " in t and "T" not in t:
        t = t.replace(" ", "T", 1)
    measured_at = datetime.fromisoformat(t)

    from datetime import date as date_cls

    dob = date_cls.fromisoformat(args.dob) if args.dob else None

    req = ManualMeasurementRequest(
        patient=PatientInfo(
            external_ref=args.patient_ref,
            given_name=args.given_name,
            family_name=args.family_name,
            date_of_birth=dob,
            gestational_age_weeks=args.ga_weeks,
        ),
        context=MeasurementContext(
            measured_at=measured_at,
            measured_by=args.measured_by,
            clinical_notes=args.clinical_notes,
        ),
        vi_mm=args.vi,
        ahw_mm=args.ahw,
        tod_mm=args.tod,
        vi_percentile=args.vi_percentile,
        vi_p97_reference_mm=args.vi_p97_reference_mm,
        entry_source=args.entry_source,
    )
    out = patient_measurement_record_from_manual(req)
    data = json.loads(out.model_dump_json())
    if args.pretty:
        json.dump(data, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        json.dump(data, sys.stdout)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
