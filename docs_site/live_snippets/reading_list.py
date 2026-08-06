from citry import Component


class ReadingList(Component):
    class Kwargs:
        books: list[str]
        heading: str = "Reading list"
        empty_message: str = "Your list is empty."
        show_count: bool = True

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {
            "books": kwargs.books,
            "heading": kwargs.heading,
            "empty_message": kwargs.empty_message,
            "show_count": kwargs.show_count,
            "total": len(kwargs.books),
        }

    template = """
      <section>
        <h2>{{ heading }}</h2>
        <p c-if="show_count and total > 0">
          {{ total }} {{ "book" if total == 1 else "books" }}
        </p>
        <ul c-data-count="total">
          <li c-for="book in books">{{ book }}</li>
          <li c-empty>{{ empty_message }}</li>
        </ul>
      </section>
    """


reading_list = ReadingList(
    heading="Books for the weekend",
    books=["A Wizard of Earthsea", "Kindred", "Piranesi"],
)

if __name__ == "__main__":
    print(reading_list)

reading_list
