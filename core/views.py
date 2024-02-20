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
    todos = Todo.objects.all().order_by("id")

    form = TodoForm()

    return render(request, 'list_todos.html', {'todos': todos, 'form': form})

@authenticate
def add_todo(request):
    form = TodoForm(request.POST)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/')


def break_down_from_gpt(title):
    PROMPT = f"""
    Break down the following todo item into 3 concrete, actionable steps, which
    make it easier to complete the overall todo. 
    Respond with a JSON list of 3 strings, each representing the new todo and nothing else!

    Todo item:
    """

    prompt_with_todo = PROMPT + title

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt_with_todo}
        ]
    )

    output = completion["choices"][0]["message"]["content"]
    return output

@authenticate
def breakdown_todo(request):
    title = request.POST['title']

    existing_todo = Todo.objects.get(title=title)
    existing_todo.title = title + " (broken down 👇)"
    existing_todo.save()

    openai.api_key = os.environ["OPENAI_API_KEY"]

    output = break_down_from_gpt(title)

    todos_to_add = json.loads(output)

    for todo in todos_to_add:
        Todo.objects.create(title=todo)

    return HttpResponseRedirect('/')


@authenticate
def complete_todo(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)
    if todo.is_completed:
        todo.is_completed = False
    else:
        todo.is_completed = True
    todo.save()
    return HttpResponseRedirect("/")
