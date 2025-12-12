import csv
import re
import os
from pathlib import Path

# +-----------+
# |    MAP    |
# +-----------+
# "Object identifier"   -> dcterms:identifier
# "Divisions"           -> dcterms:collection
# "Accession Number"    -> mods:recordIdentifier
# "AccessionMethod"     -> dcterms:accrualMethod
# "AccessionDate"       -> mods:dateOther
# "Quantity"            -> mods:physicalDescription.extent
# "Type"                -> mods:typeOfResource
# "Original Number"     -> mods:recordInfo.recordInfoNote
# "Other Numbers"       -> mods:recordInfo.recordInfoNote
# "Object Type"         -> dcterms:type
# "Materials"           -> dcterms:medium
# "Display Date"        -> dcterms:date
# "Provenience"         -> dcterms:provenance
# "Verbatim Geography"  -> mods:subject.hierarchicalGeographic.continent
#                       -> mods:subject.hierarchicalGeographic.country
#                       -> mods:subject.hierarchicalGeographic.region
#                       -> mods:subject.hierarchicalGeographic.state
# "Geographic Location" -> mods:subject.hierarchicalGeographic.citySection
#                       -> mods:subject.hierarchicalGeographic.state
# "Political Location"  -> mods:subject.hierarchicalGeographic.city
# "Culture"             -> mods:originInfo
# "Description"         -> mods:abstract
# "Curatorial Notes"    -> mods:recordInfo.recordInfoNote

def is_textile(obj):
    textile_object_types = {"bag", "belt", "blanket", "blouse", "bracelet", "breechcloth", "charm", "cloth fragments", "coat", "cordage", "earring", "fan", "hat", "headdress", "jacket", "kris", "lamp", "lid (cover)", "money", "necklace", "pants", "pocket", "quiver", "sarong", "scarf", "sheath", "shirt", "skirt", "slipper", "strainer (or sieve)", "table cloth", "tapestry", "textile", "unknown"}
    textile_descriptions = {"textile"}
    textile_materials = {"cotton", "fiber", "textile", "silk"}

    for objtype in textile_object_types:
        if objtype in obj["Object Type"].lower():
            for desc in textile_descriptions:
                if desc in obj["Description"].lower():
                    return True
            for mat in textile_materials:
                if mat in obj["Materials"].lower():
                    return True
    return False


all_data = []

root_dir = Path(os.getcwd()).parent
err_count = 0

logger = open("log.txt", "w")

# extract data from the spreadsheet
with open("UMMAA_all_Philippine_objects-for_distribution.csv") as fin:
    raw_data = csv.DictReader(fin, delimiter=',')
    for entry in raw_data:
        if is_textile(entry):
            all_data.append(entry)

print("LOG:", len(all_data), "objects extracted", file=logger)

