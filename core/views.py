import os
import json
from functools import wraps
import openai

from django import forms
from django.http import (
    HttpResponseBadRequest,
    HttpResponseRedirect,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render

from core.models import Event, Todo, User


def authenticate(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if "evil" in request.headers:
            return HttpResponseForbidden()
        else:
            return function(request, *args, **kwargs)

    return wrap


class TodoForm(forms.ModelForm):
    creator = forms.ModelChoiceField(
        queryset=User.objects.all(), initial=User.objects.first()
    )

    class Meta:
        model = Todo
        fields = ["title", "creator"]


@authenticate
def list_todos(request):

    todos = Todo.objects.all().order_by("id")
    form = TodoForm()
    return render(request, "list_todos.html", {"todos": todos, "form": form})


@authenticate
def list_todos_json(request):
    todos = list(Todo.objects.order_by("id").values())
    return JsonResponse({"todos": todos})


@authenticate
def add_todo(request):
    form = TodoForm(request.POST)

    if not form.is_valid():
        return HttpResponseBadRequest("Invalid form")

    todo = form.save()

    user = todo.creator

    Event.objects.create(
        name="todo_added", data={"todo_id": todo.id, "fortune_cookie": True}, user=user
    )

    user.lifetime_todos_created = user.lifetime_todos_created + 1
    user.save(update_fields=["lifetime_todos_created"])

    todos = Todo.objects.all().order_by("id")

    fortune_cookie_message = fortune_cookie(todo.title)
    return render(
        request,
        "list_todos.html",
        {"todos": todos, "form": form, "fortune_cookie": fortune_cookie_message},
    )


def fortune_cookie(todo_title: str) -> str:
    PROMPT = f"""
    Please create a very brief fortune cookie style message which
    relates to the user provided todo.
    """

    completion = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": "Todo: " + todo_title},
        ],
    )

    fortune_cookie_message = completion["choices"][0]["message"]["content"]

    return fortune_cookie_message


def break_down_from_gpt(title):
    PROMPT = f"""
    Break down the following todo item into 3 concrete, actionable steps, which
    make it easier to complete the overall todo.
    Respond with a JSON object with top level key "todos" which is a list of 3 strings, each representing the new todo and nothing else!
    Be extremely concise with each todo, it should be no more than 5 words each.
    """

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": "Todo: " + title},
        ],
        response_format={"type": "json_object"},
    )

    output = completion["choices"][0]["message"]["content"]
    return output


@authenticate
def breakdown_todo(request):
    # TODO: Convert this to id
    title = request.POST["title"]

    existing_todo = Todo.objects.get(title=title)
    existing_todo.title = title + " (broken down 👇)"
    existing_todo.save()

    openai.api_key = os.environ["OPENAI_API_KEY"]

    output = break_down_from_gpt(title)

    todos_to_add = json.loads(output)["todos"]

    for todo in todos_to_add:
        Todo.objects.create(title=todo)

    todos = Todo.objects.all().order_by("id")
    form = TodoForm()
    return render(request, "list_todos.html", {"todos": todos, "form": form})


@authenticate
def complete_todo(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)

    if todo.is_completed:
        todo.is_completed = False
    else:
        todo.is_completed = True
    todo.save()

    todos = Todo.objects.all().order_by("id")
    form = TodoForm()
    return render(request, "list_todos.html", {"todos": todos, "form": form})


@authenticate
def delete_todo(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)

    todo.delete()

    todos = Todo.objects.all().order_by("id")
    form = TodoForm()
    return render(request, "list_todos.html", {"todos": todos, "form": form})


@authenticate
def clear_todos(request):
    Todo.objects.all().delete()

    todos = Todo.objects.all().order_by("id")
    form = TodoForm()
    return render(request, "list_todos.html", {"todos": todos, "form": form})
