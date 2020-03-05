import os
from copy import deepcopy
from random import choice, randint
from typing import (
    List,
    Callable,
    SupportsInt,
    Any
)

import numpy as np

from core.composer.gp_composer.gpnode import GPNode
from core.composer.optimisers.evo_operators import EvolutuionaryOperators
from core.composer.tree_drawing import TreeDrawing


class GPChainOptimiser:
    def __init__(self, initial_chain, requirements, primary_node_func: Callable, secondary_node_func: Callable):
        self.requirements = requirements
        self.__primary_node_func = primary_node_func
        self.__secondary_node_func = secondary_node_func

        if initial_chain and type(initial_chain) != list:
            self.population = [initial_chain] * requirements.pop_size
        else:
            self.population = initial_chain or self._make_population(self.requirements.pop_size)

    def optimise(self, metric_function_for_nodes):
        history = []
        self.fitness = [round(metric_function_for_nodes(tree_root), 3) for tree_root in self.population]
        for generation_num in range(self.requirements.num_of_generations):
            print(f'GP generation num: {generation_num}')
            self.best_individual = self.population[np.argmin(self.fitness)]
            # print all population
            if self.requirements.verbouse:
                for i, pop_ind in enumerate(self.population):
                    if not os.path.isdir(f'../../tmp/HistoryFiles/Trees/pop_individuals/pop{generation_num}'):
                        os.mkdir(f'../../tmp/HistoryFiles/Trees/pop_individuals/pop{generation_num}')
                    TreeDrawing().draw_branch(pop_ind,
                                              jpeg=f'pop_individuals/pop{generation_num}/{i}(fitness_{self.fitness[i]}).png')

                TreeDrawing().draw_branch(self.best_individual, jpeg=f'the_best_ind_(pop{generation_num}).png')

            selected_indexes = EvolutuionaryOperators.tournament_selection(fitnesses=self.fitness,
                                                    group_size=5)
            new_population = []
            for ind_num in range(self.requirements.pop_size - 1):

                if generation_num == 0:
                    history.append((self.population[ind_num], self.fitness[ind_num]))

                new_population.append(
                    EvolutuionaryOperators.standard_crossover(tree1=self.population[selected_indexes[ind_num][0]],
                                                              tree2=self.population[selected_indexes[ind_num][1]],
                                                              max_depth=self.requirements.max_depth, pair_num=ind_num,
                                                              pop_num=generation_num,
                                                              crossover_prob=self.requirements.crossover_prob,
                                                              verbouse=self.requirements.verbouse))

                new_population[ind_num] = EvolutuionaryOperators.standard_mutation(new_population[ind_num],
                                                                                   secondary_requirements=self.requirements.secondary,
                                                                                   primary_requirements=self.requirements.primary,
                                                                                   pair_num=ind_num,
                                                                                   pop_num=generation_num,
                                                                                   verbouse=self.requirements.verbouse)

            self.population = deepcopy(new_population)
            self.population.append(self.best_individual)
            self.fitness = [round(metric_function_for_nodes(tree_root), 3) for tree_root in self.population]
            history.append((self.population[ind_num], self.fitness[ind_num]))

        return self.population[np.argmin(self.fitness)], history

    def _make_population(self, pop_size: SupportsInt) -> List[GPNode]:
        return [self._random_tree() for _ in range(pop_size)]

    def _random_tree(self) -> GPNode:
        root = self.__secondary_node_func(choice(self.requirements.secondary))
        new_tree = root
        self._tree_growth(node_parent=root)
        return new_tree

    def _tree_growth(self, node_parent: Any):
        offspring_size = randint(2, self.requirements.max_arity)
        offspring_nodes = []
        for offspring_node in range(offspring_size):
            if node_parent.get_depth_up() >= self.requirements.max_depth - 1 or (
                    node_parent.get_depth_up() < self.requirements.max_depth - 1
                    and randint(0, 1)):

                new_node = self.__primary_node_func(choice(self.requirements.primary),
                                                    nodes_to=node_parent, input_data=None)
                offspring_nodes.append(new_node)
            else:
                new_node = self.__secondary_node_func(choice(self.requirements.secondary),
                                                      nodes_to=node_parent)
                self._tree_growth(new_node)
                offspring_nodes.append(new_node)
        node_parent.nodes_from = offspring_nodes
