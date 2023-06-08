from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.utils import timezone

# Импортируем модель заметки, чтобы создать экземпляр.
from news.models import Comment, News


@pytest.fixture
# Используем встроенную фикстуру для модели пользователей django_user_model.
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):  # Вызываем фикстуру автора и клиента.
    client.force_login(author)  # Логиним автора в клиенте.
    return client


@pytest.fixture
def news():
    news = News.objects.create(  # Создаём новость.
        title='Заголовок',
        text='Текст новости',
    )
    return news


@pytest.fixture
# Фикстура запрашивает другую фикстуру создания новости.
def comment(author, news):
    comment = Comment.objects.create(  # Создаём объект комментария.
        text='Текст комментария',
        author=author,
        news=news
    )
    return comment


@pytest.fixture
# Фикстура запрашивает другую фикстуру новости.
def pk_news_for_args(news):
    # И возвращает кортеж, который содержит pk новости.
    # На то, что это кортеж, указывает запятая в конце выражения.
    return news.pk,


@pytest.fixture
# Фикстура запрашивает другую фикстуру новости.
def pk_comment_for_args(comment):
    # И возвращает кортеж, который содержит pk комментария.
    # На то, что это кортеж, указывает запятая в конце выражения.
    return comment.pk,


@pytest.fixture
def news_eleven():
    today = datetime.today()
    all_news = []
    for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1):
        news = News(
            title=f'Новость {index}',
            text='Просто текст.',
            # Для каждой новости уменьшаем дату на index дней от today,
            # где index - счётчик цикла.
            date=today - timedelta(days=index)
            )
        all_news.append(news)
    News.objects.bulk_create(all_news)
    return all_news


@pytest.fixture
def comments_three(author, news):
    now = timezone.now()
    for index in range(3):
        # Создаём объект и записываем его в переменную.
        comment = Comment.objects.create(
            text='Текст комментария',
            author=author,
            news=news
        )
        # Сразу после создания меняем время создания комментария.
        comment.created = now + timedelta(days=index)
        # И сохраняем эти изменения.
        comment.save()
    return comment


# Данные для POST-запроса при создании комментария.
# Добавляем фикстуру form_data
@pytest.fixture
def form_data():
    return {
        'text': 'Новый текст комментария',
    }
