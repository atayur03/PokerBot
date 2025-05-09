from tqdm import tqdm # type: ignore
import numpy as np # type: ignore
from hand_evaluator import evaluate
import treys # type: ignore
import copy
import joblib # type: ignore
import argparse

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
        self.min_bet_size = 200
        self.starting_stack = 20000
        self.game_stage = 2
        self.consecutive_non_passive_actions = 0
        self.curr_round_plays = 0 



class Node:
    def __init__(self) -> None:
        #info set: "holecards + shown comminty cards + action" as one string
        self.infoSet = ""
        self.regretSum = np.zeros(NUM_ACTIONS)
        self.strategy = np.zeros(NUM_ACTIONS)
        self.strategySum = np.zeros(NUM_ACTIONS)

    def describe(self):
        print(
            "Infoset: {} -> Strategy at this infoset: {}, RegretSum: {}".format(
                self.infoSet, np.around(self.getAverageStrategy(), 2), self.regretSum.sum()
            )
        )

    def getStrategy(self, realization_weight):
        for a in range(NUM_ACTIONS):
            self.strategy[a] = max(0, self.regretSum[a])

        normalizingSum = self.strategy.sum()
        for a in range(NUM_ACTIONS):
            if normalizingSum > 0:
                self.strategy[a] /= normalizingSum
            else:
                self.strategy[a] = 1 / NUM_ACTIONS

            self.strategySum[a] += realization_weight * self.strategy[a]

        return self.strategy

    def getAverageStrategy(self):
        normalizingSum = self.strategySum.sum()
        avgStrategy = np.zeros(NUM_ACTIONS)
        for a in range(NUM_ACTIONS):
            if normalizingSum > 0:
                avgStrategy[a] = self.strategySum[a] / normalizingSum
            else:
                avgStrategy[a] = 1 / NUM_ACTIONS

        return avgStrategy


def check_base_case(player, all_community, player_cards, shown_community, history, p0, p1):
    #previous action was a fold
    if history.total_pot_size >= 2 * history.starting_stack:
        all_history.append(
            {
                "history": history.history_str,
                "player_cards": player_cards[0],
                "opponent_cards": player_cards[1],
                "community_cards": [str(x) for x in all_community],
            }
        )
        return history.total_pot_size

    if history.history_str[-1] == "f":  
        all_history.append(
            {
                "history": history.history_str,
                "player_cards": player_cards[0],
                "opponent_cards": player_cards[1],
                "community_cards": [str(x) for x in all_community],
            }
        )
        return history.total_pot_size
    #showdown
    elif history.game_stage == 6:
        all_history.append(
            {
                "history": history.history_str,
                "player_cards": player_cards[0],
                "opponent_cards": player_cards[1],
                "community_cards": [str(x) for x in all_community],
            }
        )
        hero_hand = [treys.Card.new(x) for x in player_cards[player]]
        villain_hand = [treys.Card.new(x) for x in player_cards[1-player]]
        board = [treys.Card.new(x) for x in all_community]
        winner = evaluate(hero_hand, villain_hand, board)  
        # if we win a 10000 pot, we profit 5000
        if winner == -1:
            return history.total_pot_size / 2
        #if we chop we win nothing
        if winner == 0:
            return 0
        #if we lose we lose half the pot
        if winner == 1:
            return -history.total_pot_size / 2
    #hand continues
    else:
        return None
                  
        
    

