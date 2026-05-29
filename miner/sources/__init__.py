from .meta_ads import MetaAdsSource
from .mercado_livre import MercadoLivreSource
from .shopee import ShopeeSource
from .amazon import AmazonSource
from .google import GoogleSource

REGISTRY = {
    "meta_ads": MetaAdsSource,
    "mercado_livre": MercadoLivreSource,
    "shopee": ShopeeSource,
    "amazon": AmazonSource,
    "google": GoogleSource,
}
