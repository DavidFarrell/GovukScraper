import pytest
from pathlib import Path
import json
from datetime import datetime, timedelta
from src.checkpoint import CheckpointManager

@pytest.fixture
def checkpoint_dir(tmp_path):
    """Provide temporary directory for checkpoints."""
    return tmp_path / "checkpoints"

@pytest.fixture
def manager(checkpoint_dir):
    """Provide configured CheckpointManager instance."""
    return CheckpointManager(str(checkpoint_dir))

@pytest.fixture
def sample_state():
    """Provide sample crawler state."""
    return {
        "scan_metadata": {
            "total_pages": 150,
            "sections_covered": 2
        },
        "visited_urls": ["/test1", "/test2"],
        "sections": {
            "test_section": {
                "pages": []
            }
        }
    }

def test_checkpoint_creation(manager, checkpoint_dir):
    """Test checkpoint directory creation."""
    assert checkpoint_dir.exists()
    assert checkpoint_dir.is_dir()

def test_save_checkpoint(manager, sample_state):
    """Test saving checkpoint file."""
    filename = manager.save_checkpoint(sample_state)
    assert filename.startswith("checkpoint_")
    assert filename.endswith(".json")
    
    filepath = manager.checkpoint_dir / filename
    assert filepath.exists()
    
    with open(filepath) as f:
        saved_data = json.load(f)
        assert saved_data["state"] == sample_state
        assert "timestamp" in saved_data
        assert saved_data["metadata"]["pages_processed"] == 150

def test_load_checkpoint(manager, sample_state):
    """Test loading checkpoint file."""
    filename = manager.save_checkpoint(sample_state)
    loaded_state = manager.load_checkpoint(filename)
    assert loaded_state == sample_state

def test_load_nonexistent_checkpoint(manager):
    """Test loading non-existent checkpoint."""
    result = manager.load_checkpoint("nonexistent.json")
    assert result is None

def test_clean_old_checkpoints(manager, sample_state):
    """Test cleaning old checkpoints."""
    # Create old checkpoint with correct timestamp format
    old_time = datetime.now() - timedelta(hours=25)
    old_timestamp = old_time.strftime("%Y%m%d_%H%M%S")
    old_file = f"checkpoint_{old_timestamp}.json"
    
    with open(manager.checkpoint_dir / old_file, 'w') as f:
        json.dump({"timestamp": old_timestamp, "state": sample_state}, f)
    
    # Create new checkpoint (which will use current time)
    filename = manager.save_checkpoint(sample_state)
    
    # Clean old checkpoints
    manager.clean_old_checkpoints(max_age_hours=24)
    
    # Check results
    old_path = manager.checkpoint_dir / old_file
    new_path = manager.checkpoint_dir / filename
    
    # Add debug output
    if old_path.exists():
        with open(old_path) as f:
            content = json.load(f)
            print(f"Old file content: {content}")
            
    assert not old_path.exists(), f"Old checkpoint {old_file} should have been deleted"
    assert new_path.exists(), f"New checkpoint {filename} should still exist"

def test_should_checkpoint(manager):
    """Test checkpoint interval logic."""
    assert not manager.should_checkpoint(50)  # 50 < 100
    assert not manager.should_checkpoint(49)  # 99 < 100
    assert manager.should_checkpoint(1)       # 100 == 100
    
    # Check reset after threshold
    assert manager.pages_since_checkpoint == 0 