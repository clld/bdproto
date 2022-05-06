from sqlalchemy.orm import joinedload, aliased
from clld.web import datatables
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol
from clld.db.models import common
from clld.db.util import get_distinct_values, icontains

from bdproto import models


class LanguageCol(LinkCol):
    def get_obj(self, item):
        return item.language

    def order(self):
        return common.Language.name

    def search(self, qs):
        return icontains(common.Language.name, qs)


class Inventories(datatables.contribution.Contributions):
    def base_query(self, query):
        q = query.join(common.Language).options(joinedload(models.Inventory.language))
        return q

    def col_defs(self):
        return [
            Col(self, "name", model_col=models.Inventory.name),
            LanguageCol(self, "language"),
            Col(
                self,
                "type",
                model_col=models.Inventory.inventory_type,
                choices=get_distinct_values(models.Inventory.inventory_type),
            ),
            Col(self, "source", model_col=models.Inventory.source),
            Col(self, "bibtex key", model_col=models.Inventory.bibtex),
            Col(self, "comments", model_col=models.Inventory.comments),
        ]


class Varieties(datatables.language.Languages):
    family = aliased(models.Variety)
    parent = aliased(models.Variety)

    def base_query(self, query):
        q = (
            query
            .outerjoin(models.Variety.family.of_type(self.family))
            .outerjoin(models.Variety.parent.of_type(self.parent))
            .options(joinedload(models.Variety.parent), joinedload(models.Variety.family))
        )
        return q

    def col_defs(self):
        return [
            LinkCol(self, "name"),
            LinkCol(self, "family", model_col=self.family.name, get_obj=lambda i: i.family),
            LinkCol(self, "parent", model_col=self.parent.name, get_obj=lambda i: i.parent),
            Col(self, "level", model_col=models.Variety.level, choices=get_distinct_values(models.Variety.level)),
            Col(self, "macroarea", model_col=models.Variety.macroarea),
            LinkToMapCol(self, "m"),
            Col(self, "description", model_col=models.Variety.description),
        ]


def includeme(config):
    """register custom datatables"""
    config.register_datatable("contributions", Inventories)
    config.register_datatable("languages", Varieties)
