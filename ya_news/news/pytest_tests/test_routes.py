from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects


# п.1: Главная страница доступна анонимному пользователю.
# п.6: Страницы регистрации, входа, выхода
# доступны анонимным пользователям.
@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',  # Имя параметра функции.
    # Значения, которые будут передаваться в name.
    ('news:home', 'users:login', 'users:logout', 'users:signup')
)
# Указываем в фикстурах встроенный клиент.
# Указываем имя изменяемого параметра в сигнатуре теста.
def test_home_login_availability_for_anonymous_user(client, name):
    # Адрес страницы получаем через reverse():
    url = reverse(name)  # Получаем ссылку на нужный адрес.
    response = client.get(url)  # Выполняем запрос.
    assert response.status_code == HTTPStatus.OK


# п.2: Страница отдельной новости доступна анонимному пользователю.
@pytest.mark.django_db
# Указываем в фикстурах встроенный клиент.
# Указываем имя изменяемого параметра в сигнатуре теста.
def test_detailnews_availability_for_anonymous_user(client, pk_news_for_args):
    # Адрес страницы получаем через reverse():
    # Получаем ссылку на нужный адрес.
    url = reverse('news:detail', args=pk_news_for_args)
    response = client.get(url)  # Выполняем запрос.
    assert response.status_code == HTTPStatus.OK


# п.3 Страницы удаления и редактирования комментария
# доступны автору комментария.
# п.5 Авторизованный пользователь не может зайти на страницы
# редактирования или удаления чужих комментариев (возвращается ошибка 404)
# Параметризуем тестирующую функцию:
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    # Предварительно оборачиваем имена фикстур
    # в вызов функции pytest.lazy_fixture().
    (
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
def test_pages_availability_for_author(
    parametrized_client,
    name,
    pk_comment_for_args,
    expected_status
):
    url = reverse(name, args=pk_comment_for_args)
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


# п.4 При попытке перейти на страницу редактирования или удаления
# комментария анонимный пользователь перенаправляется на страницу авторизации.
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', pytest.lazy_fixture('pk_comment_for_args')),
        ('news:delete', pytest.lazy_fixture('pk_comment_for_args')),
    ),
)
# Передаём в тест анонимный клиент, name проверяемых страниц и args:
def test_redirects(client, name, args):
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
