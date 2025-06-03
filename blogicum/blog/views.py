from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm
from django.http import Http404
from .forms import ProfileEditForm


User = get_user_model()


def index(request):
    post_list = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, id):
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author')
        .prefetch_related('comments__author'),
        pk=id
    )

    if (not post.is_published
            or not post.category.is_published
            or post.pub_date > timezone.now()) \
            and request.user != post.author:
        raise Http404

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', id=post.id)
    else:
        form = CommentForm()

    return render(request, 'blog/detail.html', {
        'post': post,
        'form': form,
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj
    })


def profile_view(request, username):
    profile = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=profile).order_by('-pub_date')

    if request.user == profile:
        post_list = Post.objects.filter(author=profile)
    else:
        post_list = Post.objects.filter(
            author=profile,
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    post_list = post_list.order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/profile.html', {
        'profile': profile,
        'page_obj': page_obj,
    })


class RegistrationView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('blog:index')
    template_name = 'registration/registration.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        if 'image' in self.request.FILES:
            form.instance.image = self.request.FILES['image']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return redirect('blog:post_detail', id=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'id': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return redirect('blog:post_detail', id=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileEditForm
    template_name = 'blog/profile_edit.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if not post.is_published or post.pub_date > timezone.now():
        raise Http404("Пост не доступен для комментирования")

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            try:
                comment.save()
                return redirect('blog:post_detail', id=post_id)
            except Exception as e:
                print(f"Ошибка сохранения комментария: {e}")
                form.add_error(None, "Ошибка сохранения комментария")
    else:
        form = CommentForm()

    return render(request, 'blog/comment_form.html', {
        'form': form,
        'post': post
    })


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment_edit.html'
    pk_url_kwarg = 'comment_id'

    def test_func(self):
        return self.get_object().author == self.request.user

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.kwargs['post_id']}
        )


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        author=request.user
    )
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, post_id, comment_id):
    try:
        post = Post.objects.get(pk=post_id)
        comment = Comment.objects.get(pk=comment_id, post=post)
    except (Post.DoesNotExist, Comment.DoesNotExist):
        raise Http404("Комментарий или пост не найдены")

    if request.user != comment.author:
        raise Http404("Вы не можете удалить этот комментарий")

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post': post
    })


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment_confirm_delete.html'
    pk_url_kwarg = 'comment_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' in context:
            del context['form']
        return context

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'id': self.object.post.id})
