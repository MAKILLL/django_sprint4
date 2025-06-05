from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView
)

from .mixin import (
    CommentMixin,
    CommentSuccessUrlMixin,
    OnlyAuthorMixin,
    PostFormMixin,
    PostMixin
)
from .forms import CommentForm, PostForm, UserForm
from .models import Category, Post


User = get_user_model()


class IndexListView(ListView):
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return Post.published_posts.all()


class PostDetailView(LoginRequiredMixin, DetailView):
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post_id = self.kwargs.get(self.pk_url_kwarg)
        return (
            get_object_or_404(
                Post.objects.filter(
                    Q(pk=post_id)
                    & Q(author=self.request.user)
                    | Q(pk=post_id)
                    & Q(is_published=True)
                    & Q(category__is_published=True)
                    & Q(pub_date__lte=timezone.now())
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.get_object()
        context['form'] = CommentForm()
        context['comments'] = self.get_object().comments.all()
        return context


class PostCreateView(PostMixin, PostFormMixin, CreateView):
    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(OnlyAuthorMixin, PostFormMixin, PostMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.object.pk}
        )


class PostDeleteView(OnlyAuthorMixin, PostMixin, DeleteView):
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get(self.pk_url_kwarg)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class CommentCreateView(CommentSuccessUrlMixin, CreateView):
    pk_url_kwarg = 'post_id'
    form_class = CommentForm

    def get_object(self, queryset=None):
        return get_object_or_404(
            Post,
            pk=self.kwargs.get(self.pk_url_kwarg)
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.get_object()
        return super().form_valid(form)


class CommentUpdateView(CommentMixin, CommentSuccessUrlMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CommentMixin, CommentSuccessUrlMixin, DeleteView):
    pass


class CategoryPostsListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
            created_at__lte=timezone.now()
        )

    def get_queryset(self):
        return self.get_category().posts.filter(
            is_published=True,
            pub_date__lte=timezone.now()
        ).annotate(
            comment_count=models.Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_profile(self):
        return get_object_or_404(
            User,
            username=self.kwargs['username']
        )

    def get_queryset(self):
        if self.request.user == self.get_profile():
            return Post.objects.filter(
                author=self.get_profile()
            ).annotate(
                comment_count=models.Count('comments')
            ).order_by('-pub_date')
        else:
            return Post.published_posts.filter(author=self.get_profile())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_profile()
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            User,
            username=self.request.user.username
        )

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )
