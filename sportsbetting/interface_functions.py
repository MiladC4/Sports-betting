#!/usr/bin/env python3
# coding: utf-8

"""
.. module::interface_functions
:synopsis: Fonctions d'intéraction entre l'interface et les fonctions du package sportsbetting
"""

import datetime # à garder jusqu'à JSON
import sys
import io
import numpy as np
import scipy.stats
import tabulate
import PySimpleGUI as sg
import webbrowser

import sportsbetting as sb
from sportsbetting.auxiliary_functions import get_nb_outcomes, copy_to_clipboard, calculator
from sportsbetting.database_functions import get_all_current_competitions, get_all_competitions
from sportsbetting.user_functions import (best_match_under_conditions, best_match_under_conditions2,
                                          best_match_freebet, best_stakes_match,
                                          best_matches_freebet, best_matches_combine, best_matches_combine3,
                                          best_match_cashback, best_match_stakes_to_bet,
                                          best_match_pari_gagnant, odds_match, best_matches_combine_cashback,
                                          best_combine_booste, trj_match, best_matches_freebet_one_site, get_values,
                                          best_matches_freebet2, best_match_defi_rembourse_ou_gagnant, best_combine_booste_progressif)
from sportsbetting.performances import get_surebets_players_nba
from sportsbetting.basic_functions import gain, mises, mises2

WHAT_WAS_PRINTED_COMBINE = ""


def odds_table(result):
    """
    :param result: ensemble des valeurs affichées dans le terminal par une fonction du package
    sportsbetting
    :return: Tableau des cotes
    """
    lines = result.split("\n")
    i = 0
    for i, line in enumerate(lines):
        if "}}" in line:
            break
    dict_odds = eval("".join(lines[1:i + 1]))
    odds = dict_odds["odds"]
    if len(list(odds.values())[0]) == 2:
        for key in odds.keys():
            odds[key].insert(1, "-   ")
    table = []
    for key, value in odds.items():
        table.append([key] + list(map(str, value)))
    return table


def indicators(result):
    """
    :param result: ensemble des valeurs affichées dans le terminal par une fonction du package
    sportsbetting
    :return: Valeurs utiles concernant le résultat affiché (Somme des mises, plus-value, ...)
    """
    lines = result.split("}}\n")[1].split("\nmises arrondies")[0].split("\n")
    for line in lines:
        if not line:
            break
        yield line.split(" = ")


def stakes(result):
    """
    :param result: ensemble des valeurs affichées dans le terminal par une fonction du package
    sportsbetting
    :return: Dictionnaire des mises
    """
    return result.split("Répartition des mises (les totaux affichés prennent en compte les éventuels freebets):\n")[1]


def infos(result):
    """
    :param result: ensemble des valeurs affichées dans le terminal par une fonction du package
    sportsbetting
    :return: Nom et date du match sélectionné
    """
    lines = result.split("\n")
    match = lines[0]
    i = 0
    if not match or match == "No match found":
        return None, None
    for i, line in enumerate(lines):
        if "}}" in line:
            break
    dict_odds = eval("".join(lines[1:i + 1]))
    date = dict_odds["date"]
    return match, date.strftime("%A %d %B %Y %H:%M")


def odds_table_combine(result):
    """
    :param result: ensemble des valeurs affichées dans le terminal par une fonction du package
    sportsbetting
    :return: Tableau des cotes dans le cas d'un combiné
    """
    lines = result.split("\n")
    i = 0
    for i, line in enumerate(lines):
        if "}}" in line:
            break
    dict_odds = eval("".join(lines[1:i + 1]))
    odds = dict_odds["odds"]
    table = []
    combinaisons = []
    for line in result.split("freebets):\n")[1].split("\n")[3::2]:
        if "│" not in line:
            break
        if line:
            combinaisons.append(line.split("│")[1].strip())
    combinaisons = ["Combinaison"] + combinaisons
    table.append(combinaisons)
    for key, value in odds.items():
        table.append([key] + list(map(lambda x: str(round(x, 3)), value)))
    return np.transpose(table).tolist()


