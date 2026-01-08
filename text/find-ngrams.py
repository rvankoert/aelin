"""
find-ngrams.py

Find the most common n-grams in text files within a specified directory.

Usage: 
    python find-ngrams.py --directory <path_to_directory>
    python find-ngrams.py --help  # for all paramters

Output: JSON files saved in the "clusters" directory, each containing file paths for the corresponding n-gram.

Dependencies: nltk, tqdm, unidecode
"""

import os
import argparse
import nltk
import csv
import json
from collections import Counter
from nltk.util import ngrams
from nltk.tokenize import word_tokenize
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from unidecode import unidecode
import glob

nltk.download('punkt')
nltk.download('punkt_tab')


def load_excluded_files(json_path):
    """Load filenames without extensions from a JSON file."""
    excluded_files = set()
    if not json_path or not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        return excluded_files

    with open(json_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        for item in data:
            filepath = item.get('filepath', '')  # Assuming JSON has objects with 'filepath' key
            if filepath:
                filename = os.path.splitext(os.path.basename(filepath))[0]
                excluded_files.add(filename)
    print(f"Loaded {len(excluded_files)} excluded filenames from {json_path}")
    return excluded_files


def process_ngrams(most_common_ngrams, ngram_files, top_k):
    """Process n-grams to remove files linked to higher-ranked n-grams."""
    seen_files = set()  # Track files linked to higher-ranked n-grams
    processed_ngrams = []

    # Iterate through n-grams in reverse order
    for ngram, count in most_common_ngrams:
        files = ngram_files[ngram]
        # Remove files already seen
        unique_files = [file for file in files if file not in seen_files]
        # Update the seen files set
        seen_files.update(unique_files)
        # Adjust the count
        adjusted_count = count - (len(files) - len(unique_files))
        # Store the processed n-gram
        if adjusted_count > 0:
            processed_ngrams.append((ngram, adjusted_count, unique_files))

    # reorder processed_ngrams by adjusted_count in descending order
    processed_ngrams.sort(key=lambda x: x[1], reverse=True)
    # Limit the number of processed n-grams to top_k
    processed_ngrams = processed_ngrams[:top_k]



    # Keep only the top_k n-grams
    if len(processed_ngrams) > top_k:
        processed_ngrams = processed_ngrams[:top_k]

    return processed_ngrams


def clean_text(text):
    """Clean the text by removing punctuation and normalizing diacritics."""
    text = ((text.replace('-', '').replace(',', '').replace('.', '').replace('!', '').replace('?', '').replace(';','')
            .replace(':', '').replace('/', '').replace('\\', '')).replace(',', '').replace('„', '').replace('\'', '')
            .replace('(', '').replace(')', '').replace('=',''))

    text = unidecode(text)  # Normalize all diacritics
    return text.strip()

def process_file_for_ngrams(file_path, tokens_to_ignore, n):
    """Process a single file to extract n-grams."""
    ngram_counter = Counter()
    ngram_files = {}
    # print(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        text = clean_text(text)  # Clean the text
        tokens = [token for token in word_tokenize(text) if token not in tokens_to_ignore]
        # print(tokens)
        n_grams = ngrams(tokens, n)
        for ngram in n_grams:
            ngram_counter[ngram] += 1
            if ngram not in ngram_files:
                ngram_files[ngram] = set()
            ngram_files[ngram].add(file_path)

    return ngram_counter, ngram_files


def find_ngrams(directory, prefix, excluded_files, n=5, top_k=1000, limit=500000, limit_ngrams=100000, num_threads=20,
                exclude_words=None, required_words=None, tokens_to_ignore=1, exclude_words_insensitive=None,
                required_words_insensitive=None):
    """Find the most common n-grams in text files within a directory."""
    if exclude_words is None:
        exclude_words = set()
    if required_words is None:
        required_words = set()
    for word in exclude_words:
        print(f"Excluding word: {word}")
    for word in required_words:
        print(f"Required word: {word}")


    ngram_counter = Counter()
    ngram_files = {}
    token_counter = Counter()
    pbar = tqdm(total=0, desc="Total files processed")

    # First pass: Count all tokens
    files_to_include = []
    for subdir, _, files in os.walk(directory):
        for file in files:
            filename_without_ext = os.path.splitext(file)[0]
            if file.endswith('.txt') and (prefix is None or file.startswith(prefix)) and filename_without_ext not in excluded_files:
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    text = clean_text(text)  # Clean the text
                    stop_processing = False
                    # Check for exclude words case-insensitive
                    for exclude_word_insensitive in exclude_words_insensitive:
                        if clean_text(exclude_word_insensitive).lower() in text.lower():
                            stop_processing = True
                            break
                    # Check for required words case-insensitive
                    for req_word_insensitive in required_words_insensitive:
                        if clean_text(req_word_insensitive).lower() not in text.lower():
                            stop_processing = True
                            break
                    # Check for exclude words case-sensitive
                    for exclude_word in exclude_words:
                        if clean_text(exclude_word) in text:
                            stop_processing = True
                            break  # Skip this file
                    # Check for required words case-sensitive
                    for req_word in required_words:
                        if clean_text(req_word) not in text:
                            stop_processing = True
                            break  # Skip this file if required words are not present
                    if stop_processing:
                        continue

                    text = text.replace('-', '').replace(',', '').replace('.', '')
                    # Normalize all diacritics
                    text = unidecode(text)
                    tokens = word_tokenize(text)
                    token_counter.update(tokens)
                    files_to_include.append(file_path)
                    pbar.update(1)
                if pbar.n >= limit:
                    pbar.close()
                    break
        if pbar.n >= limit:
            pbar.close()
            break
    # Identify the top n most common tokens
    tokens_to_ignore = {token for token, _ in token_counter.most_common(tokens_to_ignore)}
    print(f"Top {len(tokens_to_ignore)} tokens to ignore: {', '.join(list(tokens_to_ignore)[:10])}...")
    # Remove tokens that occur less than 10 times
    print(f"Total tokens counted: {len(token_counter)}")
    # tokens_to_ignore = {token for token, count in token_counter.items() if count <= 10 and token not in tokens_to_ignore}
    tokens_to_ignore = {token for token, count in token_counter.items() if count <= 10 or token in tokens_to_ignore}
    print(f"Tokens to ignore: {len(tokens_to_ignore)}")

    files_seen = 0
    # Second pass: Generate n-grams excluding top 10 tokens
    pbar = tqdm(total=0, desc="Processing files for n-grams")
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for file in files_to_include:
            filename_without_ext = os.path.splitext(file)[0]
            # print(file, prefix, file.startswith(prefix), filename_without_ext not in excluded_files)
            if file.endswith('.txt') and (prefix is None or file.split('/')[-1].startswith(prefix)) and filename_without_ext not in excluded_files:
                # print(file)
                files_seen += 1
                file_path = os.path.join(subdir, file)
                # with open(file_path, 'r', encoding='utf-8') as f:
                #     text = f.read()
                #     text = clean_text(text)  # Clean the text
                # print(f"Processing file: {file_path}")
                futures.append(executor.submit(process_file_for_ngrams, file_path, tokens_to_ignore, n))
                pbar.update(1)
            if pbar.n >= limit:
                break
        print(f"Total files seen: {files_seen}")

        for future in as_completed(futures):
            file_ngram_counter, file_ngram_files = future.result()
            ngram_counter.update(file_ngram_counter)
            for ngram, files in file_ngram_files.items():
                if ngram not in ngram_files:
                    ngram_files[ngram] = set()
                ngram_files[ngram].update(files)

            # Trim ngram_counter to top `limit_ngrams` n-grams
            if len(ngram_counter) > limit_ngrams:
                ngram_counter = Counter(dict(ngram_counter.most_common(limit_ngrams // 2)))

    pbar.close()

    print("Get the most common n-grams")
    most_common_ngrams = ngram_counter.most_common(top_k)
    return most_common_ngrams, ngram_files


def load_predictions_map(predictions_dir):
    """Load predictions from JSON files."""
    predictions_map = {}
    for json_file in glob.glob(os.path.expanduser(os.path.join(predictions_dir, "*.json"))):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                print(f"Loading predictions from {json_file}")
                data = json.load(f)
                for result in data.get("results", []):
                    identifier = result.get("identifier").replace('thumbnails/data/','').replace('.jp2.thumbnail.jpg','.txt').replace('NL-HaNA_2.09.09','page/NL-HaNA_2.09.09')
                    combined = result.get("predictions", {}).get("combined", {})
                    if identifier and isinstance(combined, dict) and combined:
                        top_prediction = max(combined.values())
                        predictions_map[identifier] = top_prediction
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    return predictions_map


def save_ngrams_to_json(common_ngrams, output_dir="clusters", required_words=None, exclude_words=None, n=5, prefix_output=None, limit_output=None, predictions_dir=None, exclude_words_insensitive=None, required_words_insensitive=None):
    """Save the most common n-grams to JSON files."""
    predictions_map = None
    if predictions_dir is not None:
        predictions_map = load_predictions_map(predictions_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for order, (ngram, adjusted_count, unique_files) in enumerate(common_ngrams, start=1):
        ngram_str = '-'.join(ngram)
        ngram_str = unidecode(ngram_str)
        if exclude_words:
            ngram_str = 'exclude-' + '-'.join(exclude_words) + '-' + ngram_str
        if required_words:
            ngram_str = 'required-'+ '-'.join(required_words) + '-' + ngram_str
        if exclude_words_insensitive:
            ngram_str = 'exclude-insensitive-' + '-'.join(exclude_words_insensitive) + '-' + ngram_str
        if required_words_insensitive:
            ngram_str = 'required-insensitive-' + '-'.join(required_words_insensitive) + '-' + ngram_str
        if prefix_output:
            output_path = os.path.join(output_dir, f"{prefix_output}-{str(order).zfill(3)}-{str(n).zfill(2)}-{ngram_str}.json")
        else:
            output_path = os.path.join(output_dir, f"{str(order).zfill(3)}-{str(n).zfill(2)}-{ngram_str}.json")

        if predictions_map is not None:
            print("Sorting files by prediction value")
            # Sort unique_files by prediction value (ascending)
            def get_prediction(file_path):
                return predictions_map.get(file_path, float('inf'))
            sorted_files = sorted(unique_files, key=get_prediction)
        else:
            sorted_files = unique_files
        if limit_output:
            sorted_files = sorted_files[:limit_output]
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(sorted_files, json_file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find the most common n-grams in text files.')
    parser.add_argument('--directory', type=str, required=True, help='Root directory to search for files')
    parser.add_argument('--exclude', type=str, help='Path to the JSON file containing excluded filenames', default=None)
    parser.add_argument('--n', type=int, default=5, help='Size of the n-grams (default: 5)')
    parser.add_argument('--top_k', type=int, default=1000, help='Number of top n-grams to return (default: 1000)')
    parser.add_argument('--limit', type=int, default=100000000, help='Limit the number of files to process (default: 100000000)')
    parser.add_argument('--limit_output', type=int, default=10000, help='Limit the number of files to include in the output (default: 10000)')
    parser.add_argument('--exclude_words', type=str, nargs='*', help='Skip files containing these words, case sensitive', default=[])
    parser.add_argument('--exclude_words_insensitive', type=str, nargs='*', help='Skip files containing these words, case insensitive', default=[])
    parser.add_argument('--required_words', type=str, nargs='*', help='Only process files containing these words, case sensitive', default=[])
    parser.add_argument('--required_words_insensitive', type=str, nargs='*', help='Only process files containing these words, case insensitive', default=[])
    parser.add_argument('--tokens_to_ignore', type=int, default=10, help='Number of top tokens to ignore (default: 10)')
    parser.add_argument('--prefix_output', type=str, default=None, help='Prefix the output files with this string')
    parser.add_argument('--predictions_dir', type=str, default=None, help='Directory containing predictions JSON files')
    parser.add_argument('--input_file_prefix', type=str, default=None, help='Only process files starting with this prefix')

    args = parser.parse_args()

    # Load excluded filenames from the JSON file
    excluded_files = load_excluded_files(args.exclude)

    # Find the most common n-grams
    common_ngrams, ngram_files = find_ngrams(
        args.directory,
        args.input_file_prefix,
        excluded_files,
        n=args.n,
        top_k=args.top_k * 100,
        limit=args.limit,
        exclude_words=args.exclude_words,
        required_words=args.required_words,
        tokens_to_ignore=args.tokens_to_ignore,
        exclude_words_insensitive=args.exclude_words_insensitive,
        required_words_insensitive=args.required_words_insensitive
    )
    print(f"Found {len(common_ngrams)} common n-grams before processing.")
    processed_ngrams = process_ngrams(common_ngrams, ngram_files, top_k=args.top_k)
    print(f"Found {len(processed_ngrams)} n-grams after processing.")

    print("Saving the results to JSON files")
    save_ngrams_to_json(processed_ngrams, required_words=args.required_words, exclude_words=args.exclude_words,
                        n=args.n, prefix_output=args.prefix_output, limit_output=args.limit_output,
                        predictions_dir=args.predictions_dir, exclude_words_insensitive=args.exclude_words_insensitive,
                        required_words_insensitive=args.required_words_insensitive)

    # Print the results
    for ngram, adjusted_count, unique_files in processed_ngrams:
        files = ', '.join(ngram_files[ngram])
        # print(f"{' '.join(ngram)}: {adjusted_count} (Files: {unique_files})")
        print(f"{' '.join(ngram)}: {adjusted_count}")
