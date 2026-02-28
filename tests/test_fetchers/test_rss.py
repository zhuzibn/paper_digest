# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

from unittest.mock import Mock, patch

from paper_digest.fetchers.rss import fetch_feed_entries


def _rss_fixture() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <item>
      <title>First Paper</title>
      <link>https://example.com/p1?utm_source=rss&id=1#section</link>
      <pubDate>Mon, 15 Jan 2024 12:34:56 GMT</pubDate>
      <author>Alice Example</author>
      <description>A summary for the first paper.</description>
      <category>Condensed Matter</category>
    </item>
    <item>
      <title></title>
      <link>https://example.com/missing-title</link>
      <pubDate>Tue, 16 Jan 2024 00:00:00 GMT</pubDate>
      <description>Missing title should be dropped.</description>
    </item>
    <item>
      <title>Missing Link</title>
      <pubDate>Wed, 17 Jan 2024 00:00:00 GMT</pubDate>
      <description>Missing link should be dropped.</description>
    </item>
    <item>
      <title>Second Paper</title>
      <link>https://example.com/p2?ref=abc&utm_medium=email</link>
      <pubDate>Thu, 18 Jan 2024 09:30:00 GMT</pubDate>
      <author>Bob Example</author>
      <description>Second summary.</description>
      <category>Physics</category>
    </item>
  </channel>
</rss>
"""


def _rdf_fixture() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns="http://purl.org/rss/1.0/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
>
  <channel rdf:about="https://example.com/rdf.xml">
    <title>Example RDF Feed</title>
    <link>https://example.com/</link>
    <description>Example RDF Channel</description>
    <items>
      <rdf:Seq>
        <rdf:li rdf:resource="https://example.com/rdf-paper" />
      </rdf:Seq>
    </items>
  </channel>
  <item rdf:about="https://example.com/rdf-paper">
    <title>RDF Paper</title>
    <link>https://example.com/rdf-paper?utm_campaign=feed</link>
    <dc:date>2024-02-20T11:12:13Z</dc:date>
    <dc:creator>Alice Author</dc:creator>
    <dc:creator>Bob Author</dc:creator>
    <content:encoded><![CDATA[<p>RDF content summary only.</p>]]></content:encoded>
  </item>
</rdf:RDF>
"""


@patch("paper_digest.fetchers.rss.requests.get")
def test_fetch_feed_entries_normalizes_and_drops_invalid_entries(
    mock_get: Mock,
) -> None:
    response = Mock()
    response.text = _rss_fixture()
    response.raise_for_status = Mock()
    mock_get.return_value = response

    entries = fetch_feed_entries(
        "https://example.com/feed.xml", user_agent="PaperDigestTest/1.0"
    )

    mock_get.assert_called_once_with(
        "https://example.com/feed.xml",
        headers={"User-Agent": "PaperDigestTest/1.0"},
        timeout=30,
    )
    assert len(entries) == 2
    assert entries[0]["title"] == "First Paper"
    assert entries[0]["link"] == "https://example.com/p1?id=1"
    assert entries[0]["published"] == "2024-01-15"
    assert entries[0]["authors"] == ["Alice Example"]
    assert entries[0]["summary"] == "A summary for the first paper."
    assert entries[0]["categories"] == ["Condensed Matter"]
    assert entries[0]["raw"] is not None


@patch("paper_digest.fetchers.rss.requests.get")
def test_fetch_feed_entries_respects_max_entries_cap(mock_get: Mock) -> None:
    response = Mock()
    response.text = _rss_fixture()
    response.raise_for_status = Mock()
    mock_get.return_value = response

    entries = fetch_feed_entries(
        "https://example.com/feed.xml", user_agent="PaperDigestTest/1.0", max_entries=1
    )

    assert len(entries) == 1
    assert entries[0]["title"] == "First Paper"


@patch("paper_digest.fetchers.rss.requests.get")
def test_fetch_feed_entries_supports_rdf_content_updated_and_many_authors(
    mock_get: Mock,
) -> None:
    response = Mock()
    response.text = _rdf_fixture()
    response.raise_for_status = Mock()
    mock_get.return_value = response

    parsed_feed = Mock()
    parsed_feed.entries = [
        {
            "title": "RDF Paper",
            "link": "https://example.com/rdf-paper?utm_campaign=feed",
            "updated": "2024-02-20T11:12:13Z",
            "authors": [{"name": "Alice Author"}, {"name": "Bob Author"}],
            "summary": "",
            "description": "",
            "content": [{"value": "<p>RDF content summary only.</p>"}],
        }
    ]

    with patch("paper_digest.fetchers.rss.feedparser.parse", return_value=parsed_feed):
        entries = fetch_feed_entries(
            "https://example.com/rdf.xml", user_agent="PaperDigestTest/1.0"
        )

    assert len(entries) == 1
    assert entries[0]["title"] == "RDF Paper"
    assert entries[0]["link"] == "https://example.com/rdf-paper"
    assert entries[0]["published"] == "2024-02-20"
    assert len(entries[0]["authors"]) > 1
    assert entries[0]["summary"] == "<p>RDF content summary only.</p>"