def cfr(all_community, player_cards, shown_community, history, p0, p1):
    #determine who has next action
    plays = len(history.history_str)
    player = plays % 2
    opponent = 1 - player
    #check if hand is over
    if plays >= 1:
      res = check_base_case(player, all_community, player_cards, shown_community, history, p0, p1)
      #if hand ends 
      if res is not None:
          return res
    #otherwise move on

    #build infoSet
    #preflop infoSet
    player_cards_str = ''.join(player_cards[player])
    if shown_community == None:
        infoSet = player_cards_str + history.history_str
    else:
        shown_community_str = ''.join(shown_community)
        infoSet = player_cards_str + shown_community_str + history.history_str
    
    #map to our node
    # if no node make one
    if infoSet not in nodeMap:
        node = Node()
        node.infoSet = infoSet
        nodeMap[infoSet] = node
    else:
        node = nodeMap[infoSet]
    
    strategy = node.getStrategy(p0 if player == 0 else p1)
    util = np.zeros(NUM_ACTIONS)
    nodeUtil = 0

    for a in range(NUM_ACTIONS):
        nextHistory = copy.deepcopy(history)
        nextHistory.curr_round_plays += 1
        
        #fold
        if a == 0:
            nextHistory.history_str += "f"
            nextHistory.consecutive_non_passive_actions = 0
        #passive action
        elif a == 1:
            nextHistory.history_str += "c"  # Check/Call
            nextHistory.consecutive_non_passive_actions = 0
            if history.history_str == "":
                history.total_pot_size = 2 * history.min_bet_size
            elif history.history_str[-1] == "c":
                history.total_pot_size = history.total_pot_size
            elif history.history_str[-1] == "b":
                history.total_pot_size = history.total_pot_size * 1.25
            elif history.history_str[-1] == "r":
                history.total_pot_size = history.total_pot_size * 1.5
            elif history.history_str[-1] == "a":
                history.total_pot_size = 2 * history.starting_stack
            #passive action ends this round of betting
            if (nextHistory.curr_round_plays > 1):
                nextHistory.game_stage += 1
                nextHistory.curr_round_plays = 0
                nextHistory.min_bet_size = 0
                if nextHistory.game_stage == 3:
                    shown_community = all_community[0:3]
                elif nextHistory.game_stage == 4:
                    shown_community = all_community[0:4]
                elif nextHistory.game_stage == 5:
                    shown_community = all_community[0:5]        
        #raise 1/3 pot
        elif a == 2:
            nextHistory.consecutive_non_passive_actions += 1
            if nextHistory.consecutive_non_passive_actions >= 3:
                continue
            if len(history.history_str) >= 1 and history.history_str[-1] == "a":
                continue
            nextHistory.history_str += "b"
            nextHistory.total_pot_size *= 4/3
        #raise pot
        elif a == 3:
            continue
            nextHistory.consecutive_non_passive_actions += 1
            if nextHistory.consecutive_non_passive_actions >= 3:
                continue
            if len(history.history_str) >= 1 and history.history_str[-1] == "a":
                continue
            nextHistory.history_str += "r"
            nextHistory.total_pot_size *= 2
        #jam
        elif a == 4:
            nextHistory.consecutive_non_passive_actions += 1
            if nextHistory.consecutive_non_passive_actions >= 3:
                continue
            if len(history.history_str) >= 1 and history.history_str[-1] == "a":
                continue
            nextHistory.history_str += "a"
            nextHistory.total_pot_size = history.starting_stack + nextHistory.total_pot_size / 2
        #recursive next step
        util[a] = (
            -cfr(
                all_community,
                player_cards,
                shown_community,
                nextHistory,
                p0 * strategy[a],
                p1,
            )
            if player == 0
            else -cfr(
                all_community,
                player_cards,
                shown_community,
                nextHistory,
                p0,
                p1 * strategy[a],
            )
        )
        nodeUtil += strategy[a] * util[a]

    # For each action, compute and accumulate counterfactual regret
    for a in range(NUM_ACTIONS):
        regret = util[a] - nodeUtil
        node.regretSum[a] += (p1 if player == 0 else p0) * regret
    return nodeUtil

averageUtils = []

def train(iterations, save=True):
    util = 0
    for i in tqdm(range(startIterations, iterations), desc="Training Loop"):
        deck = treys.Deck()
        hero_cards = [treys.Card.int_to_str(c) for c in deck.draw(2)]
        villain_cards = [treys.Card.int_to_str(c) for c in deck.draw(2)]
        community = [treys.Card.int_to_str(c) for c in deck.draw(5)]
        player_cards = [hero_cards, villain_cards]
        shown_community = None
        history = History()
        for j in tqdm(range(5)):
          util += cfr(community, player_cards, shown_community, history, 1, 1)
          if i % 1 == 0:
              print("Average game value: ", util / i)
              averageUtils.append(util / i)

        if save and i % 100 == 0:
            joblib.dump(nodeMap, "HoldemNodeMap.joblib")
            joblib.dump(all_history, "HoldemTrainingHistory.joblib")
            joblib.dump(averageUtils, "averageUtils.joblib")
    

if __name__ == "__main__":
    train_from_scratch = True  # Set this to True if you want to retrain from scratch
    parser = argparse.ArgumentParser(description="Train a Hold'Em AI.")
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        dest="save",
        default=True,
        help="Save the trained model and history",
    )
    parser.add_argument(
        "-l",
        "--load",
        action="store_true",
        dest="load",
        default=False,
        help="Load the trained model and history to resume training",
    )
    parser.add_argument(
        "-v",
        "--visualize",
        action="store_true",
        dest="visualize",
        default=False,
        help="Print out all information sets with their corresponding strategy. Do NOT train",
    )

    args = parser.parse_args()
    save = args.save  # Save history and information set
    load = args.load
    visualize = args.visualize
    if load:
        nodeMap = joblib.load("HoldemNodeMap.joblib")
        history = joblib.load("HoldemTrainingHistory.joblib")
        averageUtils = joblib.load("averageUtils.joblib")

        assert len(nodeMap) > 0
        assert len(history) > 0
        assert startIterations > 0

    if not visualize:
        train(5, save)

    nodeMap = joblib.load("HoldemNodeMap.joblib")  # Load information sets
    print("Total Number of Infosets:", len(nodeMap))
    for infoset in nodeMap:
        nodeMap[infoset].describe()

        
    


