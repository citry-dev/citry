-app-name = Citry

my-app-account-card-greeting = Hello from { -app-name }, { $name }.

my-app-account-card-actions = Actions
    .aria-label = Account actions for { $name }

my-app-terms-acceptance = { $terms_link } was accepted by { $account_name }. <unsafe>&

my-app-inbox-count = { $count ->
    [one] One inbox item
   *[other] { $count } inbox items
}
