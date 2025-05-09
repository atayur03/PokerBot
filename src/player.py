import numpy as np
import joblib

"""
5 actions:
1) Fold                 'f'
2) Check/Call           'c'
3) Bet/Raise 1/3        'b'
4) Bet/Raise Pot        'r'
5) Bet/Raise All In     'a' 
"""

def player(all_community, player_cards, shown_community, history, preflop=True):
  """
  Assume player_cards is a list of 2 strings (cards), ex: ['Ks', 'As']
  Assume same for shown_community
  """

  infoSet = None
  if preflop:
    # look up from preflop chart
    pass

  else:
    # create infoset string
    player_cards_str = ''.join(player_cards)
    if shown_community == None:
        infoSet = player_cards_str + history.history_str
    else:
        shown_community_str = ''.join(shown_community)
        infoSet = player_cards_str + shown_community_str + history.history_str

  # import joblib file here, look up probability array
  # assume each infoset is dictionary with keys ['f', 'c', ...] and probabilities that sum to 1
  strategy = joblib.load("infoset_path")

  # choose action from array and return
  r = np.random.rand()    # generate number [0, 1]
  running_sum = 0
  for action in strategy.keys():
     running_sum += strategy[action]
     if r < running_sum:
        return action
  return 'a'    # should only reach here if weird floating point stuff, so why not jam

