from django.contrib import admin
from recipes.models import ShoppingCart

from .models import Follow, User

admin.site.register(User)
admin.site.register(Follow)
admin.site.register(ShoppingCart)
