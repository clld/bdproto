from pathlib import Path

from clld.web.assets import environment

import bdproto


environment.append_path(
    Path(bdproto.__file__).parent.joinpath('static').as_posix(),
    url='/bdproto:static/')
environment.load_path = list(reversed(environment.load_path))
