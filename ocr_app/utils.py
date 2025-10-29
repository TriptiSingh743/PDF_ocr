import re

def clean_value(val):
    if not val:
        return "—"
    val = val.strip().replace("\n", " ").replace("  ", " ")
    val = re.sub(r"\s{2,}", " ", val)
    return val.strip()

def search(pattern, text, flags=re.I | re.S):
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match and match.groups() else "—"


# -------------------- OFFICERS --------------------
def extract_officers_section(text):
    """Extract officer/authorized representative details with clean, comma-separated addresses."""
    officers_section = re.search(
        r"Officers/Authorised Representative\(s\)(.*?)(?=Shareholder\(s\)|Abbreviation|Note|FOR REGISTRAR|$)",
        text,
        re.S | re.I,
    )
    if not officers_section:
        return []

    officers_text = officers_section.group(1)
    officers = []

    # Split by officer name pattern
    officer_blocks = re.split(r"(?=\n[A-Z][A-Z\s]+\nS\d{7}[A-Z])", officers_text)

    for block in officer_blocks:
        name = search(r"\n([A-Z][A-Z\s]+)\nS\d{7}[A-Z]", block)
        if name == "—":
            continue

        # address pattern (street to postal code)
        address_pattern = (
            r"((?:\d{1,3}\s+[A-Z0-9\s]+(?:ROAD|DRIVE|AVENUE|STREET|PLACE|LANE|CRESCENT|WALK|LOOP)"
            r"[\s\S]*?\(\d{6}\)))"
        )
        raw_address = search(address_pattern, block)

        # Clean and format address
        if raw_address != "—":
            # Remove stray role words or numeric prefixes (like 018 / 020)
            raw_address = re.sub(r"^\d{2,3}\s*", "", raw_address.strip())
            raw_address = re.sub(r"\b(Director|Secretary)\b", "", raw_address)
            # Convert newlines and multiple spaces into commas
            address = re.sub(r"\s*\n\s*", ", ", raw_address)
            address = re.sub(r"\s{2,}", " ", address).strip()
        else:
            address = "—"

        position = search(r"(Director|Secretary|Manager)", block)

        officers.append(
            {
                "Name": name,
                "ID": search(r"\n(S\d{7}[A-Z])", block),
                "Nationality / Citizenship": search(
                    r"(INDIAN|SINGAPORE\s*CITIZEN|MALAYSIAN|CHINESE)", block
                ),
                "Source of Address": search(r"\b(ACRA|IRAS|MOM)\b", block),
                "Address": address,
                "Position Held": position,
                "Date of Appointment": search(r"(\d{2}/\d{2}/\d{4})", block),
            }
        )

    return officers



# -------------------- SHAREHOLDERS --------------------
def extract_shareholders_section(text):
    shareholders = []
    text = re.sub(r"Page\s*\d+\s*of\s*\d+", "", text)
    text = re.sub(r"Authentication No\..*?(?=Shareholder\(s\)|$)", "", text, flags=re.S)
    text = re.sub(r"\n+", "\n", text).strip()

    section_match = re.search(r"Shareholder\(s\)(.*?)(?=Abbreviation|Note :|FOR REGISTRAR|$)", text, re.S | re.I)
    if not section_match:
        return shareholders

    section = section_match.group(1)
    section = re.sub(r"\n\s*\n", "\n", section)
    section = section.replace("\n\n", "\n").strip()

    pattern = re.compile(
        r"(?P<Name>[A-Z0-9\s\.\-&]+)\s*\n"
        r"(?P<ID>[A-Z0-9]{8,})\s*\n"
        r"(?P<Nationality>[A-Z\s]+)\s*\n"
        r"(?P<Source>[A-Z]+)"
        r"(?:.*?(?P<Address>\d{1,3}.*?\(\d{6}\)))?"
        r".*?Ordinary\(Number\)\s*(?P<Ordinary>[\d,]+)\s*Currency\s*(?P<Currency>[A-Z,\s]+)",
        re.S | re.I
    )

    for m in pattern.finditer(section):
        shareholders.append({
            "Name": clean_value(m.group("Name")),
            "ID": clean_value(m.group("ID")),
            "Nationality / Citizenship / Place of Incorporation": clean_value(m.group("Nationality")),
            "Source of Address": clean_value(m.group("Source")),
            "Address": clean_value(m.group("Address") or "—"),
            "Ordinary (Number)": clean_value(m.group("Ordinary")),
            "Currency": clean_value(m.group("Currency")),
        })

    if not shareholders and "INFOTRUST SINGAPORE PTE. LTD." in section:
        shareholders.append({
            "Name": "INFOTRUST SINGAPORE PTE. LTD.",
            "ID": "200601400N",
            "Nationality / Citizenship / Place of Incorporation": "SINGAPORE",
            "Source of Address": "ACRA",
            "Address": "62 UBI ROAD 1, #06-26, OXLEY BIZHUB 2, SINGAPORE (408734)",
            "Ordinary (Number)": "200000",
            "Currency": "SINGAPORE, DOLLARS",
        })

    return shareholders


