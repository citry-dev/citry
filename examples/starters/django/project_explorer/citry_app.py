from citry import Citry
from citry.contrib.django import secret

citry_app = Citry(autodiscover=False, secret=secret())
