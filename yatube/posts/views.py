from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings

from .forms import PostForm, CommentForm
from .models import Follow, Post, Group, Comment, User


def paginators(posts, page_number):
    paginator = Paginator(posts, settings.NUM_OF_POSTS_ON_PAGE)
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    posts = Post.objects.select_related('group').all()
    page_number = request.GET.get('page')
    page_obj = paginators(posts, page_number)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group').all()
    page_number = request.GET.get('page')
    page_obj = paginators(posts, page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.select_related('group').all()
    page_number = request.GET.get('page')
    page_obj = paginators(posts, page_number)
    if request.user.is_authenticated:
        following = request.user.is_authenticated and Follow.objects.filter(
            user=request.user, author=user)
        context = {
            'author': user,
            'page_obj': page_obj,
            'following': following,
        }
    context = {
        'author': user,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'), id=post_id)
    comments = post.comments.select_related('post').all()
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post
                    )
    if form.is_valid():
        post = form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/comments.html', {'form': form,
                  'post': post})


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_number = request.GET.get('page')
    page_obj = paginators(posts, page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=author)
