"""
URL configuration for todo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from core.views import (
    list_todos,
    add_todo,
    breakdown_todo,
    complete_todo,
    delete_todo,
    clear_todos,
    list_todos_json,
)

urlpatterns = [
    path("", list_todos, name="list_todos"),
    path("add/", add_todo, name="add_todo"),
    path("break/", breakdown_todo, name="breakdown_todo"),
    path("complete/<int:todo_id>/", complete_todo, name="complete_todo"),
    path("delete/<int:todo_id>/", delete_todo, name="delete_todo"),
    path("clear/", clear_todos, name="clear_todos"),
    path("todos.json", list_todos_json, name="list_todos_json"),
]
