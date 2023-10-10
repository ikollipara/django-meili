# Django-Meili

![](./docs/Meilisearch_-_Django.jpg)

A package to integrate Meilisearch with Django in a seamless way.

## Usage

Set the following variables in `settings.py`.

```python
MEILI_HOST=localhost # This is the host for meilisearch
MEILI_PORT=7700      # The port to listen on
MEILI_HTTPS=False   # Is the meilisearch running on http or https
MEILI_MASTER_KEY="..." # Meilisearch's master key
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
```

## API

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
