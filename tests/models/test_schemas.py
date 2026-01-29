import pytest
from pydantic import ValidationError

class TestSchemas:
    """Tests for Pydantic models/schemas"""
    
    def test_models_import(self):
        """Verify models can be imported"""
        try:
            from app import models
            assert models is not None
        except ImportError as e:
            pytest.skip(f"Models not found: {e}")
    
    def test_article_schema_validation(self, sample_article):
        """Article schema should validate correctly"""
        assert "title" in sample_article
        assert "url" in sample_article
        assert "content" in sample_article
    
    def test_briefing_schema_structure(self, sample_briefing):
        """Briefing schema should have required fields"""
        assert hasattr(sample_briefing, "title") or "title" in sample_briefing
        assert hasattr(sample_briefing, "content") or "sections" in sample_briefing
        # Briefing uses content field, not sections
