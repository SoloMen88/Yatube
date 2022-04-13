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

    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        with open('yatube/posts/bed_author.txt', 'r', encoding='utf-8') as bed:
            variants = bed.read().split()
        message = self.cleaned_data['text']
        # Нашел такой вариант на стеке, разобрался как работает,
        # вроде более эффективно фильтрует, но мне кажется больше ресурсов ест.
        # Для подсчета расстояний Левенштейна нашел модуль, но его нужно
        # устанавливать - не проходят тесты на практикуме.
        ln = len(variants)
        filtred_message = ''
        string = ''
        pattern = '*'
        for i in message:
            string += i
            string2 = string.lower()
            flag = 0
            for j in variants:
                if string2 not in j:
                    flag += 1
                if string2 == j:
                    filtred_message += pattern * len(string)
                    flag -= 1
                    string = ''
            if flag == ln:
                filtred_message += string
                string = ''
        if string2 != '' and string2 not in variants:
            filtred_message += string
        elif string2 != '':
            filtred_message += pattern * len(string)
        return filtred_message
