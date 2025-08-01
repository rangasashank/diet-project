"""
Simple script to balance sentiment in Reddit NDJSON data using VADER.
Designed for the diet-project workflow.
"""

import json
import random
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import defaultdict
import argparse
import os
import tempfile
from config import get_random_state
from env_utils import get_dataset_path

def classify_topic(subreddit):
    """
    Classify subreddit into diet topic categories.
    Based on ClassifyTopic.py logic.
    """
    if not subreddit:
        return "none"
    
    diet_subs_list = ["keto", "intermittentfasting", "plantbaseddiet", "vegan", "vegetarian"]
    diet_subs_set = set(diet_subs_list)
    
    subreddit_lower = subreddit.lower()
    
    if subreddit_lower in diet_subs_set:
        if subreddit_lower in set(["plantbaseddiet", "vegan", "vegetarian"]):
            return "plantbaseddiet"
        else:
            return subreddit_lower
    else:
        return "none"

def discover_raw_files(raw_dir):
    """
    Dynamically discover submission and comment files in raw directory.
    
    Args:
        raw_dir (str): Path to raw directory
        
    Returns:
        list: List of submission files (excluding README and comment files)
    """
    if not os.path.exists(raw_dir):
        print(f"Warning: raw directory not found: {raw_dir}")
        return []
    
    all_files = os.listdir(raw_dir)
    
    # Filter for submission files (exclude comments, README, and other non-data files)
    submission_files = []
    for filename in all_files:
        # Skip README and other non-data files
        if filename.upper() == 'README' or filename.startswith('.'):
            continue
        
        # Include submission files but skip comment files for now (they'll be processed with submissions)
        if filename.endswith('_submissions')  and '_comments_' not in filename:
            submission_files.append(filename)
    
    # Sort for consistent processing order
    submission_files.sort()
    
    print(f"Discovered {len(submission_files)} submission files in {raw_dir}")
    for f in submission_files:
        print(f"  - {f}")
    
    return submission_files

def correct_sentiment_label(text_content, current_sentiment, topic="none"):
    """
    Apply domain-specific sentiment corrections based on diet context and topic.
    Adapted from correct_keto_sentiment.py logic with topic-specific rules.
    
    Args:
        text_content (str): The text content to analyze
        current_sentiment (str): Current sentiment classification ('positive', 'negative', 'neutral')
        topic (str): The diet topic ('keto', 'intermittentfasting', 'plantbaseddiet', 'none')
        
    Returns:
        str: Corrected sentiment classification
    """
    if not text_content:
        return current_sentiment
    
    text_lower = text_content.lower()
    
    # Topic-specific correction rules
    if topic == "keto":
        return correct_keto_sentiment(text_lower, current_sentiment)
    elif topic == "intermittentfasting":
        return correct_if_sentiment(text_lower, current_sentiment)
    elif topic == "plantbaseddiet":
        return correct_plantbased_sentiment(text_lower, current_sentiment)
    else:
        # General corrections for other topics
        return correct_general_sentiment(text_lower, current_sentiment)

def correct_keto_sentiment(text_lower, current_sentiment):
    """Keto-specific sentiment corrections."""
    # Positive keto indicators
    positive_indicators = [
        # Keto adaptation success
        ("fat adapted", None, None), ("ketosis", None, None),
        ("keto flu gone", None, None), ("energy increase", None, None),
        ("mental clarity", None, None), ("focus", None, None),
        
        # Weight loss celebrations
        ("down", "lbs", None), ("pounds down", None, None),
        ("sv", None, None),  # Scale Victory
        ("nsv", None, None),  # Non-Scale Victory
        ("goal weight", None, None),
        
        # Keto food enjoyment
        ("bacon", "delicious", None), ("butter", "amazing", None),
        ("keto", "tasty", None), ("fat bomb", None, None),
        
        # Health improvements
        ("inflammation", "gone", None), ("pain", "better", None),
        ("diabetes", "improved", None), ("blood sugar", "stable", None)
    ]
    
    # Negative keto indicators
    negative_indicators = [
        # Keto struggles
        ("keto flu", None, None), ("keto rash", None, None),
        ("electrolyte", "imbalance", None), ("leg cramps", None, None),
        ("kicked out", "ketosis", None), ("carb", "cravings", None),
        
        # Keto challenges
        ("plateau", None, None), ("stalled", None, None),
        ("constipation", None, None), ("bad breath", None, None),
        ("keto", "difficult", None), ("too restrictive", None, None)
    ]
    
    return apply_correction_patterns(text_lower, current_sentiment, positive_indicators, negative_indicators)

