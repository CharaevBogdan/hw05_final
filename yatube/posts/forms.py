from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        labels = {
            'group': ('Группа.'),
            'text': ('Текст сообщения.'),
        }
        help_texts = {
            'group': ('Тут группа.'),
            'text': ('А тут текст ;)'),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
