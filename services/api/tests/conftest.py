import os

from hypothesis import settings

# `ci` runs more examples; select it with HYPOTHESIS_PROFILE=ci.
settings.register_profile("ci", max_examples=500)
settings.register_profile("dev", max_examples=100)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
