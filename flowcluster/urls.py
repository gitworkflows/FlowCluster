from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from rest_framework_extensions.routers import ExtendedDefaultRouter
from flowcluster.api.instance import InstanceViewset
from flowcluster.api.cluster import ClusterViewset
from flowcluster.api.backups import BackupViewset, ScheduledBackupViewset
from flowcluster.api.analyze import AnalyzeViewset
from flowcluster.api.async_migration import AsyncMigrationsViewset
from flowcluster.views import healthz
from flowcluster.api.saved_queries import SavedQueryViewset


class DefaultRouterPlusPlus(ExtendedDefaultRouter):
    """DefaultRouter with optional trailing slash and drf-extensions nesting."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = r"/?"


router = DefaultRouterPlusPlus()
router.register(r"api/instance", InstanceViewset, basename="instance")
router.register(r"api/clusters", ClusterViewset, basename="cluster")
router.register(r"api/backups", BackupViewset, basename="backup")
router.register(r"api/scheduled_backups", ScheduledBackupViewset, basename="scheduled_backup")
router.register(r"api/analyze", AnalyzeViewset, basename="analyze")
router.register(r"api/async_migrations", AsyncMigrationsViewset, basename="async_migrations")
router.register(r"api/saved_queries", SavedQueryViewset, basename="saved_queries")
urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz, name="healthz"),
    path("logout", auth_views.LogoutView.as_view()),
    *router.urls,
]
