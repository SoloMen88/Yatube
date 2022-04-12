from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Текст поста',
            'group': 'Сообщество',
            'image': 'Картинка',
        }


class CommentForm(forms.ModelForm):
    # text = forms.CharField()

    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        bed = ['донцова', 'левицкий', 'шалыгин']
        data = self.cleaned_data['text'].split()
        data_corr = ''
        for t in data:
            if t.lower() in bed:
                data_corr += ('*' * len(t)) + ' '
            else:
                data_corr += t + ' '
        return data_corr.rstrip()
