from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import apis


urlpatterns = [ 
    # User
    path('create-user', apis.CreateUser.as_view()),

    # Nearby
    path('nearby-users', apis.ListNearbyUsers.as_view()),

    path('nearby-temples', apis.ListNearbyTemples.as_view()),

    # Temples
    # path('temples/<int:pk>', apis.GetTemple.as_view()),
    path('temples/<int:pk>/check-ins', apis.ListCreateTempleCheckIn.as_view()),
    path('temples/<int:temple_id>/check-ins/<str:user_id>', apis.GetUserTempleCheckIn.as_view()),
    # path('temples/<int:pk>/yatra-complete', apis.MarkYatraComplete.as_view()),
    
    # Reels
    path('temples/<int:pk>/reels', apis.ListTempleReels.as_view()),
    # path('user/reels', apis.GetUserReels.as_view()),
    # path('reels/<int:pk>/like', apis.LikeReel.as_view()),
    
    # Location
    path('locations', apis.LocationList.as_view()),
    path('locations/<int:pk>/', apis.LocationDetail.as_view()),

]
