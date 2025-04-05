from django.db import models

from mixins.models import BaseModel


class User(BaseModel):
    user_id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    image = models.URLField(blank=True, null=True)  # or ImageField if using media uploads

    def __str__(self):
        return self.name


class Temple(BaseModel):
    srm = models.BooleanField(default=False)
    chadhava = models.BooleanField(default=False)
    puja = models.BooleanField(default=False)
    yatra = models.BooleanField(default=False)
    lat = models.FloatField(default=0.0)
    lng = models.FloatField(default=0.0)
    rating = models.FloatField(default=0.0)
    checkin_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.srm


class UserTempleCheckin(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    temple = models.ForeignKey(Temple, on_delete=models.CASCADE)
    checkin_time = models.DateTimeField(auto_now_add=True)


class Reels(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    temple = models.ForeignKey(Temple, on_delete=models.CASCADE)
    video_url = models.URLField()
    thumbnail = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Reel by {self.user.name} at {self.temple.srm}"


class ReelsLike(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reel = models.ForeignKey(Reels, on_delete=models.CASCADE)
    like = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'reel')


class Location(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lat = models.FloatField()
    lng = models.FloatField()
