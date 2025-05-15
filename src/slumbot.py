from player import random_player
import requests
import numpy as np
import sys
import argparse
import os
from tqdm import tqdm

sys.path.append("../src")

host = "slumbot.com"

"""
Strategy options:
1) all-in
2) check-call
3) random
4) bet_equity
5) 
) cfr
"""
STRATEGY = 'random'  # SET THE STRATEGY HERE

player = None
USERNAME = "cs4701_project"
PASSWORD = "password"


NUM_STREETS = 4
SMALL_BLIND = 50
BIG_BLIND = 100
STACK_SIZE = 20000


def ParseAction(action):
    """
    Returns a dict with information about the action passed in.
    Returns a key "error" if there was a problem parsing the action.
    pos is returned as -1 if the hand is over; otherwise the position of the player next to act.
    street_last_bet_to only counts chips bet on this street, total_last_bet_to counts all
      chips put into the pot.
    Handles action with or without a final '/'; e.g., "ck" or "ck/".
    """
    st = 0
    street_last_bet_to = BIG_BLIND
    total_last_bet_to = BIG_BLIND
    last_bet_size = BIG_BLIND - SMALL_BLIND
    last_bettor = 0
    sz = len(action)
    pos = 1
    if sz == 0:
        return {
            "st": st,
            "pos": pos,
            "street_last_bet_to": street_last_bet_to,
            "total_last_bet_to": total_last_bet_to,
            "last_bet_size": last_bet_size,
            "last_bettor": last_bettor,
        }

    check_or_call_ends_street = False
    i = 0
    while i < sz:
        if st >= NUM_STREETS:
            return {"error": "Unexpected error"}
        c = action[i]
        i += 1
        if c == "k":
            if last_bet_size > 0:
                return {"error": "Illegal check"}
            if check_or_call_ends_street:
                # After a check that ends a pre-river street, expect either a '/' or end of string.
                if st < NUM_STREETS - 1 and i < sz:
                    if action[i] != "/":
                        return {"error": "Missing slash"}
                    i += 1
                if st == NUM_STREETS - 1:
                    # Reached showdown
                    pos = -1
                else:
                    pos = 0
                    st += 1
                street_last_bet_to = 0
                check_or_call_ends_street = False
            else:
                pos = (pos + 1) % 2
                check_or_call_ends_street = True
        elif c == "c":
            if last_bet_size == 0:
                return {"error": "Illegal call"}
            if total_last_bet_to == STACK_SIZE:
                # Call of an all-in bet
                # Either allow no slashes, or slashes terminating all streets prior to the river.
                if i != sz:
                    for st1 in range(st, NUM_STREETS - 1):
                        if i == sz:
                            return {"error": "Missing slash (end of string)"}
                        else:
                            c = action[i]
                            i += 1
                            if c != "/":
                                return {"error": "Missing slash"}
                if i != sz:
                    return {"error": "Extra characters at end of action"}
                st = NUM_STREETS - 1
                pos = -1
                last_bet_size = 0
                return {
                    "st": st,
                    "pos": pos,
                    "street_last_bet_to": street_last_bet_to,
                    "total_last_bet_to": total_last_bet_to,
                    "last_bet_size": last_bet_size,
                    "last_bettor": last_bettor,
                }
            if check_or_call_ends_street:
                # After a call that ends a pre-river street, expect either a '/' or end of string.
                if st < NUM_STREETS - 1 and i < sz:
                    if action[i] != "/":
                        return {"error": "Missing slash"}
                    i += 1
                if st == NUM_STREETS - 1:
                    # Reached showdown
                    pos = -1
                else:
                    pos = 0
                    st += 1
                street_last_bet_to = 0
                check_or_call_ends_street = False
            else:
                pos = (pos + 1) % 2
                check_or_call_ends_street = True
            last_bet_size = 0
            last_bettor = -1
        elif c == "f":
            if last_bet_size == 0:
                return {"error", "Illegal fold"}
            if i != sz:
                return {"error": "Extra characters at end of action"}
            pos = -1
            return {
                "st": st,
                "pos": pos,
                "street_last_bet_to": street_last_bet_to,
                "total_last_bet_to": total_last_bet_to,
                "last_bet_size": last_bet_size,
                "last_bettor": last_bettor,
            }
        elif c == "b":
            j = i
            while i < sz and action[i] >= "0" and action[i] <= "9":
                i += 1
            if i == j:
                return {"error": "Missing bet size"}
            try:
                new_street_last_bet_to = int(action[j:i])
            except (TypeError, ValueError):
                return {"error": "Bet size not an integer"}
            new_last_bet_size = new_street_last_bet_to - street_last_bet_to
            # Validate that the bet is legal
            remaining = STACK_SIZE - street_last_bet_to
            if last_bet_size > 0:
                min_bet_size = last_bet_size
                # Make sure minimum opening bet is the size of the big blind.
                if min_bet_size < BIG_BLIND:
                    min_bet_size = BIG_BLIND
            else:
                min_bet_size = BIG_BLIND
            # Can always go all-in
            if min_bet_size > remaining:
                min_bet_size = remaining
            if new_last_bet_size < min_bet_size:
                return {"error": "Bet too small"}
            max_bet_size = remaining
            if new_last_bet_size > max_bet_size:
                return {"error": "Bet too big"}
            last_bet_size = new_last_bet_size
            street_last_bet_to = new_street_last_bet_to
            total_last_bet_to += last_bet_size
            last_bettor = pos
            pos = (pos + 1) % 2
            check_or_call_ends_street = True
        else:
            return {"error": "Unexpected character in action"}

    return {
        "st": st,
        "pos": pos,
        "street_last_bet_to": street_last_bet_to,
        "total_last_bet_to": total_last_bet_to,
        "last_bet_size": last_bet_size,
        "last_bettor": last_bettor,
    }


