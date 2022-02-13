# Generated by Django 2.2.19 on 2022-02-13 18:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_auto_20220211_0058'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientinrecipe',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredient_to_recipe', to='recipes.Recipe'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(default='d76e00', max_length=7, verbose_name='HEX Цвет'),
        ),
    ]
