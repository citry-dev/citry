# AlertDialog

`CAlertDialog` presents an urgent modal decision with required title,
description, cancel, and action content.

- Authoritative design: [`docs/design/ui_components/alert-dialog.md`](../../../../../../../docs/design/ui_components/alert-dialog.md)
- Public guide: [`api.md`](api.md)
- Structured API: [`api.yml`](api.yml)

The family deliberately reuses `CDialog`'s native modal runtime. Keep outside
dismissal disabled, initial focus on Cancel, and the public AlertDialog CSS
variables aligned with the shared Dialog implementation.
