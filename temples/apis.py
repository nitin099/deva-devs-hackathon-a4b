from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.db.models import F, Max, Q, ExpressionWrapper, FloatField, Count
from django.db.models.functions import Radians, Sin, Cos, Sqrt
from django.utils import timezone
from datetime import timedelta
from math import atan2
from math import radians, sin, cos, sqrt, atan2
from .models import User, Location, Temple, UserTempleCheckin, Reels
from .serializers import UserSerializer, UserCreateSerializer, LocationSerializer, TempleSerializer, UserTempleCheckinSerializer, ReelsSerializer
from django.core.cache import cache
from django.conf import settings
import hashlib
import json


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    return distance


class CreateUser(APIView):
    def post(self, request):
        try:
            # First check if user_id is provided
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Try to get existing user or create new one
            user, created = User.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'name': request.data.get('name', ''),
                    'image': request.data.get('image')
                }
            )

            # If user exists, update their data
            if not created:
                serializer = UserCreateSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    user = serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListNearbyUsers(APIView):
    def get(self, request):
        try:
            # Get parameters from request
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            radius = float(request.query_params.get('radius', 2))  # Default 2km radius
            
            # Convert radius to degrees (approximate)
            # 1 degree is approximately 111km at the equator
            radius_degrees = radius / 111.0
            
            # Get distinct users with their latest location within radius
            locations = Location.objects.filter(
                lat__range=(lat - radius_degrees, lat + radius_degrees),
                lng__range=(lng - radius_degrees, lng + radius_degrees)
            ).values('user').annotate(
                latest_created=Max('created_at')
            ).filter(
                latest_created__isnull=False
            )
            
            # Get the actual location records with coordinates
            latest_locations = Location.objects.filter(
                created_at__in=[loc['latest_created'] for loc in locations]
            ).select_related('user')
            
            nearby_users = []
            
            # Calculate exact distances and filter users within radius
            for location in latest_locations:
                distance = calculate_distance(
                    lat, lng,
                    location.lat,
                    location.lng
                )
                
                if distance <= radius:
                    user_data = UserSerializer(location.user).data
                    user_data['distance'] = round(distance, 2)  # Round to 2 decimal places
                    nearby_users.append(user_data)
            
            # Sort by distance
            nearby_users.sort(key=lambda x: x['distance'])
            
            return Response({"data": {
                'count': len(nearby_users),
                'results': nearby_users
            }}, status=status.HTTP_200_OK)
            
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid parameters. Please provide valid lat, lng, and radius values.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LocationList(APIView):

    def get(self, request):
        """
        List all locations or filter by user_id
        """
        try:
            queryset = Location.objects.all()
            user_id = request.query_params.get('user_id', None)
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            queryset = queryset.order_by('-created_at')
            serializer = LocationSerializer(queryset, many=True)
            
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Create a new location
        """
        try:
            serializer = LocationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LocationDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Location, pk=pk)

    def get(self, request, pk):
        """
        Retrieve a single location
        """
        try:
            location = self.get_object(pk)
            serializer = LocationSerializer(location)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        """
        Update a location
        """
        try:
            location = self.get_object(pk)
            serializer = LocationSerializer(location, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """
        Delete a location
        """
        try:
            location = self.get_object(pk)
            location.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListNearbyTemples(APIView):
    def _generate_cache_key(self, lat, lng, radius):
        """
        Generate a unique cache key based on the input parameters.
        Round coordinates to 4 decimal places to ensure nearby requests hit the same cache.
        """
        # Round coordinates to reduce cache key variations for very close coordinates
        rounded_lat = round(lat, 4)
        rounded_lng = round(lng, 4)
        rounded_radius = round(radius, 1)
        
        # Create a string with the parameters
        params_str = f"nearby_temples:{rounded_lat}:{rounded_lng}:{rounded_radius}"
        
        # Create a hash of the parameters for a shorter key
        return hashlib.md5(params_str.encode()).hexdigest()

    def get(self, request):
        """
        List temples within a specified radius of given coordinates.
        Query parameters:
        - lat: latitude (required)
        - lng: longitude (required)
        - radius: radius in kilometers (optional, default=5)
        """
        try:
            # Get parameters from request
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            radius = float(request.query_params.get('radius', 5))  # Default 5km radius

            # Generate cache key
            cache_key = self._generate_cache_key(lat, lng, radius)

            # Try to get data from cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response({"data": {"temples":json.loads(cached_data)}})

            # Convert radius to degrees (approximate)
            # 1 degree is approximately 111km at the equator
            radius_degrees = radius / 111.0
            
            # Get temples within the bounding box
            temples = Temple.objects.filter(
                lat__range=(lat - radius_degrees, lat + radius_degrees),
                lng__range=(lng - radius_degrees, lng + radius_degrees)
            )
            
            nearby_temples = []
            
            # Calculate exact distances and filter temples within radius
            for temple in temples:
                distance = calculate_distance(
                    lat, lng,
                    temple.lat,
                    temple.lng
                )
                
                if distance <= radius:
                    temple_data = TempleSerializer(temple).data
                    temple_data['distance'] = round(distance, 2)  # Round to 2 decimal places
                    nearby_temples.append(temple_data)
            
            # Sort by distance
            nearby_temples.sort(key=lambda x: x['distance'])

            # Cache the results
            cache_ttl = getattr(settings, 'NEARBY_TEMPLES_CACHE_TTL', 300)  # Default 5 minutes
            cache.set(cache_key, json.dumps(nearby_temples), cache_ttl)
            
            return Response({"data": {"count": len(nearby_temples),"temples": nearby_temples}})
            
        except ValueError as e:
            return Response(
                {'error': 'Invalid parameters. lat and lng must be valid numbers.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ListCreateTempleCheckIn(generics.ListCreateAPIView):
    serializer_class = UserTempleCheckinSerializer
    
    def get_queryset(self):
        queryset = UserTempleCheckin.objects.all()
        temple_id = self.kwargs.get('pk')
        user_id = self.request.query_params.get('user_id', None)
        
        if temple_id:
            queryset = queryset.filter(temple_id=temple_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset.order_by('-checkin_time')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Group check-ins by user and count
        user_checkins = queryset.values(
            'user',
            'user__name'
        ).annotate(
            checkin_count=Count('id')
        ).order_by('-checkin_count')
        
        # Get all check-ins for serialization
        checkins = self.get_serializer(queryset, many=True).data
        
        return Response({
            "data": {
                "checkins": checkins,
                "user_counts": list(user_checkins)
            }
        })
    
    def create(self, request, *args, **kwargs):
        try:
            # Get temple_id from URL
            temple_id = kwargs.get('pk')
            temple = get_object_or_404(Temple, pk=temple_id)
            
            # Get user_id from request
            user_id = request.data.get('user')
            if not user_id:
                return Response(
                    {'error': 'user is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user has checked in within last 6 hours
            six_hours_ago = timezone.now() - timedelta(hours=6)
            recent_checkin = UserTempleCheckin.objects.filter(
                user_id=user_id,
                temple_id=temple_id,
                checkin_time__gte=six_hours_ago
            ).first()
            
            if recent_checkin:
                return Response(
                    {
                        'error': 'You have already checked in at this temple within the last 6 hours',
                        'last_checkin': UserTempleCheckinSerializer(recent_checkin).data
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add temple to request data
            request.data['temple'] = temple_id
            
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                # Increment the temple's checkin_count
                temple.checkin_count = F('checkin_count') + 1
                temple.save()
                
                # Create the check-in
                self.perform_create(serializer)
                return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)
            return Response({"data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetUserTempleCheckIn(APIView):
    def get(self, request, user_id, temple_id):
        """
        Get a specific temple check-in by user_id and temple_id along with check-in counts
        """
        try:
            # Get the specific check-in
            checkin = get_object_or_404(
                UserTempleCheckin.objects.select_related('user', 'temple'),
                user_id=user_id,
                temple_id=temple_id
            )
            
            # Check if user has checked in within last 6 hours
            six_hours_ago = timezone.now() - timedelta(hours=6)
            recent_checkin = UserTempleCheckin.objects.filter(
                user_id=user_id,
                temple_id=temple_id,
                checkin_time__gte=six_hours_ago
            ).first()
            
            # Calculate hours remaining until next check-in
            hours_remaining = None
            if recent_checkin:
                next_checkin_time = recent_checkin.checkin_time + timedelta(hours=6)
                hours_remaining = round((next_checkin_time - timezone.now()).total_seconds() / 3600, 1)
            
            # Get all check-ins for this temple grouped by user
            user_checkins = UserTempleCheckin.objects.filter(
                temple_id=temple_id
            ).values(
                'user_id',
                'user__name'
            ).annotate(
                checkin_count=Count('id')
            ).order_by('-checkin_count')
            
            serializer = UserTempleCheckinSerializer(checkin)
            return Response({
                "data": {
                    "user": serializer.data,
                    "checkin_counts": list(user_checkins),
                    "checkin_enabled": not bool(recent_checkin),
                    "last_checkin_time": recent_checkin.checkin_time if recent_checkin else None,
                    "next_checkin_available_after": hours_remaining
                }
            })
        except Exception as e:
            # Get check-in counts even if user check-in not found
            user_checkins = UserTempleCheckin.objects.filter(
                temple_id=temple_id
            ).values(
                'user_id',
                'user__name'
            ).annotate(
                checkin_count=Count('id')
            ).order_by('-checkin_count')
            
            return Response({
                "data": {
                    "user": None,
                    "checkin_counts": list(user_checkins),
                    "checkin_enabled": True,
                    "last_checkin_time": None,
                    "next_checkin_available_after": None
                }
            }, status=status.HTTP_200_OK)


class ListTempleReels(generics.ListAPIView):
    serializer_class = ReelsSerializer
    
    def get_queryset(self):
        temple_id = self.kwargs.get('pk')
        return Reels.objects.filter(temple_id=temple_id).select_related('user', 'temple').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Group reels by user and count
        user_reels = queryset.values(
            'user',
            'user__name'
        ).annotate(
            reel_count=Count('id')
        ).order_by('-reel_count')
        
        # Get all reels for serialization
        reels = self.get_serializer(queryset, many=True).data
        
        return Response({
            "data": {
                "reels": reels,
                "user_counts": list(user_reels)
            }
        })

