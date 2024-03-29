from typing import Dict, Tuple

import numpy as np

from .env import Env, EnvSpec, EnvWithModel


class ActionConstants(object):
    NUM_ACTIONS = 4
    LEFT_ACTION = 0
    UP_ACTION = 1
    RIGHT_ACTION = 2
    DOWN_ACTION = 3


class GridWorldMDP(Env):

    def __init__(self, num_states: int):
        env_spec = EnvSpec(num_states, ActionConstants.NUM_ACTIONS, 1.)

        super().__init__(env_spec)

        self._num_states = num_states
        self._state = None
        self._final_state = 0
        self._trans_mat = self._build_trans_mat()
        self._r_mat = self._build_r_mat()

    def reset(self) -> Tuple[int, Dict]:
        self._state = np.random.choice(range(1, self._num_states))
        return self._state, {'prob': 1}

    def step(self, action: int) -> Tuple[int, int, bool, bool, Dict]:
        assert action in list(range(self.spec.num_actions)), "Invalid Action"
        assert self._state != self._final_state, "Episode has ended!"

        prev_state = self._state
        self._state = np.random.choice(self.spec.num_states, p=self._trans_mat[self._state, action])
        r = self._r_mat[prev_state, action, self._state]

        return self._state, r, self._state == self._final_state, False, {}

    def _build_trans_mat(self) -> np.array:
        raise NotImplementedError("_build_trans_mat")

    def _build_r_mat(self) -> np.array:
        r_mat = np.zeros((self._num_states, ActionConstants.NUM_ACTIONS, self._num_states))

        # initialize all rewards to -1
        r_mat[:, :, :] = -1.

        # except the final state, which is 0
        r_mat[self._final_state, :, :] = 0.

        return r_mat


class GeneralGridWorldMDP(Env):
    """
    A
    2x2:
    +---+---+
    | F | 1 |
    +---+---+
    | 2 | F |
    +---+---+

    4x4:
    +---+---+---+---+
    | F | 1 | 2 | 3 |
    +---+---+---+---+
    | 4 | 5 | 6 | 7 |
    +---+---+---+---+
    | 8 | 9 | 10| 11|
    +---+---+---+---+
    | 12| 13| 14| F |
    +---+---+---+---+
    """

    def __init__(self, width: int, height: int, gamma: float = 1.):
        num_states = width * height - 1

        assert num_states > 0, "width * height - 1 must be greater than 0!"

        env_spec = EnvSpec(num_states, ActionConstants.NUM_ACTIONS, gamma)

        super().__init__(env_spec)

        self._width = width
        self._num_states = num_states
        self._state = None
        self._final_state = 0
        self._td = self._build_trans_mat()
        self._r = self._build_r_mat()

    def reset(self) -> Tuple[int, Dict]:
        self._state = np.random.choice(range(1, self._num_states))
        return self._state, {'prob': 1}

    def step(self, action: int) -> Tuple[int, int, bool, bool, Dict]:
        assert action in list(range(self.spec.num_actions)), "Invalid Action"
        assert self._state != self._final_state, "Episode has ended!"

        prev_state = self._state
        self._state = np.random.choice(self.spec.num_states, p=self._td[self._state, action])
        r = self._r[prev_state, action, self._state]

        return self._state, r, self.is_terminal(self._state), False, {}

    def is_terminal(self, state):
        return state == self._final_state

    def _build_r_mat(self) -> np.array:
        raise NotImplementedError("_build_r_mat not implemented!")

    def _build_trans_mat(self) -> np.array:
        raise NotImplementedError("_build_trans_mat not implemented!")


class GeneralDeterministicGridWorldMDP(GeneralGridWorldMDP):

    def __init__(self, width: int, height: int, gamma: float = 1.):
        super().__init__(width, height, gamma)

    def _build_r_mat(self) -> np.array:

        r_mat = np.zeros((self._num_states, ActionConstants.NUM_ACTIONS, self._num_states))

        # initialize all rewards to -1
        r_mat[:, :, :] = -1.

        # except the final state, which is 0
        r_mat[self._final_state, :, :] = 0.

        return r_mat

    def _build_trans_mat(self) -> np.array:

        trans_mat = np.zeros((self._num_states, ActionConstants.NUM_ACTIONS, self._num_states))

        # final state
        trans_mat[self._final_state, :, self._final_state] = 1

        # all the actions are deterministic, so all the transition probabilities are 1

        for s in range(1, self._num_states):

            # left actions
            if s == 1:  # to the left of the final state, we go to the final state
                trans_mat[s, ActionConstants.LEFT_ACTION, self._final_state] = 1
            elif s % self._width == 0:  # in the left column, we go back to the same state
                trans_mat[s, ActionConstants.LEFT_ACTION, s] = 1
            else:
                trans_mat[s, ActionConstants.LEFT_ACTION, s - 1] = 1

            # up actions
            if s == self._width:  # below the final state, we go to the final state
                trans_mat[s, ActionConstants.UP_ACTION, self._final_state] = 1
            elif s < self._width:  # in the top row, we go back to the same state
                trans_mat[s, ActionConstants.UP_ACTION, s] = 1
            else:
                trans_mat[s, ActionConstants.UP_ACTION, s - self._width] = 1

            # right actions
            if (s + 1) == self._num_states:  # to the right of the final state, we go to the final state
                trans_mat[s, ActionConstants.RIGHT_ACTION, self._final_state] = 1
            elif (s + 1) % self._width == 0:  # in the right column, we go back to the same state
                trans_mat[s, ActionConstants.RIGHT_ACTION, s] = 1
            else:
                trans_mat[s, ActionConstants.RIGHT_ACTION, s + 1] = 1

            # down actions
            if (s + self._width) == self._num_states:  # above the final state, we go to the final state
                trans_mat[s, ActionConstants.DOWN_ACTION, self._final_state] = 1
            elif (self._num_states - s) < self._width:  # in the bottom row, we go back to the same state
                trans_mat[s, ActionConstants.DOWN_ACTION, s] = 1
            else:
                trans_mat[s, ActionConstants.DOWN_ACTION, s + self._width] = 1

        return trans_mat


