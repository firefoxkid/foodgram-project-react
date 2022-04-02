from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import SimpleRouter

from .views import (CustomUserViewSet, FavoriteViewSet, IngredientsViewSet,
                    RecipeViewSet, ShoppingListViewSet, SubscriptionListView,
                    SubscriptionViewSet, TagViewSet)

router_v1 = SimpleRouter()
router_v1.register('users', CustomUserViewSet, basename='users')
router_v1.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router_v1.register(r'tags', TagViewSet, basename='tags'),
router_v1.register(r'recipes', RecipeViewSet, basename='recipes'),

urlpatterns = [

     path('users/subscriptions/',
          SubscriptionListView.as_view(),
          name='subscriptions'),
     path('users/<int:author_id>/subscribe/',
          SubscriptionViewSet.as_view({'post': 'create',
                                      'delete': 'destroy'})
          ),
     path('auth/token/login/', TokenCreateView.as_view(), name='login'),
     path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
     path('recipes/<int:recipe_id>/shopping_cart/',
          ShoppingListViewSet.as_view(
               {'post': 'create',
                'delete': 'destroy'}
               ),
          name='shopping_list'),
     path('', include(router_v1.urls)),
     path('recipes/<int:recipe_id>/favorite/',
          FavoriteViewSet.as_view({'post': 'create',
                                   'delete': 'destroy',
                                   }),
          name='favorites')
]
