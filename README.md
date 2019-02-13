# django-shared-mediaarchive

Partially based an django-cabinet by Feinheit AG.

We don't use a fixed directory structured for managing files but a hierarchical structure of categories called "working folders". An uploaded file can be part of multiple categories. Filesystem locations are fully transparent and request paths will be calculated dynamically based on metadata.

Needs at least Django 1.11.
