import collections
import functools

from pyramid.config import Configurator

from clld.interfaces import IMapMarker, IValueSet, IValue, IDomainElement
from clldutils.svg import pie, icon, data_url
from clld.web.app import menu_item
# we must make sure custom models are known at database initialization!
from bdproto import models





def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['route_patterns'] = {
        'contributions': '/inventories',
        'contribution': r'/inventories/view/{id:[^/\.]+}',
    }
    config = Configurator(settings=settings)
    config.include('clld.web.app')

    config.include('clldmpg')

    config.register_menu(
        (
            "languages",
            functools.partial(menu_item, "languages", label="Languages"),
        ),
        (
            "contributions",
            functools.partial(menu_item, "contributions", label="Inventories"),
        ),
        (
            "parameters",
            functools.partial(menu_item, "parameters", label="Phonemes"),
        ),
        (
            "values",
            functools.partial(menu_item, "values", label="Values"),
        ),
    )

    return config.make_wsgi_app()
