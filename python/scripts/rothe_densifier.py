#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Implementation of Rothe's DENSIFIER."""

import argparse
from itertools import cycle, islice, permutations

import numpy as np
import tensorflow as tf

from cc_emergency.utils import openall, setup_stream_logger
from cc_emergency.utils.vector_io import read_vectors


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Implementation of Rothe\'s DENSIFIER.')
    parser.add_argument('vector_file', help='the word vector file.')
    parser.add_argument('gold', help='the gold standard file.')
    parser.add_argument('--iterations', '-i', type=int, default=500,
                        help='the number of iterations [500].')
    parser.add_argument('--batch-size', '-b', type=int, default=100,
                        help='the batch size [100].')
    parser.add_argument('--seed', '-s', type=int, default=64,
                        help='the random seed.')
    parser.add_argument('--lr-initial', type=float, default=5,
                        help='the initial learning rate [5].')
    parser.add_argument('--lr-decay', type=float, default=0.99,
                        help='learning rate decay [0.99].')
    parser.add_argument('--log-level', '-L', type=str, default='info',
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        help='the logging level.')
    args = parser.parse_args()
    return args


def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))


def main():
    args = parse_arguments()
    logger = setup_stream_logger(args.log_level, 'cc_emergency')

    words, vectors = read_vectors(args.vector_file)
    swords, vectors = set(words), np.asarray(vectors)
    with openall(args.gold) as inf:
        gold = {words.index(word): int(value) for word, value in
                (line.strip().split('\t') for line in inf)
                if word in swords}
        logger.info('Gold data size: {} words ({} positive, {} negative)'.format(
            len(gold), sum(gold.values()), len(gold) - sum(gold.values())))
    input_it = cycle(list(permutations(gold.keys(), 2)))

    with tf.Graph().as_default() as graph:
        tf.set_random_seed(args.seed)
        initializer = tf.random_uniform_initializer(-0.05, 0.05)

        # Inputs
        v_in = tf.placeholder(tf.int32, [args.batch_size], 'v')
        w_in = tf.placeholder(tf.int32, [args.batch_size], 'w')
        rel_in = tf.placeholder(tf.float32, [args.batch_size], 'rel')
        embedding_var = tf.get_variable(
            'embedding', vectors.shape, tf.float32, trainable=False)
        assign_em_op = embedding_var.assign(vectors)

        # The transformation
        Q_var = tf.get_variable('Q', [vectors.shape[1]] * 2, tf.float32,
                                initializer)
        new_Q_in = tf.placeholder(tf.float32, [vectors.shape[1]] * 2, 'new_Q')
        assign_q_op = tf.assign(Q_var, new_Q_in)

        e_v_var = tf.nn.embedding_lookup(embedding_var, v_in)
        e_w_var = tf.nn.embedding_lookup(embedding_var, w_in)
        u_v_var = tf.transpose(tf.matmul(Q_var, e_v_var, transpose_b=True), name='u_v')
        u_w_var = tf.transpose(tf.matmul(Q_var, e_w_var, transpose_b=True), name='u_w')
        u_vs_var = tf.slice(u_v_var, [0, 0], [-1, 1], name='u_vs')
        u_ws_var = tf.slice(u_w_var, [0, 0], [-1, 1], name='u_ws')
        objective_var = tf.reduce_sum((tf.norm(u_vs_var - u_ws_var, axis=1)) * rel_in, name='obj')

        # Optimization
        lr_var = tf.get_variable('learning_rate', shape=[], dtype=tf.float32,
                                 initializer=tf.constant_initializer(args.lr_initial),
                                 trainable=False)
        new_lr_in = tf.placeholder(tf.float32, shape=[], name='new_learning_rate')
        assign_lr_op = tf.assign(lr_var, new_lr_in)
        optimizer_op = tf.train.GradientDescentOptimizer(lr_var).minimize(objective_var)

    with tf.Session(graph=graph) as session:
        session.run(assign_em_op)
        session.run(tf.global_variables_initializer())

        logger.info('Starting training...')
        fetches = [objective_var, optimizer_op, Q_var, lr_var]
        lr = args.lr_initial
        for it in range(args.iterations):
            vs, ws, rels = zip(*[(v, w, 1 if gold[v] == gold[w] else 0) for v, w
                                 in take(args.batch_size, input_it)])
            feed_dict = {v_in: vs, w_in: ws, rel_in: rels}
            cost, _, Q, curr_lr = session.run(fetches, feed_dict)
            logger.debug('Cost at step {}: {:.2f} (lr: {:.2f})'.format(it, cost, curr_lr))
            U, _, V = np.linalg.svd(Q, full_matrices=False)
            new_Q = U.dot(V)
            logger.debug('SVD norm error: {:.2f} of {:.2f}'.format(
                np.linalg.norm(Q - new_Q), np.linalg.norm(Q)))
            lr *= 0.99
            session.run(assign_lr_op, feed_dict={new_lr_in: lr})
            session.run(assign_q_op, feed_dict={new_Q_in: new_Q})

        logger.info('Training done.')

        for word, emergency in zip(words, new_Q.dot(vectors.T).T[:, 0]):
            print('{}\t{}'.format(word, emergency))


if __name__ == '__main__':
    main()
