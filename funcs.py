import probablepeople as pp
import usaddress
import humps

def address_str_to_dict(string="5757 South Woodlawn avenue, Chicago, IL 60637"):
    """Convert address string into standardized dictionary"""
    # TODO consider lookups for common spellings ("philly, phila.")
    # TODO consider street name formatting, standardization ("ave","AV","AVE.", "avenue" all saved separate at the moment"
    # TODO maybe add formatting https://usaddress.readthedocs.io/en/latest/ to create comparable add1 add2
    d = dict.fromkeys(usaddress.LABELS)
    try:
        tagged_address, address_type = usaddress.tag(string)
    except usaddress.RepeatedLabelError as e:
        tagged_address = e.parsed_string
        tagged_address = {k: v for (n, (v, k)) in enumerate(tagged_address) if
                          k not in [k for (n, (v, k)) in enumerate(tagged_address)][:n]}
    d = {**d, **tagged_address}
    return humps.decamelize(d)

def name_str_to_dict(string="Davids, David Dave Davie", type='person'):
    """Convert a person's name string into standardized dictionary"""
    d = dict.fromkeys(pp.LABELS)
    try:
        tagged_name, name_type = pp.tag(string, type)
    except pp.RepeatedLabelError as e:
        tagged_name = e.parsed_string
        tagged_name = {k: v for (n, (v, k)) in enumerate(tagged_name) if
                       k not in [k for (n, (v, k)) in enumerate(tagged_name)][:n]}
    d = {**d, **tagged_name}
    return humps.decamelize(d)


def test_parse():
    print(name_str_to_dict())
    print(address_str_to_dict())