def best_match_under_conditions_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction best_match_under_condition dans l'interface
    """
    try:
        site = values["SITE_UNDER_CONDITION"][0]
        bet = float(values["BET_UNDER_CONDITION"])
        minimum_odd = float(values["ODD_UNDER_CONDITION"])
        sport = values["SPORT_UNDER_CONDITION"][0]
        date_min, time_min, date_max, time_max = None, None, None, None
        if values["DATE_MIN_UNDER_CONDITION_BOOL"]:
            date_min = values["DATE_MIN_UNDER_CONDITION"]
            time_min = values["TIME_MIN_UNDER_CONDITION"].replace(":", "h")
        if values["DATE_MAX_UNDER_CONDITION_BOOL"]:
            date_max = values["DATE_MAX_UNDER_CONDITION"]
            time_max = values["TIME_MAX_UNDER_CONDITION"].replace(":", "h")
        one_site = values["ONE_SITE_UNDER_CONDITION"]
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        if one_site:
            best_match_under_conditions2(site, minimum_odd, bet, sport, date_max, time_max,
                                         date_min, time_min)
        else:
            best_match_under_conditions(site, minimum_odd, bet, sport, date_max, time_max, date_min,
                                        time_min, one_site)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()  # contains the entire contents of the buffer.
        match, date = infos(what_was_printed)
        if match is None:
            window["MATCH_UNDER_CONDITION"].update("Aucun match trouvé")
            window["DELETE_MATCH_UNDER_CONDITION"].update(visible=False)
            window["DATE_UNDER_CONDITION"].update("")
            window["ODDS_UNDER_CONDITION"].update(visible=False)
            window["RESULT_UNDER_CONDITION"].update(visible=False)
            window["TEXT_UNDER_CONDITION"].update(visible=False)
            for i in range(5):
                window["INDICATORS_UNDER_CONDITION" + str(i)].update(visible=False)
                window["RESULTS_UNDER_CONDITION" + str(i)].update(visible=False)
        else:
            window["MATCH_UNDER_CONDITION"].update(match)
            window["DELETE_MATCH_UNDER_CONDITION"].update(visible=True)
            window["RELOAD_ODDS_UNDER_CONDITION"].update(visible=True)
            window["DATE_UNDER_CONDITION"].update(date)
            window["ODDS_UNDER_CONDITION"].update(odds_table(what_was_printed), visible=True)
            window["RESULT_UNDER_CONDITION"].update(stakes(what_was_printed), visible=True)
            window["TEXT_UNDER_CONDITION"].update(visible=True)
            for i in range(5):
                window["INDICATORS_UNDER_CONDITION" + str(i)].update(visible=False)
                window["RESULTS_UNDER_CONDITION" + str(i)].update(visible=False)
            for i, elem in enumerate(indicators(what_was_printed)):
                window["INDICATORS_UNDER_CONDITION" + str(i)].update(elem[0].capitalize(),
                                                                     visible=True)
                window["RESULTS_UNDER_CONDITION" + str(i)].update(elem[1], visible=True)
        buffer.close()
    except IndexError:
        pass
    except ValueError:
        pass


def best_stakes_match_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction best_stakes_match dans l'interface
    """
    site = ""
    try:
        site = values["SITE_STAKE"][0]
        bet = float(values["BET_STAKE"])
        minimum_odd = float(values["ODD_STAKE"])
        sport = values["SPORT_STAKE"][0]
        match = values["MATCHES"][0]
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        best_stakes_match(match, site, bet, minimum_odd, sport)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()
        match, date = infos(what_was_printed)
        if "No match found" in what_was_printed:
            window["MATCH_STAKE"].update("Cote trop élevée pour le match choisi")
            window["DATE_STAKE"].update("")
            window["ODDS_STAKE"].update(visible=False)
            window["RESULT_STAKE"].update(visible=False)
            window["TEXT_STAKE"].update(visible=False)
            for i in range(5):
                window["INDICATORS_STAKE" + str(i)].update(visible=False)
                window["RESULTS_STAKE" + str(i)].update(visible=False)
        else:
            window["MATCH_STAKE"].update(match)
            window["DATE_STAKE"].update(date)
            window["ODDS_STAKE"].update(odds_table(what_was_printed), visible=True)
            window["RESULT_STAKE"].update(stakes(what_was_printed), visible=True)
            window["TEXT_STAKE"].update(visible=True)
            for i, elem in enumerate(indicators(what_was_printed)):
                window["INDICATORS_STAKE" + str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_STAKE" + str(i)].update(elem[1], visible=True)
        buffer.close()
    except IndexError:
        sg.Popup("Site ou match non défini")
    except ValueError:
        sg.Popup("Mise ou cote invalide")
    except KeyError:
        sg.Popup("Match non disponible sur {}".format(site))


def best_match_freebet_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction best_match_freebet dans l'interface
    """
    try:
        site = values["SITE_FREEBET"][0]
        freebet = float(values["BET_FREEBET"])
        sport = values["SPORT_FREEBET"][0]
        split_freebet = values["SPLIT_FREEBET"]
        nb_matches = values["NB_MATCHES_FREEBET"]
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        if split_freebet:
            best_matches_freebet_one_site(site, freebet, sport)
        elif nb_matches == 1:
            best_match_freebet(site, freebet, sport)
        else:
            best_matches_freebet2(site, freebet, sport, nb_matches)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()
        match, date = infos(what_was_printed)
        if match is None:
            window["MATCH_FREEBET"].update("Aucun match trouvé")
            window["DATE_FREEBET"].update("")
            window["ODDS_FREEBET"].update(visible=False)
            window["RESULT_FREEBET"].update(visible=False)
            window["TEXT_FREEBET"].update(visible=False)
            for i in range(5):
                window["INDICATORS_FREEBET" + str(i)].update(visible=False)
                window["RESULTS_FREEBET" + str(i)].update(visible=False)
        else:
            window["MATCH_FREEBET"].update(match)
            window["DATE_FREEBET"].update(date)
            window["ODDS_FREEBET"].update(odds_table(what_was_printed), visible=not split_freebet and nb_matches == 1)
            window["RESULT_FREEBET"].update(stakes(what_was_printed), visible=True)
            window["TEXT_FREEBET"].update(visible=True)
            window["DELETE_MATCH_FREEBET"].update(visible=not split_freebet and nb_matches == 1)
            window["RELOAD_ODDS_FREEBET"].update(visible=not split_freebet and nb_matches == 1)
            for i, elem in enumerate(indicators(what_was_printed)):
                window["INDICATORS_FREEBET" + str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_FREEBET" + str(i)].update(elem[1], visible=True)
            for j in range(i+1, 5):
                window["INDICATORS_FREEBET" + str(j)].update(visible=False)
                window["RESULTS_FREEBET" + str(j)].update(visible=False)
        buffer.close()
    except IndexError:
        pass
    except ValueError:
        pass
    except KeyError:
        pass


def best_match_cashback_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction best_match_cashback dans l'interface
    """
    try:
        site = values["SITE_CASHBACK"][0]
        bet = float(values["BET_CASHBACK"])
        minimum_odd = float(values["ODD_CASHBACK"])
        sport = values["SPORT_CASHBACK"][0]
        freebet = float(values["FREEBET_CASHBACK"])
        combi_max = float(values["COMBI_MAX_CASHBACK"]) / 100
        combi_odd = float(values["COMBI_ODD_CASHBACK"])
        rate_cashback = float(values["RATE_CASHBACK"]) / 100
        nb_matches_combine = values["NB_MATCHES_CASHBACK"]
        date_min, time_min, date_max, time_max = None, None, None, None
        if values["DATE_MIN_CASHBACK_BOOL"]:
            date_min = values["DATE_MIN_CASHBACK"]
            time_min = values["TIME_MIN_CASHBACK"].replace(":", "h")
        if values["DATE_MAX_CASHBACK_BOOL"]:
            date_max = values["DATE_MAX_CASHBACK"]
            time_max = values["TIME_MAX_CASHBACK"].replace(":", "h")
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        if nb_matches_combine == 1:
            best_match_cashback(site, minimum_odd, bet, sport, freebet, combi_max, combi_odd,
                                rate_cashback, date_max, time_max, date_min, time_min)
        else:
            best_matches_combine_cashback(site, minimum_odd, bet, sport, freebet, combi_max,
                                          rate_cashback, nb_matches_combine, date_max, time_max,
                                          date_min, time_min)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()
        match, date = infos(what_was_printed)
        if match is None:
            window["MATCH_CASHBACK"].update("Aucun match trouvé")
            window["DATE_CASHBACK"].update("")
            window["ODDS_CASHBACK"].update(visible=False)
            window["RESULT_CASHBACK"].update(visible=False)
            window["TEXT_CASHBACK"].update(visible=False)
            window["DELETE_MATCH_CASHBACK"].update(visible=False)
            for i in range(5):
                window["INDICATORS_CASHBACK" + str(i)].update(visible=False)
                window["RESULTS_CASHBACK" + str(i)].update(visible=False)
        else:
            window["MATCH_CASHBACK"].update(match)
            window["DATE_CASHBACK"].update(date)
            window["ODDS_CASHBACK"].update(odds_table(what_was_printed), visible=True)
            window["DELETE_MATCH_CASHBACK"].update(visible=nb_matches_combine==1)
            window["RELOAD_ODDS_CASHBACK"].update(visible=nb_matches_combine==1)
            window["RESULT_CASHBACK"].update(stakes(what_was_printed), visible=True)
            window["TEXT_CASHBACK"].update(visible=True)
            for i, elem in enumerate(indicators(what_was_printed)):
                window["INDICATORS_CASHBACK" + str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_CASHBACK" + str(i)].update(elem[1], visible=True)
        buffer.close()
    except IndexError:
        pass


def best_matches_combine_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction best_matches_combine dans l'interface
    """
    try:
        site = values["SITE_COMBINE"][0]
        bet = float(values["BET_COMBINE"])
        minimum_odd = float(values["ODD_COMBINE"])
        minimum_odd_selection = float(values["ODD_SELECTION_COMBINE"])
        sport = values["SPORT_COMBINE"][0]
        nb_matches = int(values["NB_MATCHES_COMBINE"])
        date_min, time_min, date_max, time_max = None, None, None, None
        if values["DATE_MIN_COMBINE_BOOL"]:
            date_min = values["DATE_MIN_COMBINE"]
            time_min = values["TIME_MIN_COMBINE"].replace(":", "h")
        if values["DATE_MAX_COMBINE_BOOL"]:
            date_max = values["DATE_MAX_COMBINE"]
            time_max = values["TIME_MAX_COMBINE"].replace(":", "h")
        one_site = values["ONE_SITE_COMBINE"]
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        best_matches_combine(site, minimum_odd, bet, sport, nb_matches, one_site, date_max,
                             time_max, date_min, time_min, minimum_odd_selection)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()
        match, date = infos(what_was_printed)
        if match is None:
            window["MATCH_COMBINE"].update("Aucun match trouvé")
            window["DATE_COMBINE"].update("")
            window["ODDS_COMBINE"].update(visible=False)
            window["RESULT_COMBINE"].update(visible=False)
            window["TEXT_COMBINE"].update(visible=False)
            for i in range(5):
                window["INDICATORS_COMBINE" + str(i)].update(visible=False)
                window["RESULTS_COMBINE" + str(i)].update(visible=False)
        else:
            window["MATCH_COMBINE"].update(match)
            window["DATE_COMBINE"].update(date)
            window["ODDS_COMBINE"].update(visible=True)
            window["RESULT_COMBINE"].update(stakes(what_was_printed), visible=True)
            window["TEXT_COMBINE"].update(visible=True)
            for i, elem in enumerate(indicators(what_was_printed)):
                window["INDICATORS_COMBINE" + str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_COMBINE" + str(i)].update(elem[1], visible=True)
        buffer.close()
        sb.ODDS_INTERFACE = what_was_printed
    except IndexError:
        pass
    except ValueError:
        pass


def best_match_stakes_to_bet_interface(window, values, visible_stakes):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :param visible_stakes: Nombre de mises requises
    :return: Affiche le résultat de la fonction best_match_stakes_to_bet dans l'interface
    """
    stakes_list = []
    nb_matches = int(values["NB_MATCHES_STAKES"])
    for i in range(visible_stakes):
        stakes_list.append([float(values["STAKE_STAKES_" + str(i)]),
                            values["SITE_STAKES_" + str(i)],
                            float(values["ODD_STAKES_" + str(i)])])
    date_max = None
    time_max = None
    sport = values["SPORT_STAKES"]
    if values["DATE_MAX_STAKES_BOOL"]:
        date_max = values["DATE_MAX_STAKES"]
        time_max = values["TIME_MAX_STAKES"].replace(":", "h")
    old_stdout = sys.stdout  # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()
    best_match_stakes_to_bet(stakes_list, nb_matches, sport, date_max, time_max)
    sys.stdout = old_stdout  # Put the old stream back in place
    what_was_printed = buffer.getvalue()
    match, date = infos(what_was_printed)
    window["MATCH_STAKES"].update(match)
    window["DATE_STAKES"].update(date)
    window["ODDS_STAKES"].update(visible=True)
    window["RESULT_STAKES"].update(stakes(what_was_printed), visible=True)
    window["TEXT_STAKES"].update(visible=True)
    for i, elem in enumerate(indicators(what_was_printed)):
        window["INDICATORS_STAKES" + str(i)].update(elem[0].capitalize(), visible=True)
        window["RESULTS_STAKES" + str(i)].update(elem[1], visible=True)
    buffer.close()
    sb.ODDS_INTERFACE = what_was_printed


def best_matches_freebet_interface(window, values, visible_freebets):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :param visible_freebets: Nombre de mises_requises
    :return: Affiche le résultat de la fonction best_matches_freebet dans l'interface
    """
    freebets_list = []
    for i in range(visible_freebets):
        try:
            freebets_list.append([float(values["STAKE_FREEBETS_" + str(i)]),
                                values["SITE_FREEBETS_" + str(i)]])
        except ValueError:
            pass
    sites = values["SITES_FREEBETS"]
    match0 = values["MATCH_FREEBETS_0"]
    match1 = values["MATCH_FREEBETS_1"]
    match, date = None, None
    old_stdout = sys.stdout  # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()
    what_was_printed = ""
    if sites and freebets_list:
        if match0 and match1:
            best_matches_freebet(sites, freebets_list, "football", match0, match1)
        else:
            best_matches_freebet(sites, freebets_list, "football")
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()
        match, date = infos(what_was_printed)
    if match is None:
        window["MATCH_FREEBETS"].update("Aucun match trouvé")
        window["DATE_FREEBETS"].update("")
        window["ODDS_FREEBETS"].update(visible=False)
        window["RESULT_FREEBETS"].update(visible=False)
        window["TEXT_FREEBETS"].update(visible=False)
        for i in range(5):
            window["INDICATORS_FREEBETS" + str(i)].update(visible=False)
            window["RESULTS_FREEBETS" + str(i)].update(visible=False)
    else:
        window["MATCH_FREEBETS"].update(match)
        window["DATE_FREEBETS"].update(date)
        window["ODDS_FREEBETS"].update(visible=True)
        window["RESULT_FREEBETS"].update(stakes(what_was_printed), visible=True)
        window["TEXT_FREEBETS"].update(visible=True)
        for i, elem in enumerate(indicators(what_was_printed)):
            window["INDICATORS_FREEBETS" + str(i)].update(elem[0].capitalize(), visible=True)
            window["RESULTS_FREEBETS" + str(i)].update(elem[1], visible=True)
    buffer.close()
    return what_was_printed


def best_match_pari_gagnant_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction best_match_pari_gagnant dans l'interface
    """
    try:
        site = values["SITE_GAGNANT"][0]
        bet = float(values["BET_GAGNANT"])
        minimum_odd = float(values["ODD_GAGNANT"])
        sport = values["SPORT_GAGNANT"][0]
        date_min, time_min, date_max, time_max = None, None, None, None
        if values["DATE_MIN_GAGNANT_BOOL"]:
            date_min = values["DATE_MIN_GAGNANT"]
            time_min = values["TIME_MIN_GAGNANT"].replace(":", "h")
        if values["DATE_MAX_GAGNANT_BOOL"]:
            date_max = values["DATE_MAX_GAGNANT"]
            time_max = values["TIME_MAX_GAGNANT"].replace(":", "h")
        nb_matches_combine = values["NB_MATCHES_GAGNANT"]
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        if values["RISKY_GAGNANT"] and nb_matches_combine>1:
            best_matches_combine3(site, minimum_odd, bet, sport, date_max, time_max, date_min, time_min, nb_matches_combine)
        elif values["DEFI_REMBOURSE_OU_GAGNANT"] and nb_matches_combine == 1:
            best_match_defi_rembourse_ou_gagnant(site, minimum_odd, bet, sport, date_max, time_max, date_min, time_min)
        else:
            best_match_pari_gagnant(site, minimum_odd, bet, sport, date_max, time_max, date_min,
                                    time_min, nb_matches_combine)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()
        match, date = infos(what_was_printed)
        if match is None:
            window["MATCH_GAGNANT"].update("Aucun match trouvé")
            window["DELETE_MATCH_GAGNANT"].update(visible=False)
            window["DATE_GAGNANT"].update("")
            window["ODDS_GAGNANT"].update(visible=False)
            window["ODDS_COMBINE_GAGNANT"].update(visible=False)
            window["RESULT_GAGNANT"].update(visible=False)
            window["TEXT_GAGNANT"].update(visible=False)
            for i in range(5):
                window["INDICATORS_GAGNANT" + str(i)].update(visible=False)
                window["RESULTS_GAGNANT" + str(i)].update(visible=False)
        else:
            window["MATCH_GAGNANT"].update(match)
            window["DATE_GAGNANT"].update(date)
            if nb_matches_combine > 1:
                window["ODDS_GAGNANT"].update(visible=False)
                window["ODDS_COMBINE_GAGNANT"].update(visible=True)
            else:
                window["ODDS_GAGNANT"].update(odds_table(what_was_printed), visible=True)
                window["ODDS_COMBINE_GAGNANT"].update(visible=False)
                window["DELETE_MATCH_GAGNANT"].update(visible=True)
                window["RELOAD_ODDS_GAGNANT"].update(visible=True)
            window["RESULT_GAGNANT"].update(stakes(what_was_printed), visible=True)
            window["TEXT_GAGNANT"].update(visible=True)
            for i, elem in enumerate(indicators(what_was_printed)):
                window["INDICATORS_GAGNANT" + str(i)].update(elem[0].capitalize(), visible=True)
                window["RESULTS_GAGNANT" + str(i)].update(elem[1], visible=True)
            sb.ODDS_INTERFACE = what_was_printed
        buffer.close()
    except IndexError:
        pass
    except ValueError:
        pass


def odds_match_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction odds_match dans l'interface
    """
    try:
        match = values["MATCHES_ODDS"][0]
        sport = values["SPORT_ODDS"][0]
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = io.StringIO()
        odds_dict = odds_match(match, sport)[1]
        sys.stdout = old_stdout  # Put the old stream back in place
        odds = odds_dict["odds"]
        date = odds_dict["date"]
        competition = odds_dict.get("competition", "Compétition inconnue")
        if len(list(odds.values())[0]) == 2:
            for key in odds.keys():
                odds[key].insert(1, "-   ")
        table = []
        for key, value in odds.items():
            table.append([key] + list(map(str, value)))
        table.sort()
        window["ODDS_ODDS"].update(table, visible=True)
        if date:
            window["DATE_ODDS"].update(date.strftime("%A %d %B %Y %H:%M"), visible=True)
        else:
            window["DATE_ODDS"].update(visible=False)
        window["MATCH_ODDS"].update(match, visible=True)
        window["COMPETITION_ODDS"].update(competition, visible=True)
        trj, bookmakers, best_odds = trj_match(sb.ODDS[sport][match])
        window["TRJ_ODDS"].update("TRJ : {}%".format(round(trj*100, 3)))
        window["INFOS_ODDS"].update("\n".join(bookmaker + " @ " + str(odd) for bookmaker, odd in zip(bookmakers, best_odds)))
        window["GOTO_SITE_ODDS"].update(visible=sb.BETA)
        window["DELETE_SITE_ODDS"].update(visible=True)
        window["DELETE_MATCH_ODDS"].update(visible=True)
    except IndexError:
        pass

def delete_site_interface(window, values):
    try:
        match = values["MATCHES_ODDS"][0]
        sport = values["SPORT_ODDS"][0]
        i_line = values["ODDS_ODDS"][0]
        lines = window["ODDS_ODDS"].get()
        del sb.ODDS[sport][match]["odds"][lines[i_line][0]]
        if not sb.ODDS[sport][match]["odds"]:
            delete_odds_interface(window, values)
        else:
            odds_match_interface(window, values)
    except IndexError:
        pass

def delete_odds_interface(window, values):
    try:
        match = values["MATCHES_ODDS"][0]
        sport = values["SPORT_ODDS"][0]
        del sb.ODDS[sport][match]
        matches = sorted(list([x for x in sb.ODDS[values["SPORT_ODDS"][0]] if values["SEARCH_ODDS"].lower() in x.lower()]), key=lambda x:trj_match(sb.ODDS[values["SPORT_ODDS"][0]][x])[0], reverse=True)
        window['MATCHES_ODDS'].update(values=matches)
        window["MATCHES"].update(values=matches)
        window["ODDS_ODDS"].update(visible=False)
        window["DATE_ODDS"].update(visible=False)
        window["MATCH_ODDS"].update(visible=False)
        window["DELETE_SITE_ODDS"].update(visible=False)
        window["DELETE_MATCH_ODDS"].update(visible=False)
    except IndexError:
        pass

def compute_odds(window, values):
    try:
        sport = values["SPORT_ODDS"][0]
        stake = float(values["STAKE_ODDS"])
        match = values["MATCHES_ODDS"][0]
        _, bookmakers, best_odds = trj_match(sb.ODDS[sport][match])
    except (ValueError, IndexError) as _:
        return
    if values["OUTCOME_ODDS_SPLIT_STAKE"]:
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        mises(best_odds, stake, True)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()
        profit = float(what_was_printed.split("\n")[4].split(' = ')[1])
        stakes = eval(what_was_printed.split("\n")[5].split(' = ')[1])
    else:
        outcomes = ["1", "2"]
        if get_nb_outcomes(sport) == 3:
            outcomes.insert(1, "N")
        outcome = 0
        for i, outcome_i in enumerate(outcomes):
            if values["OUTCOME_ODDS_"+outcome_i]:
                outcome = i
                break
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        mises2(best_odds, stake, outcome, True)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()
        profit = float(what_was_printed.split("\n")[5].split(' = ')[1])
        stakes = eval(what_was_printed.split("\n")[6].split(' = ')[1])
    teams = match.split(" - ")
    if get_nb_outcomes(sport) == 3:
        teams.insert(1, "Nul")
    totals = [round(stake_i * odd_i, 2) for stake_i, odd_i in zip(stakes, best_odds)]
    table = {"Issue": teams, "Bookmaker": bookmakers, "Cote": best_odds, "Mise": stakes, "Total": totals}
    infos = {"TRJ" : [str(round(gain(best_odds)*100, 3))+"%"], "Plus-value": [profit]}
    text = "\n".join([tabulate.tabulate(table, headers='keys', tablefmt='fancy_grid'),
                      tabulate.tabulate(infos, headers='keys', tablefmt='fancy_grid')])
    window["RESULT_ODDS"].update(text, visible=True)
    if sys.platform.startswith("win"):
        copy_to_clipboard(text)


def get_current_competitions_interface(window, values):
    try:
        sport = values['SPORT'][0]
        current_competitions = get_all_current_competitions(sport)
        current_competitions = [_ for _ in current_competitions if _]
        competitions = get_all_competitions(sport)
        window['COMPETITIONS'].update(values=competitions)
        index_list = list(map(competitions.index, current_competitions))
        window['COMPETITIONS'].update(set_to_index=index_list)
    except IndexError:
        pass

def best_combine_reduit_interface(window, values, visible_combi_opt):
    match_list = []
    combi_boostee = []
    sport = values["SPORT_COMBI_OPT"][0]
    issues = ["1", "N", "2"] if sport and get_nb_outcomes(sport) == 3 else ["1", "2"]
    for i in range(visible_combi_opt):
        match_list.append(values["MATCH_COMBI_OPT_" + str(i)].split(" / ")[0])
        for j, issue in enumerate(issues):
            if values[issue + "_RES_COMBI_OPT_" + str(i)]:
                combi_boostee.append(j)
                break
    site_booste = values["SITE_COMBI_OPT"]
    mise_max = float(values["STAKE_COMBI_OPT"])
    cote_boostee = float(values["ODD_COMBI_OPT"])
    old_stdout = sys.stdout  # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()
    if values["PROGRESSIVE_COMBI_OPT"]:
        best_combine_booste_progressif(match_list, combi_boostee, site_booste, mise_max, sport, cote_boostee)
    else:
        best_combine_booste(match_list, combi_boostee, site_booste, mise_max, sport, cote_boostee)
    sys.stdout = old_stdout  # Put the old stream back in place
    what_was_printed = buffer.getvalue()
    window["RESULT_COMBI_OPT"].update(stakes(what_was_printed), visible=True)
    if values["PROGRESSIVE_COMBI_OPT"]:
        window["MATCH_COMBI_OPT"].update(visible=False)
        window["DATE_COMBI_OPT"].update(visible=False)
        window["ODDS_COMBI_OPT"].update(visible=False)
        window["TEXT_COMBI_OPT"].update(visible=False)
        for i in range(5):
            window["INDICATORS_COMBI_OPT" + str(i)].update(visible=False)
            window["RESULTS_COMBI_OPT" + str(i)].update(visible=False)
    else:
        match, date = infos(what_was_printed)
        window["MATCH_COMBI_OPT"].update(match)
        window["DATE_COMBI_OPT"].update(date)
        window["ODDS_COMBI_OPT"].update(visible=True)
        window["TEXT_COMBI_OPT"].update(visible=True)
        for i, elem in enumerate(indicators(what_was_printed)):
            window["INDICATORS_COMBI_OPT" + str(i)].update(elem[0].capitalize(), visible=True)
            window["RESULTS_COMBI_OPT" + str(i)].update(elem[1], visible=True)
    buffer.close()
    sb.ODDS_INTERFACE = what_was_printed


def find_surebets_interface(window, values):
    matches = []
    sport = values["SPORT_SUREBETS"][0]
    trj_min = float(values["TRJ_SUREBETS"])/100
    for match in sb.ODDS[sport]:
        if trj_match(sb.ODDS[sport][match])[0] >= trj_min:
            matches.append(match)
    matches.sort(key=lambda x :trj_match(sb.ODDS[sport][x])[0], reverse=True)
    window["MATCHES_SUREBETS"].update(matches)
    if not matches:
        window["MESSAGE_SUREBETS"].update("Aucun surebet trouvé")
    else:
        window["MESSAGE_SUREBETS"].update("")


def odds_match_surebets_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction odds_match dans l'interface
    """
    try:
        match = values["MATCHES_SUREBETS"][0]
        sport = values["SPORT_SUREBETS"][0]
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = io.StringIO()
        odds_dict = odds_match(match, sport)[1]
        sys.stdout = old_stdout  # Put the old stream back in place
        odds = odds_dict["odds"]
        date = odds_dict["date"]
        if len(list(odds.values())[0]) == 2:
            for key in odds.keys():
                odds[key].insert(1, "-   ")
        table = []
        for key, value in odds.items():
            table.append([key] + list(map(str, value)))
        table.sort()
        window["ODDS_SUREBETS"].update(table, visible=True)
        if date:
            window["DATE_SUREBETS"].update(date.strftime("%A %d %B %Y %H:%M"), visible=True)
        else:
            window["DATE_SUREBETS"].update(visible=False)
        window["MATCH_SUREBETS"].update(match, visible=True)
        trj, bookmakers, best_odds = trj_match(sb.ODDS[sport][match])
        window["INFOS_TRJ_SUREBETS"].update("TRJ : {}%".format(round(trj*100, 3)))
        window["INFOS_ODDS_SUREBETS"].update(" / ".join(bookmaker + " @ " + str(odd) for bookmaker, odd in zip(bookmakers, best_odds)))
    except (IndexError, ValueError) as _:
        pass



def find_values_interface(window, values):
    matches = []
    if not (values["SPORT_VALUES"] and values["RATE_VALUES"] and values["TRJ_VALUES"]):
        return
    sport = values["SPORT_VALUES"][0]
    rate_min = float(values["RATE_VALUES"])/100
    trj_min = float(values["TRJ_VALUES"])/100
    for match in sb.ODDS[sport]:
        if get_values(sb.ODDS[sport][match], rate_min)[0] >= rate_min and trj_match(sb.ODDS[sport][match])[0] >= trj_min:
            matches.append(match)
    matches.sort(key=lambda x :get_values(sb.ODDS[sport][x], rate_min)[0], reverse=True)
    window["MATCHES_VALUES"].update(matches)
    if not matches:
        window["MESSAGE_VALUES"].update("Aucune value trouvée")
    else:
        window["MESSAGE_VALUES"].update("")


def odds_match_values_interface(window, values):
    """
    :param window: Fenêtre principale PySimpleGUI
    :param values: Valeurs de la fenêtre principale
    :return: Affiche le résultat de la fonction odds_match dans l'interface
    """
    try:
        match = values["MATCHES_VALUES"][0]
        sport = values["SPORT_VALUES"][0]
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = io.StringIO()
        odds_dict = odds_match(match, sport)[1]
        sys.stdout = old_stdout  # Put the old stream back in place
        odds = odds_dict["odds"]
        date = odds_dict["date"]
        if len(list(odds.values())[0]) == 2:
            for key in odds.keys():
                odds[key].insert(1, "-   ")
        table = []
        for key, value in odds.items():
            table.append([key] + list(map(str, value)))
        table.sort()
        window["ODDS_VALUES"].update(table, visible=True)
        if date:
            window["DATE_VALUES"].update(date.strftime("%A %d %B %Y %H:%M"), visible=True)
        else:
            window["DATE_VALUES"].update(visible=False)
        window["MATCH_VALUES"].update(match, visible=True)
        rate, infos_value = get_values(sb.ODDS[sport][match], 0)
        window["INFOS_VALUE_VALUES"].update("Value max : {}%".format(round(rate*100, 2)))
        window["INFOS_ODDS_VALUES"].update(" / ".join("{} @ {} (+{}%)".format(bookmaker, odd, round(r*100, 2)) for bookmaker, r, odd in infos_value))
        trj = trj_match(sb.ODDS[sport][match])[0]
        window["INFOS_TRJ_VALUES"].update("TRJ : {}%".format(round(trj*100, 3)))
    except (IndexError, ValueError, TypeError) as _:
        pass

def get_url_by_id(bookmaker, id_match, sport):
    if not id_match:
        print("Match non trouvé")
        return
    if bookmaker == "betclic":
        return "https://www.betclic.fr/a-m"+str(id_match)
    if bookmaker == "winamax":
        return "https://www.winamax.fr/paris-sportifs/match/"+id_match
    if bookmaker == "pmu":
        return "https://paris-sportifs.pmu.fr/event/"+id_match
    if bookmaker == "zebet":
        return "https://www.zebet.fr/fr/event/{}-a".format(id_match)
    if bookmaker == "parionssport":
        return "https://www.enligne.parionssport.fdj.fr/paris-football/a/a/{}/a".format(id_match.strip("e"))
    if bookmaker == "unibet":
        return "https://www.unibet.fr/sport/a/event/a-{}.html".format(id_match)
    if bookmaker == "bwin":
        return "https://sports.bwin.fr/fr/sports/tournois/a-{}".format(id_match)
    if bookmaker == "joa":
        return "https://www.joabet.fr/fr/sport/evenement/0/0/0/{}".format(id_match)
    if bookmaker == "pokerstars":
        return "https://www.pokerstarssports.fr/#/a/event/{}".format(id_match)
    if bookmaker == "france_pari":
        return "https://www.france-pari.fr/evenement/{}-a".format(id_match)
    if bookmaker == "betfair":
        return "https://orbitxch.com/customer/sport/event/{}".format(id_match)
    if bookmaker == "betway":
        return "https://www.betway.fr/evenement/{}".format(id_match)
    if bookmaker == "netbet":
        return "https://www.netbet.fr" + id_match
    if bookmaker in ["barrierebet", "pasinobet", "vbet"]:
        sports = {"football":"Soccer", "tennis":"Tennis", "rugby":"RugbyUnion",
                  "handball":"Handball", "hockey-sur-glace":"IceHockey",
                  "basketball":"Basketball"}
        return "https://www.{}.fr/paris-sportifs#/{}/a/1/{}".format(bookmaker, sports[sport], id_match)
    return ""


def open_bookmaker_odds(window, values):
    if not window["MATCH_ODDS"] or not values["SPORT_ODDS"] or not values["ODDS_ODDS"]:
        print("Merci de sélectionner un sport, un match et un bookmaker")
        return
    match = window["MATCH_ODDS"].get()
    sport = values["SPORT_ODDS"][0]
    rank = values["ODDS_ODDS"][0]
    bookmaker = sorted(sb.ODDS[sport][match]["odds"].keys())[rank]
    url = get_url_by_id(bookmaker, sb.ODDS[sport][match]["id"].get(bookmaker), sport)
    if url:
        webbrowser.open(url, new=2)


def find_perf_players(window, values):
    if not values["SITES_PERF"]:
        return
    if not values["COMPETITION_PERF"]:
        return
    sb.SUREBETS, sb.MIDDLES = get_surebets_players_nba(values["SITES_PERF"], values["COMPETITION_PERF"])
    middles = sorted(sb.MIDDLES.keys(), key=lambda x:trj_match(sb.MIDDLES[x])[0], reverse=True)
    surebets = sorted(sb.SUREBETS.keys(), key=lambda x:trj_match(sb.SUREBETS[x])[0], reverse=True)
    window["MIDDLES_PERF"].update(middles)
    window["SUREBETS_PERF"].update(surebets)

def search_perf(window, values):
    try:
        perfs = sorted([x for x in sb.SUREBETS.keys() if values["SEARCH_PERF"].lower() in x.lower()], key=lambda x:trj_match(sb.SUREBETS[x])[0], reverse=True)
        window['SUREBETS_PERF'].update(values=perfs)
    except KeyError:
        window['SUREBETS_PERF'].update(values=[])

def display_surebet_info(window, values):
    if not values["SUREBETS_PERF"]:
        return
    player_limit_market = values["SUREBETS_PERF"][0]
    if player_limit_market not in sb.SUREBETS:
        return
    player, limit_market = player_limit_market.split(" / ")
    limit, market = limit_market.split(".5 ")
    limit += ".5 "
    trj, bookmakers, best_odds = trj_match(sb.SUREBETS[player_limit_market])
    odds = sb.SUREBETS[player_limit_market]["odds"]
    table = []
    for key, value in odds.items():
        table.append([key] + list(map(lambda x : str(x).replace("1.01", "-   "), value)))
    table.sort()
    window["ODDS_PERF"].update(table, visible=True)
    window["MATCH_PERF"].update(sb.SUREBETS[player_limit_market]["match"])
    window["PLAYER_PERF"].update(player)
    window["MARKET_PERF"].update(market)
    window["OUTCOME0_PERF"].update("Over {} @ {} : {}".format(limit, best_odds[0], bookmakers[0]))
    window["OUTCOME1_PERF"].update("Under {} @ {} : {}".format(limit, best_odds[1], bookmakers[1]), visible=best_odds[1]>1.01)
    window["TRJ_PERF"].update("TRJ : {}%".format(round(trj*100, 3)), visible=best_odds[1]>1.01)
    window["PROBA_MIDDLE_PERF"].update("")
    window["SUM_MIDDLE_PERF"].update("")


def display_middle_info(window, values):
    if not values["MIDDLES_PERF"]:
        return
    player_down_up_market = values["MIDDLES_PERF"][0]
    if player_down_up_market not in sb.MIDDLES:
        return
    player, down_up_market = player_down_up_market.split(" / ")
    down, up_market = down_up_market.split(" - ")
    up, market = up_market.split(".5 ")
    up += ".5 "
    trj, bookmakers, best_odds = trj_match(sb.MIDDLES[player_down_up_market])
    if market == "Points":
        mean = float(up)
    else:
        mean = (float(up) + float(down))/2
    proba = 0
    for i in range(int(float(down)+1), int(float(up)+1)):
        proba += scipy.stats.poisson.pmf(i, mean)
    proba = round(proba*100, 3)
    trj = round(trj*100, 3)
    odds = sb.MIDDLES[player_down_up_market]["odds"]
    table = []
    for key, value in odds.items():
        table.append([key] + list(map(lambda x : str(x).replace("1.01", "-   "), value)))
    table.sort()
    window["ODDS_PERF"].update(table, visible=True)
    window["MATCH_PERF"].update(sb.MIDDLES[player_down_up_market]["match"])
    window["PLAYER_PERF"].update(player)
    window["MARKET_PERF"].update(market)
    window["OUTCOME0_PERF"].update("Over {} @ {} : {}".format(down, best_odds[0], bookmakers[0]))
    window["OUTCOME1_PERF"].update("Under {} @ {} : {}".format(up, best_odds[1], bookmakers[1]))
    window["TRJ_PERF"].update("TRJ : {}%".format(trj))
    window["PROBA_MIDDLE_PERF"].update("Probabilité de middle : {} %".format(proba))
    window["SUM_MIDDLE_PERF"].update("TRJ + proba : {} %".format(trj + proba), text_color="red" if trj+proba>100 else "black")

def sort_middle_gap(window, values):
    if not sb.MIDDLES:
        return
    def get_gap_length(key):
        gap = key.split(" / ")[1]
        limit1, limit2 = gap.split()[:3:2]
        return float(limit2)-float(limit1), trj_match(sb.MIDDLES[key])[0]
    middles = sorted(sb.MIDDLES.keys(), key=get_gap_length, reverse=True)
    window["MIDDLES_PERF"].update(middles)


def sort_middle_trj(window, values):
    if not sb.MIDDLES:
        return
    middles = sorted(sb.MIDDLES.keys(), key=lambda x:trj_match(sb.MIDDLES[x])[0], reverse=True)
    window["MIDDLES_PERF"].update(middles)

def sort_middle_proba(window, values):
    if not sb.MIDDLES:
        return
    def get_gap_proba(key):
        _, down_up_market = key.split(" / ")
        down, up_market = down_up_market.split(" - ")
        up, market = up_market.split(".5 ")
        up += ".5 "
        trj, _, best_odds = trj_match(sb.MIDDLES[key])
        if market == "Points":
            mean = float(up)
        else:
            mean = (float(up) + float(down))/2
        proba = 0
        for i in range(int(float(down)+1), int(float(up)+1)):
            proba += scipy.stats.poisson.pmf(i, mean)
        return proba + trj
    middles = sorted(sb.MIDDLES.keys(), key=get_gap_proba, reverse=True)
    window["MIDDLES_PERF"].update(middles)
    

def best_match_miles_interface(window, values):
    try:
        bet = float(values["BET_MILES"])
        sport = values["SPORT_MILES"][0]
        ticket = values["TICKET_MILES"][0]
        multiplicator = float(values["MULTIPLICATOR_MILES"])
        rate = int(ticket.strip("€"))/sb.MILES_RATES[ticket]
        date_max, time_max = None, None
        if values["DATE_MAX_MILES_BOOL"]:
            date_max = values["DATE_MAX_MILES"]
            time_max = values["TIME_MAX_MILES"].replace(":", "h")
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()
        best_match_under_conditions2("winamax", 1.05, bet, sport, date_max, time_max, miles=True, rate_eur_miles=rate, multiplicator=multiplicator)
        sys.stdout = old_stdout  # Put the old stream back in place
        what_was_printed = buffer.getvalue()  # contains the entire contents of the buffer.
        match, date = infos(what_was_printed)
        if match is None:
            window["MATCH_MILES"].update("Aucun match trouvé")
            window["DELETE_MATCH_MILES"].update(visible=False)
            window["DATE_MILES"].update("")
            window["ODDS_MILES"].update(visible=False)
            window["RESULT_MILES"].update(visible=False)
            window["TEXT_MILES"].update(visible=False)
            for i in range(8):
                window["INDICATORS_MILES" + str(i)].update(visible=False)
                window["RESULTS_MILES" + str(i)].update(visible=False)
        else:
            window["MATCH_MILES"].update(match)
            window["DELETE_MATCH_MILES"].update(visible=True)
            window["RELOAD_ODDS_MILES"].update(visible=True)
            window["DATE_MILES"].update(date)
            window["ODDS_MILES"].update(odds_table(what_was_printed), visible=True)
            window["RESULT_MILES"].update(stakes(what_was_printed), visible=True)
            window["TEXT_MILES"].update(visible=True)
            for i, elem in enumerate(indicators(what_was_printed)):
                window["INDICATORS_MILES" + str(i)].update(elem[0].capitalize(),
                                                                        visible=True)
                window["RESULTS_MILES" + str(i)].update(elem[1], visible=True)
        buffer.close()
    except IndexError:
        pass
    except ValueError:
        pass

def get_best_conversion_rates_freebet(window):
    conversion_rates = {}
    high_conversion_rates = []
    with open(sb.PATH_FREEBETS, "r") as file:
        lines = file.readlines()
        for line in lines:
            bookmaker, rate = line.split()
            sb.FREEBETS_RATES[bookmaker] = float(rate)
    for sport in sb.ODDS:
        if sb.SEEN_SUREBET[sport]:
            continue
        if not sb.ODDS[sport]:
            continue
        for site in sb.FREEBETS_RATES:
            old_stdout = sys.stdout  # Memorize the default stdout stream
            sys.stdout = buffer = io.StringIO()
            best_match_freebet(site, 100, sport)
            sys.stdout = old_stdout  # Put the old stream back in place
            what_was_printed = buffer.getvalue()
            match, _ = infos(what_was_printed)
            if match is None:
                continue
            conversion_rate = float(list(indicators(what_was_printed))[1][1].strip(" %"))
            if conversion_rates.get(site, [0])[0] < conversion_rate:
                conversion_rates[site] = [conversion_rate, sport]
    table = []
    for site, details in conversion_rates.items():
        if details[0] >= sb.FREEBETS_RATES[site]:
            high_conversion_rates.append(site)
        table.append([site]+details)
    table.sort(key=lambda x: x[1], reverse=True)
    window["CONVERT_RATES_FREEBET"].update(table)
    visible = len(high_conversion_rates) > 0
    window["HIGH_FREEBET_PARSING"].update("Taux de conversion freebet haut ({})".format(", ".join(high_conversion_rates)), visible=visible, text_color="orange")

def calculator_interface(window, values, visible_calc):
    odds = []
    lay = []
    commissions = []
    stake = 0
    reference = 0
    outcomes = []
    sites = []
    for i in range(visible_calc):
        odd = 0
        try:
            odd = float(values["ODD_CALC_" + str(i)])
        except ValueError:
            pass
        odds.append(odd)
        lay.append(bool(values["LAY_BACK_LAY_CALC_" + str(i)]))
        commission = values["COMMISSION_CALC_" + str(i)]
        commissions.append(float(commission)/100 if commission else 0)
        outcomes.append(values["NAME_CALC_" + str(i)])
        sites.append(values["SITE_CALC_" + str(i)])
        if values["REFERENCE_STAKE_CALC_" + str(i)]:
            reference = i
            stake = values["STAKE_CALC_" + str(i)]
            stake = float(stake) if stake else 0
    old_stdout = sys.stdout  # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()
    calculator(odds, lay, commissions, stake, reference, outcomes, sites)
    sys.stdout = old_stdout  # Put the old stream back in place
    what_was_printed = buffer.getvalue()  # contains the entire contents of the buffer.
    window["RESULT_CALC"].update(what_was_printed, visible=True)
    
    