from rest_framework import serializers
from .models import User, Location, Temple, UserTempleCheckin


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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('raw_data') and isinstance(data['raw_data'], dict):
            data['raw_data'] = None
        return data

    class Meta:
        model = Temple
        fields = ('id', 'name', 'srm', 'chadhava', 'puja', 'yatra', 
                 'lat', 'lng', 'rating', 'checkin_count', 'distance',
                 'created_at', 'updated_at', 'raw_data')
        read_only_fields = ('created_at', 'updated_at')


class UserTempleCheckinSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    temple = serializers.PrimaryKeyRelatedField(queryset=Temple.objects.all())
    user_name = serializers.CharField(source='user.name', read_only=True)
    temple_name = serializers.CharField(source='temple.name', read_only=True)

    class Meta:
        model = UserTempleCheckin
        fields = ('id', 'user', 'user_name', 'temple', 'temple_name', 'checkin_time', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at', 'checkin_time') 