def correct_if_sentiment(text_lower, current_sentiment):
    """Intermittent Fasting specific sentiment corrections."""
    # Positive IF indicators
    positive_indicators = [
        # IF success
        ("fasting", "easy", None), ("autophagy", None, None),
        ("16:8", "working", None), ("omad", "great", None),
        ("hunger", "gone", None), ("mental clarity", None, None),
        
        # Weight loss and health
        ("lost", "weight", "fasting"), ("energy", "increased", None),
        ("sleep", "better", None), ("focus", "improved", None),
        ("if", "amazing", None), ("intermittent", "love", None),
        
        # Fasting milestones
        ("24", "hour", "fast"), ("48", "hour", "success", None),
        ("extended", "fast", "completed", None)
    ]
    
    # Negative IF indicators  
    negative_indicators = [
        # IF struggles
        ("hangry", None, None), ("dizzy", "fasting", None),
        ("binge", "eating", None), ("broke", "fast", "early"),
        ("hungry", "miserable", None), ("fasting", "hard", None),
        
        # IF problems
        ("headache", "fasting", None), ("weakness", None, None),
        ("social", "pressure", None), ("can't", "fast", None),
        ("giving up", "if", None), ("too difficult", None, None)
    ]
    
    return apply_correction_patterns(text_lower, current_sentiment, positive_indicators, negative_indicators)

def correct_plantbased_sentiment(text_lower, current_sentiment):
    """Plant-based diet specific sentiment corrections."""
    # Positive plant-based indicators
    positive_indicators = [
        # Health improvements
        ("cholesterol", "dropped", None), ("blood pressure", "normal", None),
        ("energy", "amazing", None), ("skin", "clear", None),
        ("digestion", "better", None), ("weight loss", None, None),
        
        # Ethical satisfaction
        ("animals", "saved", None), ("compassionate", None, None),
        ("environment", "helping", None), ("sustainable", None, None),
        ("cruelty", "free", None), ("plant", "power", None),
        
        # Food enjoyment
        ("delicious", "plants", None), ("whole foods", "amazing", None),
        ("vegetables", "love", None), ("fruits", "incredible", None),
        ("wfpb", "great", None), ("plant based", "easy", None)
    ]
    
    # Negative plant-based indicators
    negative_indicators = [
        # Nutritional concerns
        ("b12", "deficient", None), ("iron", "low", None),
        ("protein", "worried", None), ("supplements", "expensive", None),
        ("anemia", None, None), ("fatigue", "plant", None),
        
        # Social challenges
        ("family", "unsupportive", None), ("eating out", "hard", None),
        ("expensive", "vegetables", None), ("time consuming", None, None),
        ("miss", "meat", None), ("cravings", "cheese", None),
        
        # Digestive issues
        ("bloated", "beans", None), ("gas", "vegetables", None),
        ("fiber", "too much", None), ("stomach", "upset", None)
    ]
    
    return apply_correction_patterns(text_lower, current_sentiment, positive_indicators, negative_indicators)

def correct_general_sentiment(text_lower, current_sentiment):
    """General diet-related sentiment corrections."""
    # General positive indicators
    positive_indicators = [
        ("weight loss", None, None), ("healthy", None, None),
        ("goal", "reached", None), ("feeling", "great", None),
        ("energy", "up", None), ("thanks", None, None)
    ]
    
    # General negative indicators
    negative_indicators = [
        ("struggling", None, None), ("difficult", None, None),
        ("frustrated", None, None), ("plateau", None, None),
        ("giving up", None, None), ("too hard", None, None)
    ]
    
    return apply_correction_patterns(text_lower, current_sentiment, positive_indicators, negative_indicators)

