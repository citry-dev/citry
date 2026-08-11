import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ResponsivePopover(Component):
    template = """
      <section class="responsive-popover" dir="rtl">
        <c-CPopover
          placement="bottom-start"
          style="--cui-popover-inline-size: 28rem"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">افتح سجل المريخ</c-CButton>
          </c-fill>
          <c-fill name="title">سجل المريخ الطويل</c-fill>
          <c-fill name="description">محتوى يختبر الاتجاه والعرض الضيق</c-fill>
          <c-fill name="default">
            <p>يبقى السطح داخل مساحة العرض ويتيح التمرير عند الحاجة.</p>
            <p>OlympusMonsSummitTraverseObservationIdentifier2026</p>
            <p>هبطت المركبة قرب سهل صخري واسع، ثم بدأت قياس الغبار والرياح.</p>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.responsive-popover) {
        min-block-size: 14rem;
        padding-block: 3rem;
      }
    """


preview = ResponsivePopover()

preview  # noqa: B018
