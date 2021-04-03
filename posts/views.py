from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Follow, Post, Group, User
from .forms import PostForm, CommentForm


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


def index(request):
    """Вовращает на главную страницу"""
    latest = Post.objects.all()[:11]
    paginator = Paginator(latest, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"page": page}
    return render(request, "index.html", context)


def group_posts(request, slug: str):
    """Возвращает на страницу группы постов"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:12]
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "group": group,
        "page": page,
    }
    return render(request, "group.html", context)


@login_required
def new_post(request):
    """Создает новый пост и возвращает на главную страницу, если форма
    заполнения валидна. Если не валидна, то возвращает на страницу
    создания поста"""
    form = PostForm(request.POST or None, request.FILES or None,)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "posts/new.html", {"form": form})


def profile(request, username: str):
    """Вовзращает страницу профиля"""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_count = post_list.count()
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    follow_count = author.follower.all().count()
    followers_count = author.following.all().count()

    following = (
        request.user.is_authenticated and Follow.objects.filter(
            user=request.user, author=author).exists()
    )
    context = {
        "page": page,
        "author": author,
        "post_count": post_count,
        "follow_count": follow_count,
        "followers_count": followers_count,
        "following": following,
    }
    return render(request, "posts/profile.html", context, )


def post_view(request, username: str, post_id: int):
    """Возвращает страницу просмотра конкретного поста"""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        "post": post,
        "author": post.author,
        "form": form,
        "comments": post.comments.all(),
    }
    return render(request, "posts/post.html", context)


@login_required
def post_edit(request, username: str, post_id: int):
    """Редактирует пост, если залогиненный пользователь является автором поста.
    После редактирования отправляет на конкретный пост автора."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("post", username=username, post_id=post_id)
    elif request.method == "POST":
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect("post", username=username, post_id=post_id)
    form = PostForm(instance=post)
    return render(request, "posts/new.html", {"form": form, "post": post})


@login_required
def add_comment(request, post_id, username):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("post", username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'paginator': paginator,
    }

    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect("profile", username=username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(Follow, user=request.user,
                               author__username=username)
    follow.delete()
    return redirect("profile", username=username)
