from langcache import LangCache
import json
import boto3

# Configuration
REGION = "eu-west-1"
secretsmanager = boto3.client("secretsmanager", region_name=REGION)

# Secrets
def get_secrets(secret_name):
    return json.loads(
        secretsmanager.get_secret_value(SecretId=secret_name)["SecretString"]
    )

secret = get_secrets("dev/python/api")


LANGCACHE_ENABLED = True

LANGCACHE_API_KEY = secret["LANGCACHE_API_KEY"]
LANGCACHE_SERVER_URL = secret["LANGCACHE_SERVER_URL"]
LANGCACHE_CACHE_ID = secret["LANGCACHE_CACHE_ID"]

def get_langcache_client():
    if not LANGCACHE_ENABLED:
        return None

    return LangCache(
        server_url=LANGCACHE_SERVER_URL,
        cache_id=LANGCACHE_CACHE_ID,
        api_key=LANGCACHE_API_KEY
    )

def langcache_lookup(prompt: str):
    if not LANGCACHE_ENABLED:
        print("🚫 LANGCACHE DISABLED")
        return None

    with get_langcache_client() as lc:
        print("🔍 LANGCACHE SEARCH")

        search_response = lc.search(prompt=prompt)
        print(search_response)
        # Defensive checks
        if not search_response:
            print("❄️ LANGCACHE MISS (no response object)")
            return None

        entries = getattr(search_response, "data", None)

        if not entries:
            print("❄️ LANGCACHE MISS (no entries)")
            return None

        # Pick best match (LangCache already sorts by similarity)
        best_entry = entries[0]

        print(
            f"⚡ LANGCACHE HIT → "
            f"similarity={best_entry.similarity}, "
            f"id={best_entry.id}"
        )

        return best_entry.response

def langcache_store(prompt: str, response: str):
    if not LANGCACHE_ENABLED:
        return

    with get_langcache_client() as lc:
        lc.set(prompt=prompt, response=response)
        print("🧊 STORED RESPONSE IN LANGCACHE")