from http import HTTPStatus

import pytest
from django.urls import reverse
# Импортируем из файла с формами список стоп-слов и предупреждение формы.
from news.forms import BAD_WORDS, WARNING
from news.models import Comment
from pytest_django.asserts import assertFormError, assertRedirects


# п.1 Анонимный пользователь не может создать коммент
# Обозначаем, что нужно задействовать базу данных:
@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    client,
    form_data,
    pk_news_for_args
):
    url = reverse('news:detail', args=pk_news_for_args)
    # Через анонимный клиент пытаемся создать заметку:
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    # Проверяем, что произошла переадресация на страницу логина:
    assertRedirects(response, expected_url)
    # Считаем количество заметок в БД, ожидаем 0 заметок.
    assert Comment.objects.count() == 0


# п.2 Залогиненный пользователь может создать комментарий
@pytest.mark.django_db
# Указываем фикстуру form_data в параметрах теста.
def test_user_can_create_commnet(
        author_client,
        author,
        pk_news_for_args,
        form_data):
    url = reverse('news:detail', args=pk_news_for_args)
    # В POST-запросе отправляем данные, полученные из фикстуры form_data:
    response = author_client.post(url, data=form_data)
    # Проверяем, что был выполнен редирект на страницу
    # успешного добавления заметки:
    assertRedirects(response, f'{url}#comments')
    # Считаем общее количество заметок в БД, ожидаем 1 заметку.
    assert Comment.objects.count() == 1
    # Чтобы проверить значения полей заметки -
    # получаем её из базы при помощи метода get():
    new_comment = Comment.objects.get()
    # Сверяем атрибуты объекта с ожидаемыми.
    assert new_comment.text == form_data['text']
    assert new_comment.author == author


# п.3 Если комментарий содержит запрещённые слова, он не будет опубликован,
# а форма вернёт ошибку.
def test_user_cant_use_bad_words(
        author_client,
        pk_news_for_args,
):
    # Формируем данные для отправки формы; текст включает
    # первое слово из списка стоп-слов.
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    url = reverse('news:detail', args=pk_news_for_args)
    # В POST-запросе отправляем данные
    response = author_client.post(url, data=bad_words_data)
    # Проверяем, что в ответе содержится ошибка формы:
    assertFormError(
        response,
        'form',
        'text',
        errors=WARNING)
    # Убеждаемся, что количество заметок в базе осталось равным 1:
    assert Comment.objects.count() == 0


# п.4.1 Пользователь может редактировать свои комменты
# В параметрах вызвана фикстура comment:.
def test_author_can_edit_comment(
        author_client,
        form_data,
        comment,
        pk_comment_for_args,
        pk_news_for_args
):
    # Получаем адрес страницы редактирования:
    url = reverse('news:edit', args=pk_comment_for_args)
    url_success = reverse('news:detail', args=pk_news_for_args)
    # В POST-запросе на адрес редактирования
    # отправляем form_data - новые значения для полей:
    response = author_client.post(url, form_data)
    # Проверяем редирект:
    assertRedirects(response, f'{url_success}#comments')
    # Обновляем объект comment: получаем обновлённые данные из БД:
    comment.refresh_from_db()
    # Проверяем, что атрибуты заметки соответствуют обновлённым:
    assert comment.text == form_data['text']


# п.4.2 Пользователь не может редактировать чужие заметки
def test_other_user_cant_edit_comment(
        admin_client,
        form_data,
        comment,
        pk_comment_for_args
):
    url = reverse('news:edit', args=pk_comment_for_args)
    response = admin_client.post(url, form_data)
    # Проверяем, что страница не найдена:
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Получаем новый объект запросом из БД.
    comment_from_db = Comment.objects.get(id=comment.id)
    # Проверяем, что атрибуты объекта из БД равны атрибутам заметки до запроса.
    assert comment.text == comment_from_db.text


# п.4.3 Пользователь может удалять свои заметки
def test_author_can_delete_comment(
        author_client,
        pk_comment_for_args,
        pk_news_for_args
):
    # вывожу кол-во комментов до удаления
    print(Comment.objects.count())
    url = reverse('news:delete', args=pk_comment_for_args)
    url_success = reverse('news:detail', args=pk_news_for_args)
    response = author_client.post(url)
    assertRedirects(response, f'{url_success}#comments')
    assert Comment.objects.count() == 0


# п.4.4 Пользователь не может удалять чужие заметки
def test_other_user_cant_delete_note(
        admin_client,
        pk_comment_for_args,
        pk_news_for_args
):
    url = reverse('news:delete', args=pk_comment_for_args)
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1
