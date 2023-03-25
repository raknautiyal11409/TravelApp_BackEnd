from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.gis.db import models as gis_models
# Create your models here.
class UserManager(BaseUserManager):
    use_in_migration = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is Required')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff = True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser = True')

        return self.create_user(email, password, **extra_fields)


class UserData(AbstractUser):
    username = None
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=400)
    lonlat = gis_models.PointField(primary_key=True)
    usersPins = models.ManyToManyField(UserData, through='manage_locationPin_manytomany')
    userFavourites = models.ManyToManyField(UserData, through='manageUserFavourites_manytomany', related_name='favourite_locations')

    def __str__(self):
        return self.name

class manageUserFavourites_manytomany(models.Model):
    userFavourites = models.ForeignKey(UserData, on_delete=models.CASCADE)
    favouriteLocation = models.ForeignKey(Location, on_delete=models.PROTECT)

class manage_locationPin_manytomany(models.Model):
    usersPins = models.ForeignKey(UserData, on_delete=models.CASCADE)
    pinLocation = models.ForeignKey(Location, on_delete=models.PROTECT)

class BookmarkFolder(models.Model):
    folderID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(UserData, on_delete=models.PROTECT)
    location = models.ManyToManyField(Location, through='manage_bookmarkLocation_manytomany')

    def __str__(self):
        return self.name

class manage_bookmarkLocation_manytomany(models.Model):
    userBookmark = models.ForeignKey(BookmarkFolder, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)

