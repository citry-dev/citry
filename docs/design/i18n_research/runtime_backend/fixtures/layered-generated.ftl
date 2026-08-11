# Compiler-generated stand-in for two source layers that both define `-shared`.
# The app-owned public message wins normal precedence, while the library-owned
# wrapper retains its own private term. Internal IDs are illustrative only.
-citry-app-shared = application private term
-citry-lib-shared = library private term

citry-app-public = application override via { -citry-app-shared }
citry-lib-wrapper = Library wrapper: { citry-app-public } / { -citry-lib-shared }
