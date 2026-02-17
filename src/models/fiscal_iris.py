from pymongo import ASCENDING, IndexModel

def get_fiscal_iris_indexes():
    return [
        IndexModel([("cnpj", ASCENDING), ("periodo", ASCENDING)], unique=True),
        IndexModel("deletedAt"),
    ]