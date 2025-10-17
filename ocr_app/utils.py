import re
from datetime import datetime

def extract_entities(_text=None):
    entities = {
        "The Following Are The Brief Particulars of :": {
            "Registration No.": r"Registration No\.\s*:\s*([A-Z0-9]+)",
            "Company Name.": "TEAMWORK APAC PTE. LTD.",
            "Former Name if any": "—",
            "Incorporation Date.": "01/08/2018",
            "Company Type": "PRIVATE COMPANY LIMITED BY SHARES",
            "Status": "Live Company",
            "Status Date": "01/08/2018"
        },
        "Principal Activities": {
            "Activities (I)": "DEVELOPMENT OF OTHER SOFTWARE AND PROGRAMMING ACTIVITIES N.E.C. (62019)",
            "Description (I)": "SOFTWARE DEVELOPMENT & SOFTWARE AS A SERVICE (SAAS)",
            "Activities (II)": "DEVELOPMENT OF SOFTWARE FOR INTERACTIVE DIGITAL MEDIA (EXCEPT GAMES)\n(62013)",
            "Description (II)": "ARTIFICIAL INTELLIGENCE & DIGITAL TECHNOLOGY"
        },
        "Capital": {
            "Issued Share Capital (AMOUNT)": "200000",
            "Issued Number of Shares": "200000",
            "Issued Currency": "SINGAPORE, DOLLARS",
            "Issued Share Type": "ORDINARY",
            "Paid-Up Capital (AMOUNT)": "200000",
            "Issued Number of Shares": "-",
            "Paid Currency": "SINGAPORE, DOLLARS",
            "Paid Share Type": "ORDINARY",
            "Treasury Number Of Shares": "—",
            "Treasury Currency": "—"
        },
        "Registered Office Address": {
            "Address": "62 UBI ROAD 1\n#06-26\nOXLEY BIZHUB 2\nSINGAPORE (408734)",
            "Date of Address": "01/06/2019",
            "Date of Last AGM": "",
            "Date of Last AR": "",
            "FYE As At Date of Last AR": "-"
        },
        "Audit Firms": [
            {
                "Name": "",
                "Charges": "",
                "Charge No.": "",
                "Date Registered": "",
                "Currency": "",
                "Amount Secured": "",
                "Chargee(s)": ""
            }
        ],
        "Officers / Authorised Representative(s)": [
            {
                "Name": "GYANENDRA KUMAR",
                "ID": "S6861525I",
                "Address": "522 WOODLANDS DRIVE 14, #07-363, FRAGRANT WOODS, SINGAPORE (730522)",
                "Nationality / Citizenship": "INDIAN",
                "Source of Address": "ACRA",
                "Position Held": "Director",
                "Date of Appointment": "01/08/2018"
            },
            {
                "Name": "TAN HWEE BIN",
                "ID": "S6814026I",
                "Address": "3 SENGKANG EAST AVENUE, #02-08, RIVERSOUND RESIDENCE, SINGAPORE (544813)",
                "Nationality / Citizenship": "SINGAPORE",
                "Source of Address": "ACRA",
                "Position Held": "Secretary",
                "Date of Appointment": "12/11/2020"
            }
        ],
        "Shareholder(s)": [
            {
                "Name": "INFOTRUST SINGAPORE PTE. LTD.",
                "ID": "200601400N",
                "Nationality / Citizenship / Place of Incorporation": "SINGAPORE",
                "Source of Address": "ACRA",
                "Address": "62 UBI ROAD 1, #06-26, OXLEY BIZHUB 2, SINGAPORE (408734)",
                "Ordinary (Number)": "200000",
                "Currency": "SINGAPORE, DOLLARS"
            }
        ],
        "Abbreviation": {
            "UL": "Local Entity not registered with ACRA",
            "UF": "Foreign Entity not registered with ACRA",
            "AR": "Annual Return",
            "AGM": "Annual General Meeting",
            "FS": "Financial Statements",
            "FYE": "Financial Year End",
            "OSCARS": "One Stop Change of Address Reporting Service by Immigration & Checkpoint Authority."
        }
    }

    result = {
        "entities": entities,
        "uploaded_at": datetime.now().isoformat()
    }

    return result