def apply_correction_patterns(text_lower, current_sentiment, positive_indicators, negative_indicators):
    """Apply correction patterns based on indicators."""
    # Check for positive corrections
    for pattern in positive_indicators:
        if all(term is None or term in text_lower for term in pattern if term is not None):
            if current_sentiment != "positive":
                return "positive"
    
    # Check for negative corrections  
    for pattern in negative_indicators:
        if all(term is None or term in text_lower for term in pattern if term is not None):
            if current_sentiment != "negative":
                return "negative"
    
    return current_sentiment

def apply_sentiment_corrections(objects):
    """
    Apply domain-specific sentiment corrections to sampled objects.
    
    Args:
        objects: List of post/comment objects
        
    Returns:
        List of objects with corrected sentiment classifications
    """
    corrections_made = 0
    
    print("Applying topic-specific sentiment corrections...")
    
    for obj in objects:
        text_content = obj.get('text_content', '')
        current_sentiment = obj.get('sentiment', 'neutral')
        topic = obj.get('topic', 'none')
        
        corrected_sentiment = correct_sentiment_label(text_content, current_sentiment, topic)
        
        if corrected_sentiment != current_sentiment:
            corrections_made += 1
            obj['sentiment'] = corrected_sentiment
        
    print(f"Applied {corrections_made} sentiment corrections to {len(objects)} objects")
    
    return objects

