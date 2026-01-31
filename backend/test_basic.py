"""Basic functionality test for Skill Management Center.

This script tests the basic functionality of the skill management system
without requiring a database connection.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Test that all modules can be imported."""
    try:
        print("Testing imports...")

        # Test core imports
        from app.core.config import settings
        print("✓ Config module imported successfully")

        from app.core.database import get_db_session
        print("✓ Database module imported successfully")

        # Test skill module imports
        from app.skill.manager import SkillManager
        print("✓ SkillManager imported successfully")

        from app.skill.event_manager import SkillEventManager
        print("✓ SkillEventManager imported successfully")

        from app.skill.editor import SkillEditor
        print("✓ SkillEditor imported successfully")

        from app.skill.version_manager import SkillVersionManager
        print("✓ SkillVersionManager imported successfully")

        from app.skill.importer import SkillImporter
        print("✓ SkillImporter imported successfully")

        from app.skill.analytics import SkillAnalytics
        print("✓ SkillAnalytics imported successfully")

        # Test model imports
        from app.skill.models.skill import Skill
        print("✓ Skill model imported successfully")

        from app.skill.models.skill_category import SkillCategory
        print("✓ SkillCategory model imported successfully")

        from app.skill.models.skill_tag import SkillTag
        print("✓ SkillTag model imported successfully")

        from app.skill.models.skill_version import SkillVersion
        print("✓ SkillVersion model imported successfully")

        # Test schema imports
        from app.skill.schemas.skill_operations import SkillCreate
        print("✓ SkillCreate schema imported successfully")

        from app.skill.schemas.skill_creation import SkillCreateRequest
        print("✓ SkillCreateRequest schema imported successfully")

        from app.skill.schemas.skill_import import ImportRequest
        print("✓ ImportRequest schema imported successfully")

        print("\n✅ All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_config():
    """Test configuration loading."""
    try:
        print("\nTesting configuration...")
        from app.core.config import settings

        print(f"✓ App Name: {settings.APP_NAME}")
        print(f"✓ Version: {settings.VERSION}")
        print(f"✓ Environment: {settings.ENVIRONMENT}")
        print(f"✓ Debug: {settings.DEBUG}")
        print(f"✓ Host: {settings.HOST}")
        print(f"✓ Port: {settings.PORT}")

        print("\n✅ Configuration loaded successfully!")
        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_skill_manager():
    """Test SkillManager instantiation."""
    try:
        print("\nTesting SkillManager...")
        from app.skill.manager import SkillManager
        from unittest.mock import Mock

        # Create a mock session
        mock_session = Mock()

        # Create SkillManager instance
        manager = SkillManager(mock_session)

        print("✓ SkillManager instantiated successfully")
        print(f"✓ Manager type: {type(manager)}")

        print("\n✅ SkillManager test passed!")
        return True

    except Exception as e:
        print(f"❌ SkillManager error: {e}")
        return False


def test_event_manager():
    """Test SkillEventManager instantiation."""
    try:
        print("\nTesting SkillEventManager...")
        from app.skill.event_manager import SkillEventManager

        # Create SkillEventManager instance
        event_manager = SkillEventManager()

        print("✓ SkillEventManager instantiated successfully")
        print(f"✓ Manager type: {type(event_manager)}")
        print(f"✓ Subscribers: {event_manager.subscribers}")
        print(f"✓ Event history: {event_manager.event_history}")

        print("\n✅ SkillEventManager test passed!")
        return True

    except Exception as e:
        print(f"❌ SkillEventManager error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Skill Management Center Basic Tests\n")

    tests = [
        test_imports,
        test_config,
        test_skill_manager,
        test_event_manager,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
