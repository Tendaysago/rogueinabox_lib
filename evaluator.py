# -*- coding: utf-8 -*-

import collections


class RogueEvaluator:
    """Implements the evaluation of an agent"""

    def __init__(self, max_step_count=500, episodes_for_evaluation=200):
        """
        :param int max_step_count:
            maximum number of steps per episode
        :param int episodes_for_evaluation:
            number of latest episode to consider when computing statistics
            (use 0, None or any "falsy" value to consider them all)
        """
        self.max_step_count = max_step_count
        self.episodes_for_evaluation = episodes_for_evaluation or None
        self.episodes = collections.deque(maxlen=self.episodes_for_evaluation)  # type: deque[Episode]
        self.current_episode = None  # type: Episode

    def reset(self):
        self.episodes.clear()
        self.current_episode = None  # type: Episode

    def on_run_begin(self):
        """Records the beginning of a run"""
        self.current_episode = Episode()

    def on_step(self, frame_history, action, reward, step):
        """Records a step taken by the agent during the run and returns whether the run should stop

        :param list[frame_info.RogueFrameInfo] frame_history:
            list of parsed frames until now
        :param str action:
            action performed
        :param float reward:
            reward obtained
        :param int step:
            rougueinabox step number
        :rtype: bool
        :return:
            True if the run should stop
        """
        self.current_episode.steps += 1
        self.current_episode.total_reward += reward
        return self.current_episode.steps >= self.max_step_count

    def on_run_end(self, frame_history, won, is_rogue_dead):
        """Records the end of a run

        :param list[frame_info.RogueFrameInfo] frame_history:
            list of parsed frames
        :param bool won:
            whether the game was won, according to a reward generator
        :param bool is_rogue_dead:
            whether the rogue died
        """
        # we use the penultimate frame if we can because the last one may be the tombstone or a new level
        frame = frame_history[-2] if len(frame_history) > 1 else frame_history[0]
        self.current_episode.final_tiles_count = frame.get_known_tiles_count()
        self.current_episode.won = won
        self._add_episode(self.current_episode)

    def _add_episode(self, episode):
        """Adds the given episode to the collection, keeping a maximum of self.episodes_for_evaluation.
        When the number of collected episodes exceeds this amounts, the oldest episodes are removed (FIFO policy)

        :param Episode episode:
            episode to add to the collection
        """
        self.episodes.append(episode)

    def statistics(self):
        """
        :return:
            dict of statistics:
            {
             "win_perc": float,        # % of victories, as determined by the reward generator
             "reward_avg": float,      # cumulative reward average
             "tiles_avg": float,       # average number of tiles seen
             "all_steps_avg": float,   # average number of steps taken in all episodes
             "win_steps_avg": float    # average number of steps taken in won episodes
            }
        """
        result = {}
        result["win_perc"] = 0
        result["reward_avg"] = 0
        result["tiles_avg"] = 0
        result["all_steps_avg"] = 0
        result["win_steps_avg"] = 0

        evaluated_episodes = self.episodes
        # accumulate stats for each episode
        for e in evaluated_episodes:
            result["reward_avg"] += e.total_reward
            result["tiles_avg"] += e.final_tiles_count
            result["all_steps_avg"] += e.steps
            if e.won:
                result["win_perc"] += 1
                result["win_steps_avg"] += e.steps

        # average stats across all episodes
        n_episodes = len(evaluated_episodes)
        if n_episodes > 0:
            result["win_steps_avg"] /= result["win_perc"]
            result["win_perc"] /= n_episodes
            result["all_steps_avg"] /= n_episodes
            result["reward_avg"] /= n_episodes
            result["tiles_avg"] /= n_episodes

        return result


class Episode:
    """Game episode representation"""
    def __init__(self):
        self.won = False
        self.steps = 0
        self.final_tiles_count = 0
        self.total_reward = 0
