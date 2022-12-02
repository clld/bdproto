import logging

from pathlib import Path
from sqlalchemy.orm import joinedload

from pycldf import StructureDataset
from clldutils.misc import nfilter
from clldutils.color import qualitative_colors
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex

import bdproto
from bdproto import models


def main(args):
    data = Data()
    data.add(
        common.Dataset,
        bdproto.__name__,
        id=bdproto.__name__,
        domain="bdproto.clld.org",
        publisher_name="Max Planck Institute for Evolutionary Anthropology",
        publisher_place="Leipzig",
        publisher_url="http://www.eva.mpg.de",
        license="http://creativecommons.org/licenses/by/4.0/",
        jsondata={
            "license_icon": "cc-by.png",
            "license_name": "Creative Commons Attribution 4.0 International License",
        },
    )

    cldf_dataset_path = (
        Path(__file__).parent.parent.parent.parent
        / "bdproto-cldf"
        / "cldf"
        / "StructureDataset-metadata.json"
    )

    if not cldf_dataset_path.exists():
        print(
            f"{cldf_dataset_path} does not exist.\n"
            f"Please clone the cldf dataset into {cldf_dataset_path.parent.parent}"
        )
        return

    cldf_dataset = StructureDataset.from_metadata(cldf_dataset_path)

    for source in bibtex.Database.from_file(cldf_dataset.bibpath):
        source_obj = bibtex2source(source)
        data.add(common.Source, source_obj.id, _obj=source_obj)

    DBSession.flush()

    for lang in cldf_dataset["LanguageTable"]:
        if not lang["ID"]:
            logging.warning(f"Language row without ID: {str(lang)}")
            continue
        data.add(
            models.Variety,
            lang["ID"],
            id=lang["ID"],
            name=lang["Name"],
            macroarea=lang["Macroarea"],
            latitude=lang["Latitude"],
            longitude=lang["Longitude"],
            level=lang["level"],
            description=lang["description"],
        )

    # add family and parent relationships to languages
    for lang in cldf_dataset["LanguageTable"]:
        if not lang["ID"]:
            continue

        if lang["parent_id"] and lang["parent_id"] != "NA":
            try:
                data["Variety"][lang["ID"]].parent = data["Variety"][lang["parent_id"]]
            except KeyError:
                logging.warning(
                    f"parent {lang['parent_id']} of {lang['ID']} not in LanguageTable"
                )

        if lang["family_id"] and lang["family_id"] != "NA":
            try:
                data["Variety"][lang["ID"]].family = data["Variety"][lang["family_id"]]
            except KeyError:
                logging.warning(
                    f"family {lang['family_id']} of {lang['ID']} not in LanguageTable"
                )

    DBSession.flush()

    for contrib in cldf_dataset["ContributionTable"]:
        o = data.add(
            models.Inventory,
            contrib["ID"],
            pk=contrib["ID"],
            id=contrib["ID"],
            name=":".join([contrib["Glottocode"], contrib["ID"]]),
            language=data["Variety"].get(contrib["Glottocode"]),
            inventory_type=contrib["InventoryType"],
            source=contrib["Source"],
            bibtex=contrib["BibtexKey"],
            comments=contrib["Comments"] if contrib["Comments"] != "NA" else "",
        )
        if o.bibtex in data["Source"]:
            DBSession.add(
                common.ContributionReference(
                    source=data["Source"][o.bibtex], contribution=o
                )
            )

    for parameter in cldf_dataset["ParameterTable"]:
        data.add(
            models.Segment,
            parameter["ID"],
            id=parameter["ID"],
            name=parameter["Name"],
            description=parameter["Description"],
        )

    value_iterator = cldf_dataset["ValueTable"].iterdicts(log=logging.getLogger())

    for value in value_iterator:
        vs = common.ValueSet(
            id=value["ID"],
            language=data["Variety"][value["Language_ID"]],
            parameter=data["Segment"][value["Parameter_ID"]],
            contribution=data["Inventory"][value["Inventory_ID"]],
        )
        DBSession.add(common.Value(id=value["ID"], name=value["Value"], valueset=vs))


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
    total_inventories = DBSession.query(models.Inventory).count()
    q = DBSession.query(models.Segment).outerjoin(common.ValueSet).distinct()
    for segment in q:
        segment.in_inventories = len(segment.valuesets)
        segment.total_inventories = total_inventories

    for variety in DBSession.query(models.Variety).options(
        joinedload(models.Variety.inventories)
    ):
        variety.inventories_count = len(variety.inventories)

    for inventory in DBSession.query(models.Inventory).options(
        joinedload(models.Inventory.valuesets)
    ):
        inventory.phonemes_count = len(inventory.valuesets)
