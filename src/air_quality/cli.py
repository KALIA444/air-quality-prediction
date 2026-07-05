"""Point d'entrée en ligne de commande du pipeline.

Exposé comme script console ``air-quality`` (voir pyproject) et réexporté par
``scripts/run.py`` pour l'usage ``python scripts/run.py ...``.
"""
from __future__ import annotations

import argparse

from . import config
from .data import build_dataset, save_processed
from .evaluate import run as evaluate_run
from .modeling import train_and_evaluate


def cmd_build_target(_):
    df = build_dataset()
    save_processed(df)
    print(f"Écrit {config.PROCESSED_CSV} ({len(df)} lignes)")
    print("\nRésumé de l'AQI :")
    print(df[config.TARGET].describe().round(2).to_string())
    print("\nDécompte des polluants dominants :")
    print(df["DominantPollutant"].value_counts().to_string())


def cmd_train(_):
    results, best = train_and_evaluate()
    print(f"{len(results)} modèles entraînés. Meilleur selon le R² de test : {best}")
    for name, m in results.items():
        print(f"  {name:18s} test_r2={m['test_r2']:.4f} test_rmse={m['test_rmse']:.3f}")


def cmd_evaluate(_):
    evaluate_run()


def cmd_all(args):
    cmd_train(args)
    cmd_evaluate(args)


def cmd_monitor(args):
    # Importé paresseusement : Evidently est une dépendance optionnelle (monitoring).
    from .monitoring import run_drift_report

    summary = run_drift_report(perturb=args.perturb)
    status = "ALERTE" if summary["alert"] else "ok"
    print(f"Rapport de dérive [{status}] — part dérivée "
          f"{summary['drift_share']:.2f} (seuil {summary['threshold']:.2f})")
    print(f"  HTML:  {summary['html_path']}")
    print(f"  JSON:  {summary['json_path']}")
    if summary["alert"]:
        print(f"  ALERTE : {summary['alert_path']}")
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="air-quality", description="Pipeline AQI de qualité de l'air")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-target").set_defaults(func=cmd_build_target)
    sub.add_parser("train").set_defaults(func=cmd_train)
    sub.add_parser("evaluate").set_defaults(func=cmd_evaluate)
    sub.add_parser("all").set_defaults(func=cmd_all)
    mon = sub.add_parser("monitor")
    mon.add_argument("--perturb", action="store_true",
                     help="injecter une dérive synthétique (démo / test d'alerte)")
    mon.set_defaults(func=cmd_monitor)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
