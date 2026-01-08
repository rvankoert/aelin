"""
Test suite for find-ngrams.py

Run with: pytest tests/test_find_ngrams.py -v
"""

import pytest
import os
import json
import tempfile
import sys
import importlib.util

# Load the find-ngrams.py script dynamically
script_path = os.path.join(os.path.dirname(__file__), '..', 'text', 'find-ngrams.py')
spec = importlib.util.spec_from_file_location("find_ngrams", script_path)
find_ngrams_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(find_ngrams_module)

# Import the function
find_ngrams = find_ngrams_module.find_ngrams

# Add the text directory to Python path
text_dir = os.path.join(os.path.dirname(__file__), '..', 'text')
sys.path.insert(0, os.path.abspath(text_dir))

class TestFindNgramsMain:
    """Integration tests for the main find_ngrams function"""
    
    def test_basic_ngram_extraction(self):
        """Test basic n-gram extraction from multiple files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files with overlapping content
            with open(os.path.join(tmpdir, "doc1.txt"), 'w') as f:
                f.write("the quick brown fox jumps over the lazy dog")
            with open(os.path.join(tmpdir, "doc2.txt"), 'w') as f:
                f.write("the quick brown fox runs very fast")
            with open(os.path.join(tmpdir, "doc3.txt"), 'w') as f:
                f.write("the lazy dog sleeps under the tree")
            
            ngrams, ngram_files = find_ngrams(
                directory=tmpdir,
                prefix=None,
                excluded_files=set(),
                n=3,
                top_k=10,
                limit=100,
                num_threads=1
            )
            
            # Should find n-grams
            assert len(ngrams) > 0
            
            # 'quick brown fox' should be common (appears in 2 files)
            assert any(('quick', 'brown', 'fox') == ngram for ngram, _ in ngrams)
            
            # Check that ngram_files contains file mappings
            assert len(ngram_files) > 0
    
    def test_prefix_filtering(self):
        """Test that only files with specified prefix are processed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with different prefixes
            with open(os.path.join(tmpdir, "data_file1.txt"), 'w') as f:
                f.write("important data appears here frequently")
            with open(os.path.join(tmpdir, "test_file2.txt"), 'w') as f:
                f.write("test content should be ignored")
            with open(os.path.join(tmpdir, "data_file3.txt"), 'w') as f:
                f.write("more important data appears here")
            
            ngrams, ngram_files = find_ngrams(
                directory=tmpdir,
                prefix="data_",
                excluded_files=set(),
                n=2,
                top_k=10,
                limit=100,
                num_threads=1
            )
            
            # Should only process data_* files
            all_files = set()
            for ngram, files in ngram_files.items():
                all_files.update(files)
            
            # Check that only data_* files appear
            for file in all_files:
                assert "data_" in file
                assert "test_" not in file
    
    def test_excluded_files(self):
        """Test that excluded files are not processed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "include.txt"), 'w') as f:
                f.write("include this file with special content")
            with open(os.path.join(tmpdir, "exclude.txt"), 'w') as f:
                f.write("exclude this file even though it has content")
            with open(os.path.join(tmpdir, "also_include.txt"), 'w') as f:
                f.write("also include this file with content")
            
            ngrams, ngram_files = find_ngrams(
                directory=tmpdir,
                prefix=None,
                excluded_files={'exclude'},  # Exclude by filename without extension
                n=2,
                top_k=10,
                limit=100,
                num_threads=1
            )
            
            # Check that exclude.txt does not appear in any results
            all_files = set()
            for ngram, files in ngram_files.items():
                all_files.update(files)
            
            assert not any("exclude.txt" in f for f in all_files)
            assert any("include.txt" in f for f in all_files)
    
    def test_exclude_words_case_sensitive(self):
        """Test case-sensitive word exclusion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "bad.txt"), 'w') as f:
                f.write("this file contains the forbidden word here")
            with open(os.path.join(tmpdir, "good.txt"), 'w') as f:
                f.write("this file is clean and acceptable")
            
            ngrams, ngram_files = find_ngrams(
                directory=tmpdir,
                prefix=None,
                excluded_files=set(),
                n=2,
                top_k=10,
                limit=100,
                num_threads=1,
                exclude_words=['forbidden']
            )
            
            # bad.txt should not appear in results
            all_files = set()
            for ngram, files in ngram_files.items():
                all_files.update(files)
            
            assert not any("bad.txt" in f for f in all_files)
            assert any("good.txt" in f for f in all_files)
    
    def test_required_words_case_sensitive(self):
        """Test case-sensitive required word filtering"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "relevant.txt"), 'w') as f:
                f.write("this document has the required keyword inside")
            with open(os.path.join(tmpdir, "irrelevant.txt"), 'w') as f:
                f.write("this document lacks the important term")
            
            ngrams, ngram_files = find_ngrams(
                directory=tmpdir,
                prefix=None,
                excluded_files=set(),
                n=2,
                top_k=10,
                limit=100,
                num_threads=1,
                required_words=['keyword']
            )
            
            # Only relevant.txt should appear
            all_files = set()
            for ngram, files in ngram_files.items():
                all_files.update(files)
            
            assert any("relevant.txt" in f for f in all_files)
            assert not any("irrelevant.txt" in f for f in all_files)
    
    def test_different_ngram_sizes(self):
        """Test extraction with different n-gram sizes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.txt"), 'w') as f:
                f.write("one two three four five six seven eight")
            
            # Test bigrams (n=2)
            ngrams2, _ = find_ngrams(
                directory=tmpdir, prefix=None, excluded_files=set(),
                n=2, top_k=5, limit=100, num_threads=1
            )
            assert len(ngrams2) > 0
            
            # Test 5-grams
            ngrams5, _ = find_ngrams(
                directory=tmpdir, prefix=None, excluded_files=set(),
                n=5, top_k=5, limit=100, num_threads=1
            )
            assert len(ngrams5) > 0
    
    def test_top_k_limit(self):
        """Test that top_k limits the number of results"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with many unique n-grams
            with open(os.path.join(tmpdir, "test.txt"), 'w') as f:
                f.write(" ".join([f"word{i}" for i in range(100)]))
            
            ngrams, _ = find_ngrams(
                directory=tmpdir, prefix=None, excluded_files=set(),
                n=2, top_k=5, limit=100, num_threads=1
            )
            
            # Should return at most top_k results
            assert len(ngrams) <= 5
    
    def test_handles_empty_directory(self):
        """Test graceful handling of directory with no text files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ngrams, ngram_files = find_ngrams(
                directory=tmpdir, prefix=None, excluded_files=set(),
                n=3, top_k=10, limit=100, num_threads=1
            )
            
            assert len(ngrams) == 0
            assert len(ngram_files) == 0
    
    def test_multithreading(self):
        """Test that multithreading works correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files
            for i in range(5):
                with open(os.path.join(tmpdir, f"file{i}.txt"), 'w') as f:
                    f.write(f"document {i} has some common words here")
            
            # Run with multiple threads
            ngrams, ngram_files = find_ngrams(
                directory=tmpdir, prefix=None, excluded_files=set(),
                n=2, top_k=10, limit=100, num_threads=4
            )
            
            # Should successfully process files
            assert len(ngrams) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
