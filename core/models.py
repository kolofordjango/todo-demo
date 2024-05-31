from django.db import models


class User(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    lifetime_todos_created = models.IntegerField(default=0)


    def __str__(self):
        return self.name


class Todo(models.Model):
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


class Event(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    data = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
