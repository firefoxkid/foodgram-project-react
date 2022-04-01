from django.db.models import Count, Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from users.models import Follow, User

from .filters import RecipeFilter
from .mixins import CreateDestroyMixin, ListOneMixin
from .pagination import PaginatorLimit
from .permissions import OwnerOrReadOnly
from .serializers import (CustomUserSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipeWriteSerializer, ShoppingListSerializer,
                          SubscriptionSerializer, TagSerializer)


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

    def get_queryset(self):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        return Follow.objects.filter(author=author)

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        serializer.save(user=self.request.user, author=author)

    def destroy(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        user = self.request.user
        instance = get_object_or_404(Follow, author=author, user=user)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        instance = Favorite.objects.filter(user=request.user, recipe__id=pk)
        if request.method == 'POST' and not instance.exists():
            recipe = get_object_or_404(Recipe, id=pk)
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = FavoriteSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE' and instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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


class ShoppingListViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin, viewsets.GenericViewSet):
    model = ShoppingCart
    serializer_class = ShoppingListSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ShoppingCart.objects.all()

    def get_queryset(self):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        return ShoppingCart.objects.filter(recipe=recipe)

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        if ShoppingCart.objects.filter(recipe=recipe):
            raise ValueError('Рецепт уже в корзине!!')
        serializer.save(user=self.request.user, recipe=recipe)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        user = self.request.user
        instance = get_object_or_404(ShoppingCart, recipe=recipe, user=user)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
