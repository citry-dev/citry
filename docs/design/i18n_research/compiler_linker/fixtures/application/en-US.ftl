-shared = APPLICATION-EN

my-app-target = { $name } accepted { $terms_link }; details: { $terms_link }.
my-app-wrapper = Application: { my-app-target }
my-app-ordinal = { NUMBER($position, type: "ordinal") ->
    [one] { NUMBER($position, profile: "integer") }st
    [two] { NUMBER($position, profile: "integer") }nd
    [few] { NUMBER($position, profile: "integer") }rd
   *[other] { NUMBER($position, profile: "integer") }th
}

citry-ui-account = { -shared }: { my-app-target }
