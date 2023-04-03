from django.shortcuts import render
from rest_framework import response, decorators, permissions, status
from .serializers import (UserSerializer, OverpassSerializer, bookmarkFolderSerializer,
                          addBookmarkSerializer, folderContentSrealizer, add_Pin_and_Favourite_Serializer,
                          removeBookmarkFromFolderSerialzer, locationSerialzer)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import OutstandingToken, BlacklistedToken
from django.contrib.auth import logout
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.gis.geos import Point, Polygon
from rest_framework.views import APIView
from .models import BookmarkFolder, Location, UserData
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404
import overpy
import json


# view for registering users
class RegisterView(APIView):
    def post(self, request):
        try:
            if(request.data['regCode'] == 'fyp@2301'):
                serializer = UserSerializer(data=request.data)
                if not serializer.is_valid():
                    return response.Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                res = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                return response.Response(res, status.HTTP_201_CREATED)
            else:
                return response.Response({"message": f"Error: invalid signup token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)


# view for registering users
class SearchMap(APIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = OverpassSerializer

    def post(self, request, *args, **kwargs):
        try:
            api = overpy.Overpass()
            api_query_top = \
                """
                [out:json][timeout:25];
                (
                """

            api_query_bottom = \
                """
                );
                out center;
                >;
                out skel qt;
                """
            api_middle = ""
            my_serializer = OverpassSerializer(data=request.data)
            if my_serializer.is_valid():
                bbox = my_serializer.validated_data["bbox"]
                for item in my_serializer.validated_data["query"]:
                    if item == "*":
                        api_middle += f'node["amenity"]{tuple(bbox)};\nway["amenity"]{tuple(bbox)};\nrelation["amenity"]{tuple(bbox)};'
                        break
                    else:
                        api_middle += f'node["amenity"="{item}"]{tuple(bbox)};\nway["amenity"="{item}"]{tuple(bbox)};\nrelation["amenity"="{item}"]{tuple(bbox)};'

                api_query = f"{api_query_top}\n{api_middle}\n{api_query_bottom}\n"
                result = api.query(api_query)

                geojson_result = {
                    "type": "FeatureCollection",
                    "features": [],
                }

                nodes_in_way = []

                for way in result.ways:
                    geojson_feature = None
                    geojson_feature = {
                        "type": "Feature",
                        "id": "",
                        "geometry": "",
                        "properties": {}
                    }
                    poly = []
                    for node in way.nodes:
                        # Record the nodes and make the polygon
                        nodes_in_way.append(node.id)
                        poly.append([float(node.lon), float(node.lat)])
                        try:
                            poly = Polygon(poly)
                        except:
                            continue
                        geojson_feature["id"] = f"way_{way.id}"
                        geojson_feature["geometry"] = json.loads(poly.centroid.geojson)
                        geojson_feature["properties"] = {}
                        for k, v in way.tags.items():
                            geojson_feature["properties"][k] = v

                        geojson_result["features"].append(geojson_feature)

                    for node in result.nodes:
                        # Ignore nodes which are also in a 'way' as we will have already processed the 'way'.
                        if node.id in nodes_in_way:
                            continue
                        geojson_feature = None
                        geojson_feature = {
                            "type": "Feature",
                            "id": "",
                            "geometry": "",
                            "properties": {}
                        }
                        point = Point([float(node.lon), float(node.lat)])
                        geojson_feature["id"] = f"node_{node.id}"
                        geojson_feature["geometry"] = json.loads(point.geojson)
                        geojson_feature["properties"] = {}
                        for k, v in node.tags.items():
                            geojson_feature["properties"][k] = v

                        geojson_result["features"].append(geojson_feature)

                # Return the complete GeoJSON structure.
                return response.Response(geojson_result, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)

# view to add bookmark folder
class addBookmarFolder(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = bookmarkFolderSerializer
    def post(self, request):
        try:
            my_serializer = bookmarkFolderSerializer(data=request.data)

            if my_serializer.is_valid():
                name = my_serializer.validated_data
                user = request.user
                bookmark_folder = BookmarkFolder.objects.create(name=name, user=user)
                return response.Response({"message" : f"Success: Added folder." }, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)

class addBookmark(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = addBookmarkSerializer

    def post(self, request):
        try:
            my_serializer = addBookmarkSerializer(data=request.data)

            if my_serializer.is_valid():
                name = my_serializer.validated_data["location_name"]
                address = my_serializer.validated_data["address"]
                longlat = Point(float(my_serializer.validated_data["lat"]), float(my_serializer.validated_data["long"]))
                folderId = my_serializer.validated_data["folderID"]

                location, created = Location.objects.get_or_create(
                    name=name,
                    address=address,
                    lonlat=longlat
                )

                bookmark_folder = BookmarkFolder.objects.get(folderID=folderId)

                bookmark_folder.location.add(location)

                return response.Response({"message": f"Success: Added Location to Folder."}, status=status.HTTP_200_OK)
        except Exception as e:
                return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)

class getBookmarkFoldersOrderedByDate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            bookmarkFolderNames = BookmarkFolder.objects.filter(user=user).order_by('-created_at').values('name', 'folderID')
            return response.Response(bookmarkFolderNames, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)

class getFolderContent(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = folderContentSrealizer

    def post(self, request):
        try:
            my_serializer = folderContentSrealizer(data=request.data)

            locationResults =[]


            if my_serializer.is_valid():
                folderID = my_serializer.validated_data
                bookmark_folder = BookmarkFolder.objects.prefetch_related('location').get(folderID=folderID)
                locations = bookmark_folder.location.all().values('name', 'address', 'lonlat')
                for location in locations:

                    lat, long = location['lonlat'].coords
                    Result = {
                        "name":  location['name'],
                        "address": location['address'],
                        "lng": long,
                        "lat": lat
                    }
                    locationResults.append(Result)
                return response.Response(locationResults, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)



class addFavoutriteLocation(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = add_Pin_and_Favourite_Serializer

    def post(self, request):
        try:
            my_serializer = add_Pin_and_Favourite_Serializer(data=request.data)

            if my_serializer.is_valid():
                name = my_serializer.validated_data["location_name"]
                address = my_serializer.validated_data["address"]
                longlat = Point(float(my_serializer.validated_data["lat"]), float(my_serializer.validated_data["long"]))
                user = request.user

                location, created = Location.objects.get_or_create(
                    name=name,
                    address=address,
                    lonlat=longlat
                )

                location.userFavourites.add(user)

                return response.Response({"message": f"Success: Added Location to Folder."}, status=status.HTTP_200_OK)

        except Exception as e:
                return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)

class addPinLocation(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = add_Pin_and_Favourite_Serializer

    def post(self, request):
        try:
            my_serializer = add_Pin_and_Favourite_Serializer(data=request.data)

            if my_serializer.is_valid():
                name = my_serializer.validated_data["location_name"]
                address = my_serializer.validated_data["address"]
                longlat = Point(float(my_serializer.validated_data["lat"]), float(my_serializer.validated_data["long"]))
                user = request.user

                location, created = Location.objects.get_or_create(
                    name=name,
                    address=address,
                    lonlat=longlat
                )

                location.usersPins.add(user)

                return response.Response({"message": f"Success: Added Location to Folder."}, status=status.HTTP_200_OK)

        except Exception as e:
                return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)


class getPinLocations(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            locationResults = []

            user = request.user
            locations = Location.objects.filter(usersPins=user).values('name', 'address', 'lonlat')

            for location in locations:
                lat, long = location['lonlat'].coords
                Result = {
                    "name": location['name'],
                    "address": location['address'],
                    "lng": long,
                    "lat": lat
                }
                locationResults.append(Result)
            return response.Response(locationResults, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)

class getFavLocations(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            locationResults = []

            user = request.user
            locations = Location.objects.filter(userFavourites=user).values('name', 'address', 'lonlat')

            for location in locations:
                lat, long = location['lonlat'].coords
                Result = {
                    "name": location['name'],
                    "address": location['address'],
                    "lng": long,
                    "lat": lat
                }
                locationResults.append(Result)
            return response.Response(locationResults, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)

class removeBookmarkFromFolder(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = removeBookmarkFromFolderSerialzer

    def post(self, request):
        try:
            my_serializer = removeBookmarkFromFolderSerialzer(data=request.data)

            if my_serializer.is_valid():
                bookmarkFolder = BookmarkFolder.objects.get(folderID=my_serializer.validated_data['folderID'])
                longlat = Location.objects.get(lonlat=my_serializer.validated_data['location'])

                bookmarkFolder.location.remove(longlat)

            return response.Response({"message": f"Success: Removed location from folder."}, status=status.HTTP_200_OK)

        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)


class removeFavourite(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = locationSerialzer

    def post(self, request):
        try:
            my_serializer = locationSerialzer(data=request.data)

            if my_serializer.is_valid():
                user = request.user
                longlat = Location.objects.get(lonlat=my_serializer.validated_data)

                longlat.userFavourites.remove(user)

            return response.Response({"message": f"Success: Removed location from favourites."}, status=status.HTTP_200_OK)

        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)

class removePin(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = locationSerialzer

    def post(self, request):
        try:
            my_serializer = locationSerialzer(data=request.data)

            if my_serializer.is_valid():
                user = request.user
                longlat = Location.objects.get(lonlat=my_serializer.validated_data)

                longlat.usersPins.remove(user)

            return response.Response({"message": f"Success: Removed location from favourites."}, status=status.HTTP_200_OK)

        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)


class removeBookmarkFolder(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = folderContentSrealizer

    def post(self, request):
        try:
            my_serialiser = folderContentSrealizer(data=request.data)

            if my_serialiser.is_valid():
                bookmarkFolder = get_object_or_404(BookmarkFolder, folderID=my_serialiser.validated_data)

                bookmarkFolder.location.clear()

                bookmarkFolder.delete()

                return response.Response({"message": f"Success: Removed folder."}, status=status.HTTP_200_OK)

        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)


class logoutVIEW(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refreshToken = request.data['refreshToken']

            try:
                rToken =  RefreshToken(refreshToken)
                rToken.blacklist()
            except BlacklistedToken:
                pass
            finally:
                logout(request)
                return response.Response({"message": f"Logged out user."}, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({"message": f"Error: {e}."}, status=status.HTTP_400_BAD_REQUEST)





