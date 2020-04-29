from syncloudlib import logger
from subprocess import check_output


class Database:

    def __init__(self):
        self.log = logger.get_logger('database')

    def execute(self, database, user, sql):
        self.log.info("executing: {0}".format(sql))
        cmd = 'snap run diaspora.psql -U {0} -d {1} -c "{2}"'.format(user, database, sql)
        self.log.info(check_output(cmd, shell=True))
