from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField, ValidationError

from recipes.models import (Favorite,  # isort:skip
                            Ingredient, IngredientInRecipe,   # isort:skip
                            Recipe, ShoppingCart, Tag)  # isort:skip
from users.models import Follow, User   # isort:skip
from .fields import ImageField, TagsField  # isort:skip


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')
        read_only_fields = ['id']


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')
        read_only_fields = ['id']

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        return not user.is_anonymous and Follow.objects.filter(
            user=user,
            author=author.id
        ).exists()


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['email']
        model = User
        extra_kwargs = {
            'email': {'required': True}
        }


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name', 'color')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredients.id')
    name = serializers.CharField(source='ingredients.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        source='ingredient_to_recipe',
        read_only=True,
        many=True
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = ImageField()

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=recipe).exists()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')


class RecipeWriteSerializer(RecipeGetSerializer):
    ingredients = IngredientRecipeSerializer(
        source='ingredient_to_recipe',
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        pk_field=TagsField()
    )

    def validate_image(self, image):
        if not image:
            raise ValidationError('Добавьте картинку рецепта!')
        return image

    def validate_name(self, name):
        if not name:
            raise ValidationError('Не заполнено название рецепта!')
        if self.context.get('request').method == 'POST':
            current_user = self.context.get('request').user
            if Recipe.objects.filter(author=current_user, name=name).exists():
                raise ValidationError(
                    'Рецепт с таким названием у вас уже есть!'
                )
        return name

    def validate_text(self, text):
        if not text:
            raise ValidationError('Не заполнено описание рецепта!')
        return text

    def validate_cooking_time(self, cooking_time):
        if not cooking_time or int(cooking_time) < 0:
            raise ValidationError('Некорректное время приготовления рецепта!')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise ValidationError('В рецепте не заполнены ингредиенты!')
        return ingredients

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredient_to_recipe')
        recipe = Recipe.objects.create(**validated_data)
        return self.update_related_data(ingredients_data, tags_data, recipe)

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredient_to_recipe')
        instance = super().update(instance, validated_data)
        return self.update_related_data(ingredients_data, tags_data, instance)

    def update_related_data(self, ingredients_data, tags_data, recipe):
        recipe.tags.clear()
        recipe.ingredients.clear()
        recipe.tags.set(tags_data)
        for ingredient_el in ingredients_data:
            ingredient_id = ingredient_el['ingredients'].get('id')
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            IngredientInRecipe.objects.update_or_create(
                recipe=recipe,
                ingredients=ingredient,
                amount=ingredient_el['amount']
            )
        return recipe

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data

        if data['cooking_time'] < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше ноля')
        ingredients = []
        for ingredient in data['ingredient_to_recipe']:
            ingredients.append(ingredient['ingredients'].get('id'))
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество ингредиентов должно быть больше ноля')
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'В запросе присутствуют дублирующиеся ингредиенты')
        if len(data['tags']) != len(set(data['tags'])):
            raise serializers.ValidationError(
                'В запросе присутствуют дублирующиеся тэги')
        return data

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')


class RecipeInFollowSerializer(serializers.ModelSerializer):
    image = ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')
        read_only_fields = ('id',)


class ShoppingListSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    cooking_time = serializers.CharField(source='recipe.cooking_time',
                                         read_only=True)
    image = serializers.CharField(source='recipe.image', read_only=True)

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data
        recipe_id = request.parser_context.get('kwargs').get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.context['request'].user
        if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                'Нельзя добавить в список покупок один рецепт дважды')
        return data

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(source='author.first_name',
                                       read_only=True)
    last_name = serializers.CharField(source='author.last_name',
                                      read_only=True)
    # recipes_count = serializers.IntegerField(read_only=True)

    is_subscribed = serializers.BooleanField(read_only=True)
    # recipes = RecipeGetSerializer(source='author.recipes',
    #                               many=True,
    #                               read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'recipes_count', 'recipes', 'is_subscribed')

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request.GET.get('recipes_limit'):
            recipes_limit = int(request.GET.get('recipes_limit'))
            queryset = Recipe.objects.filter(author__id=obj.id).order_by(
                'pub_date')[:recipes_limit]
        else:
            queryset = Recipe.objects.filter(author__id=obj.id).order_by(
                'pub_date')
        # return RecipeInFollowSerializer(queryset, many=True).data
        return RecipeGetSerializer(queryset, many=True).data

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data
        author_id = request.parser_context.get('kwargs').get('author_id')
        author = get_object_or_404(User, id=author_id)
        user = self.context['request'].user
        if author == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')
        if Follow.objects.filter(author=author, user=user).exists():
            raise serializers.ValidationError(
                'Нельзя подписаться дважды')
        return data


class FavoriteSerializer (serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    cooking_time = serializers.CharField(source='recipe.cooking_time',
                                         read_only=True)
    image = serializers.CharField(source='recipe.image', read_only=True)

    def validate(self, data):
        request = self.context.get('request')
        if request.method == 'DELETE':
            return data

        recipe_id = request.parser_context.get('kwargs').get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        user = self.context['request'].user

        if Favorite.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                'Нельзя добавить в избранное один рецепт дважды')
        return data

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'cooking_time', 'image')
