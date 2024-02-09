import logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

processes = {}

db_path = 'gns3.db'

