from syncloud_app import logger
from subprocess import check_output


def execute(sql, psql_bin, db_user, db_socket, db_port, database):

    log = logger.get_logger('diaspora_postgres')
    log.info("executing: {0}".format(sql))
    log.info(check_output('{0} -U {1} -h {2} -p {3} -d {4} -c "{5}"'.format(
        psql_bin, db_user, db_socket, db_port, database, sql),
        shell=True))
