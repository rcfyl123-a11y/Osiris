from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Todo


def todo_list(request):
    todos = Todo.objects.all().order_by('-created_at')
    return render(request, 'todo/list.html', {'todos': todos})


def todo_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if title:
            Todo.objects.create(title=title, description=description)
            messages.success(request, 'Задача успешно добавлена!')
        else:
            messages.error(request, 'Название задачи обязательно!')
        
        return redirect('todo_list')
    
    return redirect('todo_list')


def todo_toggle_complete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.completed = not todo.completed
    todo.save()
    return redirect('todo_list')


def todo_delete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.delete()
    messages.success(request, 'Задача удалена!')
    return redirect('todo_list')
