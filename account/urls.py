from django.urls import path
from .views import (RegisterView,
                    SearchMap
                    )
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name="sign_up"),
    path('api/login/verify/', TokenVerifyView.as_view(), name="token_verify"),
    path('api/map_search', SearchMap.as_view(), name="search_map"),
]