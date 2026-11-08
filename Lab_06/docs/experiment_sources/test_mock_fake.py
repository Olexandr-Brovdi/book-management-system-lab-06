from unittest.mock import Mock
from book_catalog.models import Book
from book_catalog.protocols import BookRepository
from book_catalog.repositories import InMemoryBookRepository
def test_mock_interaction():
    book = Book("9780000000002","Кобзар","Тарас Шевченко",1840,240)
    repository = Mock(spec=BookRepository)
    repository.all.return_value = (book,)
    assert repository.all() == (book,)
    repository.all.assert_called_once_with()
def test_fake_state():
    book = Book("9780000000002","Кобзар","Тарас Шевченко",1840,240)
    repository = InMemoryBookRepository()
    repository.add(book)
    assert repository.all() == (book,)