def collect_top_comments_as_separate_objects(posts, comments_file):
    """
    Collect top 2 comments for each post and create separate objects with parent_id.
    
    Args:
        posts: List of post dictionaries
        comments_file: Path to comments NDJSON file
        
    Returns:
        List of all objects (posts + comments) with parent_id linking comments to posts
    """
    print("Building comment index...")
    
    # Create a mapping of post IDs to collect comments for
    post_ids_needed = set()
    for post in posts:
        post_id = post.get('id', '')
        if post_id:
            post_ids_needed.add(f"t3_{post_id}")  # Reddit submission format
    
    # Collect comments for our posts
    post_comments = defaultdict(list)
    
    try:
        with open(comments_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    comment = json.loads(line.strip())
                    link_id = comment.get('link_id', '')
                    
                    # Check if this comment belongs to one of our posts
                    if link_id in post_ids_needed:
                        # Process comment text
                        body = comment.get('body', '')
                        if body and body.strip() and body not in ['[deleted]', '[removed]']:
                            
                            # Get comment sentiment
                            analyzer = SentimentIntensityAnalyzer()
                            scores = analyzer.polarity_scores(body)
                            compound = scores['compound']
                            
                            # Create comment object with same structure as posts
                            subreddit = comment.get('subreddit', '')
                            topic = classify_topic(subreddit)
                            
                            comment_obj = {
                                'text_content': body,
                                'sentiment': 'positive' if compound >= 0.5 else 'negative' if compound <= -0.5 else 'neutral',
                                'subreddit': subreddit,
                                'topic': topic,
                                'score': comment.get('score', 0),
                                'created_utc': comment.get('created_utc', ''),
                                'id': comment.get('id', ''),
                                'post_type': 'comment',
                                'parent_id': link_id.replace('t3_', '') if link_id.startswith('t3_') else link_id
                            }
                            
                            post_comments[link_id].append(comment_obj)
                    
                    if line_num % 10000 == 0:
                        print(f"  Processed {line_num:,} comments")
                        
                except Exception as e:
                    continue
        
        print(f"Found comments for {len(post_comments)} posts")
        
        # Create final output with posts and their top comments as separate objects
        final_objects = []
        comments_added = 0
        
        for post in posts:
            # Add the post first
            final_objects.append(post)
            
            # Add top 3 comments as separate objects
            post_id = post.get('id', '')
            link_id = f"t3_{post_id}"
            
            if link_id in post_comments:
                # Sort comments by score (descending) and take top 2
                comments = post_comments[link_id]
                comments.sort(key=lambda x: x.get('score', 0), reverse=True)
                top_comments = comments[:2]
                
                for comment in top_comments:
                    final_objects.append(comment)
                    comments_added += 1
                
                print(f"  Added {len(top_comments)} comments for post {post_id}")
        
        posts_with_comments = len([link_id for link_id in post_comments if post_comments[link_id]])
        print(f"Added {comments_added} total comments from {posts_with_comments} posts")
        print(f"Final output: {len(posts)} posts + {comments_added} comments = {len(final_objects)} total objects")
        
    except Exception as e:
        print(f"Error processing comments file: {e}")
        final_objects = posts  # Return just posts if comment processing fails
    
    return final_objects

def balance_reddit_sentiment(input_file, output_file, target_per_sentiment=1000, random_seed=42, include_comments=False, comments_file=None):
    """
    Balance sentiment distribution in Reddit NDJSON file using memory-efficient approach.
    
    Args:
        input_file: Path to input NDJSON file
        output_file: Path to output NDJSON file  
        target_per_sentiment: Number of posts to sample per sentiment
        random_seed: Random seed for reproducibility
        include_comments: Whether to include top 3 comments for each post
        comments_file: Path to corresponding comments file (if include_comments=True)
    """
    
    # Initialize
    analyzer = SentimentIntensityAnalyzer()
    random.seed(random_seed)
    
    print(f"Processing {input_file}...")
    
    # First pass: Count sentiment distribution and create temporary files
    temp_files = {}
    temp_handles = {}
    sentiment_counts = defaultdict(int)
    total_processed = 0
    
    try:
        # Create temporary files for each sentiment
        for sentiment in ['positive', 'negative', 'neutral']:
            temp_filename = f"temp_{sentiment}_{random.randint(1000, 9999)}.ndjson"
            temp_files[sentiment] = temp_filename
            temp_handles[sentiment] = open(temp_filename, 'w', encoding='utf-8')
        
        print("First pass: Analyzing sentiment and creating temporary files...")
        
        # Process each line in NDJSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    post = json.loads(line.strip())
                    
                    # Extract text for sentiment analysis
                    title = post.get('title', '')
                    selftext = post.get('selftext', '')
                    body = post.get('body', '')  # For comments
                    
                    # Combine title, selftext, and body
                    text_parts = []
                    if title and title.strip():
                        text_parts.append(title)
                    if selftext and selftext.strip() and selftext not in ['[deleted]', '[removed]']:
                        text_parts.append(selftext)
                    if body and body.strip() and body not in ['[deleted]', '[removed]']:
                        text_parts.append(body)
                    
                    text_content = ' '.join(text_parts).strip()
                    
                    if not text_content.strip():
                        continue
                    
                    # Get VADER sentiment
                    scores = analyzer.polarity_scores(text_content)
                    compound = scores['compound']
                    
                    # Classify sentiment with stricter positive threshold
                    # More posts will be neutral unless they are strongly positive
                    if compound >= 0.5:  # Increased from 0.05 to 0.5 for stricter positive classification
                        sentiment = 'positive'
                    elif compound <= -0.50:  # Keep negative threshold the same
                        sentiment = 'negative'
                    else:
                        sentiment = 'neutral'  # Broader neutral range: -0.05 to 0.3
                    
                    # Add metadata and create clean output format
                    subreddit = post.get('subreddit', '')
                    topic = classify_topic(subreddit)
                    
                    # Use the combined text_content (already contains title + selftext + body)
                    clean_post = {
                        'text_content': text_content,
                        'sentiment': sentiment,
                        'subreddit': subreddit,
                        'topic': topic,
                        'score': post.get('score', 0),
                        'created_utc': post.get('created_utc', ''),
                        'id': post.get('id', ''),
                        'post_type': 'submission' if title else 'comment'
                    }
                    
                    # Write to appropriate temporary file
                    json.dump(clean_post, temp_handles[sentiment], ensure_ascii=False)
                    temp_handles[sentiment].write('\n')
                    
                    sentiment_counts[sentiment] += 1
                    total_processed += 1
                    
                    if total_processed % 1000 == 0:
                        print(f"  Processed {total_processed:,} posts")
                        
                except Exception as e:
                    print(f"Warning: Error on line {line_num}: {e}")
                    continue
        
        # Close temporary files
        for handle in temp_handles.values():
            handle.close()
        
        # Show distribution
        print(f"\nSentiment distribution from {total_processed:,} posts:")
        for sentiment in ['positive', 'negative', 'neutral']:
            count = sentiment_counts[sentiment]
            percentage = (count / total_processed * 100) if total_processed > 0 else 0
            print(f"  {sentiment}: {count:,} posts ({percentage:.1f}%)")
        
        # Check if we have enough posts for balancing
        min_count = min(sentiment_counts[s] for s in ['positive', 'negative', 'neutral'])
        if min_count == 0:
            print("Error: One or more sentiment categories has no posts!")
            return 0
        
        # Determine actual target
        actual_target = min(target_per_sentiment, min_count)
        print(f"\nSampling {actual_target:,} posts per sentiment...")
        
        # Second pass: Sample from temporary files
        balanced_posts = []
        topic_counts = defaultdict(lambda: defaultdict(int))
        
        for sentiment in ['positive', 'negative', 'neutral']:
            # Read all posts from temp file
            sentiment_posts = []
            with open(temp_files[sentiment], 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        post = json.loads(line.strip())
                        sentiment_posts.append(post)
            
            # Sample posts
            if sentiment_posts:
                sampled = random.sample(sentiment_posts, 
                                      min(actual_target, len(sentiment_posts)))
                balanced_posts.extend(sampled)
                print(f"  {sentiment}: {len(sampled):,} posts sampled")
                
                # Count topics for reporting
                for post in sampled:
                    topic_counts[sentiment][post['topic']] += 1
        
        # Show topic distribution in final sample
        print(f"\nTopic distribution in balanced sample:")
        all_topics = set()
        for sentiment_topics in topic_counts.values():
            all_topics.update(sentiment_topics.keys())
        
        for topic in sorted(all_topics):
            print(f"  {topic}:")
            for sentiment in ['positive', 'negative', 'neutral']:
                count = topic_counts[sentiment][topic]
                if count > 0:
                    print(f"    {sentiment}: {count:,}")
        
        # Total topic counts in sample
        total_topic_counts = defaultdict(int)
        for sentiment_topics in topic_counts.values():
            for topic, count in sentiment_topics.items():
                total_topic_counts[topic] += count
        
        print(f"\nFinal sample by topic:")
        for topic, count in sorted(total_topic_counts.items()):
            percentage = (count / len(balanced_posts) * 100) if balanced_posts else 0
            print(f"  {topic}: {count:,} ({percentage:.1f}%)")
        
        # Shuffle final dataset
        random.shuffle(balanced_posts)
        
        # If comments are requested, collect top 2 comments for each post
        final_output = []
        if include_comments and comments_file and os.path.exists(comments_file):
            print(f"Collecting top 2 comments for each post from {comments_file}...")
            final_output = collect_top_comments_as_separate_objects(balanced_posts, comments_file)
        else:
            final_output = balanced_posts
        
        # Apply domain-specific sentiment corrections to sampled data
        final_output = apply_sentiment_corrections(final_output)
        
        # Save results
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        print(f"\nSaving {len(final_output):,} objects (posts + comments) to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            for obj in final_output:
                json.dump(obj, f, ensure_ascii=False)
                f.write('\n')
        
        print("Done!")
        return len(final_output)
        
    finally:
        # Clean up temporary files
        for sentiment in ['positive', 'negative', 'neutral']:
            if sentiment in temp_handles:
                try:
                    temp_handles[sentiment].close()
                except:
                    pass
            if sentiment in temp_files:
                try:
                    import os
                    if os.path.exists(temp_files[sentiment]):
                        os.remove(temp_files[sentiment])
                except:
                    pass

# Updated to work with raw files
if __name__ == "__main__":
    import os
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Balance sentiment in Reddit NDJSON data using VADER',
        epilog="""
USAGE EXAMPLES:
  # Process without comments:
  python scripts/simple_balance_sentiment.py

  # Process with top 2 comments per post:
  python scripts/simple_balance_sentiment.py --include-comments

  # Custom settings:
  python scripts/simple_balance_sentiment.py --include-comments --target-per-sentiment 1500 --output-dir my_output
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--include-comments', action='store_true', 
                        help='Include top 2 comments for each post')
    parser.add_argument('--target-per-sentiment', type=int, default=1000,
                        help='Number of posts to sample per sentiment (default: 1000)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for processed files (default: DATASETDIRPATH)')
    parser.add_argument('--random-seed', type=int, default=get_random_state(),
                        help=f'Random seed for reproducibility (default: {get_random_state()})')
    
    args = parser.parse_args()
    
    # Process files from raw directory
    # Get base path from environment configuration
    base_path = get_dataset_path()
    raw_dir = os.path.join(base_path, "raw_output")
    
    # Set output directory - use DATASETDIRPATH if not specified
    if args.output_dir is None:
        output_dir = base_path  # Use DATASETDIRPATH as default
    else:
        output_dir = args.output_dir
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Option to include comments from command line
    include_comments = args.include_comments
    
    # Dynamically discover files from raw directory
    files_to_process = discover_raw_files(raw_dir)
    
    if not files_to_process:
        print("No files found to process. Exiting.")
        exit(1)
    
    print("Processing raw files for sentiment analysis...")
    if include_comments:
        print("Comments will be included (top 2 per post)")
    else:
        print("Only processing submissions (no comments)")
    print(f"Target per sentiment: {args.target_per_sentiment}")
    print(f"Output directory: {output_dir}")
    print(f"Random seed: {args.random_seed}")
    
    results = {}
    for filename in files_to_process:
        # Skip comment files when include_comments is True (we'll process them with submissions)
        if include_comments and filename.endswith('_comments_out'):
            continue
            
        input_path = os.path.join(raw_dir, filename)
        output_path = os.path.join(output_dir, f"{filename}_balanced.ndjson")
        
        # Determine corresponding comments file
        comments_file = None
        if include_comments and filename.endswith('_submissions_out'):
            comments_filename = filename.replace('_submissions_out', '_comments_out')
            comments_path = os.path.join(raw_dir, comments_filename)
            if os.path.exists(comments_path):
                comments_file = comments_path
        
        if os.path.exists(input_path):
            print(f"\n{'='*50}")
            print(f"Processing: {filename}")
            if comments_file:
                print(f"With comments from: {os.path.basename(comments_file)}")
            
            try:
                count = balance_reddit_sentiment(
                    input_file=input_path,
                    output_file=output_path,
                    target_per_sentiment=args.target_per_sentiment,
                    random_seed=args.random_seed,
                    include_comments=include_comments,
                    comments_file=comments_file
                )
                results[filename] = count
                print(f"✓ Completed: {count:,} balanced objects saved")
            except Exception as e:
                print(f"✗ Error processing {filename}: {e}")
                results[filename] = 0
        else:
            print(f"✗ File not found: {input_path}")
            results[filename] = 0
    
    # Summary
    print(f"\n{'='*50}")
    print("PROCESSING SUMMARY")
    print(f"{'='*50}")
    total_objects = 0
    successful_files = 0
    
    for filename, count in results.items():
        status = "✓" if count > 0 else "✗"
        print(f"{status} {filename}: {count:,} objects")
        total_objects += count
        if count > 0:
            successful_files += 1
    
    print(f"\nProcessed {successful_files}/{len([f for f in files_to_process if not (include_comments and f.endswith('_comments_out'))])} files successfully")
    print(f"Total objects (posts + comments): {total_objects:,}")
    print(f"Output directory: {output_dir}")
    

    # Single file processing example (commented out)
    # balance_reddit_sentiment(
    #     input_file="raw/keto_submissions_out",
    #     output_file="processed_sentiment/keto_custom.ndjson",
    #     target_per_sentiment=1500,
    #     random_seed=42,
    #     include_comments=True,
    #     comments_file="raw/keto_comments_out"
    # )
