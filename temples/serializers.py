from rest_framework import serializers
from .models import User, Location, Temple, UserTempleCheckin, Reels


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


class TempleSerializer(serializers.ModelSerializer):
    distance = serializers.FloatField(required=False)
    raw_data = serializers.SerializerMethodField()

    class Meta:
        model = Temple
        fields = ('id', 'name', 'srm', 'chadhava', 'puja', 'yatra', 
                 'lat', 'lng', 'rating', 'checkin_count', 'distance',
                 'created_at', 'updated_at', 'raw_data')
        read_only_fields = ('created_at', 'updated_at')

    def get_raw_data(self, obj):
        raw_data = obj.raw_data
        if raw_data is None:
            return []
        if isinstance(raw_data, dict):
            return [raw_data]
        if isinstance(raw_data, list):
            return raw_data
        return []


class UserTempleCheckinSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    temple = serializers.PrimaryKeyRelatedField(queryset=Temple.objects.all())
    user_name = serializers.CharField(source='user.name', read_only=True)
    temple_name = serializers.CharField(source='temple.name', read_only=True)
    temple_raw_data = serializers.SerializerMethodField()

    class Meta:
        model = UserTempleCheckin
        fields = ('id', 'user', 'user_name', 'temple', 'temple_name', 'checkin_time', 'created_at', 'updated_at', 'temple_raw_data')
        read_only_fields = ('created_at', 'updated_at', 'checkin_time')

    def get_temple_raw_data(self, obj):
        raw_data = obj.temple.raw_data
        if raw_data is None:
            return []
        if isinstance(raw_data, dict):
            return [raw_data]
        if isinstance(raw_data, list):
            return raw_data
        return []


class ReelsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    temple_name = serializers.CharField(source='temple.name', read_only=True)
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = Reels
        fields = ('id', 'user', 'user_name', 'temple', 'temple_name', 'video_url', 'thumbnail', 'like_count', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    def get_like_count(self, obj):
        return obj.reelslike_set.filter(like=True).count() 