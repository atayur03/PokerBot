import numpy as np
import joblib

"""
5 actions:
1) Fold           
2) Check/Call      
3) Bet/Raise 1/3 
4) Bet/Raise Pot
5) Bet/Raise All In
"""


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
