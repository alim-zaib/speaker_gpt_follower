''' Evaluation of agent trajectories '''

import json
import os
import sys
from collections import defaultdict
import networkx as nx
import numpy as np
import pprint
pp = pprint.PrettyPrinter(indent=4)

from env import R2RBatch, ImageFeatures
import utils
from utils import load_datasets, load_nav_graphs
from agent import BaseAgent, StopAgent, RandomAgent, ShortestAgent

import argparse


class Evaluation(object):
    ''' Results submission format:  [{'instr_id': string, 'trajectory':[(viewpoint_id, heading_rads, elevation_rads),] } ] '''

    def __init__(self, splits):
        self.error_margin = 3.0
        self.splits = splits
        self.gt = {}
        self.instr_ids = []
        self.scans = []
        for item in load_datasets(splits):
            self.gt[item['path_id']] = item
            self.scans.append(item['scan'])
            self.instr_ids += ['%d_%d' % (item['path_id'],i) for i in range(3)]
        self.scans = set(self.scans)
        self.instr_ids = set(self.instr_ids)
        self.graphs = load_nav_graphs(self.scans)
        self.distances = {}
        for scan,G in self.graphs.items(): # compute all shortest paths
            self.distances[scan] = dict(nx.all_pairs_dijkstra_path_length(G))

    def _get_nearest(self, scan, goal_id, path):
        near_id = path[0][0]
        near_d = self.distances[scan][near_id][goal_id]
        for item in path:
            d = self.distances[scan][item[0]][goal_id]
            if d < near_d:
                near_id = item[0]
                near_d = d
        return near_id

    def _score_item(self, instr_id, path):
        ''' Calculate error based on the final position in trajectory, and also
            the closest position (oracle stopping rule). '''
        gt = self.gt[int(instr_id.split('_')[0])]
        start = gt['path'][0]
        assert start == path[0][0], 'Result trajectories should include the start position'
        goal = gt['path'][-1]
        final_position = path[-1][0]
        nearest_position = self._get_nearest(gt['scan'], goal, path)
        self.scores['nav_errors'].append(self.distances[gt['scan']][final_position][goal])
        self.scores['oracle_errors'].append(self.distances[gt['scan']][nearest_position][goal])
        self.scores['trajectory_steps'].append(len(path)-1)
        distance = 0 # Work out the length of the path in meters
        prev = path[0]
        for curr in path[1:]:
            distance += self.distances[gt['scan']][prev[0]][curr[0]]
            prev = curr
        self.scores['trajectory_lengths'].append(distance)


    def score_results(self, results):
        # results should be a dictionary mapping instr_ids to dictionaries, with each dictionary containing (at least) a 'trajectory' field
        self.scores = defaultdict(list)
        model_scores = []
        instr_ids = set(self.instr_ids)

        instr_count = 0
        for instr_id, result in results.items():
            if instr_id in instr_ids:
                instr_count += 1
                instr_ids.remove(instr_id)
                self._score_item(instr_id, result['trajectory'])
                if 'score' in result:
                    model_scores.append(result['score'])

        assert len(instr_ids) == 0, 'Missing %d of %d instruction ids from %s' \
                                    % (len(instr_ids), len(self.instr_ids), ",".join(self.splits))

        assert len(self.scores['nav_errors']) == len(self.instr_ids)
        score_summary = {
            'nav_error': np.average(self.scores['nav_errors']),
            'oracle_error': np.average(self.scores['oracle_errors']),
            'steps': np.average(self.scores['trajectory_steps']),
            'lengths': np.average(self.scores['trajectory_lengths'])
        }
        if len(model_scores) > 0:
            assert len(model_scores) == instr_count
            score_summary['model_score'] = np.average(model_scores)

        num_successes = len([i for i in self.scores['nav_errors'] if i < self.error_margin])
        score_summary['success_rate'] = float(num_successes)/float(len(self.scores['nav_errors']))
        oracle_successes = len([i for i in self.scores['oracle_errors'] if i < self.error_margin])
        score_summary['oracle_rate'] = float(oracle_successes)/float(len(self.scores['oracle_errors']))
        return score_summary, self.scores

    def score_file(self, output_file):
        ''' Evaluate each agent trajectory based on how close it got to the goal location '''
        with open(output_file) as f:
            return self.score_results(json.load(f))


RESULT_DIR = 'tasks/R2R/results/'

def eval_simple_agents(args):
    ''' Run simple baselines on each split. '''
    img_features = ImageFeatures.from_args(args)
    for split in ['train', 'val_seen', 'val_unseen', 'test']:
        env = R2RBatch(img_features, batch_size=1, splits=[split])
        ev = Evaluation([split])

        for agent_type in ['Stop', 'Shortest', 'Random']:
            outfile = '%s%s_%s_agent.json' % (RESULT_DIR, split, agent_type.lower())
            agent = BaseAgent.get_agent(agent_type)(env, outfile)
            agent.test()
            agent.write_results()
            score_summary, _ = ev.score_file(outfile)
            print('\n%s' % agent_type)
            pp.pprint(score_summary)


def eval_seq2seq():
    ''' Eval sequence to sequence models on val splits (iteration selected from training error) '''
    outfiles = [
        RESULT_DIR + 'seq2seq_teacher_imagenet_%s_iter_5000.json',
        RESULT_DIR + 'seq2seq_sample_imagenet_%s_iter_20000.json'
    ]
    for outfile in outfiles:
        for split in ['val_seen', 'val_unseen']:
            ev = Evaluation([split])
            score_summary, _ = ev.score_file(outfile % split)
            print('\n%s' % outfile)
            pp.pprint(score_summary)

if __name__ == '__main__':
    from train import make_arg_parser
    utils.run(make_arg_parser(), eval_simple_agents)
    #eval_seq2seq()






