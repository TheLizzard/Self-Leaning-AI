# -*- coding: utf-8 -*-
import numpy as np
import random
import copy
import sys

from board.alphabeta import alphabeta_values
from .datasets import TrainDataset, TestDataset


test_dataset = TestDataset()


class Trainer:
    def __init__(self, environment, AI):
        self.training_data = TrainDataset(number_vars=3)
        self.environment = environment
        self.AI = AI
        self.reset()

    def full_test(self):
        global test_dataset
        error = 0
        for case, correct_value in test_dataset:
            error += self.test_value_case(case, correct_value)
        return error

    def test(self, sample_size=1000):
        global test_dataset
        error = 0
        samples = random.sample(test_dataset.data, sample_size)
        for sample in samples:
            case, correct_value = sample
            error += self.test_value_case(case, correct_value)
        return error

    def test_value_case(self, environment, correct_value):
        value = self.ask_ai_value(environment)
        value = self.normalise_value(environment, value)

        #print(environment, environment.player, correct_value, value, sep="\t")
        #input(">>> ")

        return (correct_value-value)**2

    def reset(self):
        self.current_environment = self.environment()

    def train(self):
        last_done = False
        #for move in (7, 8, 9, 5, 4, 1, 6, 3, 2):
        #    self.current_environment.act(move)
        while (not self.current_environment.over) or (not last_done):
            amplified_v, amplified_p = self.amplify(self.AI, self.current_environment)
            policy = self.add_missing([p+0.1 for p in amplified_p], self.current_environment)

            neg_environment = self.normalise_environment(self.current_environment, reverse=True)
            environment = self.normalise_environment(self.current_environment)
            amplified_p = self.add_missing(amplified_p, self.current_environment)

            #print(self.current_environment, self.current_environment.player, amplified_v, amplified_p, sep="\t")
            #input(">>> ")

            self.training_data.add(environment, amplified_p, amplified_v)
            self.training_data.add(neg_environment, amplified_p, -amplified_v)

            if not self.current_environment.over:
                action = self.current_environment.random_action_from_policy(policy)
                self.current_environment.act(action)
            else:
                last_done = True
        self.reset()

    def flush(self):
        self.AI.train(self.training_data)

    def normalise_environment(self, environment, reverse=False):
        if reverse:
            if environment.player:
                xs, os, ns = environment.state_as_list
                return [os, xs, ns]
            else:
                return environment.state_as_list

        if environment.player:
            return environment.state_as_list
        else:
            xs, os, ns = environment.state_as_list
            return [os, xs, ns]

    def normalise_value(self, environment, value):
        if environment.player:
            return value
        else:
            return -value

    def amplify(self, ai, environment):
        amplified_vs = alphabeta_values(environment, eval=self.ask_ai_value, depth=10)
        amplified_vs = [self.normalise_value(environment, value) for value in amplified_vs]
        amplified_p = [(i+1)/2 for i in amplified_vs] # Note: `(i+1)/2` converts the score to 0<score<1
        amplified_v = max(amplified_vs)
        return amplified_v, amplified_p

    def add_missing(self, policy, environment):
        """
        Sometimes the policy wouldn't be 9 items long
        but to have a numpy array of policies we need
        all of them to have the same size.
        """
        # Must be in order that they are considered in the alphabeta
        all_actions = (7, 8, 9, 4, 5, 6, 1, 2, 3)
        extended_policy = []
        legal_actions = tuple(environment.legal_actions)
        idx = 0
        for action in all_actions:
            if action in legal_actions:
                extended_policy.append(policy[idx])
                idx += 1
            else:
                extended_policy.append(0)
        return extended_policy

    def ask_ai(self, environment):
        question = np.asarray(self.normalise_environment(environment))
        policy, value = self.AI.predict_single(question)
        return self.normalise_value(environment, value[0]), policy

    def ask_ai_value(self, environment):
        return self.ask_ai(environment)[0]