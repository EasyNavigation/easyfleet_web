# EasyFleet web

This folder holds the source and configuration files used to generate the
[EasyFleet documentation](https://github.com/EasyNavigation/EasyFleet) web site.

Dependencies for Build:

A Python virtualenv, shared with the `easynavigation.github.io` site next to
this one, lives at `../venv` (i.e. `web/venv`, one level up from this
folder). Create it once, then activate it whenever you want to build either
site:

``` bash
cd web
python3 -m venv venv
source venv/bin/activate
pip install -r easyfleet.github.io/requirements.txt
```

On later sessions, just `source ../venv/bin/activate` (or `web/venv/bin/activate`
from the workspace root) before building.

Build the docs locally with `make html` and you'll find the built docs entry point in `_build/html/index.html`.