class GeneralDeterministicGridWorldMDPWithModel(GeneralDeterministicGridWorldMDP, EnvWithModel):

    def __init__(self, width: int, height: int, gamma: float = 1.):
        super().__init__(width, height, gamma)

    @property
    def td(self) -> np.array:
        return self._td

    @property
    def r(self) -> np.array:
        return self._r


class CliffWalkingMDP(Env):

    def __init__(self, width: int, height: int, cliff_states: [int],
                 start_state: int, goal_state: int, gamma: float = 1.):

        num_states = width * height

        assert num_states > 0, "width * height must be greater than 0!"

        env_spec = EnvSpec(num_states, ActionConstants.NUM_ACTIONS, gamma)

        super().__init__(env_spec)

        self._width = width
        self._num_states = num_states
        self._start_state = start_state
        self._goal_state = goal_state
        self._cliff_states = cliff_states
        self._state = start_state
        self._terminal_states = [goal_state] + cliff_states
        self._td = self._build_trans_mat()
        self._r = self._build_r_mat()

    def reset(self):
        self._state = self._start_state
        return self._state

    def step(self, action):
        assert action in list(range(self.spec.num_actions)), "Invalid Action"
        assert self._state != self._goal_state, "Episode has ended!"

        prev_state = self._state
        try:
            self._state = np.random.choice(self.spec.num_states, p=self._td[self._state, action])
        except:
            print(self._td[self._state, action])

        r = self._r[prev_state, action, self._state]

        return self._state, r, self.is_terminal(self._state)

    def is_terminal(self, state):
        return state == self._goal_state

    def _build_r_mat(self) -> np.array:

        r_mat = np.zeros((self._num_states, ActionConstants.NUM_ACTIONS, self._num_states))

        # initialize all rewards to -1
        r_mat[:, :, :] = -1.

        # initialize cliff state rewards to -100
        r_mat[self._cliff_states, :, :] = -100

        # except the goal state, which is 0
        r_mat[self._goal_state, :, :] = 0.

        return r_mat

    def _build_trans_mat(self) -> np.array:

        trans_mat = np.zeros((self._num_states, ActionConstants.NUM_ACTIONS, self._num_states))

        # final state
        trans_mat[self._goal_state, :, self._goal_state] = 1
        trans_mat[self._cliff_states, :, self._start_state] = 1

        for s in range(0, self._num_states):

            if s in self._terminal_states:
                break

            # left actions
            if s % self._width == 0:  # in the left column, we go back to the same state
                trans_mat[s, ActionConstants.LEFT_ACTION, s] = 1
            else:
                trans_mat[s, ActionConstants.LEFT_ACTION, s - 1] = 1

            # up actions
            if s < self._width:  # in the top row, we go back to the same state
                trans_mat[s, ActionConstants.UP_ACTION, s] = 1
            else:
                trans_mat[s, ActionConstants.UP_ACTION, s - self._width] = 1

            # right actions
            if s == self._start_state:
                trans_mat[s, ActionConstants.RIGHT_ACTION, self._start_state] = 1
            elif (s + 1) % self._width == 0:  # in the right column, we go back to the same state
                trans_mat[s, ActionConstants.RIGHT_ACTION, s] = 1
            else:
                trans_mat[s, ActionConstants.RIGHT_ACTION, s + 1] = 1

            # down actions
            if s in self._cliff_states:
                trans_mat[s, ActionConstants.RIGHT_ACTION, self._start_state] = 1
            elif (self._num_states - s) <= self._width:  # in the bottom row, we go back to the same state
                trans_mat[s, ActionConstants.DOWN_ACTION, s] = 1
            else:
                trans_mat[s, ActionConstants.DOWN_ACTION, s + self._width] = 1

        return trans_mat


class OneStateRandomMDP(Env):

    def __init__(self, gamma: float = 1.):

        num_states = 2
        num_actions = 2

        env_spec = EnvSpec(num_states, num_actions, gamma)

        super().__init__(env_spec)
        self._num_states = num_states
        self._num_actions = num_actions
        self._state = None
        self._final_state = 1
        self._td = self._build_trans_mat()
        self._r = self._build_r_mat()

    def reset(self):
        self._state = 0
        return self._state

    def step(self, action):

        assert action in list(range(self.spec.num_actions)), "Invalid action"
        assert self._state != self._final_state, "Episode has ended!"

        prev_state = self._state
        self._state = np.random.choice(self.spec.num_states, p=self._td[self._state, action])
        r = self._r[prev_state, action, self._state]

        return self._state, r, self._state == self._final_state

    def _build_r_mat(self) -> np.array:
        r_mat = np.zeros((self._num_states, self._num_actions, self._num_states))
        r_mat[0, 0, 1] = 1.

        return r_mat

    def _build_trans_mat(self) -> np.array:

        trans_mat = np.zeros((self._num_states, self._num_actions, self._num_states))

        trans_mat[0, 0, 0] = 0.9
        trans_mat[0, 0, 1] = 0.1
        trans_mat[0, 1, 0] = 0.
        trans_mat[0, 1, 1] = 1.0
        trans_mat[1, :, 1] = 1.

        return trans_mat
