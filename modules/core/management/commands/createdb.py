# Ref https://github.com/Vacasa/django-db-auto-create/tree/master

import logging

import psycopg2
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help=(
                'Nominates a database to synchronize. Defaults to the "default" '
                "database."
            ),
        )

    def handle(self, *args: tuple, **options: str) -> None:
        selected_database = options["database"]
        database_config = settings.DATABASES[selected_database]

        if not database_config.get("AUTO_CREATE"):
            raise Exception("AUTO_CREATE is set to false in settings for this database")
        self.create_db(selected_database)

    def create_db(self, database):
        database_vendor = connections[database].vendor

        if database_vendor == "postgresql":
            database_config = settings.DATABASES[database]
            try:
                db_name = database_config["NAME"]
                db = psycopg2.connect(
                    dbname="postgres",
                    host=database_config.get("HOST"),
                    user=database_config.get("USER"),
                    password=database_config.get("PASSWORD"),
                )
                db.autocommit = True

                cursor = db.cursor()
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = '{}';".format(db_name)
                )

                if not cursor.fetchone():
                    cursor.execute("CREATE DATABASE {};".format(db_name))

                cursor.close()
                db.close()
                self.stdout.write(
                    "Auto-created database '{}'".format(database_config.get("NAME"))
                )
                return True

            except psycopg2.Error as err:
                self.stderr("Something went wrong: {}".format(err))
