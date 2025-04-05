from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import F, Max, Q, ExpressionWrapper, FloatField
from django.db.models.functions import Radians, Sin, Cos, Sqrt
from math import atan2
from math import radians, sin, cos, sqrt, atan2
from .models import User, Location
from .serializers import UserSerializer, UserCreateSerializer, LocationSerializer


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
