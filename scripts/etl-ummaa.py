import csv
import re
import pprint

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

all_data = []

# extract data from the spreadsheet
with open("ummaa-textiles.csv") as fin:
    raw_data = csv.DictReader(fin, delimiter=',')
    for entry in raw_data:
        all_data.append(entry)

# transform the data according to the MAP
mapped_data = []
for entry in all_data:
    elem = {}

    # required fields
    elem["dcterms:identifier"] = entry["Object identifier"]
    elem["dcterms:collection"] = entry["Divisions"]

    accdate = entry["AccessionDate"]
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

    elem["dcterms:accrualMethod"] = entry["AccessionMethod"]
    elem["mods:recordIdentifier"] = entry["Accession Number"]
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
        geog = entry["Verbatim Geography"].split("-")
        i = 0
        for i in range(len(geog)):
            if geog[i] == '':
                break;
            elem["mods:subject.hierarchicalGeographic." + gterms[i]] = geog[i]
            i += 1
    if entry["Geographic Location"] != '':
        geog = entry["Geographic Location"]
        gterms = ["citySection", "state"]
        geog = geog.split(", ")
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

    mapped_data.append(elem)

    # pprint.pp(mapped_data)

# export the data to csv
headers = [
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
    "mods:recordInfo.recordInfoNote"
]
with open("output.csv", 'w', newline="", encoding="utf-8") as dataout:
    fout = csv.DictWriter(dataout, fieldnames=headers, extrasaction="ignore", dialect="unix")
    fout.writeheader()
    fout.writerows(mapped_data)


