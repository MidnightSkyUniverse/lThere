"""
Author: Ali Binkowska
Date: August 2023

Description: manage database; create & drop calls
"""
import yaml

from utils import (
    create_database_from_schema,
    drop_tables,
    update_database
)

with open('../config.yaml') as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

_steps= [
    'create',
    # 'drop'
]

def manage():

    db_name = cfg['db']['file']
    schema = cfg['db']['schema']

    if 'create' in _steps:
        create_database_from_schema(db_name=db_name, schema_file=schema)

    if 'update' in _steps:
        update_database(db_name=db_name)

    if 'drop' in _steps:
        drop_tables(db_name=db_name)


if __name__ == "__main__":
    manage()