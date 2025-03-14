import os
from datetime import datetime

import structlog
from croniter import croniter
from celery import Celery
from django_structlog.celery.steps import DjangoStructLogInitStep
from django.utils import timezone

logger = structlog.get_logger(__name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flowcluster.settings")

app = Celery("flowcluster")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.steps["worker"].add(DjangoStructLogInitStep)


@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(60.0, schedule_backups.s(), name="schedule backups")


@app.task(track_started=True, ignore_result=False, max_retries=0)
def run_backup(backup_id: str, incremental: bool = False):
    from flowcluster.flowvluster import backups

    logger.info("Running backup", backup_id=backup_id, incremental=incremental)

    backups.run_backup(backup_id, incremental=incremental)


@app.task(track_started=True, ignore_result=False, max_retries=0)
def schedule_backups():
    # Every interval (default 60 seconds), check if any backups need to be run
    # We do this so that if we disable or change the schedule of a backup, it will be picked up within 60 seconds
    # instead of waiting for the next deployment or restart of FlowCluster service
    from flowcluster.models.backup import ScheduledBackup

    logger.info("Checking if scheduled backups need to be run")
    backups = ScheduledBackup.objects.filter(enabled=True)
    now = timezone.now()
    for backup in backups:
        lrt = backup.last_run_time
        if lrt is None:
            lrt = backup.created_at
        nr = croniter(backup.schedule, lrt).get_next(datetime)
        if nr.tzinfo is None:
            nr = timezone.make_aware(nr)

        nir = None
        if backup.incremental_schedule is not None:
            lirt = backup.last_incremental_run_time
            if lirt is None:
                lirt = backup.created_at
            nir = croniter(backup.incremental_schedule, lirt).get_next(datetime)
            if nir.tzinfo is None:
                nir = timezone.make_aware(nir)

        logger.info("Checking backup", backup_id=backup.id, next_run=nr, next_incremental_run=nir, now=now)
        # The idea here is to first check if the base backup needs to be run, and if not, check if the incremental
        # backup needs to be run. This is because incremental backups are only useful if the base backup has been run
        # at least once.
        if nr < now:
            # check if base backup needs to be run and run it
            run_backup.delay(backup.id)
            backup.last_run_time = now
            backup.save()
        elif backup.incremental_schedule is not None and nir < now:
            # check if incremental backup needs to be run and run it
            run_backup.delay(backup.id, incremental=True)
            backup.last_incremental_run_time = now
            backup.save()


@app.task(track_started=True, ignore_result=False, max_retries=0)
def run_async_migration(migration_name: str):
    from flowcluster.async_migrations.runner import start_async_migration
    from flowcluster.models.async_migration import AsyncMigration

    migration = AsyncMigration.objects.get(name=migration_name)
    start_async_migration(migration)
