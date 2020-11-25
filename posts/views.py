from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {
            'page': page, 
            'paginator': paginator
        }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 
        "group.html", 
        {
            'group': group,
            'posts': posts,
            'page': page, 
            'paginator': paginator
        },
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'new.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    cache.clear()
    return redirect('index')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    following = (
        request.user.is_authenticated and 
        author.following.filter(user=request.user).exists()
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'paginator' : paginator,
        'author': author,
        'following': following,
    }    
    return render(
        request, 
        'profile.html', 
        context
    )
 
 
def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    author = post.author
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'author':author,
        'form': form,
        'comments': comments,
    }
    return render(
        request, 
        'post.html', 
        context
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    if post.author != request.user:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
        request.POST or None, 
        files=request.FILES or None, 
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request,
        'new.html',
        {
            'form': form,
            'post': post
        }
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
    return redirect('post', username=username, post_id=post_id)
    

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
    return render(
        request, 
        "misc/500.html", 
        status=500
    )


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    following_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(following_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 
        'follow.html', 
        {
            'page': page, 
            'paginator': paginator
        },
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = author.following.filter(user=request.user).exists()
    if request.user != author and not following:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    get_object_or_404(Follow, user=request.user, author=author).delete()
    return redirect("profile", username=username)
