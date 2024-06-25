# Django-Meili

![](./docs/Meilisearch_-_Django.jpg)

A package to integrate Meilisearch with Django in a seamless way. This pacakge is tested on Meilisearch `v1.60`.

## Install
```
pip install django_meili
```

## Usage
### Settings
Update your `settings.py` file to include the following:
```python
INSTALLED_APPS = [
    # ...,  <--- Any 3rd Party code
    "django_meili",
    # ...,  <--- All your modules
]

# ....

MEILISEARCH = {}
```
You must define the `django_meili` application before any of your code that
uses the application.

### Example in Models
Update a model to include the following:
```python
from django_meili.models import IndexMixin
from django.db import models

class Post(IndexMixin, models.Model):
    """Model definition for Post."""

    title = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        """Meta definition for Post."""

        verbose_name = "Post"
        verbose_name_plural = "Posts"

    class MeiliMeta:
        filterable_fields = ("title",)
        searchable_fields = ("id", "title", "body")
        displayed_fields = ("id", "title", "body")

    def __str__(self):
        return self.title
```

### Searching
Now you can search from meilisearch using `Model.meilisearch`:
```python
Post.meilisearch.search("Hello World") # => <Queryset for Post>
```

## API
### `MEILISEARCH` in `settings.py`
These are the settings available to the package. The values
show are the defaults.
```python
MEILISEARCH = {
    'HTTPS': False, # Whether HTTPS is enabled for the meilisearch server
    'HOST': 'localhost', # The host for the meilisearch server
    'MASTER_KEY': None, # The master key for meilisearch. See https://www.meilisearch.com/docs/learn/security/basic_security for more detail
    'PORT': 7700, # The port for the meilisearch server
    'TIMEOUT': None, # The timeout to wait for when using sync meilisearch server
    'CLIENT_AGENTS': None, # The client agents for the meilisearch server
    'DEBUG': DEBUG, # Whether to throw exceptions on failed creation of documents
    'SYNC': False, # Whether to execute operations to meilisearch in a synchronous manner (waiting for each rather than letting the task queue operate)
    'OFFLINE': False, # Whether to make any http requests for the application.
}
```

### `django_meili.models.IndexMixin`

The `IndexMixin` is how an index is defined on a model.
To configure the `IndexMixin` define a class on the model called `MeiliMeta`.
The `IndexMixin` defines two new properties on the model:
1. `meilisearch` - The queryset used to search.
2. `_meilisearch` - the `MeiliMeta` values available on the model.

In addition, the `IndexMixin` defines three methods:
1. `meili_filter()` - Should this row be synced in meilisearch
2. `meili_serialize()` - How the model is serialized into a dictionary
3. `meili_geo()` - What does the `_geo` column look like (optional)

#### `MeiliMeta`
The listed values here are default values. The displayed, searchable, filterable, and sortable should all be iterables containing field names, see the example above.

```python
class MeiliMeta:
    displayed_fields = None # the fields displayed when querying meilisearch
    searchable_fields = None # the searchable fields when querying meilisearch
    filterable_fields = None # the fields available to filter by using meilisearch
    sortable_fields = None # the fields that can be sorted by using meilisearch
    supports_geo = False # Does the model support geolocation
    index_name = "<model.__name__>" # the name of the meilisearch index
    primary_key = "pk" # the primary key field for the index
```

### `django_meili.querysets.IndexQuerySet`
The queryset defines the searchable operations on the index.
It attempts to mimic the django queryset API, but differs in 2 notable ways:
1. To do geo-filtering, you pass a positional argument
2. Not all queryset operations are implemented.

## Contact
If there are any issues, please feel free to make an issue.
If you have suggested improvements, please make an issue where we can discuss.
