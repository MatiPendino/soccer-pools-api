from rest_framework.routers import DefaultRouter
from .views import PrizeViewSet

router = DefaultRouter()
router.register(r'prize', PrizeViewSet)

urlpatterns = router.urls