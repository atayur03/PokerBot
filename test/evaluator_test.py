import unittest
from treys import Card
from hand_evaluator import evaluate, simulate_equity


class TestEvaluateFunction(unittest.TestCase):

    def test_player1_wins(self):
        p1 = [Card.new('As'), Card.new('Ah')]
        p2 = [Card.new('Ks'), Card.new('Kh')]
        board = [Card.new(x) for x in ['7c', '8d', '9s', 'Jc', '2h']]
        self.assertEqual(evaluate(p1, p2, board), -1)

    def test_player2_wins(self):
        p1 = [Card.new('2s'), Card.new('2h')]
        p2 = [Card.new('Qh'), Card.new('Qs')]
        board = [Card.new(x) for x in ['7c', '8d', '9s', 'Jc', '2h']]
        self.assertEqual(evaluate(p1, p2, board), 1)

    def test_chop(self):
        p1 = [Card.new('As'), Card.new('Kd')]
        p2 = [Card.new('Ah'), Card.new('Ks')]
        board = [Card.new(x) for x in ['Qs', 'Jh', 'Tc', '2d', '3c']]
        self.assertEqual(evaluate(p1, p2, board), 0)

    def test_straight_vs_set(self):
        p1 = [Card.new('9s'), Card.new('Th')]
        p2 = [Card.new('8c'), Card.new('8h')]
        board = [Card.new(x) for x in ['Jc', 'Qd', '8s', '2c', '3h']]
        self.assertEqual(evaluate(p1, p2, board), -1)

    def test_flush_beats_two_pair(self):
        p1 = [Card.new('As'), Card.new('7s')]
        p2 = [Card.new('Kh'), Card.new('Kd')]
        board = [Card.new(x) for x in ['2s', '5s', '9s', 'Kc', '2d']]
        self.assertEqual(evaluate(p1, p2, board), -1)


class TestEquityFunction(unittest.TestCase):
    def test_river_equity(self):
        equity = simulate_equity(["Ah", "Ad"], ["Kc", "Ks"], [
                                 "2h", "3d", "5s", "9c", "Th"])
        self.assertEqual(equity, 1.0)


if __name__ == '__main__':
    unittest.main()
