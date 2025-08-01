#!/usr/bin/env python3
"""
Memory-efficient script to balance sentiment distribution in NDJSON Reddit data using VADER sentiment analysis.

This script:
1. Reads NDJSON file containing Reddit posts (memory-efficient two-pass approach)
2. Analyzes sentiment using VADER for titles and selftext
3. Classifies posts as positive, negative, or neutral
4. Samples equal numbers from each sentiment category
5. Outputs simplified dataset with only "Comment" and "Sentiment" fields

Usage:
    python balance_sentiment_ndjson.py input.ndjson output.ndjson [--target-count 1000]
"""

import json
import argparse
import random
from pathlib import Path
from typing import Dict, List, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import defaultdict
import sys
import tempfile
import os

class SentimentBalancer:
    def __init__(self, random_seed: int = 42):
        """Initialize the sentiment balancer with VADER analyzer."""
        self.analyzer = SentimentIntensityAnalyzer()
        random.seed(random_seed)
        
        # Sentiment classification thresholds
        self.positive_threshold = 0.05
        self.negative_threshold = -0.05
        
    def get_sentiment_label(self, text: str) -> str:
        """
        Classify text sentiment using VADER.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Sentiment label: 'positive', 'negative', or 'neutral'
        """
        if not text or not text.strip():
            return 'neutral'
            
        scores = self.analyzer.polarity_scores(text)
        compound_score = scores['compound']
        
        if compound_score >= self.positive_threshold:
            return 'positive'
        elif compound_score <= self.negative_threshold:
            return 'negative'
        else:
            return 'neutral'
    
    def extract_text_content(self, post: Dict) -> str:
        """
        Extract text content from Reddit post for sentiment analysis.
        
        Args:
            post: Reddit post dictionary
            
        Returns:
            Combined text from title, selftext, and/or body
        """
        title = post.get('title', '')
        selftext = post.get('selftext', '')
        body = post.get('body', '')  # For comments
        
        # Combine available text fields
        text_parts = []
        
        if title and title.strip():
            text_parts.append(title.strip())
            
        if selftext and selftext.strip() and selftext not in ['[deleted]', '[removed]', '']:
            text_parts.append(selftext.strip())
            
        if body and body.strip() and body not in ['[deleted]', '[removed]', '']:
            text_parts.append(body.strip())
        
        combined_text = ' '.join(text_parts)
        return combined_text.strip()
    
    def process_ndjson_file_memory_efficient(self, input_file: str) -> Dict[str, int]:
        """
        First pass: Count posts by sentiment category without loading into memory.
        Creates temporary files for each sentiment category.
        
        Args:
            input_file: Path to input NDJSON file
            
        Returns:
            Dictionary with sentiment counts
        """
        sentiment_counts = defaultdict(int)
        
        # Create temporary files for each sentiment
        temp_files = {}
        temp_handles = {}
        
        try:
            for sentiment in ['positive', 'negative', 'neutral']:
                temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                                      suffix=f'_{sentiment}.ndjson',
                                                      encoding='utf-8')
                temp_files[sentiment] = temp_file.name
                temp_handles[sentiment] = temp_file
            
            print(f"Processing {input_file} (memory-efficient mode)...")
            
            total_lines = 0
            valid_posts = 0
            empty_lines = 0
            json_errors = 0
            no_text_posts = 0
            
            with open(input_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    total_lines += 1
                    
                    # Skip empty lines
                    line = line.strip()
                    if not line:
                        empty_lines += 1
                        continue
                        
                    try:
                        # Parse each line as separate JSON object (NDJSON format)
                        post = json.loads(line)
                        
                        # Extract text content
                        text_content = self.extract_text_content(post)
                        
                        if not text_content:
                            no_text_posts += 1
                            continue
                            
                        valid_posts += 1
                        
                        # Get sentiment classification
                        sentiment = self.get_sentiment_label(text_content)
                        
                        # Create simplified record with only Comment and Sentiment
                        simplified_record = {
                            'Comment': text_content,
                            'Sentiment': sentiment
                        }
                        
                        # Write to appropriate temp file
                        json.dump(simplified_record, temp_handles[sentiment], ensure_ascii=False)
                        temp_handles[sentiment].write('\n')
                        
                        sentiment_counts[sentiment] += 1
                        
                        if line_num % 1000 == 0:
                            print(f"Processed {line_num} posts... (valid: {valid_posts})")
                            
                    except json.JSONDecodeError as e:
                        json_errors += 1
                        if json_errors <= 5:  # Only show first 5 errors
                            print(f"Warning: Skipping malformed JSON on line {line_num}: {e}")
                            print(f"  Line content (first 100 chars): {line[:100]}")
                        continue
                    except Exception as e:
                        print(f"Warning: Error processing line {line_num}: {e}")
                        continue
            
            print(f"\nProcessing summary:")
            print(f"  Total lines read: {total_lines}")
            print(f"  Empty lines: {empty_lines}")
            print(f"  JSON decode errors: {json_errors}")
            print(f"  Posts with no text content: {no_text_posts}")
            print(f"  Valid posts processed: {valid_posts}")
            
            # Show a sample of what we're trying to parse
            if total_lines > 0 and valid_posts == 0:
                print(f"\nDEBUG: Let's check the first few lines of your file...")
                with open(input_file, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if i >= 3:  # Show first 3 lines
                            break
                        print(f"  Line {i+1}: {line.strip()[:200]}...")
                        
                        # Try to parse this line and show what fields it has
                        try:
                            post = json.loads(line.strip())
                            print(f"    Available fields: {list(post.keys())}")
                            print(f"    'title' field: {post.get('title', 'NOT FOUND')}")
                            print(f"    'selftext' field: {post.get('selftext', 'NOT FOUND')}")
                            print(f"    'body' field: {post.get('body', 'NOT FOUND')}")
                        except json.JSONDecodeError as e:
                            print(f"    JSON Error: {e}")
                        print()
            
            # Close all temp files
            for handle in temp_handles.values():
                handle.close()
                
            self.temp_files = temp_files
            return dict(sentiment_counts)
            
        except Exception as e:
            # Clean up temp files on error
            for handle in temp_handles.values():
                if not handle.closed:
                    handle.close()
            for temp_file in temp_files.values():
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            raise e
    
    def balance_sentiments_from_temp_files(self, sentiment_counts: Dict[str, int], 
                                          target_count: int = None) -> List[Dict]:
        """
        Second pass: Sample balanced posts from temporary files.
        
        Args:
            sentiment_counts: Dictionary with sentiment counts
            target_count: Target number of posts per sentiment (None = use minimum)
            
        Returns:
            List of balanced posts
        """
        sentiments = ['positive', 'negative', 'neutral']
        
        # Print current distribution
        print("\nCurrent sentiment distribution:")
        for sentiment in sentiments:
            count = sentiment_counts.get(sentiment, 0)
            print(f"  {sentiment}: {count:,} posts")
        
        # Determine target count per sentiment
        if target_count is None:
            available_counts = [sentiment_counts.get(s, 0) for s in sentiments]
            target_count = min(available_counts)
            
        print(f"\nTarget count per sentiment: {target_count:,}")
        
        # Check if we have enough posts for each sentiment
        for sentiment in sentiments:
            available = sentiment_counts.get(sentiment, 0)
            if available < target_count:
                print(f"Warning: Only {available} {sentiment} posts available, "
                      f"but {target_count} requested. Using {available}.")
                target_count = min(target_count, available)
        
        # Sample posts from each sentiment category
        balanced_posts = []
        
        for sentiment in sentiments:
            temp_file = self.temp_files[sentiment]
            available_count = sentiment_counts.get(sentiment, 0)
            
            if available_count == 0:
                print(f"  {sentiment}: No posts available")
                continue
                
            sample_size = min(target_count, available_count)
            
            # Generate random line numbers to sample
            if available_count <= target_count:
                # Use all posts
                selected_lines = list(range(available_count))
            else:
                # Randomly sample
                selected_lines = sorted(random.sample(range(available_count), sample_size))
            
            # Read selected posts from temp file
            sampled_posts = []
            with open(temp_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    if line_num in selected_lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            post = json.loads(line)
                            sampled_posts.append(post)
                        except json.JSONDecodeError as e:
                            print(f"Warning: Skipping malformed JSON in temp file: {e}")
                            continue
                    
                    # Early exit if we've found all selected lines
                    if len(sampled_posts) >= sample_size:
                        break
            
            balanced_posts.extend(sampled_posts)
            print(f"  Sampled {len(sampled_posts)} {sentiment} posts")
        
        # Shuffle the final dataset
        random.shuffle(balanced_posts)
        
        print(f"\nFinal balanced dataset: {len(balanced_posts)} posts")
        return balanced_posts
    
    def save_balanced_dataset(self, posts: List[Dict], output_file: str):
        """
        Save balanced posts to output NDJSON file.
        
        Args:
            posts: List of balanced posts
            output_file: Path to output file
        """
        print(f"Saving balanced dataset to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for post in posts:
                json.dump(post, f, ensure_ascii=False)
                f.write('\n')
        
        print(f"Successfully saved {len(posts)} posts to {output_file}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        if hasattr(self, 'temp_files'):
            for temp_file in self.temp_files.values():
                if os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except OSError:
                        pass


def main():
    """Main function to run the sentiment balancing script."""
    parser = argparse.ArgumentParser(
        description="Balance sentiment distribution in NDJSON Reddit data using VADER (memory-efficient)"
    )
    parser.add_argument('input_file', help='Input NDJSON file path')
    parser.add_argument('output_file', help='Output NDJSON file path')
    parser.add_argument('--target-count', type=int, default=None,
                        help='Target number of posts per sentiment (default: use minimum available)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducible sampling (default: 42)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)
    
    # Create output directory if needed
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize balancer
    balancer = SentimentBalancer(random_seed=args.seed)
    
    try:
        # First pass: Process input file and create temp files
        sentiment_counts = balancer.process_ndjson_file_memory_efficient(args.input_file)
        
        if not sentiment_counts:
            print("Error: No valid posts found in input file.")
            sys.exit(1)
        
        # Second pass: Balance sentiments from temp files
        balanced_posts = balancer.balance_sentiments_from_temp_files(sentiment_counts, args.target_count)
        
        if not balanced_posts:
            print("Error: Could not create balanced dataset.")
            sys.exit(1)
        
        # Save results
        balancer.save_balanced_dataset(balanced_posts, args.output_file)
        
        print("\nSentiment balancing completed successfully!")
        print(f"Output contains simplified records with only 'Comment' and 'Sentiment' fields")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Always clean up temp files
        balancer.cleanup_temp_files()


if __name__ == "__main__":
    main()
