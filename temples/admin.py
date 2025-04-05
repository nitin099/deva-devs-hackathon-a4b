from django.contrib import admin
from .models import User, Temple, UserTempleCheckin, Reels, ReelsLike, Location


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')


@admin.register(Temple)
class TempleAdmin(admin.ModelAdmin):
    list_display = ('srm', 'chadhava', 'puja', 'yatra', 'lat', 'lng', 'rating', 'checkin_count', 'created_at')
    list_filter = ('srm', 'chadhava', 'puja', 'yatra', 'created_at')
    search_fields = ('srm',)
    ordering = ('-created_at',)


@admin.register(UserTempleCheckin)
class UserTempleCheckinAdmin(admin.ModelAdmin):
    list_display = ('user', 'temple', 'checkin_time', 'created_at')
    list_filter = ('checkin_time', 'created_at')
    search_fields = ('user__name', 'temple__srm')
    ordering = ('-checkin_time',)


@admin.register(Reels)
class ReelsAdmin(admin.ModelAdmin):
    list_display = ('user', 'temple', 'video_url', 'thumbnail', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__name', 'temple__srm')
    ordering = ('-created_at',)


@admin.register(ReelsLike)
class ReelsLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'reel', 'like', 'created_at')
    list_filter = ('like', 'created_at')
    search_fields = ('user__name', 'reel__user__name')
    ordering = ('-created_at',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'lat', 'lng', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__name',)
    ordering = ('-created_at',)