def NewHand(token):
    data = {}
    if token:
        data["token"] = token
    # Use verify=false to avoid SSL Error
    # If porting this code to another language, make sure that the Content-Type header is
    # set to application/json.
    response = requests.post(
        f"https://{host}/api/new_hand", headers={}, json=data)
    success = getattr(response, "status_code") == 200
    if not success:
        print("Status code: %s" % repr(response.status_code))
        try:
            print("Error response: %s" % repr(response.json()))
        except ValueError:
            pass
        sys.exit(-1)

    try:
        r = response.json()
    except ValueError:
        print("Could not get JSON from response")
        sys.exit(-1)

    if "error_msg" in r:
        print("Error: %s" % r["error_msg"])
        sys.exit(-1)

    return r


def Act(token, action):
    data = {"token": token, "incr": action}
    # Use verify=false to avoid SSL Error
    # If porting this code to another language, make sure that the Content-Type header is
    # set to application/json.
    response = requests.post(f"https://{host}/api/act", headers={}, json=data)
    success = getattr(response, "status_code") == 200
    if not success:
        print("Status code: %s" % repr(response.status_code))
        try:
            print("Error response: %s" % repr(response.json()))
        except ValueError:
            pass
        sys.exit(-1)

    try:
        r = response.json()
    except ValueError:
        print("Could not get JSON from response")
        sys.exit(-1)

    return r


def ComputeStrategy(hole_cards, board, action, strategy=STRATEGY):
    a = ParseAction(action)

    player_balance = 20000 - (a["total_last_bet_to"] - a["street_last_bet_to"])
    total_pot_balance = 2 * a["total_last_bet_to"]
    stage_pot_balance = total_pot_balance
    highest_current_bet = a["street_last_bet_to"]
    BIG_BLIND = 100
    card_str = hole_cards
    community_cards = board
    isDealer = a["pos"] == 1
    checkAllowed = a["last_bettor"] == -1

    history = convert_action_to_history(hole_cards, board, action, isDealer)
    print(history)

    if strategy == 'all-in':  # all-in
        incr = "b20000"
    elif strategy == 'check-call':  # always check or call
        if a["last_bettor"] == -1:  # no one has bet yet
            incr = "k"
        else:  # opponent has bet, so simply call
            incr = "c"
    elif strategy == 'random':  # randomized action
        incr = random_player(player_balance, total_pot_balance,
                             highest_current_bet, isDealer, checkAllowed)
    elif strategy == 'base_equity':  #
        pass
    elif strategy == 'cfr':
        incr = player.get_action(
            card_str,
            community_cards,
            total_pot_balance,
            highest_current_bet,
            BIG_BLIND,
            player_balance,
            isDealer,
            checkAllowed,
        )
    return incr


