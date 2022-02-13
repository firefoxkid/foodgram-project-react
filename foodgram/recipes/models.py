from django.core.validators import MinValueValidator
from django.db import models
# from django.db.models import Exists, OuterRef
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(max_length=256)
    measurement_unit = models.CharField(max_length=64)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Тэг",
    )
    color = models.CharField(
        max_length=7,
        verbose_name="HEX Цвет",
        default='d76e00'
    )
    slug = models.SlugField(max_length=100, unique=True, verbose_name='slug')

    def __str__(self):
        return f'{self.name}'


# class RecipeQuerySet(models.QuerySet):
#     def add_flags(self, user_id):
#         return self.annotate(
#             is_favorited=Exists(
#                 Favorite.objects.filter(
#                     user_id=user_id, recipe=OuterRef('id')
#                 )
#             )
#         ).annotate(
#             is_in_shopping_cart=Exists(
#                 Shopping_cart.objects.filter(
#                     user_id=user_id, recipe=OuterRef('id')
#                 )
#             )
#         )


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Название рецепта",

    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты",
        related_name="recipes",
        through="IngredientInRecipe"
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Тэги",
        related_name="recipes"
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        related_name="recipes",
        on_delete=models.CASCADE
    )
    text = models.TextField(
        verbose_name="Текст рецепта"
    )
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to='media/recipes/images/'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления в минутах",
        validators=(
            MinValueValidator(
                1,
                message="Минимальное время приготовления - одна минута"
            ),
        )
    )
    pub_date = models.DateTimeField(verbose_name="Дата публикации",
                                    auto_now_add=True)
    # objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return f'{self.name}'


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_to_recipe'
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_to_recipe'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество ингредиентов",
        validators=(
            MinValueValidator(1, "Минимальное количество ингредиентов - 1"),
        )
    )

    def __str__(self):
        return f'В рецепт {self.recipe} добавлен ингредиент {self.ingredients}'


class Favorite(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_favorite_user_recipe",
                fields=('user', 'recipe'),
            ),
        ]
    """Подписка Кто на кого"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт, на который подпишемся',
        related_name='favorites'
    )

    def __str__(self):
        return f'Результат: {self.user}  подписался на {self.recipe}'


class Shopping_cart(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_shop_user_recipe",
                fields=('user', 'recipe'),
            ),
        ]
    """Юзер и рецепт в корзине"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт, который добавим в корзину',
        related_name='shopping_cart'
    )

    def __str__(self):
        return f'Результат: {self.user}  добавил в корзину {self.recipe}'
