import pytest
from django.conf import settings
from django.urls import reverse


# п.1 Количество новостей на главной странице — не более 10
# фикстура создания 11 объектов новостей в БД
@pytest.mark.usefixtures('news_eleven')
@pytest.mark.django_db
# В тесте используем фикстуру новости и фикстуру клиента.
def test_news_count(client):
    url = reverse('news:home')
    # Запрашиваем страницу со списком заметок:
    response = client.get(url)
    # Получаем список объектов из контекста:
    object_list = response.context['object_list']
    # Определяем длину списка.
    news_count = len(object_list)
    # Проверяем, что на странице именно 10 новостей.
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


# п.2 Новости отсортированы от самой свежей к самой старой.
# фикстура создания 11 объектов новостей в БД
@pytest.mark.usefixtures('news_eleven')
@pytest.mark.django_db
def test_news_order(client):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    # Получаем даты новостей в том порядке, как они выведены на странице.
    all_dates = [news.date for news in object_list]
    # Сортируем полученный список по убыванию.
    sorted_dates = sorted(all_dates, reverse=True)
    # Проверяем, что исходный список был отсортирован правильно.
    assert all_dates == sorted_dates


# п.3 Комментарии на странице отдельной новости отсортированы от старых к новым
@pytest.mark.usefixtures('comments_three')
@pytest.mark.django_db
def test_comments_order(client, pk_news_for_args):
    url = reverse('news:detail', args=pk_news_for_args)
    response = client.get(url)
    # Проверяем, что объект новости находится в словаре контекста
    # под ожидаемым именем - названием модели.
    assert 'news' in response.context
    # Получаем объект новости.
    news = response.context['news']
    # Получаем все комментарии к новости.
    all_comments = news.comment_set.all()
    # Вытаскиваем даты создания комментариев
    # и формируем список без списочных выражений
    all_dates_comments = []
    for date_comments in all_comments:
        all_dates_comments.append(date_comments.created)
    # Сортируем полученный список по убыванию.
    sorted_dates_comments = sorted(all_dates_comments)
    # Проверяем, что исходный список был отсортирован правильно.
    assert all_dates_comments == sorted_dates_comments


# п.4 Анонимному пользователю недоступна форма для отправки комментария
# на странице отдельной новости
@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, pk_news_for_args):
    url = reverse('news:detail', args=pk_news_for_args)
    response = client.get(url)
    assert 'form' not in response.context


# п.4 Авторизированному пользователю доступна форма для отправки комментария
# на странице отдельной новости
def test_authorized_client_has_form(author_client, pk_news_for_args):
    url = reverse('news:detail', args=pk_news_for_args)
    response = author_client.get(url)
    assert 'form' in response.context
