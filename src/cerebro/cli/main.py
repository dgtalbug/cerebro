"""Cerebro command-line interface.

Thin wrappers over the extraction + storage library. Every command body
runs inside a process-boundary handler that catches the `CerebroError`
taxonomy, logs the failure with structured context, and exits with a
mapped non-zero code — the only place broad-ish catches are allowed
(library code uses specific exceptions everywhere else).
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from cerebro.exceptions import (
    ArtifactNotFoundError,
    CerebroError,
    CorruptArtifactError,
    UnsupportedFrameworkError,
    UnsupportedObjectiveError,
)
from cerebro.extractors import get_extractor
from cerebro.logging import configure_logging, get_logger
from cerebro.schema.v1 import CerebroArtifact
from cerebro.storage import read_artifact, write_artifact

configure_logging(level=logging.INFO)
_LOG = get_logger(__name__)


app = typer.Typer(
    name="cerebro",
    help=(
        "Model introspection platform — extract canonical artifacts from "
        "trained models, validate them, and serve them."
    ),
    no_args_is_help=True,
)


# Exit codes are stable so CI scripts can branch on them. Generic CerebroError
# falls back to 1. Non-CerebroError exceptions propagate uncaught so genuine
# bugs surface with a full traceback (loud-fail on actual defects).
_EXIT_CODES: dict[type[CerebroError], int] = {
    ArtifactNotFoundError: 2,
    CorruptArtifactError: 3,
    UnsupportedObjectiveError: 4,
    UnsupportedFrameworkError: 4,
}


def _exit_code_for(error: CerebroError) -> int:
    for exc_class, code in _EXIT_CODES.items():
        if isinstance(error, exc_class):
            return code
    return 1


def _handle_cerebro_errors[**P](
    func: Callable[P, None],
) -> Callable[P, None]:
    """Process-boundary handler — the only place broad-ish catches live.

    PEP 695 `[**P]` preserves the decorated function's typed signature so
    typer can introspect command parameters through the wrapper, and
    mypy can keep checking call sites.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            return func(*args, **kwargs)
        except CerebroError as error:
            _LOG.error(
                "cli.failed",
                command=func.__name__,
                error_class=type(error).__name__,
                **{key: str(value) for key, value in error.context.items()},
            )
            typer.echo(f"error: {type(error).__name__}: {error.message}", err=True)
            raise typer.Exit(code=_exit_code_for(error)) from error

    return wrapper


def _format_summary(artifact: CerebroArtifact) -> str:
    """Single-line, key=value summary suitable for stdout / scripts."""
    return (
        f"framework={artifact.source.framework} "
        f"objective={artifact.model.objective} "
        f"trees={len(artifact.trees)} "
        f"features={len(artifact.model.feature_schema.names)}"
    )


@app.command()
@_handle_cerebro_errors
def extract(
    model: Annotated[
        Path,
        typer.Argument(
            help="Path to the framework-native model file (e.g. a LightGBM .txt).",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Where to write the .cerebro.json artifact (gzip-encoded).",
        ),
    ],
    samples: Annotated[
        Path | None,
        typer.Option(
            "--samples",
            help="CSV/Parquet/JSON samples for SHAP and permutation importance.",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    labels: Annotated[
        Path | None,
        typer.Option(
            "--labels",
            help="Single-column CSV with ground-truth labels aligned to --samples.",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    eval_samples: Annotated[
        Path | None,
        typer.Option(
            "--eval-samples",
            help="Held-out feature samples for evaluation metrics (CSV/Parquet/JSON).",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    eval_labels: Annotated[
        Path | None,
        typer.Option(
            "--eval-labels",
            help="Ground-truth labels aligned to --eval-samples.",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    training_table: Annotated[
        Path | None,
        typer.Option(
            "--training-table",
            help="Full training table (CSV/Parquet/JSON) for data profiling.",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
) -> None:
    """Extract a canonical artifact from a trained model.

    When --samples and --labels are provided, also computes SHAP explanations
    and permutation importance. When --eval-samples and --eval-labels are
    provided, computes objective-aware evaluation metrics. When --training-table
    is provided, computes a data profile of the training distribution.
    """
    import numpy as np

    np_samples: np.ndarray | None = None
    np_labels: np.ndarray | None = None
    np_eval_samples: np.ndarray | None = None
    np_eval_labels: np.ndarray | None = None

    if samples is not None or labels is not None:
        if samples is None or labels is None:
            typer.echo("error: --samples and --labels must be used together", err=True)
            raise typer.Exit(code=1)
        from cerebro.data.loader import load_table
        with load_table(samples) as h:
            np_samples = h.relation.fetchnumpy()
            np_samples = np.column_stack(list(np_samples.values()))
        with load_table(labels) as h:
            cols = h.relation.fetchnumpy()
            np_labels = next(iter(cols.values()))

    if eval_samples is not None or eval_labels is not None:
        if eval_samples is None or eval_labels is None:
            typer.echo("error: --eval-samples and --eval-labels required together", err=True)  # noqa: E501
            raise typer.Exit(code=1)
        from cerebro.data.loader import load_table
        with load_table(eval_samples) as h:
            np_eval_samples = np.column_stack(list(h.relation.fetchnumpy().values()))
        with load_table(eval_labels) as h:
            np_eval_labels = next(iter(h.relation.fetchnumpy().values()))

    extractor = get_extractor(model)
    artifact = extractor.extract(
        model,
        samples=np_samples,
        labels=np_labels,
        eval_samples=np_eval_samples,
        eval_labels=np_eval_labels,
        training_table_path=training_table,
    )
    write_artifact(artifact, output)
    typer.echo(f"extracted: {_format_summary(artifact)} -> {output}")


@app.command()
@_handle_cerebro_errors
def validate(
    artifact: Annotated[
        Path,
        typer.Argument(
            help="Path to a .cerebro.json artifact to validate.",
        ),
    ],
) -> None:
    """Read and validate a canonical artifact end to end."""
    loaded = read_artifact(artifact)
    typer.echo(f"valid: schema={loaded.schema_version} {_format_summary(loaded)}")


if __name__ == "__main__":
    app()
