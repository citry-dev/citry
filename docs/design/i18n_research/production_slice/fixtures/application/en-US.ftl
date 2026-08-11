-shared = APPLICATION-EN

my-app-target = { $name } accepted { $terms_link }; details: { $terms_link }.
citry-ui-account = { -shared }: { my-app-target }

my-app-rich-choice = { $count ->
    [one] { $name }: { $terms_link } and again { $terms_link }
   *[other] { $name }: { $terms_link }, then { $terms_link }
}
