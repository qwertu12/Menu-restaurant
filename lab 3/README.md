# FastAPI Recipes — Laboratory 3

## Запуск

```powershell
docker compose up -d
uv sync
cd app
..\.venv\Scripts\activate
alembic upgrade head
python main.py
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## GET /api/recipes

Пагинация:

```text
/api/recipes?page=1&size=10
```

Поиск по названию:

```text
/api/recipes?name__like=Блин
```

Фильтр по ингредиентам:

```text
/api/recipes?ingredient_id=1,2,3
```

Сортировка:

```text
/api/recipes?sort=-difficulty
```

Комбинация:

```text
/api/recipes?name__like=Блин&ingredient_id=1&sort=-difficulty&page=1&size=10
```

## GET /api/ingredients/{id}/recipes

Базовый ответ:

```text
/api/ingredients/1/recipes
```

Подгрузка связей:

```text
/api/ingredients/1/recipes?include=cuisine
/api/ingredients/1/recipes?include=ingredients,cuisine,allergens
```

Data Shaping:

```text
/api/ingredients/1/recipes?select=name
/api/ingredients/1/recipes?select=name,difficulty
```

Совместное использование:

```text
/api/ingredients/1/recipes?include=cuisine,allergens&select=name,difficulty
```
