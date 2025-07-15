import os
import fnmatch
from pathlib import Path

class S3IgnoreHandler:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.ignore_file = self.base_path / '.s3ignore'
        self.patterns = []
        self._load_ignore_patterns()

    def _load_ignore_patterns(self):
        """Load patterns from .s3ignore file if it exists"""
        if self.ignore_file.exists():
            with open(self.ignore_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        self.patterns.append(line)

    def should_ignore(self, path):
        """Check if a file should be ignored"""
        if not self.patterns:
            return False

        # Convert path to relative path from base
        rel_path = str(Path(path).relative_to(self.base_path))
        # Convert Windows paths to forward slashes for consistent matching
        rel_path = rel_path.replace('\\', '/')

        for pattern in self.patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith('/'):
                if self._is_dir_match(rel_path, pattern):
                    return True
            # Handle file patterns
            elif fnmatch.fnmatch(rel_path, pattern):
                return True
            # Handle patterns without slashes (match in any directory)
            elif '/' not in pattern and fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True

        return False

    def _is_dir_match(self, path, pattern):
        """Check if a path matches a directory pattern"""
        pattern = pattern.rstrip('/')
        path_parts = path.split('/')
        pattern_parts = pattern.split('/')
        
        # Check each part of the path against the pattern
        for i in range(len(path_parts)):
            if fnmatch.fnmatch('/'.join(path_parts[:i+1]), pattern):
                return True
        return False
