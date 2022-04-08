from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import RecipeFilter
from .mixins import (CreateDestroyMixin, CustomShoppingFavoriteMixin,
                     ListOneMixin)
from .pagination import PaginatorLimit
from .permissions import OwnerOrReadOnly
from .serializers import (CustomUserSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipeWriteSerializer, ShoppingListSerializer,
                          SubscriptionSerializer, TagSerializer)

from recipes.models import (Favorite, Ingredient,  # isort:skip
                            IngredientInRecipe, Recipe,  # isort:skip
                            ShoppingCart, Tag)  # isort:skip
from users.models import Follow  # isort:skip

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]
    pagination_class = PaginatorLimit

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        return super(CustomUserViewSet, self).me(request, *args, **kwargs)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientsViewSet(ListOneMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (OwnerOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = PaginatorLimit

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeGetSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(total_amount=Sum('amount'))
        shopping_list = ['{} ({}) - {}\n'.format(
            ingredient['ingredients__name'],
            ingredient['ingredients__measurement_unit'],
            ingredient['total_amount']
        ) for ingredient in ingredients]
        response = HttpResponse(shopping_list, content_type='text/plain')
        attachment = 'attachment; filename="shopping_list.txt"'
        response['Content-Disposition'] = attachment
        return response

    def get_queryset(self):
        queryset = Recipe.objects.all()
        return queryset.add_flags(self.request.user.id)


class SubscriptionListView(ListAPIView):
    model = Follow
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user_id = self.request.user.id
        return (self.request.user.follower.all()
                .annotate(recipes_count=Count('author__recipes'))
                .annotate(is_subscribed=Exists(
                    Follow.objects.filter(
                        user_id=user_id, author__id=OuterRef('id')
                    )
                )))

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        serializer.save(user=self.request.user, author=author)


class SubscriptionViewSet(CreateDestroyMixin):
    model = Follow
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'author_id'

    def get_queryset(self):
        author = get_object_or_404(User, id=self.kwargs.get(self.lookup_field))
        return Follow.objects.filter(author=author)

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get(self.lookup_field))
        serializer.save(user=self.request.user, author=author)

    def perform_destroy(self, instance):
        author = get_object_or_404(User, id=self.kwargs.get(self.lookup_field))
        user = self.request.user
        instance = get_object_or_404(Follow, author=author, user=user)
        try:
            instance.delete()
        except Http404:
            raise ValidationError('Не найден ОБЪЕКТ для удаления')
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListViewSet(CustomShoppingFavoriteMixin):
    model = ShoppingCart
    serializer_class = ShoppingListSerializer
    queryset = ShoppingCart.objects.all()


class FavoriteViewSet(CustomShoppingFavoriteMixin):
    model = Favorite
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
