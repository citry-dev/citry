from django.urls import path

from components.board_page.board_page import BoardPage
from components.counter.counter import Counter

# Routing to the components' Views with as_view() gives them names that the
# templates can use in {% url %}, as the Django app's views have.
urlpatterns = [
    path('', BoardPage.as_view(), name='page'),
    path('save/', Counter.as_view(), name='save'),
]
