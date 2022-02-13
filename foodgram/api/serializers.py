import base64

from django.core.files.base import ContentFile
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            Shopping_cart, Tag)
from rest_framework import serializers, validators
from rest_framework.serializers import (ReadOnlyField, SerializerMethodField,
                                        ValidationError)
from users.models import Follow, User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, author_id=obj.id
        ).exists()

    email = serializers.EmailField(
        validators=[validators.UniqueValidator(
            queryset=User.objects.all(),
            message='Этот email уже зарегистрирован')]
    )
    username = serializers.CharField(
        validators=[validators.UniqueValidator(
            queryset=User.objects.all(),
            message='Это имя пользователя уже используется')]
    )

    def validate(self, data):
        if data.get('username') == 'me' or data.get('username') == 'Me':
            raise serializers.ValidationError(
                'username Ме (или me) запрещено!!!')
        return data


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
        fields = ('__all__')
        read_only_fields = ('id',)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = ReadOnlyField(source='ingredients.id')
    name = ReadOnlyField(source='ingredients.name')
    measurement_unit = ReadOnlyField(source='ingredients.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class ImageField(serializers.Field):

    def to_representation(self, value):
        return 'rfhnbyrf картинка название'

    def to_internal_value(self, data):
        format, imgstr = data.split(';base64,')
        ext = format.split('/')[-1]
        image = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return image


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        source='ingredient_to_recipe',
        read_only=True,
        many=True
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Shopping_cart.objects.filter(user=user, recipe=recipe).exists()


class RecipeWriteSerializer(RecipeGetSerializer):

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
        if not cooking_time:
            raise ValidationError('Не заполнено время приготовления рецепта!')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise ValidationError('В рецепте не заполнены ингредиенты!')
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredients_id=ingredient.get('id'),
                amount=ingredient.get('amount')
            )

    def create(self, validated_data):
        tags = self.context['request'].data['tags']
        ingredients = self.validate_ingredients(
            self.initial_data.get('ingredients')
        )
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(
            ingredients,
            recipe
        )
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        recipe = super().update(recipe, validated_data)
        if ingredients:
            recipe.ingredients.clear()
            self.create_ingredients(ingredients, recipe)
        if tags:
            recipe.tags.set(tags)
        return recipe

    class Meta:
        model = Recipe
        fields = ('__all__')


class RecipeFollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time',)
        read_only_fields = ('id',)


class ShoppingListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shopping_cart
        fields = ('recipe',)
        read_only_fields = ('recipe',)


class FollowSerializer (serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('user', 'author',)


class FavoriteSerializer (serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes_count(self, author):
        return author.recipes.count()

    def get_recipes(self, author):
        recipes = author.recipes.all()
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return FavoriteSerializer(recipes, many=True).data
