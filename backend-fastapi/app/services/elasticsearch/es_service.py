"""Service for Elasticsearch ingredient indexing and fuzzy search."""

import logging
from typing import Optional
from elasticsearch import AsyncElasticsearch

from app.core.config import settings

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """Service for indexing and searching ingredients in Elasticsearch."""

    INDEX_NAME = "ingredients"

    # Index mapping with fuzzy search configuration
    INDEX_MAPPING = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "fdc_id": {
                    "type": "keyword"
                },
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "data_type": {
                    "type": "keyword"
                },
                "search_terms": {
                    "type": "text"
                },
                "nutrients": {
                    "type": "object",
                    "enabled": False
                }
            }
        }
    }

    def __init__(self):
        self.es_url = settings.ELASTICSEARCH_URL
        self._client: Optional[AsyncElasticsearch] = None
        logger.debug(f"ElasticsearchService initialized with URL: {self.es_url}")

    async def connect(self):
        """Initialize Elasticsearch connection."""
        if not self._client:
            self._client = AsyncElasticsearch([self.es_url])
            logger.debug("Connected to Elasticsearch")

    async def disconnect(self):
        """Close Elasticsearch connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.debug("Disconnected from Elasticsearch")

    async def initialize(self):
        """Create index with fuzzy search mapping if it doesn't exist."""
        await self.connect()

        try:
            exists = await self._client.indices.exists(index=self.INDEX_NAME)
            if not exists:
                await self._client.indices.create(
                    index=self.INDEX_NAME,
                    **self.INDEX_MAPPING
                )
                logger.info(f"Created Elasticsearch index: {self.INDEX_NAME}")
            else:
                logger.info(f"Elasticsearch index already exists: {self.INDEX_NAME}")
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch: {e}")
            raise

    async def search_ingredients(
        self,
        query: str,
        data_types: list[str],
        limit: int = 20
    ) -> list[dict]:
        """
        Fuzzy search for ingredients with dataType filter.

        Args:
            query: Search query string
            data_types: List of data types to filter by (e.g., ["Foundation", "SR Legacy"])
            limit: Maximum number of results to return

        Returns:
            List of ingredient dictionaries with fdc_id, name, data_type
        """
        if not self._client:
            await self.connect()

        try:
            search_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^2", "search_terms"],
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": [
                        {"terms": {"data_type": data_types}}
                    ]
                }
            }

            response = await self._client.search(
                index=self.INDEX_NAME,
                query=search_query,
                size=limit,
                _source=["fdc_id", "name", "data_type"]
            )

            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                results.append({
                    "fdc_id": source["fdc_id"],
                    "name": source["name"],
                    "data_type": source["data_type"]
                })

            return results

        except Exception as e:
            print(f"✗ Error searching Elasticsearch: {e}")
            return []

    async def index_ingredient(self, usda_data: dict):
        """
        Index a single ingredient in Elasticsearch.

        Args:
            usda_data: Raw USDA API response dictionary
        """
        if not self._client:
            await self.connect()

        try:
            fdc_id = usda_data.get("fdcId")
            name = usda_data.get("description", "Unknown")
            data_type = usda_data.get("dataType", "Branded")

            # Extract search terms from name (split by common delimiters)
            search_terms = name.lower().split(",")
            search_terms = [term.strip() for term in search_terms if term.strip()]

            document = {
                "fdc_id": fdc_id,
                "name": name,
                "data_type": data_type,
                "search_terms": search_terms,
                "nutrients": usda_data.get("foodNutrients", [])
            }

            await self._client.index(
                index=self.INDEX_NAME,
                id=str(fdc_id),
                document=document
            )

            print(f"✓ Indexed ingredient {fdc_id} in Elasticsearch")

        except Exception as e:
            print(f"✗ Error indexing ingredient {usda_data.get('fdcId')}: {e}")
            raise

    async def delete_index(self):
        """Delete the entire ingredients index (useful for testing)."""
        if not self._client:
            await self.connect()

        try:
            exists = await self._client.indices.exists(index=self.INDEX_NAME)
            if exists:
                await self._client.indices.delete(index=self.INDEX_NAME)
                print(f"✓ Deleted Elasticsearch index: {self.INDEX_NAME}")
        except Exception as e:
            print(f"✗ Error deleting index: {e}")
            raise


elasticsearch_service = ElasticsearchService()
