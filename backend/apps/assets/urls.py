from rest_framework.routers import DefaultRouter

from apps.assets.views import AssetAssignmentViewSet, AssetViewSet

router = DefaultRouter()
router.register(r"assets", AssetViewSet, basename="asset")
router.register(r"assignments", AssetAssignmentViewSet, basename="assignment")

urlpatterns = router.urls
