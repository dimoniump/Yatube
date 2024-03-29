from django.shortcuts import (
    render,
    redirect, get_object_or_404)
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, Follow, User
from .forms import CommentForm, PostForm
from .utils import module_paginator


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    context_pagin = module_paginator(post_list, request)
    return render(request, "posts/index.html", context_pagin)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    count = Follow.objects.count()
    context = {
        'posts': posts,
        'count': count,
    }
    context.update(module_paginator(posts, request))
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    post_author = get_object_or_404(User, username=username)
    follower = request.user
    if request.user != post_author:
        Follow.objects.get_or_create(
            user=follower,
            author=post_author,
        )
    return redirect('posts:profile', post_author)


@login_required
def profile_unfollow(request, username):
    post_author = get_object_or_404(User, username=username)
    follower = request.user
    Follow.objects.filter(
        user=follower,
        author=post_author,
    ).delete()
    return redirect('posts:profile', post_author)


def group_posts(request, slug):
    group = get_object_or_404(Group.objects.all().prefetch_related('posts'),
                              slug=slug
                              )
    context = {
        'group': group,
    }
    context.update(module_paginator(group.posts.all(), request))
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    posts_author = get_object_or_404(User, username=username)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=posts_author
        )
    context = {
        'posts_author': posts_author,
        'following': following,
    }
    context.update(module_paginator(posts_author.posts.all(), request))
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
