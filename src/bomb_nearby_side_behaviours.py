import py_trees
import numpy as np
import utils


class BombNearByCheck(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super(BombNearByCheck, self).__init__(name)
        self.blackboard = py_trees.blackboard.Blackboard()

    def setup(self):
        pass

    def initialise(self):
        pass

    def update(self):
        position = self.blackboard.obs['position']
        board = self.blackboard.obs['board']
        bomb_blast_strength = self.blackboard.obs['bomb_blast_strength']
        flame_board = (board == 4)
        nonzero_indices = np.nonzero(flame_board)
        bomb_blast_strength[nonzero_indices] = 1
        #return utils.check_visibility(position, bomb_blast_strength)

        if not utils.check_bomb_range(position,
                                      bomb_blast_strength) == utils.SUCCESS:
            # print('Bomb nearby!')
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class KickCheck(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super(KickCheck, self).__init__(name)
        self.blackboard = py_trees.blackboard.Blackboard()

    def setup(self):
        pass

    def initialise(self):
        pass

    def update(self):
        position = self.blackboard.obs['position']
        board = self.blackboard.obs['board']
        canKick = self.blackboard.obs['can_kick']
        if not canKick:
            return py_trees.common.Status.FAILURE
        elif self.blackboard.recently_kicked_bomb < 4:
            self.blackboard.recently_kicked_bomb += 1
            return py_trees.common.Status.FAILURE

        neighbours = utils.get_neighbour_indices(position)

        # Check if immediate neighbor is a bomb
        for neighbor in neighbours:
            if board[neighbor[0], neighbor[1]] == 3:
                return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.FAILURE


class Kick(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super(Kick, self).__init__(name)
        self.blackboard = py_trees.blackboard.Blackboard()

    def setup(self):
        pass

    def initialise(self):
        pass

    def update(self):
        position = self.blackboard.obs['position']
        board = self.blackboard.obs['board']
        bomb_positions = []
        neighbours = utils.get_neighbour_indices(position)

        for neighbor in neighbours:
            if neighbor == self.blackboard.bomb_position:
                self.blackboard.bomb_position = None
                continue
            if board[neighbor[0], neighbor[1]] == 3:
                potential_action = utils.next_action(position, neighbor)
                if potential_action == 1 and neighbor[0] > 1 and board[
                        neighbor[0] - 1, neighbor[1]] == 0:
                    self.blackboard.action = potential_action
                    self.blackboard.recently_kicked_bomb = 0
                    return py_trees.common.Status.SUCCESS
                if potential_action == 2 and neighbor[0] < 10 and board[
                        neighbor[0] + 1, neighbor[1]] == 0:
                    self.blackboard.action = potential_action
                    self.blackboard.recently_kicked_bomb = 0
                    return py_trees.common.Status.SUCCESS
                if potential_action == 3 and neighbor[1] > 1 and board[
                        neighbor[0], neighbor[1] - 1] == 0:
                    self.blackboard.action = potential_action
                    self.blackboard.recently_kicked_bomb = 0
                    return py_trees.common.Status.SUCCESS
                if potential_action == 4 and neighbor[1] < 10 and board[
                        neighbor[0], neighbor[1] + 1] == 0:
                    self.blackboard.action = potential_action
                    self.blackboard.recently_kicked_bomb = 0
                    return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class SafePlaceCheck(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super(SafePlaceCheck, self).__init__(name)
        self.blackboard = py_trees.blackboard.Blackboard()

    def setup(self):
        pass

    def initialise(self):
        pass

    def update(self):
        # print(self.blackboard)
        # return py_trees.common.Status.RUNNING
        position = self.blackboard.obs['position']
        bomb_blast_strength = self.blackboard.obs['bomb_blast_strength']
        board = self.blackboard.obs['board']
        flame_board = (board == 4)
        nonzero_indices = np.nonzero(flame_board)
        bomb_blast_strength[nonzero_indices] = 1

        # print('In SafePlaceCheck')

        # Do nothing if we are in a safe place and there is a bomb around
        if utils.check_bomb_range(
                position, bomb_blast_strength
        ) == utils.SUCCESS and not utils.is_our_friend_blocked_by_us(
                0, position):
            self.blackboard.action = 0
            # print('I am safe!')
            return py_trees.common.Status.SUCCESS

        # Not in safe place
        return py_trees.common.Status.FAILURE


class FindAndGoToSafePlace(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super(FindAndGoToSafePlace, self).__init__(name)
        self.blackboard = py_trees.blackboard.Blackboard()

    def setup(self):
        pass

    def initialise(self):
        pass

    def update(self):
        position = self.blackboard.obs['position']

        #Find scores of surrounding cells
        scores, positions = self.find_scores(position)

        #print(scores)

        optimum_index = np.argwhere(scores == np.amax(scores))
        if np.shape(optimum_index)[0] > 1:
            for neighbor in optimum_index:
                n_scores, _ = self.find_scores(positions[neighbor[0]])
                max_n_scores = np.amax(n_scores)
                scores[neighbor[0]] += max_n_scores

        best_index = np.argmax(scores)
        #print('best_index: ',best_index)
        #print('length scores: ', scores.shape)
        #if best_index == 0:
        #print('best index = 0')
        self.blackboard.action = best_index
        # print('Go to safeplace: ', best_index)
        return py_trees.common.Status.SUCCESS

    def find_scores(self, position):

        pos_x, pos_y = position
        positions = np.clip(
            np.array([(pos_x, pos_y), (pos_x - 1, pos_y), (pos_x + 1, pos_y),
                      (pos_x, pos_y - 1), (pos_x, pos_y + 1)]), 0, 10)

        scores = np.zeros((positions.shape[0], 1))

        for i, board_index in enumerate(positions):

            scores[i] = utils.calculate_score(board_index)

            total_neighbour_score = 0
            """
            already_encountered_start_pos = False
            for neighbor in utils.get_neighbour_indices(board_index):
                # Reaching end of the board
                if neighbor[0] == board_index[0] and neighbor[
                        1] == board_index[1]:
                    if already_encountered_start_pos:
                        neighbor_score = -1000 * 0.1
                    else:
                        already_encountered_start_pos = True
                        neighbor_score = utils.calculate_score(neighbor)
                # Free to roam
                else:
                    neighbor_score = utils.calculate_score(neighbor)
                total_neighbour_score += neighbor_score * 0.01
                """
            scores[i] += total_neighbour_score
        # print(scores)

        return scores, positions
