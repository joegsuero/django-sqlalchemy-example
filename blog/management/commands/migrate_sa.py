"""
Management command: migrate_sa
Wraps Alembic commands as Django management commands.

Usage:
    python manage.py migrate_sa upgrade head
    python manage.py migrate_sa downgrade -1
    python manage.py migrate_sa current
    python manage.py migrate_sa history
    python manage.py migrate_sa revision --autogenerate -m "add index"
"""
import subprocess
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run Alembic migration commands"

    def add_arguments(self, parser):
        parser.add_argument(
            "alembic_args",
            nargs="...",
            help="Arguments to pass to alembic",
        )

    def handle(self, *args, **options):
        # Get all arguments after the command name
        # sys.argv contains: ['manage.py', 'migrate_sa', 'revision', '--autogenerate', ...]
        # We need to extract everything after 'migrate_sa'
        try:
            idx = sys.argv.index("migrate_sa")
            alembic_args = sys.argv[idx + 1 :]
        except ValueError:
            alembic_args = options.get("alembic_args", []) or []

        cmd = ["alembic"] + alembic_args

        self.stdout.write(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)

        if result.returncode != 0:
            self.stderr.write(self.style.ERROR("Alembic command failed."))
            sys.exit(result.returncode)
        else:
            self.stdout.write(self.style.SUCCESS("Done."))
