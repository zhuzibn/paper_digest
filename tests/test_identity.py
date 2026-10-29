"""Only explicit identifiers and harmless URL variations imply equivalence."""

import pytest

from paper_digest.identity import identity_keys
from paper_digest.identity import paper_id


@pytest.mark.parametrize("left,right", [
    ("https://doi.org/10.1103/PhysRevLett.1", "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.1"),
    ("https://doi.org/10.1038/s41467-024-12345-1", "https://www.nature.com/articles/s41467-024-12345-1.pdf"),
    ("http://arxiv.org/abs/2401.00001v1", "https://export.arxiv.org/pdf/2401.00001v3.pdf"),
    ("https://arxiv.org/abs/cond-mat/9901001v1", "https://arxiv.org/pdf/cond-mat/9901001v2"),
    ("https://EXAMPLE.com/a?b=2&utm_source=rss&a=1#section", "https://example.com/a?a=1&b=2"),
])
def test_equivalent_identifiers_have_same_primary_key(left, right):
    assert identity_keys(left)[0] == identity_keys(right)[0]
    assert paper_id(left) == paper_id(right)


def test_explicit_doi_bridges_publisher_links():
    assert identity_keys("https://example.com/a", "DOI:10.1234/ABC")[0] == "doi:10.1234/abc"


def test_distinct_query_identifiers_and_unrelated_hosts_are_preserved():
    assert paper_id("https://example.com/?id=1") != paper_id("https://example.com/?id=2")
    assert identity_keys("https://example.com/abs/2401.00001")[0].startswith("url:")
