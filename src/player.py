import numpy as np
from hand_evaluator import simulate_equity
import treys
import random
"""
5 actions:
1) Fold           
2) Check/Call      
3) Bet/Raise 1/3 
4) Bet/Raise Pot
5) Bet/Raise All In
"""

DECK = [
    "As", "Ks", "Qs", "Js", "Ts", "9s", "8s", "7s", "6s", "5s", "4s", "3s", "2s",
    "Ah", "Kh", "Qh", "Jh", "Th", "9h", "8h", "7h", "6h", "5h", "4h", "3h", "2h",
    "Ad", "Kd", "Qd", "Jd", "Td", "9d", "8d", "7d", "6d", "5d", "4d", "3d", "2d",
    "Ac", "Kc", "Qc", "Jc", "Tc", "9c", "8c", "7c", "6c", "5c", "4c", "3c", "2c"
]


def random_player(stack_size, pot_size, check_allowed):
    """
    Randomly choose action from above
    """
    r = np.random.rand()    # generate number [0, 1]
    incr = ''
    if r < 0.2:       # fold but check if allowed
        if not check_allowed:
            incr = 'f'
        else:
            incr = 'k'
    elif r < 0.4:     # check/call
        if check_allowed:
            incr = 'k'
        else:
            incr = 'c'
    elif r < 0.6:
        if stack_size >= 1/3 * pot_size:
            raise_amount = str(max(round(1/3 * pot_size), 300))
            incr = f'b{raise_amount}'
        else:
            raise_amount = str(stack_size)
            incr = f'b{raise_amount}'
    elif r < 0.8:   # raise 3/4 pot
        if stack_size >= 3/4 * pot_size:
            raise_amount = str(max(round(3/4 * pot_size), 300))
            incr = f'b{raise_amount}'
        else:
            raise_amount = str(stack_size)
            incr = f'b{raise_amount}'
    else:           # raise all in
        raise_amount = str(stack_size)
        incr = f'b{raise_amount}'

    return incr


def base_equity_player(hole_cards, community_cards, stack_size, pot_size,
                       check_allowed, highest_current_bet):
    """
    Bet simulated equity against random hands on flop, turn, river. Preflop just check/call
    """
    NUM_SIMULATED_HANDS = 10
    incr = ''
    if len(community_cards) == 0:
        if check_allowed:
            incr = 'k'
        else:
            incr = 'c'
    else:
        # simlulate equity against random hands
        used_cards = hole_cards + community_cards
        deck = list(set(DECK) - set(used_cards))
        equity = 0
        for _ in range(NUM_SIMULATED_HANDS):
            villain_cards = random.sample(deck, 2)
            equity += simulate_equity(hole_cards, villain_cards,
                                      community_cards) / NUM_SIMULATED_HANDS
        if highest_current_bet > 0:   # call if getting odds to call
            odds = highest_current_bet / (pot_size + 2*highest_current_bet)
            if equity >= odds:
                incr = 'c'
            else:
                incr = 'f'
        else:
            raise_amount = max(round(equity * pot_size), 100)
            if stack_size >= raise_amount:
                incr = f'b{raise_amount}'
            else:
                incr = f'b{stack_size}'
    return incr
