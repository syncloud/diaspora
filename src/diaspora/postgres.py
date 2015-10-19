from syncloud_app import logger
from subprocess import check_output
from diaspora.config import Config


def execute(sql, database=None):

    log = logger.get_logger('diaspora.postgres.execute')
    config = Config()

    if not database:
        database = config.db_name()

    log.info("executing: {0}".format(sql))
    log.info(check_output('{0} -U {1} -h {2} -d {3} -c "{4}"'.format(
        config.psql(), config.db_user(), config.db_socket(), database, sql),
        shell=True))
