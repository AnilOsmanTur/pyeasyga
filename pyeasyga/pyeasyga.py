# -*- coding: utf-8 -*-
"""
    pyeasyga module

"""
import time
import random
import copy
import numpy as np
from operator import attrgetter

from six.moves import range


class GeneticAlgorithm(object):
    """Genetic Algorithm class.

    This is the main class that controls the functionality of the Genetic
    Algorithm.

    A simple example of usage:

    >>> # Select only two items from the list and maximise profit
    >>> from pyeasyga.pyeasyga import GeneticAlgorithm
    >>> input_data = [('pear', 50), ('apple', 35), ('banana', 40)]
    >>> easyga = GeneticAlgorithm(input_data)
    >>> def fitness (member, data):
    >>>     return sum([profit for (selected, (fruit, profit)) in
    >>>                 zip(member, data) if selected and
    >>>                 member.count(1) == 2])
    >>> easyga.fitness_function = fitness
    >>> easyga.run()
    >>> print easyga.best_individual()

    """

    def __init__(self,
                 seed_data,
                 population_size=50,
                 generations=100,
                 crossover_probability=0.8,
                 mutation_probability=0.2,
                 elitism=True,
                 maximise_fitness=True,
                 random_seed=None):
        """Instantiate the Genetic Algorithm.

        :param seed_data: input data to the Genetic Algorithm
        :type seed_data: list of objects
        :param int population_size: size of population
        :param int generations: number of generations to evolve
        :param float crossover_probability: probability of crossover operation
        :param float mutation_probability: probability of mutation operation

        """
        random.seed(random_seed)
        self.seed_data = seed_data
        self.population_size = population_size
        self.generations = generations
        self.crossover_probability = crossover_probability
        self.mutation_probability = mutation_probability
        self.elitism = elitism
        self.maximise_fitness = maximise_fitness

        self.current_generation = []
        self.fitness_stats = np.zeros(population_size)
    

        def create_individual(seed_data):
            """Create a candidate solution representation.

            e.g. for a bit array representation:

            >>> return [random.randint(0, 1) for _ in range(len(data))]

            :param seed_data: input data to the Genetic Algorithm
            :type seed_data: list of objects
            :returns: candidate solution representation as a list

            """
            return [random.randint(0, 1) for _ in range(len(seed_data))]

        def crossover(parent_1, parent_2):
            """Crossover (mate) two parents to produce two children.

            :param parent_1: candidate solution representation (list)
            :param parent_2: candidate solution representation (list)
            :returns: tuple containing two children

            """
            index = random.randrange(1, len(parent_1))
            child_1 = np.concatenate([parent_1[:index], parent_2[index:]], axis=0)
            child_2 = np.concatenate([parent_2[:index], parent_1[index:]], axis=0)
            return child_1, child_2

        def mutate(individual):
            """Reverse the bit of a random index in an individual."""
            mutate_index = random.randrange(len(individual))
            individual[mutate_index] = (0, 1)[individual[mutate_index] == 0]

        def random_selection(population):
            """Select and return a random member of the population."""
            return random.choice(population)

        def tournament_selection(population):
            """Select a random number of individuals from the population and
            return the fittest member of them all.
            """
            if self.tournament_size == 0:
                self.tournament_size = 2
            members = random.sample(population, self.tournament_size)
            members.sort(
                key=attrgetter('fitness'), reverse=self.maximise_fitness)
            return members[0]

        self.fitness_function = None
        self.tournament_selection = tournament_selection
        self.tournament_size = self.population_size // 10
        self.random_selection = random_selection
        self.create_individual = create_individual
        self.crossover_function = crossover
        self.mutate_function = mutate
        self.selection_function = self.tournament_selection

    def create_initial_population(self):
        """Create members of the first population randomly.
        """
        initial_population = []
        print('first population generation started...')
        for i in range(self.population_size):
            print('\r{}/{} [{:5.2f}%]'.format(i+1, self.population_size,(i+1)/self.population_size*100), end='')
            genes = np.array(self.create_individual(self.seed_data)).astype(np.int8)
            individual = Chromosome(genes)
            initial_population.append(individual)
        self.current_generation = initial_population
        print('finished.')
        
    def calculate_population_fitness(self):
        """Calculate the fitness of every member of the given population using
        the supplied fitness_function.
        """
        for individual in self.current_generation:
            individual.fitness = self.fitness_function(
                individual.genes, self.seed_data)

    def rank_population(self):
        """Sort the population by fitness according to the order defined by
        maximise_fitness.
        """
        self.current_generation.sort(
            key=attrgetter('fitness'), reverse=self.maximise_fitness)

    def create_new_population(self):
        """Create a new population using the genetic operators (selection,
        crossover, and mutation) supplied.
        """
        new_population = []
        elite = copy.deepcopy(self.current_generation[0])
        selection = self.selection_function

        while len(new_population) < self.population_size:
            parent_1 = copy.deepcopy(selection(self.current_generation))
            parent_2 = copy.deepcopy(selection(self.current_generation))

            child_1, child_2 = parent_1, parent_2
            child_1.fitness, child_2.fitness = 0, 0

            can_crossover = random.random() < self.crossover_probability
            can_mutate = random.random() < self.mutation_probability

            if can_crossover:
                child_1.genes, child_2.genes = self.crossover_function(
                    parent_1.genes, parent_2.genes)

            if can_mutate:
                self.mutate_function(child_1.genes)
                self.mutate_function(child_2.genes)

            new_population.append(child_1)
            if len(new_population) < self.population_size:
                new_population.append(child_2)

        if self.elitism:
            new_population[0] = elite

        self.current_generation = new_population

    def create_first_generation(self):
        """Create the first population, calculate the population's fitness and
        rank the population by fitness according to the order specified.
        """
        self.create_initial_population()
        self.calculate_population_fitness()
        self.rank_population()

    def create_next_generation(self):
        """Create subsequent populations, calculate the population fitness and
        rank the population by fitness in the order specified.
        """
        self.create_new_population()
        self.calculate_population_fitness()
        self.rank_population()

    def compute_fitness_stats(self):
        self.fitness_stats.fill(0)
        
        for i, gen in enumerate(self.current_generation):
            self.fitness_stats[i] = gen.fitness
            
        return self.fitness_stats.mean(), self.fitness_stats.std(), self.fitness_stats.min(), self.fitness_stats.max()

    def run(self):
        """Run (solve) the Genetic Algorithm."""
        print('Run started....')
        start = time.time()
        self.create_first_generation()
        gen_mean, gen_std, gen_min, gen_max  = self.compute_fitness_stats()
        first_run = time.time() - start
        print('1. run fitness stats: max: {} min: {} mean: {:.3f} std: {:.3f} {:.2f} s'.format(
                gen_max, gen_min, gen_mean, gen_std, first_run))
        for i in range(1, self.generations+1):
            run_start_time = time.time()
            self.create_next_generation()
            gen_mean, gen_std, gen_min, gen_max  = self.compute_fitness_stats()
            run_time = time.time() - run_start_time
            print('\rRun {}/{} [{:5.2f}%] fitness stats: max: {} min: {} mean: {:.3f} std: {:.3f} {:.2f} s'.format(i, self.generations,
                  i/self.generations*100, gen_max, gen_min, gen_mean, gen_std, run_time), end='')
        end = time.time() - start
        print('\nDone. total {:.2f} s'.format(end))
        
    def best_individual(self):
        """Return the individual with the best fitness in the current
        generation.
        """
        best = self.current_generation[0]
        return (best.fitness, best.genes)

    def last_generation(self):
        """Return members of the last generation as a generator function."""
        return ((member.fitness, member.genes) for member
                in self.current_generation)


class Chromosome(object):
    """ Chromosome class that encapsulates an individual's fitness and solution
    representation.
    """
    def __init__(self, genes):
        """Initialise the Chromosome."""
        self.genes = genes
        self.fitness = 0

    def __repr__(self):
        """Return initialised Chromosome representation in human readable form.
        """
        return repr((self.fitness, self.genes))
