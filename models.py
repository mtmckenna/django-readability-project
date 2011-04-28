from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.db.models import signals

class UserProfile(models.Model):
    user = models.ForeignKey(User)
    oauth_token = models.CharField(max_length=200)
    oauth_secret = models.CharField(max_length=200)
    is_public = models.BooleanField()
    bookmarks = models.TextField(default="")
    date_fetched = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % (self.user)
