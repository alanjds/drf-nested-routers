__author__ = 'wangyi'

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class WebSite(models.Model):

    id = models.AutoField(primary_key=True, auto_created=True, null=False)
    url = models.URLField(max_length=256, null=False)
    name = models.CharField(max_length=64, null=False, unique=True)
    tags = models.CharField(max_length=128, null=True)

    class Meta:
        db_table = "website"


class User(models.Model):

    auth = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='custom_info',
                                on_delete=models.CASCADE, verbose_name=_("User"))
    username = models.CharField(max_length=64, null=False, unique=True)

    class Meta:
        db_table = "user"


class UserWebSite(models.Model):

    user = models.ForeignKey(User, null=False)
    website = models.ForeignKey(WebSite, null=False)
    importance = models.IntegerField(null=True)

    class Meta:
        db_table = "user_website"


class Headline(models.Model):

    url = models.URLField(max_length=256, null=False)
    post_date = models.DateField(null=True)
    digest = models.CharField(max_length=256, null=True)
    title = models.CharField(max_length=64, null=False, unique=True)
    website_id = models.ForeignKey(WebSite, db_column="website_id", null=False)
    score = models.IntegerField(null=False)

    class Meta:
        db_table = "headline"
