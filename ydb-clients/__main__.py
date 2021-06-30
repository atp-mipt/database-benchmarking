# -*- coding: utf-8 -*-
import argparse
import basic_example
import client_node
import master_node
import logging


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\033[92mYandex.Database examples binary.\x1b[0m\n""")
    parser.add_argument("-d", "--database", required=True, help="Name of the database to use")
    parser.add_argument("-e", "--endpoint", required=True, help="Endpoint url to use")
    parser.add_argument("-p", "--path", default='')
    parser.add_argument("-pt", "--transactions_path", required=True)
    parser.add_argument("-id", "--client-id", required=True, help="ids starts from 0")
    parser.add_argument("-n", '--clients-num', required=True)
    parser.add_argument("-m", '--mode', required=True, help="if m == 1 then client, else master")
    parser.add_argument("-v", '--verbose', default=False, action='store_true')

    args = parser.parse_args()

    if args.verbose:
        logger = logging.getLogger('kikimr.public.sdk.python.client.pool.Discovery')
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler())

    # Run master or client
    if args.mode == "0":
        master_node.run(args.endpoint,
                        args.database,
                        args.path,
                        args.client_id,
                        args.clients_num,
                        args.transactions_path)

    elif args.mode == "1":
        client_node.run(
            args.endpoint,
            args.database,
            args.path,
            args.client_id,
            args.clients_num,
            args.transactions_path
        )
