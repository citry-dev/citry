from citry import Component


class StatusCard(Component):
    class Kwargs:
        title: str
        complete: int
        total: int

    def template_data(self, kwargs: Kwargs, slots):  # noqa: ARG002
        progress = kwargs.complete / kwargs.total
        return {
            "title": kwargs.title,
            "complete": kwargs.complete,
            "total": kwargs.total,
            "progress": round(progress * 100),
        }

    template = """
      <article class="status-card">
        <span>{{ title }}</span>
        <strong>{{ progress }}%</strong>
        <progress
          c-value="complete"
          c-max="total"
        ></progress>
      </article>
    """
