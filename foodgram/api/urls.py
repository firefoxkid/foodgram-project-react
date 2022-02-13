from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import SimpleRouter

from .views import (TagViewSet, IngredientViewSet, RecipeViewSet)
from .views import UserViewSet, ShoppingListViewSet, SubscriptionListView

router_v1 = SimpleRouter()
router_v1.register('users', UserViewSet, basename='users')

router_v1.register(r'tags', TagViewSet, basename='tags'),
router_v1.register(r'recipes', RecipeViewSet, basename='recipes'),
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('users/subscriptions/', SubscriptionListView.as_view()),
    path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
    path('recipes/<int:recipe_id>/shopping_cart/',
         ShoppingListViewSet.as_view(
              {'post': 'create',
               'delete': 'destroy'}
              ),
         name='shopping_list'),
    path('', include(router_v1.urls)),
]
