from .storage import JSONStorage
from .models.schemas import Product, HandModel, Prompt, CacheEntry

products_storage = JSONStorage("products.json", Product)
hand_models_storage = JSONStorage("hand_models.json", HandModel)
prompts_storage = JSONStorage("prompts.json", Prompt)
results_cache = JSONStorage("results_cache.json", CacheEntry)
