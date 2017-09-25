#!/usr/bin/env python
# coding=utf-8

import csv
import sys
import random
from time import time
import datetime

import numpy as np
import itertools
from os.path import join


import matplotlib
matplotlib.use('Qt5Agg')  # Sinon pas d'affichage sur ma machine ;-)
import matplotlib.pyplot as plt

import matplotlib.style

matplotlib.style.use('fivethirtyeight')


def lire_voeux(fic="exemple.csv"):
    groupes = []
    voeux = []
    with open(fic) as fic:
        reader = csv.reader(fic, delimiter=',')
        for ligne in reader:
            if '#' in ligne[0]:
                tmp, sujets = ligne[0], ligne[1:]
            else:
                groupe, voeux_ = ligne[0], [int(_) for _ in ligne[1:]]
                groupes.append(groupe)
                voeux.append(voeux_)
    return sujets, groupes, np.array(voeux)

def __calculer_satisfactions(attributions, voeux):
    somme = 0.0
    for idx, sujet in enumerate(attributions):
        somme += voeux[idx][sujet]
    return somme / len(attributions)

def __calcul_variation_moyenne(voeux, NB=500):
    diff = 0
    somme_voeux = np.sum(voeux, axis=0)
    sujets_possibles = np.where(somme_voeux > 0)[0]  # Seulement les non nuls
    satisfaction = __calculer_satisfactions(
        sujets_possibles[0:len(groupes)], voeux)

    for _ in range(NB):
        a = random.randint(0, len(groupes) - 1)
        b = random.randint(0, sujets_possibles.shape[0] - 1)
        sujets_possibles[b], sujets_possibles[
            a] = sujets_possibles[a], sujets_possibles[b]
        satisfaction_ = __calculer_satisfactions(
            sujets_possibles[0:len(groupes)], voeux)
        diff += np.abs(satisfaction_ - satisfaction)
        satisfaction = satisfaction_

    return diff / NB

def solution_exhaustive(groupes, sujets, voeux):
    somme_voeux = np.sum(voeux, axis=0)
    sujets_possibles = np.where(somme_voeux > 0)[0]  # Seulement les non nuls

    if (sujets_possibles.shape[0] < len(groupes)):
        print("Pas assez de sujets retenus")
        exit(1)

    solutions_possibles = list(
        itertools.permutations(sujets_possibles, len(groupes)))

    print("Nombre de combinaisons : ", len(solutions_possibles))
    valeurs_solutions = [__calculer_satisfactions(
        _, voeux) for _ in solutions_possibles]
    meilleur_satisfaction = max(valeurs_solutions)
    print("Nombre de solution(s) : ", sum(
        _ == meilleur_satisfaction for _ in valeurs_solutions))

    meilleur_solution = valeurs_solutions.index(meilleur_satisfaction)

    for idx, s in enumerate(solutions_possibles[meilleur_solution]):
        print(groupes[idx], " -> ", sujets[int(s)], " : ", voeux[idx][s])
    print("Satisfaction : ", meilleur_satisfaction)

def attribuer_projet_aleatoire(groupes, sujets, voeux):
    NB_REP = 2000
    # Extraction des sujets retenus
    somme_voeux = np.sum(voeux, axis=0)
    sujets_possibles = np.where(somme_voeux > 0)[0]  # Seulement les non nuls

    if (sujets_possibles.shape[0] < len(groupes)):
        print("Pas assez de sujets retenus")
        exit(1)

    evolutions = np.zeros(NB_REP)
    for _ in range(NB_REP):
        satisfaction = __calculer_satisfactions(sujets_possibles[0:len(groupes)], voeux)
        evolutions[_] = satisfaction
        # Valeurs de permutations
        a = random.randint(0, len(groupes) - 1)
        b = random.randint(0, sujets_possibles.shape[0] - 1)
        sujets_possibles[b], sujets_possibles[a] = sujets_possibles[a], sujets_possibles[b]
        satisfaction_ = __calculer_satisfactions(sujets_possibles[0:len(groupes)], voeux)
        if satisfaction > satisfaction_:
            sujets_possibles[b], sujets_possibles[a] = sujets_possibles[a], sujets_possibles[b]

    return __calculer_satisfactions(sujets_possibles[0:len(groupes)], voeux), sujets_possibles[0:len(groupes)], evolutions


