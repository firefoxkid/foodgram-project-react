from django_filters import (ChoiceFilter, FilterSet, ModelChoiceFilter,
                            ModelMultipleChoiceFilter)
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag, User


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(FilterSet):
    is_favorited = ChoiceFilter(
        choices=enumerate([0, 1]),
        method='filter_is_favorited'
    )
    is_in_shopping_cart = ChoiceFilter(
        choices=enumerate([0, 1]),
        method='filter_is_in_shopping_cart'
    )
    author = ModelChoiceFilter(queryset=User.objects.all())
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        if int(value) == 1 and not self.request.user.is_anonymous:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if int(value) == 1 and not self.request.user.is_anonymous:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
