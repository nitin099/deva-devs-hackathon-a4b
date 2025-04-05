from rest_framework import serializers
from .models import User, Location


class UserSerializer(serializers.ModelSerializer):
    last_lat = serializers.SerializerMethodField()
    last_lng = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('user_id', 'name', 'image', 'last_lat', 'last_lng', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    def get_last_lat(self, obj):
        try:
            return obj.location_set.order_by('-created_at').first().lat
        except:
            return None

    def get_last_lng(self, obj):
        try:
            return obj.location_set.order_by('-created_at').first().lng
        except:
            return None


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'name', 'image')
        extra_kwargs = {
            'name': {'required': True},
            'user_id': {'required': True}
        }


class LocationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Location
        fields = ('id', 'user', 'user_name', 'lat', 'lng', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at') 