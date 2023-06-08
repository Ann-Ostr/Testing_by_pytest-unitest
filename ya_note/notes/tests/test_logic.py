from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TEXT = 'Text note created'
    NOTE_TITLE = 'Заголовок создания'

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.author = User.objects.create(username='Создатель')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        # Адрес страницы .
        cls.url = reverse('notes:add')
        # Данные для POST-запроса при создании заметки.
        cls.form_data = {
            'text': cls.NOTE_TEXT,
            'title': cls.NOTE_TITLE}

    # п 1.1 Анонимный пользовательн не может создать заявку
    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество Note.
        note_count = Note.objects.count()
        # Ожидаем, что аноним ни создал ни одного поста.
        self.assertEqual(note_count, 0)

    # п 1.2 Залогиненный пользователь может создать заметку,
    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        self.auth_client.post(self.url, data=self.form_data)
        # Считаем количество постов.
        note_count = Note.objects.count()
        # Убеждаемся, что заметка создалась.
        self.assertEqual(note_count, 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты  совпадают с ожидаемыми.
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.author, self.author)


# п.4 В отдельном классе проверяем уникальность slug,
# удаление/редактирование заметки
class TestNoteEditDelete(TestCase):
    NOTE_TEXT = 'Текст исходный'
    NEW_NOTE_TEXT = 'Обновлённый текст'
    NEW_TITLE_TEXT = 'Новый заголовок'

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователей и клиент, логинимся в клиенте.
        cls.author = User.objects.create(username='Создатель')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Еще один')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём заметку.
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug='kukushka')
        # Сохраняем slug заметки во временную переменную
        note_slug = cls.note.slug
        # Формируем адреса, которые понадобятся для тестов.
        # Адрес успеха
        cls.url_done = reverse('notes:success')
        # URL для редактирования.
        cls.edit_url = reverse('notes:edit', args=(note_slug,))
        # URL для удаления.
        cls.delete_url = reverse('notes:delete', args=(note_slug,))
        # Формируем данные для POST-запроса по обновлению.
        cls.form_data = {
            'text': cls.NEW_NOTE_TEXT,
            'title': cls.NEW_TITLE_TEXT,
            'slug': 'new-slug',
            'author': cls.author
        }

    # п.2 Невозможно создать две заметки с одинаковым slug
    # Вызываем фикстуру отдельной заметки, чтобы в базе появилась запись.
    def test_not_unique_slug(self):
        url = reverse('notes:add')
        # Подменяем slug новой заметки на slug уже существующей записи:
        self.form_data['slug'] = self.note.slug
        # Пытаемся создать новую заметку:
        response = self.author_client.post(url, data=self.form_data)
        # Проверяем, что в ответе содержится ошибка формы для поля slug:
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        # Дополнительно убедимся, что заметка не была создана.
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    # п.3 Если при создании заметки не заполнен slug, то он формируется
    # автоматически, с помощью функции pytils.translit.slugify
    def test_empty_slug(self):
        url = reverse('notes:add')
        # Убираем поле slug из словаря:
        self.form_data.pop('slug')
        response = self.author_client.post(url, data=self.form_data)
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, reverse('notes:success'))
        note_count = Note.objects.count()
        self.assertEqual(note_count, 2)
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data['title'])
        # Получаем созданную заметку из базы:
        new_note = Note.objects.get(slug=expected_slug)
        # Проверяем, что заметка с ожидаемым слагом существует:
        self.assertIsInstance(new_note, Note)

    # п 4.1 Автор может редактировать свою заметку
    def test_author_can_edit_note(self):
        # Выполняем запрос на редактирование от имени автора комментария.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект
        self.assertRedirects(response, self.url_done)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    # п 4.2 Чужой автор не может редактировать чужую заметку
    def test_user_cant_edit_note_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    # п 4.3 Автор может удалить свою заметку
    def test_author_can_note_delete(self):
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу успеха.
        # Заодно проверим статус-коды ответов.
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.url_done)
        # Считаем количество заметок в системе.
        note_count = Note.objects.count()
        # Ожидаем ноль  в системе.
        self.assertEqual(note_count, 0)

    # п 4.4 Чужой автор не может удалить чужую заметку
    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
