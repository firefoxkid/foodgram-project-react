from django.contrib import admin
from .models import User, Follow
from recipes.models import (Recipe, Tag, Ingredient,
                            Shopping_cart, IngredientInRecipe)


admin.site.register(User)
admin.site.register(Follow)
admin.site.register(Recipe)
admin.site.register(IngredientInRecipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Shopping_cart)
