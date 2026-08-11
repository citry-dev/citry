### Zdrojové application messages used by the i18n design spike.

-app-name = Citry

# Greeting shown above an account summary.
# @param {str} $name - User name.
my-app-account-card-greeting = Welcome to { -app-name }, { $name }.

# Accessible label for the account actions control.
# @param {str} $name - User name.
my-app-account-card-actions = Actions
    .aria-label = Actions for { $name }

# Terms acceptance copy with one application-owned link.
# @param {str} $account_name - Account display name.
# @param {Slot} $terms_link - Link to the terms document.
my-app-terms-acceptance = { $account_name } accepted the { $terms_link }.

# Inbox item count.
# @param {int} $count - Number of inbox items.
my-app-inbox-count = { $count ->
    [one] One inbox item
   *[other] { $count } inbox items
}
