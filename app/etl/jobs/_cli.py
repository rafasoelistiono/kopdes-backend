import argparse

from app.services import etl_service


def period_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", default=None)
    return parser


def run_job(job: str):
    args = period_parser().parse_args()
    print(etl_service.refresh(job, args.period))


def run_all():
    args = period_parser().parse_args()
    print(etl_service.refresh_all(args.period))
