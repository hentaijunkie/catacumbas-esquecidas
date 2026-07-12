#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de balanceamento — cada classe x Golem, no MOTOR DE COMBATE REAL.
============================================================================
Lê os valores vivos da engine e simula o combate contra o chefe no nível/gear
esperado no fim da campanha. IA: Mago prioriza magia de dano; todos bebem poção
(vida/mana) quando faz sentido. Tune CANDIDATO_GOLEM p/ ajustar o chefe.

Uso:  python balance_sim.py
"""
import rpg_loop as eng

# Ajuste aqui p/ testar um chefe diferente antes de aplicar na engine:
CANDIDATO_GOLEM = None   # lê os valores reais da engine; ex.: {"hp": 40, "dano": 6, "defesa": 3}
if CANDIDATO_GOLEM:
    eng.BESTIARIO["golem_barro"].update(CANDIDATO_GOLEM)


def nivelar(state, alvo):
    while state["player"]["nivel"] < alvo:
        n = state["player"]["nivel"] + 1
        eng.ganhar_xp(state, eng.PROGRESSAO[n]["xp"] - state["player"]["xp"])


def melhor_magia_dano(p):
    ms = [m for m in p["magias"] if eng.MAGIAS[m]["efeito"] == "dano"]
    return max(ms, key=lambda m: eng.MAGIAS[m]["valor"], default=None)


def simular(classe, nivel, arma=None, armadura=None, pocoes=2, mana_pots=2, hp_frac=1.0,
            raca="Humano", alvo="golem_barro", grupo=None, prof=1, magias_extra=(),
            seed_rng=7, veneno_inicial=None, sangramento_inicial=None):
    """Simula uma luta no motor real. alvo/grupo/prof permitem cenários de andar 2.
    veneno_inicial/sangramento_inicial simulam chegar na luta já com DoT ativo (trap/mordida
    anterior) — cenário de debuffs empilhados junto com a Fraqueza que o próprio alvo aplica."""
    eng.random.seed(seed_rng)      # determinismo (aranha envenena por chance, fuga etc.)
    st = eng.novo_jogo(classe, seed=1, raca=raca)
    st["profundidade"] = prof
    p = st["player"]
    p["inventario"] = ["pocao_cura"]*pocoes + ["pocao_mana"]*mana_pots
    for m in magias_extra:
        if m not in p["magias"]:
            p["magias"].append(m)
    nivelar(st, nivel)
    if arma: p["arma"] = arma
    if armadura: p["armadura"] = armadura
    p["hp"] = max(1, int(p["hp_max"]*hp_frac))
    if veneno_inicial: p["veneno"] = dict(veneno_inicial)
    if sangramento_inicial: p["sangramento"] = dict(sangramento_inicial)
    e = eng.stats_inimigo(alvo, prof)
    cb = eng.novo_combate(st, alvo, list(grupo) if grupo else None)
    # dano por round que o jogador leva (front + bando + DoTs ativos) — heurística p/ beber
    # poção a tempo; sem contar veneno/sangramento aqui, debuffs empilhados matariam a IA de surpresa.
    def golpe():
        total = 0
        for eid in eng.inimigos_vivos(cb):
            total += max(1, eng.stats_inimigo(eid, prof)["dano"] - eng.defesa_total(p, st))
        if p.get("veneno"): total += p["veneno"]["dano"]
        if p.get("sangramento"): total += p["sangramento"]["dano"]
        return total
    magia = melhor_magia_dano(p)
    aoe = "nova_gelida" if "nova_gelida" in p["magias"] else None
    turnos, status = 0, "continua"
    while status == "continua" and turnos < 100:
        turnos += 1
        usa = aoe if (aoe and len(cb["extras"]) >= 1) else magia   # horda -> AoE
        custo = eng.MAGIAS[usa]["custo"] if usa else 0
        if p["hp"] <= golpe() and "pocao_cura" in p["inventario"]:
            escolha = "pocao"                                   # emergência: cura (e antídoto)
        elif usa and p["mana"] >= custo:
            escolha = "magia:" + usa                            # nuke mágico / AoE
        elif usa and p["mana"] < custo and "pocao_mana" in p["inventario"]:
            escolha = "pocao_mana"                              # recarrega mana (gasta o turno)
        else:
            escolha = "atacar"
        status, _ = eng.combate_passo(st, cb, escolha)
    return status, max(0, p["hp"]), turnos


def main():
    print(f"GOLEM: hp={eng.BESTIARIO['golem_barro']['hp']} "
          f"dano={eng.BESTIARIO['golem_barro']['dano']} defesa={eng.BESTIARIO['golem_barro']['defesa']}")
    print(f"{'classe':10} {'nv':2} {'gear':22} {'result':7} {'HP':>4} {'turnos':>6}")
    print("-" * 60)
    # gear típico de fim de campanha (achável na masmorra)
    setups = {
        "Guerreiro": [("gibão", dict(armadura='gibao_couro')),
                      ("espada longa+cota", dict(arma='espada_longa', armadura='cota_malha'))],
        "Mago":      [("sem armadura", dict()),
                      ("roupas de pano", dict(armadura='roupas_pano'))],
        "Ladino":    [("adaga+gibão", dict(armadura='gibao_couro')),
                      ("espada longa+cota", dict(arma='espada_longa', armadura='cota_malha'))],
    }
    for classe in ("Guerreiro", "Mago", "Ladino"):
        for nivel in (3, 4):
            for nome, kw in setups[classe]:
                r, hp, t = simular(classe, nivel, **kw)
                print(f"{classe:10} {nivel:<2} {nome:22} "
                      f"{'OK' if r=='vitoria' else 'MORRE':7} {hp:>4} {t:>6}")
        print()
    # Amostra de raças (nível 4, gear típico)
    print("Raças (nv4, gear típico):")
    print(f"{'classe':10} {'raça':10} {'result':7} {'HP':>4} {'turnos':>6}")
    print("-" * 50)
    amostras = [
        ("Guerreiro", "Anão", dict(arma='espada_longa', armadura='cota_malha')),
        ("Mago", "Elfo", dict(armadura='roupas_pano')),
        ("Ladino", "Halfling", dict(arma='espada_longa', armadura='gibao_couro')),
        ("Guerreiro", "Humano", dict(arma='espada_longa', armadura='cota_malha')),
    ]
    for classe, raca, kw in amostras:
        r, hp, t = simular(classe, 4, raca=raca, **kw)
        print(f"{classe:10} {raca:10} {'OK' if r=='vitoria' else 'MORRE':7} {hp:>4} {t:>6}")

    # ------ ANDAR 2 (prof=2: +20% HP/dano; aranha envenena, espectro drena) ------
    print("\nANDAR 2 (nv4, gear endgame, prof=2):")
    print(f"{'classe':10} {'encontro':26} {'result':7} {'HP':>4} {'turnos':>6}")
    print("-" * 60)
    gear = {
        "Guerreiro": dict(arma='espada_longa', armadura='cota_malha'),
        "Mago":      dict(armadura='roupas_pano',
                          magias_extra=('bola_fogo', 'nova_gelida')),
        "Ladino":    dict(arma='lamina_runica', armadura='gibao_couro'),
    }
    encontros = [
        ("aranha (veneno)",       dict(alvo="aranha_cripta")),
        ("espectro (fadiga)",     dict(alvo="espectro_gelido")),
        ("sombra (fraqueza)",     dict(alvo="sombra_vampirica")),
        ("horda elite (câmara)",  dict(alvo="zumbi", grupo=["cultista", "esqueleto_animado"])),
    ]
    for classe in ("Guerreiro", "Mago", "Ladino"):
        for nome, kw in encontros:
            r, hp, t = simular(classe, 4, prof=2, **gear[classe], **kw)
            print(f"{classe:10} {nome:26} {'OK' if r=='vitoria' else 'MORRE':7} {hp:>4} {t:>6}")
        # desceu cedo (nv3): a câmara deve ser tensa, não passeio
        r, hp, t = simular(classe, 3, prof=2, alvo="zumbi",
                           grupo=["cultista", "esqueleto_animado"], **gear[classe])
        print(f"{classe:10} {'horda elite (nv3 cedo)':26} {'OK' if r=='vitoria' else 'MORRE':7} {hp:>4} {t:>6}")
        print()
    # Cenário de atrito: chega na câmara ferido (60% HP) e com 1 poção só.
    print("Atrito (câmara do andar 2 com 60% HP e 1 poção):")
    for classe in ("Guerreiro", "Mago", "Ladino"):
        r, hp, t = simular(classe, 4, prof=2, hp_frac=0.6, pocoes=1, mana_pots=1,
                           alvo="zumbi", grupo=["cultista", "esqueleto_animado"],
                           **gear[classe])
        print(f"  {classe:10} {'OK' if r=='vitoria' else 'MORRE':7} HP={hp:>3} turnos={t}")

    # ------ DEBUFFS EMPILHADOS: veneno (aranha) + sangramento (lâminas) já ativos,
    # entrando direto na luta com a Sombra Vampírica (que aplica Fraqueza). Pior caso
    # realista: jogador mal saiu de uma trap/mordida e cai numa emboscada. ------
    print("\nDEBUFFS EMPILHADOS (veneno+sangramento ativos vs. Sombra Vampírica, nv3-4):")
    print(f"{'classe':10} {'nv':2} {'HP inicial':10} {'result':7} {'HP':>4} {'turnos':>6}")
    print("-" * 55)
    for classe in ("Guerreiro", "Mago", "Ladino"):
        for nivel in (3, 4):
            r, hp, t = simular(classe, nivel, prof=2, alvo="sombra_vampirica",
                               veneno_inicial={"dano": 2, "passos": 3},
                               sangramento_inicial={"dano": 1, "passos": 4},
                               **gear[classe])
            print(f"{classe:10} {nivel:<2} {'2 DoTs ativos':10} "
                  f"{'OK' if r=='vitoria' else 'MORRE':7} {hp:>4} {t:>6}")
    # Pior caso ainda: o mesmo, mas já ferido (70% HP) e com 1 poção só.
    print("\nDEBUFFS EMPILHADOS + ferido (70% HP, 1 poção, nv4):")
    for classe in ("Guerreiro", "Mago", "Ladino"):
        r, hp, t = simular(classe, 4, prof=2, alvo="sombra_vampirica", hp_frac=0.7,
                           pocoes=1, mana_pots=1,
                           veneno_inicial={"dano": 2, "passos": 3},
                           sangramento_inicial={"dano": 1, "passos": 4},
                           **gear[classe])
        print(f"  {classe:10} {'OK' if r=='vitoria' else 'MORRE':7} HP={hp:>3} turnos={t}")


if __name__ == "__main__":
    main()
