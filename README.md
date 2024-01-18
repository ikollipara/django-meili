# Django-Meili

![](./docs/Meilisearch_-_Django.jpg)

A package to integrate Meilisearch with Django in a seamless way.

## Usage

Set the following variables in `settings.py`.

```python
MEILISEARCH = {
   "HOST": "localhost",
   "PORT": 7700,
   "HTTPS": False,
   "MASTER_KEY": "...",
   "SYNC": False, # Should Meilisearch action resolve before continuing
}
```

Register the app in `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...,
    "django_meili",
    ...,
]
```

Just subclass `django_meili.models.IndexMixin`

```python

from django_meili.models import IndexMixin

class Post(IndexMixin, models.Model):
    id = models.UUIDField()
    title = models.CharField(max_length=255)
    body = models.TextField()

    # Attributes to handle in Meilisearch
    displayed_fields = ("title", "body")
    searchable_fields = ("title", "body")

    def __str__(self):
        return self.title
```

Then when you are ready to search this model, just use the built-in "queryset".
```python
Post.objects.create(title="Hello", body="World")
posts = Post.meilisearch.search("hello") # Returns a Django Queryset of results
print(posts.first()) # Hello
```

## API

### `django_meili.models.IndexQuerySet`

This is a custom queryset built to mimic Django's queryset. Currently does not support `Q` objects, but that is a plan for the future.

Methods:
| Name | Description | Example |
|------|-------------|---------|
| **__getitem__** | Use slices to set limit and offset. The default is 20 and 0 respectively. | ```Post.meilisearch[:10]```
| **count** | Return the total number of documents within the index. *Does not reflect the count for the search query* | ```Post.meilisearch.count()```
| **order_by** | Takes a Django `order_by` parameter and sets a sort value based on that. Can take multiple sorts | ```Post.meilisearch.order_by("-likes")```
| **filter** | Takes a Django filter query. Supports: `lte`, `gte`, `lt`, `gt`, `exact`, `in`, `range`, `isnull`, `exists` | `Post.meilisearch.filter(title__exact="Hello World")`
| **matching_strategy** | Set the default strategy. Defaults to `last` | ```Post.meilisearch.matching_strategy('all')```
| **attributes_to_search_on** | Choose what fields to search on, defaults to all. | `Post.meilisearch.attributes_to_search_on("title", "body")`
| **search** | Executes the actual search. Takes an optional query and returns a Django Queryset of results | `Post.meilisearch.search()`

### `django_meili.models.IndexMixin`

Subclass Parameters:

| Name            | Type            | Description                                                          |
| --------------- | --------------- | -------------------------------------------------------------------- |
| **index_name**  | `Optional[str]` | The name of the index to generate. Defaults to `__name__` attribute. |
| **primary_key** | `Optional[str]` | The primary key of the index. Defaults to `pk`.                      |

Attributes:

| Name                  | Type         | Description                                 |
| --------------------- | ------------ | ------------------------------------------- |
| **displayed_fields**  | `tuple[str]` | The fields to display. By default uses all. |
| **searchable_fields** | `tuple[str]` | The fields to search. By default uses all.  |
| **filterable_fields** | `tuple[str]` | The fields to filter. By default uses none. |
| **meilisearch** | `django_meili.models.IndexQuerySet` | The queryset used for filtering and searching |

---

Copyright 2024 Ian Kollipara <<ian.kollipara@cune.edu>>
