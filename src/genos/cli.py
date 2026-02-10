"""GenOS CLI - Migration tool entry point."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click
import yaml

from genos.adapters.detector import detect_mud_type
from genos.compiler.compiler import GenosCompiler
from genos.uir.validator import validate_uir


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def main(verbose: bool) -> None:
    """GenOS Migration Tool - Transform MUD worlds to modern platforms."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


@main.command()
@click.argument("source", type=click.Path(exists=True))
def analyze(source: str) -> None:
    """Analyze a MUD source directory and report migration feasibility."""
    adapter = detect_mud_type(source)
    if not adapter:
        click.echo(f"Error: Could not detect MUD type at {source}", err=True)
        sys.exit(1)

    click.echo(f"Detected: {adapter.__class__.__name__}")
    click.echo()

    report = adapter.analyze()
    click.echo(report.summary())

    if report.warnings:
        click.echo()
        click.echo("Warnings:")
        for w in report.warnings:
            click.echo(f"  - {w}")


@main.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Output directory for generated files.",
)
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="UIR output format.",
)
def migrate(source: str, output: str | None, output_format: str) -> None:
    """Parse a MUD source and generate GenOS project artifacts."""
    adapter = detect_mud_type(source)
    if not adapter:
        click.echo(f"Error: Could not detect MUD type at {source}", err=True)
        sys.exit(1)

    click.echo(f"Detected: {adapter.__class__.__name__}")
    click.echo("Parsing...")

    uir = adapter.parse()

    # Validate
    validation = validate_uir(uir)
    if not validation.valid:
        click.echo("Validation errors:")
        for e in validation.errors:
            click.echo(f"  ERROR: {e}")
    if validation.warnings:
        click.echo(f"Validation warnings: {len(validation.warnings)}")

    stats = uir.migration_stats
    click.echo(
        f"Parsed: {stats.total_rooms} rooms, {stats.total_items} items, "
        f"{stats.total_monsters} mobs, {stats.total_zones} zones, "
        f"{stats.total_shops} shops, {stats.total_triggers} triggers, "
        f"{stats.total_quests} quests"
    )

    if stats.warnings:
        click.echo(f"Parse warnings: {len(stats.warnings)}")

    # Output directory
    if output is None:
        output = str(Path(source).name + "-genos-output")
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write UIR
    uir_data = _uir_to_dict(uir)
    if output_format == "yaml":
        uir_path = output_dir / "uir.yaml"
        with open(uir_path, "w") as f:
            yaml.dump(uir_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    else:
        uir_path = output_dir / "uir.json"
        with open(uir_path, "w") as f:
            json.dump(uir_data, f, indent=2, ensure_ascii=False)

    click.echo(f"UIR written to: {uir_path}")

    # Compile
    compiler = GenosCompiler(uir, output_dir)
    generated = compiler.compile()

    click.echo(f"\nGenerated {len(generated)} files:")
    for fpath, desc in generated.items():
        click.echo(f"  {fpath}: {desc}")

    click.echo("\nMigration complete!")


def _uir_to_dict(uir) -> dict:
    """Convert UIR dataclass tree to a plain dict for serialization."""
    import dataclasses

    def _convert(obj):
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            result = {}
            for f in dataclasses.fields(obj):
                value = getattr(obj, f.name)
                result[f.name] = _convert(value)
            return result
        elif isinstance(obj, list):
            return [_convert(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, tuple):
            return list(obj)
        else:
            return obj

    return _convert(uir)


if __name__ == "__main__":
    main()
