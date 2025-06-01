# catalog_service/app/search/elastic.py

from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_bulk
from elasticsearch import ConnectionError


ELASTICSEARCH_URL = "http://elasticsearch_engine:9200"
INDEX_NAME = "products_catalog"



es = AsyncElasticsearch(
    hosts=["http://elasticsearch_engine:9200"],
    headers={
        "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8"
    },
    verify_certs=False,
    ssl_show_warn=False
)


async def create_index():
    try:
        print(f"Проверка доступности Elasticsearch по адресу: {ELASTICSEARCH_URL}")
        exists = await es.indices.exists(index=INDEX_NAME)
        print(f"Индекс {INDEX_NAME} существует: {exists}")
    except ConnectionError as e:
        print(f"[ERROR] Elasticsearch недоступен: {e}")
        return
    except Exception as e:
        print(f"[ERROR] Непредвиденная ошибка при проверке индекса: {e}")
        return

    if not exists:
        print(f"Создание индекса {INDEX_NAME}")

        index_config = {
            "settings": {
                "analysis": {
                    "filter": {
                        "autocomplete_filter": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 20
                        },
                        "russian_stop": {
                            "type": "stop",
                            "stopwords": "_russian_"
                        },
                        "russian_stemmer": {
                            "type": "stemmer",
                            "language": "russian"
                        }
                        # "synonym_filter": {
                        #     "type": "synonym",
                        #     "synonyms_path": "synonyms.txt",
                        # }
                    },
                    "analyzer": {
                        "autocomplete": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "russian_stop",
                                "russian_stemmer",
                                #"synonym_filter",
                                "autocomplete_filter"
                            ]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "autocomplete",
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "autocomplete",
                        "search_analyzer": "standard"
                    },
                    "price": {"type": "float"},
                    "quantity": {"type": "integer"},
                    "available": {"type": "boolean"},
                    "category_id": {"type": "integer"},
                    "brand_id": {"type": "integer"}
                }
            }
        }

        await es.indices.create(
            index=INDEX_NAME,
            body=index_config
        )



async def index_product(product: dict):
    """Добавляет или обновляет продукт в Elasticsearch"""
    print(f"Индексируем продукт в Elastic: {product}")
    await es.index(index=INDEX_NAME, id=product["id"], document=product)


async def delete_product_from_index(product_id: int):
    """Удаляет продукт из Elasticsearch"""
    try:
        await es.delete(index=INDEX_NAME, id=product_id)
    except NotFoundError:
        pass


async def search_products(query: str):
    """Поиск продуктов по имени и описанию"""
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["name", "description"],
                "fuzziness": "AUTO"
            }
        }
    }

    response = await es.search(index="products_catalog", body=search_body)

    print(f"Ищем в Elastic запрос: '{query}'")
    print("Ответ: ", response)
    hits = response["hits"]["hits"]
    return [hit["_source"] for hit in hits]
