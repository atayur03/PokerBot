from tqdm import tqdm

"""
5 actions:
1) Fold                 'f'
2) Check/Call           'c'
3) Bet/Raise 1/3        'b'
4) Bet/Raise Pot        'r'
5) Bet/Raise All In     'a' 
"""
NUM_ACTIONS = 5
nodeMap = {} # map from infoSet to node
startIterations = 0
all_history = [] # list of all hand histories

class History:
    # SB bet size = 1, BB bet size = 2
    def __init__(self):
        self.total_pot_size = 0
        self.history_str = ""
        self.min_bet_size = 2
        self.game_stage = 2
        self.curr_round_plays = 0  # if self.curr_round_plays == 0 and we check, then we DON'T move to the next game stage


