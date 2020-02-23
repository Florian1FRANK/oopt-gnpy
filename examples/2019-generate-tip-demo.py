# How many nodes in the ring topology?
HOW_MANY = 3

# city names
ALL_CITIES = [
    'Antwerp',
    'Brussels',
    'Leuven',
]
# end of configurable parameters


J = {
    "elements": [],
    "connections": [],
}

def unidir_join(a, b):
    global J
    J["connections"].append(
        {"from_node": a, "to_node": b}
    )

def mk_edfa(name, gain, voa=0.0):
    global J
    J["elements"].append(
        {"uid": name, "type": "Edfa", "type_variety": f"fixed{gain}", "operational": {"gain_target": gain, "out_voa": voa}}
    )

def add_att(a, b, att):
    global J
    if att > 0:
        uid = f"att-({a})-({b})"
    else:
        uid = f"splice-({a})-({b})"
    J["elements"].append(
        {"uid": uid, "type": "Fused", "params": {"loss": att}},
    )
    unidir_join(a, uid)
    unidir_join(uid, b)
    return uid

def build_fiber(city1, city2):
    global J
    J["elements"].append(
        {
            "uid": f"fiber-{city1}-{city2}",
            "type": "Fiber",
            "type_variety": "SSMF",
            "params": {
                "length": 50,
                "length_units": "km",
                "loss_coef": 0.2,
                "con_in": 1.5,
                "con_out": 1.5,
            }
        }
    )

def unidir_patch(a, b):
    global J
    uid = f"patch-({a})-({b})"
    J["elements"].append(
        {
            "uid": uid,
            "type": "Fiber",
            "type_variety": "SSMF",
            "params": {
                "length": 0,
                "length_units": "km",
                "loss_coef": 0.2,
                "con_in": 0.5,
                "con_out": 0.5,
            }
        }
    )
    add_att(a, uid, 0.0)
    add_att(uid, b, 0.0)

for CITY in (ALL_CITIES[x] for x in range(0, HOW_MANY)):
    J["elements"].append(
        {"uid": f"trx-{CITY}", "type": "Transceiver"}
    )
    target_pwr = [
        {"to_node": f"trx-{CITY}", "target_pch_out_db": -25},
        {"to_node": f"splice-(roadm-{CITY}-AD)-(patch-(roadm-{CITY}-AD)-(roadm-{CITY}-L1))", "target_pch_out_db": -12},
        {"to_node": f"splice-(roadm-{CITY}-AD)-(patch-(roadm-{CITY}-AD)-(roadm-{CITY}-L2))", "target_pch_out_db": -12},
    ]
    J["elements"].append(
        {"uid": f"roadm-{CITY}-AD", "type": "Roadm", "params": {"target_pch_out_db": -2.0, "per_degree_target_pch_out_db": target_pwr}}
    )
    unidir_join(f"trx-{CITY}", f"roadm-{CITY}-AD")
    unidir_join(f"roadm-{CITY}-AD", f"trx-{CITY}")

    for n in (1,2):
        target_pwr = [
            {"to_node": f"roadm-{CITY}-L{n}-booster", "target_pch_out_db": -23},
            {"to_node": f"splice-(roadm-{CITY}-L{n})-(patch-(roadm-{CITY}-L{n})-(roadm-{CITY}-AD))", "target_pch_out_db": -5 if CITY == 'Antwerp' else -12},
        ]
        if CITY == 'Antwerp':
            target_pwr.append(
                {"to_node": f"netconf:10.0.254.105:830", "target_pch_out_db": -5},
            )
        for m in (1,2):
            if m == n:
                continue
            target_pwr.append(
              {"to_node": f"splice-(roadm-{CITY}-L{n})-(patch-(roadm-{CITY}-L{n})-(roadm-{CITY}-L{m}))", "target_pch_out_db": -12},
            )
        J["elements"].append(
            {"uid": f"roadm-{CITY}-L{n}", "type": "Roadm", "params": {"target_pch_out_db": -23.0, "per_degree_target_pch_out_db": target_pwr}}
        )
        mk_edfa(f"roadm-{CITY}-L{n}-booster", 22)
        mk_edfa(f"roadm-{CITY}-L{n}-preamp", 27)
        unidir_join(f"roadm-{CITY}-L{n}", f"roadm-{CITY}-L{n}-booster")
        unidir_join(f"roadm-{CITY}-L{n}-preamp", f"roadm-{CITY}-L{n}")

        unidir_patch(f"roadm-{CITY}-AD", f"roadm-{CITY}-L{n}")
        unidir_patch(f"roadm-{CITY}-L{n}", f"roadm-{CITY}-AD")
        for m in (1,2):
            if m == n:
                continue
            #add_att(f"roadm-{CITY}-L{n}", f"roadm-{CITY}-L{m}", 22)
            unidir_patch(f"roadm-{CITY}-L{n}", f"roadm-{CITY}-L{m}")

for city1, city2 in ((ALL_CITIES[i], ALL_CITIES[i + 1] if i < HOW_MANY - 1 else ALL_CITIES[0]) for i in range(0, HOW_MANY)):
    build_fiber(city1, city2)
    unidir_join(f"roadm-{city1}-L1-booster", f"fiber-{city1}-{city2}")
    unidir_join(f"fiber-{city1}-{city2}", f"roadm-{city2}-L2-preamp")
    build_fiber(city2, city1)
    unidir_join(f"roadm-{city2}-L2-booster", f"fiber-{city2}-{city1}")
    unidir_join(f"fiber-{city2}-{city1}", f"roadm-{city1}-L1-preamp")


for _, E in enumerate(J["elements"]):
    uid = E["uid"]
    if uid.startswith("roadm-") and (uid.endswith("-L1-booster") or uid.endswith("-L2-booster")):
        E["operational"]["out_voa"] = 12.0
    #if uid.endswith("-AD-add"):
    #    E["operational"]["out_voa"] = 21

translate = {
    #"trx-Amsterdam": "10.0.254.93",
    #"trx-Brussels": "10.0.254.94",
    "trx-Antwerp": "10.0.254.105",
    "trx-Brussels": "10.0.254.103",

    # Antwerp A/D: a passive device -> nothing
    #"roadm-Antwerp-AD": "nothing",
    # Brussels A/D: add-drop-vot
    "roadm-Brussels-AD": "10.0.254.246",

    # Antwerp -> Brussels ...Q7N
    "roadm-Antwerp-L1": "10.0.254.236",
    # Brussels -> Antwerp ...MPW
    "roadm-Brussels-L2": "10.0.254.227",

    # Brussels -> Lueven ...M0N
    "roadm-Brussels-L1": "10.0.254.226",

    # HACK: pretend that this ILA is a ROADM
    # Lueven: inline-dq0011h0
    #"roadm-Leuven-L1": "Leuven-ILA",
    "roadm-Leuven-L1": "10.0.254.106",
    #"Lueven-ILA": "10.0.254.106",

    # Antwerp -> Lueven ...NFP
    "roadm-Antwerp-L2": "10.0.254.235",
}

import json
s = json.dumps(J, indent=2)
for (old, new) in translate.items():
    s = s.replace(f'"{old}"', f'"netconf:{new}:830"')
print(s)