# transform the data according to the MAP
mapped_data = []
for entry in all_data:
    elem = {}

    # required fields
    elem["dcterms:identifier"] = entry["Object identifier"]
    elem["dcterms:collection"] = entry["Divisions"]

    accessioninfo = entry["Accession Description"].split(' ')
    accdate = accessioninfo[-2]
    match = re.search("\d{2}/\d{2}/\d{4}", accdate) # MM/DD/YYYY format
    if match:
        splitdate = accdate.split("/")
        accdate = splitdate[2] + "-" + splitdate[0] + "-" + splitdate[1]
    match = re.search("\d{2}/\d{4}", accdate) # MM/YYYY format
    if match:
        splitdate = accdate.split("/")
        accdate = splitdate[1] + "-" + splitdate[0]
    match = re.search("\d{4}s", accdate) # YYYYs format (use EDTF - YYY0/YYY9)
    if match:
        splitdate = accdate[:-2]
        accdate = splitdate + "0/" + splitdate + "9"
    match = re.search("\d{4}", accdate) # YYYY format
    if match:
        accdate = accdate
    match = re.search("\d{2}/\d{2}/\d{2}", accdate) # MM-DD-YY format
    if match:
        splitdate = accdate.split("/")
        accdate = "19" + splitdate[2] + "-" + splitdate[0] + "-" + splitdate[1]
    elem["mods:dateOther"] = accdate

    elem["dcterms:accrualMethod"] = accessioninfo[-3]
    if elem["dcterms:accrualMethod"] == "Expedition":
        elem["dcterms:accrualMethod"] = "UMMAA Expedition"

    if entry["Accession Number"]:
        elem["mods:recordIdentifier"] = entry["Accession Number"].split(": ")[1].strip()
    else:
        elem["mods:recordIdentifier"] = "0"
    elem["dcterms:type"] = entry["Object Type"]
    elem["dcterms:medium"] = entry["Materials"]
    elem["mods:abstract"] = entry["Description"]

    # optional fields
    if entry["Quantity"] != '':
        elem["mods:physicalDescription.extent"] = entry["Quantity"]
    if entry["Type"] != '':
        elem["mods:typeOfResource"] = entry["Type"]
    if entry["Display Date"] != '':
        # XXX: no textile items use this attribute
        elem["dcterms:date"] = entry["Display Date"]
    if entry["Provenience"] != '':
        elem["dcterms:provenance"] = entry["Provenience"]
    if entry["Culture"] != '':
        elem["mods:originInfo"] = entry["Culture"]
    if entry["Verbatim Geography"] != '':
        gterms = ["continent", "region", "country", "state"]
        # XXX: sometimes there's a fifth location--municipality?
        geog = entry["Verbatim Geography"].split("-", maxsplit=len(gterms)-1)
        i = 0
        for i in range(len(geog)):
            if geog[i] == '':
                break;
            elem["mods:subject.hierarchicalGeographic." + gterms[i]] = geog[i]
            i += 1
    if entry["Geographic Location"] != '':
        geog = entry["Geographic Location"]
        gterms = ["citySection", "state"]
        geog = geog.split(", ", maxsplit=len(gterms)-1)
        i = 0
        for i in range(len(geog)):
            elem["mods:subject.hierarchicalGeographic." + gterms[i]] = geog[i]
            i += 1

    # XXX: unclear if this is multiple locations or multiple granularities
    if entry["Political Location"] != '':
        elem["mods:subject.hierarchicalGeographic.city"] = entry["Political Location"]

    if entry["Original Number"] != '':
        elem["mods:recordInfo.recordInfoNote"] = entry["OriginalNumber"]

    if entry["Other Numbers"] != '':
        elem["mods:recordInfo.recordInfoNote"] = entry["Other Numbers"]

    if entry["Curatorial Notes"] != '':
        elem["mods:recordInfo.recordInfoNote"] = entry["Curatorial Notes"]

    # add fields required for CollectionBuilder
    elem["objectid"] = entry["Object identifier"].replace("-", "_")
    elem["filename"] = elem["objectid"] + ".jpg"
    elem["title"] = elem["objectid"] + ": " + elem["mods:abstract"].split("\n")[0].split(".")[0]
    elem["format"] = "image/jpeg"

    img_dir = "objects/"
    imgname = img_dir + elem["objectid"] + ".jpg"
    path = root_dir / imgname
    if path.exists():
        elem["object_location"] = imgname
        elem["image_small"] = img_dir + "small/" + elem["objectid"] + "_sm.jpg"
        elem["image_thumb"] = img_dir + "thumbs/" + elem["objectid"] + "_th.jpg"
    else:
        err_count += 1
        print("ERR: No image found for", elem["objectid"], file=logger)

    mapped_data.append(elem)

# export the data to csv
headers = [
    "objectid",
    "filename",
    "title",
    "format",
    "dcterms:identifier",
    "dcterms:collection",
    "mods:recordIdentifier",
    "dcterms:accrualMethod",
    "mods:dateOther",
    "mods:physicalDescription.extent",
    "mods:typeOfResource",
    "mods:recordInfo.recordInfoNote",
    "mods:recordInfo.recordInfoNote",
    "dcterms:type",
    "dcterms:medium",
    "dcterms:date",
    "dcterms:provenance",
    "mods:subject.hierarchicalGeographic.continent",
    "mods:subject.hierarchicalGeographic.country",
    "mods:subject.hierarchicalGeographic.region",
    "mods:subject.hierarchicalGeographic.state",
    "mods:subject.hierarchicalGeographic.citySection",
    "mods:subject.hierarchicalGeographic.state",
    "mods:subject.hierarchicalGeographic.city",
    "mods:originInfo",
    "mods:abstract",
    "mods:recordInfo.recordInfoNote",
    "object_location",
    "image_small",
    "image_thumb"
]
with open("../_data/ummaa-objects.csv", 'w', newline="", encoding="utf-8") as dataout:
    fout = csv.DictWriter(dataout, fieldnames=headers, extrasaction="ignore", dialect="unix")
    fout.writeheader()
    fout.writerows(mapped_data)

if err_count > 0:
    print(err_count, "errors found in", len(mapped_data), "processed objects", file=logger)

if logger:
    logger.close()

if err_count > 0:
    exit("Errors occurred during ETL, see scripts/log.txt")