def convert_action_to_history(hole_cards, board, action, isDealer):
    DISCRETE_ACTIONS = ["k", "c", "/"]
    stage_i = 0
    if isDealer:
        history = ["2s2h", "".join(hole_cards)]
    else:
        history = ["".join(hole_cards), "2s2h"]

    i = 0
    while i < len(action):
        a = action[i]

        if a in DISCRETE_ACTIONS:
            if a == "/":
                history += ["/"]
                stage_i += 1
                if stage_i == 1:
                    history += ["".join(board[:3])]
                elif stage_i == 2:
                    history += ["".join(board[3])]
                else:
                    history += ["".join(board[4])]

            else:
                history += [a]
            i += 1

        else:
            j = i
            while j < len(action):
                if action[j] in DISCRETE_ACTIONS or (j != i and action[j] == "b"):
                    break
                j += 1

            history += [action[i:j]]
            i = j
    return history


def PlayHand(token, debug=False):
    r = NewHand(token)
    # We may get a new token back from /api/new_hand
    new_token = r.get("token")
    if new_token:
        token = new_token

    while True:
        if r.get("session_num_hands"):
            print(
                f"Total hands played:{r.get('session_num_hands')} Total Profit: {r.get('session_total')} Total Relative Profit: {r.get('session_baseline_total')}"
            )
        if debug:
            print("-----------------")
            print(repr(r))
        action = r.get("action")
        client_pos = r.get("client_pos")
        hole_cards = r.get("hole_cards")
        board = r.get("board")
        winnings = r.get("winnings")
        baseline_winnings = r.get("baseline_winnings")
        if debug:
            print("Action: %s" % action)
            if client_pos:
                print("Client pos: %i" % client_pos)
            print("Client hole cards: %s" % repr(hole_cards))
            print("Board: %s" % repr(board))
        if winnings is not None:
            print("Hand winnings: %i" % winnings)
            return (token, winnings, baseline_winnings)
        # Need to check or call
        a = ParseAction(
            action
        )
        if "error" in a:
            print("Error parsing action %s: %s" % (action, a["error"]))
            print(a)
            return (token, 0, 0)
            sys.exit(-1)  # don't exit, just don't consider this round

        incr = ComputeStrategy(hole_cards, board, action)
        if debug:
            print("Sending incremental action: %s" % incr)
        r = Act(token, incr)
        if "error_msg" in r:
            print("Error: %s" % r["error_msg"])
            return (token, 0, 0)
    # Should never get here


def Login(username, password):
    data = {"username": username, "password": password}
    # If porting this code to another language, make sure that the Content-Type header is
    # set to application/json.
    response = requests.post(f"https://{host}/api/login", json=data)
    success = getattr(response, "status_code") == 200
    if not success:
        print("Status code: %s" % repr(response.status_code))
        try:
            print("Error response: %s" % repr(response.json()))
        except ValueError:
            pass
        sys.exit(-1)

    try:
        r = response.json()
    except ValueError:
        print("Could not get JSON from response")
        sys.exit(-1)

    if "error_msg" in r:
        print("Error: %s" % r["error_msg"])
        sys.exit(-1)

    token = r.get("token")
    if not token:
        print("Did not get token in response to /api/login")
        sys.exit(-1)
    return token


def main():
    parser = argparse.ArgumentParser(description="Slumbot API example")
    parser.add_argument("--username", type=str, default=USERNAME)
    parser.add_argument("--password", type=str, default=PASSWORD)

    args = parser.parse_args()
    username = args.username
    password = args.password

    if username and password:
        token = Login(username, password)
    else:
        token = None

    num_hands = 10
    winnings_history = []
    winnings = winnings_history[-1] if len(winnings_history) > 0 else 0

    for h in tqdm(range(num_hands)):
        (token, hand_winnings, baseline_hand_winnings) = PlayHand(token)
        winnings += hand_winnings
        winnings_history.append(winnings)

    if num_hands >= 10000:
        # save to csv
        pass

    print("Total winnings: %i" % winnings)


if __name__ == "__main__":
    main()
