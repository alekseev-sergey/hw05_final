from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {"text": "Текст", "group": "Группа", "image": "Изображение"}
        help_texts = {
            "text": "Введите текст",
            "group": "Выберите группу",
            "image": "Добавьте изображение",
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
