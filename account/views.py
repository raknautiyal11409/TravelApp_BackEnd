from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers import UserSerializer, OverpassSerializer
from rest_framework import response, decorators, permissions, status
from rest_framework_simplejwt.tokens import RefreshToken
import overpy
import shapely.ge


# view for registering users
class RegisterView(APIView):
    def post(self, request):
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


# view for registering users
class SearchMap(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OverpassSerializer

    def post(self, request, *args, **kwargs):
        try:
            api = overpy.Overpass()
            api_query_top = \
                """
                [out:json][timeout:25]
                (
                """
            api_query_bottom = \
                """
                );
                out body;
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
                        break;
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
