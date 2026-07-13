with open('c:/rpg/rpg_loop.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
lines[3964:3973] = [
    '    # subir da entrada -> Vila\n',
    '    ml["pos"] = {"x": 0, "y": 0}\n',
    '    subir_escada(ml)\n',
    '    assert ml.get("na_superficie")\n',
    '    assert ml["pos"] == {"x": 0, "y": -1}, "Aparece na entrada das catacumbas da vila"\n',
    '    r_surf = aplicar_movimento(ml, "frente")\n',
    '    assert r_surf["moveu"], "Movimento na vila agora e permitido"\n',
    '    # reentrar\n',
    '    ml["pos"] = {"x": 0, "y": -1}\n',
    '    descer_escada(ml)\n',
    '    assert not ml.get("na_superficie")\n'
]
with open('c:/rpg/rpg_loop.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
