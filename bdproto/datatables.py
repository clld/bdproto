from sqlalchemy.orm import joinedload, aliased
from clld.web import datatables
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol, filter_number
from clld.web.datatables.contribution import CitationCol
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


class RefCol(Col):
    def get_obj(self, item):
        refs = item.references
        if refs:
            return refs[0].source
        else:
            return None

    def format(self, item):
        source = self.get_obj(item)
        if source:
            return f"{source.author} ({source.year})"
        else:
            return "NA"


class Inventories(datatables.contribution.Contributions):
    def base_query(self, query):
        q = (
            query.join(common.Language)
            .distinct()
            .options(
                joinedload(models.Inventory.language),
                joinedload(common.Contribution.references).joinedload(
                    common.ContributionReference.source
                ),
            )
        )
        return q

    def col_defs(self):
        return [
            LinkCol(self, "name", sTitle="Inventory"),
            LanguageCol(self, "language"),
            Col(
                self,
                "#",
                model_col=models.Inventory.phonemes_count,
            ),
            Col(
                self,
                "type",
                model_col=models.Inventory.inventory_type,
                choices=get_distinct_values(models.Inventory.inventory_type),
            ),
            Col(self, "source", model_col=models.Inventory.source),
            Col(self, "bibtex key", model_col=models.Inventory.bibtex),
            RefCol(self, "ref"),
            CitationCol(self, "cite"),
        ]


class Varieties(datatables.language.Languages):
    family = aliased(models.Variety)
    parent = aliased(models.Variety)

    def base_query(self, query):
        q = (
            query.outerjoin(models.Variety.family.of_type(self.family))
            .outerjoin(models.Variety.parent.of_type(self.parent))
            .options(
                joinedload(models.Variety.parent), joinedload(models.Variety.family)
            )
        )
        return q

    def col_defs(self):
        return [
            LinkCol(self, "name"),
            Col(
                self,
                "#",
                sDescription="Number of inventories",
                bSearchable=False,
                model_col=models.Variety.inventories_count,
            ),
            LinkCol(
                self, "family", model_col=self.family.name, get_obj=lambda i: i.family
            ),
            LinkCol(
                self, "parent", model_col=self.parent.name, get_obj=lambda i: i.parent
            ),
            Col(
                self,
                "level",
                model_col=models.Variety.level,
                choices=get_distinct_values(models.Variety.level),
            ),
            Col(
                self,
                "macroarea",
                model_col=models.Variety.macroarea,
                choices=get_distinct_values(models.Variety.macroarea),
            ),
            LinkToMapCol(self, "m"),
        ]


class Phonemes(datatables.value.Values):
    def col_defs(self):
        if self.contribution:
            return [
                LinkCol(self, "parameter", get_obj=lambda i: i.valueset.parameter),
                Col(
                    self,
                    "description",
                    get_obj=lambda i: i.valueset.parameter,
                    model_col=common.Parameter.description,
                ),
            ]

        elif self.parameter:
            return [
                LinkCol(
                    self,
                    "contribution",
                    get_obj=lambda i: i.valueset.contribution,
                    model_col=common.Contribution.name,
                ),
                LinkCol(
                    self,
                    "language",
                    model_col=common.Language.name,
                    get_obj=lambda i: i.valueset.language,
                ),
                Col(
                    self,
                    "type",
                    model_col=models.Inventory.inventory_type,
                    get_obj=lambda i: i.valueset.contribution,
                    choices=get_distinct_values(models.Inventory.inventory_type),
                ),
                Col(
                    self,
                    "source",
                    get_obj=lambda i: i.valueset.contribution,
                ),
                Col(
                    self,
                    "bibtex key",
                    get_obj=lambda i: i.valueset.contribution,
                    model_col=models.Inventory.bibtex,
                ),
            ]

        return super().col_defs()

    def base_query(self, query):
        query = super().base_query(query)
        if self.parameter:
            query = query.join(common.ValueSet.contribution).options(
                joinedload(common.Value.valueset).joinedload(common.ValueSet.language),
                joinedload(common.Value.valueset).joinedload(
                    common.ValueSet.contribution
                ),
            )
        return query


class InvReprCol(Col):
    __kw__ = {"sClass": "right"}

    def order(self):
        return models.Segment.in_inventories

    def format(self, item):
        segment = self.get_obj(item)
        return f"{segment.in_inventories} ({segment.inv_representation * 100:.1f}%)"

    def search(self, qs):
        return filter_number(models.Segment.in_inventories, qs)


class Parameters(datatables.parameter.Parameters):
    def col_defs(self):
        return [
            LinkCol(self, "name"),
            InvReprCol(self, "#inventories"),
            Col(self, "description"),
        ]

    def get_options(self):
        opts = super().get_options()
        opts["aaSorting"] = [[1, "desc"]]
        return opts


def includeme(config):
    """register custom datatables"""
    config.register_datatable("contributions", Inventories)
    config.register_datatable("languages", Varieties)
    config.register_datatable("values", Phonemes)
    config.register_datatable("parameters", Parameters)
