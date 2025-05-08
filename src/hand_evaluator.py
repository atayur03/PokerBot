import treys
from itertools import combinations


def evaluate(hand1, hand2, board):
    """
    Inputs:
      hand1: 2 card hand of player 1
      hand2: 2 card hand of player 2
      board: 5 card board
    Returns:
      -1  if hand1 wins
       0  if chop
       1  if hand2 wins
    """
    evaluator = treys.Evaluator()
    # 1 is royal flush
    # better hand -> lower score
    p1_score = evaluator.evaluate(board, hand1)
    p2_score = evaluator.evaluate(board, hand2)
    if p1_score < p2_score:
        return -1
    elif p1_score == p2_score:
        return 0
    else:
        return 1


def simulate_equity(h1, h2, board):
    evaluator = treys.Evaluator()
    deck = treys.Deck()
    hero_hand = [treys.Card.new(c) for c in h1]
    villain_hand = [treys.Card.new(c) for c in h2]
    board = [treys.Card.new(c) for c in board]
    used_cards = set(hero_hand + villain_hand + board)
    deck.cards = [c for c in deck.cards if c not in used_cards]

    wins = 0
    ties = 0
    total = 0

    if len(board) == 5:
        res = evaluate(hero_hand, villain_hand, board)
        equity = (res - 1) / -2
        return equity

    elif len(board) == 4:
        for (river,) in combinations(deck.cards, 1):
            community = board + [river]
            hero_score = evaluator.evaluate(hero_hand, community)
            villain_score = evaluator.evaluate(villain_hand, community)
            if hero_score < villain_score:
                wins += 1
            elif hero_score == villain_score:
                ties += 1
            total += 1

    elif len(board) == 3:
        for turn, river in combinations(deck.cards, 2):
            community = board + [turn, river]
            hero_score = evaluator.evaluate(hero_hand, community)
            villain_score = evaluator.evaluate(villain_hand, community)
            if hero_score < villain_score:
                wins += 1
            elif hero_score == villain_score:
                ties += 1
            total += 1

    elif len(board) == 0:
        for flop1, flop2, flop3, turn, river in combinations(deck.cards, 5):
            community = [flop1, flop2, flop3, turn, river]
            hero_score = evaluator.evaluate(hero_hand, community)
            villain_score = evaluator.evaluate(villain_hand, community)
            if hero_score < villain_score:
                wins += 1
            elif hero_score == villain_score:
                ties += 1
            total += 1

    else:
        raise Exception("Board of wrong size")

    return (wins + ties / 2) / total