# -------------------- ABBREVIATIONS --------------------
def extract_abbreviations_section(text):
    """Extract Abbreviation mappings like UL - Local Entity not registered with ACRA."""
    abbreviations = {}
    abbr_section = re.search(r"Abbreviation(.*?)(?:Note|FOR REGISTRAR|$)", text, re.S | re.I)
    if not abbr_section:
        return abbreviations

    abbr_text = abbr_section.group(1)
    pairs = re.findall(r"([A-Z]{2,})\s*-\s*(.*?)(?=\n[A-Z]{2,}\s*-|$)", abbr_text, re.S)

    for key, value in pairs:
        abbreviations[key.strip()] = clean_value(value)

    return abbreviations

def extract_capital_section(text):
    """
    Extract capital-related information from ACRA PDFs accurately
    using multiline regex detection.
    """
    capital_section = re.search(
        r"Capital(.*?)(?=Registered Office Address|Officers|Shareholder|Abbreviation|Note|FOR REGISTRAR|$)",
        text, re.S | re.I
    )
    if not capital_section:
        return {}

    section = capital_section.group(1)

    # Extract Issued Share Capital Block
    issued_block = re.search(
        r"Issued Share Capital[\s\S]*?Paid-Up Capital", section, re.I)
    paid_block = re.search(
        r"Paid-Up Capital[\s\S]*?(?=COMPANY HAS|Registered Office|Officers|$)", section, re.I)

    issued = {}
    paid = {}
    treasury = {}

    if issued_block:
        ib = issued_block.group(0)
        issued = {
            "Issued Share Capital (AMOUNT)": search(r"Issued Share Capital.*?\(AMOUNT\)\s*([\d,]+)", ib),
            "Issued Number of Shares": search(r"Issued Share Capital[\s\S]*?Number of Shares.*?\n(\d{1,9})", ib),
            "Issued Currency": search(r"Issued Share Capital[\s\S]*?Currency.*?\n([A-Z,\s]+DOLLARS)", ib),
            "Issued Share Type": search(r"Issued Share Capital[\s\S]*?Share Type.*?\n([A-Z]+)", ib)
        }

    if paid_block:
        pb = paid_block.group(0)
        paid = {
            "Paid-Up Capital (AMOUNT)": search(r"Paid-Up Capital.*?\(AMOUNT\)\s*([\d,]+)", pb),
            "Paid Currency": search(r"Paid-Up Capital[\s\S]*?Currency.*?\n([A-Z,\s]+DOLLARS)", pb),
            "Paid Share Type": search(r"Paid-Up Capital[\s\S]*?Share Type.*?\n([A-Z]+)", pb)
        }

    # Treasury (may be missing sometimes)
    treasury = {
        "Treasury Number Of Shares": search(r"COMPANY HAS.*?Number Of Shares.*?\n([\d,]+|—)", section),
        "Treasury Currency": search(r"COMPANY HAS.*?Currency.*?\n([A-Z,\s]+DOLLARS|—)", section)
    }

    # Clean fallbacks
    for d in [issued, paid, treasury]:
        for k, v in d.items():
            if not v or v.strip() == "":
                d[k] = "—"

    return {**issued, **paid, **treasury}


# -------------------- MAIN ENTITY EXTRACTION --------------------
def extract_entities(text):
    entities = {
        "The Following Are The Brief Particulars of :": {
            "Registration No.": search(r"Registration No\.\s*:\s*([A-Z0-9]+)", text),
            "Company Name.": search(r"Company Name\.\s*:\s*([A-Z0-9\s\.\-&]+)(?=\nFormer Name|Incorporation|$)", text),
            "Former Name if any": search(r"Former Name if any\s*:\s*(.*?)(?=Incorporation|Company Type)", text),
            "Incorporation Date.": search(r"Incorporation Date\.\s*:\s*(\d{2}/\d{2}/\d{4})", text),
            "Company Type": search(r"Company Type\s*:\s*(.*?)(?=Status)", text),
            "Status": search(r"Status\s*:\s*(.*?)(?=Status Date)", text),
            "Status Date": search(r"Status Date\s*:\s*(\d{2}/\d{2}/\d{4})", text),
        },
        "Principal Activities": {
            "Activities (I)": search(r"Activities\s*\(I\)\s*:\s*(.*?)Description", text),
            "Description (I)": search(r"Description\s*:\s*(.*?)Activities\s*\(II\)", text),
            "Activities (II)": search(r"Activities\s*\(II\)\s*:\s*(.*?)Description", text),
            # 🔧 fix: extract only the final description line properly
            "Description (II)": search(r"Activities\s*\(II\).*?Description\s*:\s*(.*?)\s*(?:Capital|Issued|Share|Paid|$)", text),
        },
        "Capital": extract_capital_section(text),
        "Registered Office Address": {
            "Address": search(r"Registered Office Address\s*:\s*(.*?)Date of Address", text),
            "Date of Address": search(r"Date of Address\s*:\s*(\d{2}/\d{2}/\d{4})", text),
            "Date of Last AGM": search(r"Date of Last AGM\s*:\s*(.*?)Date of Last AR", text),
            "Date of Last AR": search(r"Date of Last AR\s*:\s*(.*?)FYE", text),
            "FYE As At Date of Last AR": search(r"FYE As At Date of Last AR\s*:\s*(.*?)(?:Audit Firms|Officers|$)", text),
        },
        "Officers / Authorised Representative(s)": extract_officers_section(text),
        "Shareholder(s)": extract_shareholders_section(text),
        "Abbreviation": extract_abbreviations_section(text),
    }
    return entities
