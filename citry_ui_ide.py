import citry_ui
from citry import Citry

app = Citry(autodiscover=False)
app.register_library(citry_ui)
