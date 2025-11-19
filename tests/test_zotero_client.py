"""Tests for ZoteroClient URL construction with group library support."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ingest_zotero_api import ZoteroClient
from src.settings import Settings, load_settings


class TestZoteroClientURLConstruction:
    """Test that ZoteroClient constructs correct URLs for personal and group libraries."""
    
    def _create_test_config(self, temp_dir: Path, group_id: str = "") -> None:
        """Helper to create test configuration files."""
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        # Create zotero.yaml
        zotero_content = f"""mode: "api"
api:
  user_id: "${{ZOTERO_USER_ID}}"
  group_id: "${{ZOTERO_GROUP_ID:-}}"
  api_key_env: "ZOTERO_API_KEY"
  page_size: 100
  polite_delay_ms: 200
"""
        (config_dir / "zotero.yaml").write_text(zotero_content)
        
        # Create sources.yaml (minimal)
        sources_content = """window_days: 30
openalex:
  enabled: true
  mailto: "test@example.com"
crossref:
  enabled: true
  mailto: "test@example.com"
arxiv:
  enabled: true
  categories: ["cs.LG"]
biorxiv:
  enabled: true
  from_days_ago: 30
medrxiv:
  enabled: false
  from_days_ago: 30
altmetric:
  enabled: false
"""
        (config_dir / "sources.yaml").write_text(sources_content)
        
        # Create scoring.yaml (minimal)
        scoring_content = """weights:
  similarity: 0.45
  recency: 0.15
  citations: 0.15
  altmetric: 0.10
  journal_quality: 0.08
  author_bonus: 0.02
  venue_bonus: 0.05
thresholds:
  must_read: 0.75
  consider: 0.5
decay_days:
  fast: 30
  medium: 60
  slow: 180
whitelist_authors: []
whitelist_venues: []
"""
        (config_dir / "scoring.yaml").write_text(scoring_content)
    
    def test_personal_library_url_construction(self):
        """Test URL construction for personal library (no group_id)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            self._create_test_config(temp_path)
            
            # Set environment variables for personal library
            with patch.dict(os.environ, {
                "ZOTERO_USER_ID": "12345",
                "ZOTERO_API_KEY": "test_api_key",
                "ZOTERO_GROUP_ID": "",  # Empty group_id
            }):
                settings = load_settings(temp_path)
                client = ZoteroClient(settings)
                
                # Verify personal library URLs
                assert client.base_library_url == "https://api.zotero.org/users/12345"
                assert client.base_items_url == "https://api.zotero.org/users/12345/items"
    
    def test_group_library_url_construction(self):
        """Test URL construction for group library (with group_id)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            self._create_test_config(temp_path)
            
            # Set environment variables for group library
            with patch.dict(os.environ, {
                "ZOTERO_USER_ID": "12345",
                "ZOTERO_API_KEY": "test_api_key",
                "ZOTERO_GROUP_ID": "6311723",  # Set group_id
            }):
                settings = load_settings(temp_path)
                client = ZoteroClient(settings)
                
                # Verify group library URLs
                assert client.base_library_url == "https://api.zotero.org/groups/6311723"
                assert client.base_items_url == "https://api.zotero.org/groups/6311723/items"
    
    def test_group_library_precedence_over_personal(self):
        """Test that group_id takes precedence when both are set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            self._create_test_config(temp_path)
            
            # Set both user_id and group_id
            with patch.dict(os.environ, {
                "ZOTERO_USER_ID": "12345",
                "ZOTERO_API_KEY": "test_api_key",
                "ZOTERO_GROUP_ID": "9876543",
            }):
                settings = load_settings(temp_path)
                client = ZoteroClient(settings)
                
                # Verify group library is used, not personal
                assert client.base_library_url == "https://api.zotero.org/groups/9876543"
                assert client.base_items_url == "https://api.zotero.org/groups/9876543/items"
                assert "users" not in client.base_library_url


if __name__ == "__main__":
    # Run tests if pytest is available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed. Install with: pip install pytest")
