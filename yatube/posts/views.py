from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "page": page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    posts_count = author.posts.count()
    follower_count = author.follower.count()
    following_count = author.following.count()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    page = paginator.get_page(page_number)
    return render(request, "profile.html", {"author": author,
                                            "page": page,
                                            "posts_count": posts_count,
                                            "follower_count": follower_count,
                                            "following_count": following_count,
                                            "following": following})


def post_view(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related("author"), id=post_id,
                             author__username=username)
    form = CommentForm(instance=None)
    comments = post.comments.select_related("author").all()
    posts_count = post.author.posts.count()
    follower_count = post.author.follower.count()
    following_count = post.author.following.count()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=post.author).exists()
    return render(request, "post.html", {"comments": comments,
                                         "author": post.author,
                                         "post": post,
                                         "form": form,
                                         "posts_count": posts_count,
                                         "follower_count": follower_count,
                                         "following_count": following_count,
                                         "following": following})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related("author"), id=post_id,
                             author__username=username)

    if request.method != "POST":

        form = PostForm()
        return render(request, "new.html", {"form": form,
                                            "post": post,
                                            "context_checker": "edit"})

    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect("posts:post", username=username, post_id=post_id)

    return render(request, "new.html", {"form": form,
                                        "context_checker": "edit"})


@login_required
def new_post(request):

    if request.method != "POST":

        form = PostForm()
        return render(request, "new.html", {"form": form,
                                            "context_checker": "new"})

    form = PostForm(request.POST or None,
                    files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect("posts:index")

    return render(request, "new.html", {"form": form,
                                        "context_checker": "new"})


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):

    post = get_object_or_404(Post.objects.select_related("author"),
                             author__username=username, id=post_id)
    comments = post.comments.all()

    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("posts:post",
                        username=post.author.username,
                        post_id=post_id)
    return render(request, "includes/comments.html",
                  {"form": form, "comments": comments, "post": post})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request,
                  "follow.html",
                  {"page": page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        unfollow = Follow.objects.filter(user=request.user, author=author)
        if unfollow.exists():
            unfollow.delete()
    return redirect("posts:profile", username)
