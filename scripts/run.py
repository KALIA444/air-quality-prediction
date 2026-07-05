#!/usr/bin/env python
"""Wrapper léger pour exécuter le pipeline via ``python scripts/run.py <command>``.

Avec le paquet installé (``pip install -e .``), l'import est direct ; le
correctif ``sys.path`` ci-dessous n'aide qu'en cas d'exécution depuis un checkout brut.

Commandes : build-target | train | evaluate | all | monitor
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from air_quality.cli import main
except ModuleNotFoundError:  # non installé — repli sur la disposition src/
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from air_quality.cli import main

if __name__ == "__main__":
    main()
