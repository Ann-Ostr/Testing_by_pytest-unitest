# Импортируем функцию для получения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
# Импортируем функцию reverse(), она понадобится для получения адреса страницы.
from django.urls import reverse
from notes.models import Note

User = get_user_model()


# Класс для проверки отдельной страницы
class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Другой Автор')
        cls.note = Note.objects.create(
            title='Заголовок заметки',
            text='Просто текст заметки.',
            slug='Svoi',
            author=cls.author,
        )

    # п.1 Отдельная заметка передаётся на страницу со списком заметок
    # в списке object_list, в словаре context
    # п.2 В список заметок одного пользователя не попадают заметки
    # другого пользователя
    def test_notes_list_for_different_users(self):
        url = reverse('notes:list')
        for users in (self.author, self.reader):
            self.client.force_login(users)
            # Выполняем запрос от имени параметризованного клиента:
            response = self.client.get(url)
            object_list = response.context['object_list']
            # Проверяем истинность утверждения "заметка есть в списке":
            if users == self.author:
                self.assertIn(self.note, object_list)
            else:
                self.assertNotIn(self.note, object_list)

    # 3. на страницы создания и редактирования заметки передаются формы.
    def test_authorized_client_has_form(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        for name in (
            'notes:edit',
            'notes:add',
        ):
            with self.subTest(name=name):
                # Адрес страницы создания или редактирования:
                if name == 'notes:add':
                    url = reverse(name)
                else:
                    url = reverse(name, args=(self.note.slug,))
                response = self.client.get(url)
                # проверка
                self.assertIn('form', response.context)
