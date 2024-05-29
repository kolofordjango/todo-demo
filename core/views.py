import os
import json
from functools import wraps
import openai

from django import forms
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from core.models import Todo


def authenticate(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if "evil" in request.headers:
            return HttpResponseForbidden()
        else:
            return function(request, *args, **kwargs)
    return wrap


class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ['title']

@authenticate
def list_todos(request):

    import requests
    google = requests.head("https://google.com")

    todos = Todo.objects.all().order_by("id")
    form = TodoForm()
    return render(request, 'list_todos.html', {'todos': todos, 'form': form})

@authenticate
def add_todo(request):
    form = TodoForm(request.POST)
    if form.is_valid():
        form.save()
        todos = Todo.objects.all().order_by("id")
        return render(request, "list_todos.html", {"todos": todos, "form": form})


def break_down_from_gpt(title):
    PROMPT = f"""
    Break down the following todo item into 3 concrete, actionable steps, which
    make it easier to complete the overall todo. 
    Respond with a JSON object with top level key "todos" which is a list of 3 strings, each representing the new todo and nothing else!
    Be extremely concise with each todo, it should be no more than 5 words each.
    """

    completion = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
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
    title = request.POST['title']

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
