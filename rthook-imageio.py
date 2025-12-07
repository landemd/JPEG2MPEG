# Runtime hook to fix imageio metadata issue
import sys

# Try to fix the imageio metadata issue by patching importlib.metadata
try:
    import importlib.metadata
    
    # Store original functions
    _original_distribution = importlib.metadata.distribution
    _original_version = importlib.metadata.version
    
    # Create patched functions
    def _patched_distribution(name):
        try:
            return _original_distribution(name)
        except importlib.metadata.PackageNotFoundError:
            if name.lower() in ['imageio', 'moviepy', 'numpy', 'pillow', 'pil']:
                # Create a dummy distribution
                class DummyDistribution:
                    def __init__(self):
                        self.version = "1.0.0"
                        self.metadata = {}
                        
                    def read_text(self, filename):
                        return None
                        
                return DummyDistribution()
            # Re-raise for other packages
            raise
    
    def _patched_version(name):
        try:
            return _original_version(name)
        except importlib.metadata.PackageNotFoundError:
            if name.lower() in ['imageio', 'moviepy', 'numpy', 'pillow', 'pil']:
                return "1.0.0"
            # Re-raise for other packages
            raise
    
    # Apply patches only if not already applied
    if not hasattr(importlib.metadata, '_pyinstaller_patches_applied'):
        importlib.metadata.distribution = _patched_distribution
        importlib.metadata.version = _patched_version
        importlib.metadata._pyinstaller_patches_applied = True
        
except ImportError:
    pass

# Ensure that the packages can be imported without metadata issues
try:
    # Pre-import the problematic packages to initialize them properly
    import imageio
    import moviepy
except ImportError:
    pass