def attribuer_projet_recuit(groupes, sujets, voeux):
    NB_REP = 10000
    # Extraction des sujets retenus
    somme_voeux = np.sum(voeux, axis=0)
    sujets_possibles = np.where(somme_voeux > 0)[0]  # Seulement les non nuls
    if (sujets_possibles.shape[0] < len(groupes)):
        print("Pas assez de sujets retenus")
        sys.exit()

    evolutions = np.zeros(0)
    # Calcul de la variation moyenne
    delta_E = __calcul_variation_moyenne(voeux)
    T_0 = (-1.0 * delta_E) / np.log(0.50)
    T = T_0
    # Sauvegarde du meilleur rencontré
    meilleure_satisfaction = __calculer_satisfactions(sujets_possibles[0:len(groupes)], voeux)
    meilleure_solution = sujets_possibles[0:len(groupes)]

    satisfaction = meilleure_satisfaction

    for _ in range(NB_REP):
        # Mise à jour de la température
        if _ % 250 == 0:
            T = 0.9 * T

        # Valeurs de permutations
        a = random.randint(0, len(groupes) - 1)
        b = random.randint(0, sujets_possibles.shape[0] - 1)
        sujets_possibles[b], sujets_possibles[a] = sujets_possibles[a], sujets_possibles[b]
        satisfaction_ = __calculer_satisfactions(sujets_possibles[0:len(groupes)], voeux)
        diff = satisfaction_ - satisfaction

        r = np.random.random()
        seuil = np.exp(1.0 * diff / T)
        # Solution trop mauvaise pour le recuit
        if diff < 0 and r > seuil:
            sujets_possibles[b], sujets_possibles[a] = sujets_possibles[a], sujets_possibles[b]
        else:
            satisfaction = satisfaction_
        # Sauvegarde de la meilleur solution
        if satisfaction_ > meilleure_satisfaction:
            meilleure_satisfaction = satisfaction_
            meilleure_solution = np.array(sujets_possibles[0:len(groupes)])

        evolutions = np.append(evolutions, satisfaction)

        # Conditions d'arrêt
        if meilleure_satisfaction == 5 or (_ > 5000 and np.std(evolutions[_ - 5000:_]) < 0.0001):
            return meilleure_satisfaction, meilleure_solution, evolutions

    return meilleure_satisfaction, meilleure_solution, evolutions


def recherches_multiples(groupes, sujets, voeux, nb_rep=100, fic="solutions.csv"):
    solutions = []
    valeurs = []
    satisfaction_maximale = 0.0
    for _ in range(nb_rep):
        print(_)
        satisfaction, attributions, evolutions = attribuer_projet_recuit(groupes, sujets, voeux)
        solutions.append(attributions)
        valeurs.append(satisfaction)
        # Valeur maximale des satisfaction
    satisfaction_maximale = max(valeurs)
    print("Satisfaction maximale : ", satisfaction_maximale)
    meilleures_solutions = set()
    for s, v in zip(solutions, valeurs):
        if v == satisfaction_maximale:
            meilleures_solutions.add(tuple(s))  # Car tuples immuable
    print("%d configurations différentes trouvées"%(len(meilleures_solutions)))
    with open(fic, 'w') as csvfile:
        writer = csv.writer(csvfile)
        # Premier ligne groupes
        writer.writerow(groupes)
        # Lignes suivantes solutions
        for s in meilleures_solutions:
            writer.writerow([sujets[int(_)] for _ in s])


sujets, groupes, voeux = lire_voeux("exemple_complet.csv")
recherches_multiples(groupes, sujets, voeux, 50)
