import joblib
import numpy as np # type: ignore

strat = ['f', 'c', 'b']
def getAction(strategy):
    return np.random.choice(strat, p=strategy)

class CFRPlayer:
  def __init__(self):
     #knowledge base
     self.kb = joblib.load('HoldemNodeMap.joblib')
  
  def get_strat(self, card_str, community_cards, action, check_allowed):
    lookup = card_str + community_cards + action
    if lookup in self.kb:
       node = self.kb[lookup]
       return node.strategy
    else:
      if check_allowed:
        return [0, 1, 0]
      else:
         return [0.5, 0.5, 0]
    
  def get_action(self, card_str, community_cards, action, check_allowed):
     return getAction(self.get_strat(card_str, community_cards, action, check_allowed))
