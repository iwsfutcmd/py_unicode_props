from collections import defaultdict
import sys
from fractions import Fraction

import regex

prop_dict = regex._regex_core.PROPERTIES
prop_val_dict = regex._regex_core.PROPERTY_NAMES

def check_if_number(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def get_numeric_value(string):
    try:
        return int(string)
    except ValueError:
        try:
            return Fraction(string)
        except ValueError:
            return float(string)

def IPC_adjust(string):
    if string == "NA": 
        return string
    else:
        if string == "VISUALORDERLEFT":
            return "Visual_Order_Left"
        return "_And_".join(string.split("AND")).title()

prop_val_dict_adjustments = {
    "GENERALCATEGORY": (lambda k: k.title(), lambda k: len(k) == 2 and not k.endswith("&") and k != "LC"),
    "SCRIPT": (lambda k: k.title(), lambda k: len(k) == 4 and not k.startswith("Q")),
    # "WORDBREAK": (lambda k: k.title() if k in {"EXTEND", "WSEGSPACE"} else k, lambda k: k in {"EXTEND", "WSEGSPACE"} or len(k) <= 3),
    # "GRAPHEMECLUSTERBREAK": (lambda k: k, lambda k: len(k) <= 3),
    # "SENTENCEBREAK": (lambda k: k, lambda k: len(k) == 2),
    # "HANGULSYLLABLETYPE": (lambda k: k, lambda k: len(k) <= 3),
    # "CANONICALCOMBININGCLASS": (lambda k: int(k), check_if_number),
    # "DECOMPOSITIONTYPE": (lambda k: k.title(), lambda k: len(k) <= 4),
    # "EASTASIANWIDTH": (lambda k: k.title(), lambda k: len(k) <= 2),
    # "JOININGTYPE": (lambda k: k, lambda k: len(k) == 1),
    # "LINEBREAK": (lambda k: k, lambda k: len(k) <= 3),
    # "NUMERICTYPE": (lambda k: k.title(), lambda k: len(k) <= 4),
    # "NUMERICVALUE": (get_numeric_value, lambda k: True),
    # "INDICPOSITIONALCATEGORY": (IPC_adjust, lambda k: True),
}
for id in prop_val_dict:
    prop = prop_val_dict[id][0]
    adjust = False
    try:
        adjustment, condition = prop_val_dict_adjustments[prop]
        prop_val_dict[id] = (
            prop,
            {prop_dict[prop][1][k]: adjustment(k) for k in prop_dict[prop][1] if condition(k)}
        )
    except KeyError:
        if prop_val_dict[id][1] == {0: "FALSE", 1: "TRUE"}:
            prop_val_dict[id] = (
                prop,
                {0: False, 1: True}
            )

def _get_prop(char, prop_id):
    try:
        char = ord(char)
    except TypeError as e:
        raise TypeError(str(e).replace("ord()", "unicode_props"))
    p_dict = prop_val_dict[prop_id][1]
    for val_id in p_dict:
        value = (prop_id << 16) | val_id
        if regex._regex.has_property_value(value, char):
            # output.add(p_dict[val_id])
            output = p_dict[val_id]
            break
    return output

class Prop:
    def __init__(self, wrapped):
        self.wrapped = wrapped
    
    def __getattr__(self, name):
        try:
            prop_id = prop_dict[regex._regex_core.standardise_name(name)][0]
        except KeyError:
            raise AttributeError("Property not found")
        return lambda char: _get_prop(char, prop_id)

    def __dir__(self):
        return [v[0].lower() for v in prop_val_dict.values()]

    def _test(self, chunks=16):
        from tqdm import tqdm
        import json
        for i in range(chunks):
            if i != 4: continue
            chunk = range((0x110000 // chunks) * i, (0x110000 // chunks) * (i + 1))
        # for i, chunk in enumerate([range(0, 0x44000), range(0x44000, 0x88000), range(0x88000, 0xCC000), range(0xCC000, 0x110000)]):
            output = []
            for c in tqdm(chunk):
                char = chr(c)
                # d = {prop: self.__getattr__(prop)(char) for prop in dir(self)}
                d = {"codepoint": "%04X" % c}
                for prop in dir(self):
                    val = self.__getattr__(prop)(char)
                    if isinstance(val, set):
                        val = list(val)
                    else:
                        val = str(val)
                    d[prop] = val
                output.append(d)
            json.dump(output, open("tests/test{}.json".format(i), "w"), sort_keys=True)

    def compare(self, char, prop, val):
        char_val = self.__getattr__(prop)(char)
        val = regex._regex_core.standardise_name(val)
        

sys.modules[__name__] = Prop(sys.modules[__name__])
