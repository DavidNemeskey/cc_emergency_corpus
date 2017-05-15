#!/usr/bin/env python3
"""Manages a Stanford CoreNLP server."""

from __future__ import absolute_import, division, print_function
try:
    from configparser import RawConfigParser
except:
    from ConfigParser import RawConfigParser
import logging
# from future.moves.urllib.parse import urlencode
import os
from subprocess import Popen
import time

import requests


class CoreNLPError(Exception):
    pass


class CoreNLP(object):
    """Stanford CoreNLP interface object."""
    def __init__(self, corenlp_props):
        """
        corenlp_props is a dictionary that contains the properties for
        the CoreNLP server under the [URL] section. There must also be three keys
        under the [server] section:
          - directory, that specifies the CoreNLP installation path;
          - port, which is the port the CoreNLP server is on localhost;
          - memory, for the java process (the default is 4g).
        """
        self.logger = logging.getLogger(
            self.__class__.__module__ + '.' + self.__class__.__name__)
        self.directory = corenlp_props['server']['directory']
        self.memory = corenlp_props['server'].get('memory', '4g')
        self.port = corenlp_props['server'].get('port', 9000)
        self.url = 'http://localhost:{}'.format(self.port)
        self.props = str(corenlp_props['URL'])
        self.server = None
        self.shutdown_key = None
        self.parsed = 0
        self.__start_server()

    def __del__(self):
        # See also http://stackoverflow.com/questions/865115/how-do-i-correctly-clean-up-a-python-object
        # for ideas on how to replace __del__ with something better (?)
        self.__stop_server()

    def __start_server(self):
        self.logger.debug("Starting server {}...".format(self.url))
        # TODO eat the server's output -- in this case, there is no need to wait
        self.server = Popen(
            ['java', '-mx{}'.format(self.memory),
             '-cp', '*', 'edu.stanford.nlp.pipeline.StanfordCoreNLPServer',
             '--port', self.port, '--server_id', self.port, '--quiet'],
            cwd=self.directory
        )
        self.parsed = 0
        time.sleep(5)
        with open('/tmp/corenlp.shutdown.{}'.format(self.port)) as inf:
            self.shutdown_key = inf.read()
        self.logger.info("Started server {}".format(self.url))

    def __stop_server(self):
        self.logger.debug("Stopping server? {}...".format(self.url))
        if self.server:
            self.logger.debug("Stopping server {}...".format(self.url))
            try:
                requests.post('{}/shutdown?key={}'.format(
                    self.url, self.shutdown_key))
            except:
                raise
            self.server.communicate()
            self.logger.info("Stopped server {}".format(self.url))
        self.server = None

    def __restart_server(self):
        self.logger.debug("Restarting server {}...".format(self.url))
        self.__stop_server()
        self.__start_server()

    def parse(self, text, anas=False):
        """Parses a text with a running CoreNLP server."""
        if not self.server:
            self.__start_server()
        with open('/dev/shm/text-{}'.format(os.getpid()), 'wt') as outf:
            print(text.encode('utf-8'), file=outf)

        try:
            reply = self.__send_request(text)
            if reply:
                return self.__split_result(reply.decode('utf-8'))
        except CoreNLPError as cnlpe:
            self.__stop_server()
            raise
        except:
            self.__stop_server()
            raise

    def __send_request(self, text):
        for tries in range(3):
            try:
                r = requests.post(self.url, params={'properties': self.props},
                                  data=text.encode('utf-8'))
                if r.status_code != 200:
                    self.logger.error(
                        u'Server {} returned an illegal status code {}'.format(
                            self.url, r.status_code))
                    r = None
            except Exception as e:
                self.logger.exception(
                    u'Exception {} while trying to access server {}'.format(
                        e, self.url))
                r = None
            if not r:
                self.__restart_server()
            if r:
                return r.content
        else:
            raise CoreNLPError(u'Number of tries exceeded with url {}'.format(self.url))

    @staticmethod
    def __split_result(text):
        """
        Splits the result string into lists of lists. Also deletes the
        per-sentence token index (the very first column) from the
        conll-format reply returned by the server.
        """
        return [
            [token.split('\t')[1:] for token in sentence.split('\n')]
            for sentence in text.split('\n\n') if sentence != ''
        ]
