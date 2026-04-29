from orderstricker.catalog.seed_data import PRODUCT_SPEC_ROWS, stable_product_id


def test_catalog_has_fifty_unique_products_and_stable_ids():
    assert len(PRODUCT_SPEC_ROWS) == 50
    names_lower = [r[0].strip().lower() for r in PRODUCT_SPEC_ROWS]
    assert len(set(names_lower)) == 50

    ids = {stable_product_id(r[0]) for r in PRODUCT_SPEC_ROWS}
    assert len(ids) == 50
