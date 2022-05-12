import logging

from pathlib import Path

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
        publisher_name="Max Planck Institute for the Science of Human History",
        publisher_place="Jena",
        publisher_url="http://www.shh.mpg.de",
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

    for lang in cldf_dataset["LanguageTable"]:
        if not lang["ID"]:
            continue
        data.add(
            models.Variety,
            lang["ID"],
            id=lang["ID"],
            name=lang["Name"],
            macroarea=lang["Macroarea"],
            latitude=lang["Latitude"],
            longitude=lang["Longitude"],
            family_id=lang["family_id"],
            parent_id=lang["parent_id"],
            level=lang["level"],
            description=lang["description"],
        )

    for contrib in cldf_dataset["ContributionTable"]:
        data.add(
            models.Inventory,
            contrib["ID"],
            pk=contrib["ID"],
            id=contrib["ID"],
            name=":".join([contrib["Glottocode"], contrib["ID"]]),
            language_pk=contrib["Glottocode"],
            inventory_type=contrib["InventoryType"],
            source=contrib["Source"],
            bibtex=contrib["BibtexKey"],
            comments=contrib["Comments"] if contrib["Comments"] != "NA" else "",
        )

    for parameter in cldf_dataset["ParameterTable"]:
        data.add(
            common.Parameter,
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
            parameter=data["Parameter"][value["Parameter_ID"]],
            contribution=data["Inventory"][value["Inventory_ID"]],
        )
        DBSession.add(common.Value(id=value["ID"], name=value["Value"], valueset=vs))


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
