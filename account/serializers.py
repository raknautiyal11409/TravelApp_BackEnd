import string

from rest_framework import serializers
from .models import UserData
from django.contrib.gis.geos import Point


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = ["id", "email", "name", "password"]

    def create(self, validated_data):
        user = UserData.objects.create(email=validated_data['email'],
                                       name=validated_data['name']
                                       )
        user.set_password(validated_data['password'])
        user.save()
        return user

class OverpassSerializer(serializers.Serializer):
    query = serializers.CharField(required=True)
    bbox = serializers.CharField(required=True)

    def to_internal_value(self, data):
        FILTERWORDS = ('and', 'or', 'amenity')
        internal_rep = {}
        if data.get("query", None):
            query = data["query"]
            mod_query = ""
            for char in query:
                if char in string.punctuation:
                    mod_query += " "
                else:
                    mod_query += char
            mod_query = mod_query.split()
            query = []
            for word in mod_query:
                if word.lower() not in FILTERWORDS:
                    query.append(word)

            internal_rep["query"] = query
        if data.get("bbox", None):
            bbox = data["bbox"].split(",")
            shuffled_bbox = [bbox[1], bbox[0], bbox[3], bbox[2]]
            mod_box = [float(item) for item in shuffled_bbox]
            internal_rep["bbox"] = mod_box

        return internal_rep

class bookmarkFolderSerializer(serializers.Serializer):

    def to_internal_value(self, data):
        name = data["name"]

        return name


class folderContentSrealizer(serializers.Serializer):

    def to_internal_value(self, data):
        folderID = data['folderID']

        return folderID

class addBookmarkSerializer(serializers.Serializer):

    def to_internal_value(self, data):
        results = {}
        results["location_name"] = data["location_name"]
        results["address"] = data["address"]
        results["long"] = data["long"]
        results["lat"] = data["lat"]
        results["folderID"] = data["folderID"]

        return results

class add_Pin_and_Favourite_Serializer(serializers.Serializer):

    def to_internal_value(self, data):
        results = {}
        results["location_name"] = data["location_name"]
        results["address"] = data["address"]
        results["long"] = data["long"]
        results["lat"] = data["lat"]

        return results

class removeBookmarkFromFolderSerialzer(serializers.Serializer):

    def to_internal_value(self, data):
        results = {}
        results['folderID'] = data['folderID']
        results['location'] = Point(float(data["lat"]), float(data["long"]))

        return results

class locationSerialzer(serializers.Serializer):

    def to_internal_value(self, data):
        result = Point(float(data["lat"]), float(data["long"]))

        return result
