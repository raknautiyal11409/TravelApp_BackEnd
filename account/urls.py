from django.urls import path
from .views import (RegisterView,
                    SearchMap,
                    addBookmarFolder,
                    getBookmarkFoldersOrderedByDate,
                    addBookmark,
                    getFolderContent,
                    addPinLocation,
                    addFavoutriteLocation,
                    getPinLocations,
                    getFavLocations)
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
    path('map_search/', SearchMap.as_view(), name="search_map"),
    path('api/addBookmarFolder/', addBookmarFolder.as_view(), name="add_bFolder"),
    path('api/get_Folder_Names/', getBookmarkFoldersOrderedByDate.as_view(), name="gwt_addedFolders"),
    path('api/add_location_to_folder/', addBookmark.as_view(), name="add_bookmarkLocation"),
    path('api/getLocationsInFolder/', getFolderContent.as_view(), name="getLocationsInFolder"),
    path('api/addPinLocation/', addPinLocation.as_view(), name="addPinLocation"),
    path('api/addFavouriteLocation/', addFavoutriteLocation.as_view(), name="addFavLocation"),
    path('api/getPins/', getPinLocations.as_view(), name="getPins"),
    path('api/getFavs/', getFavLocations.as_view(), name="getFavs"),
]