import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from flask import Flask, jsonify, request
from flask_cors import CORS
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Configuration & Setup ---
app = Flask(__name__)
CORS(app) 
analyzer = SentimentIntensityAnalyzer()

YOUTUBE_API_KEY = "AIzaSyBCBYNEs2ieFKj-fabToczAiXbWH-kZK04" 
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Initialize the YouTube API client
try:
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)
except Exception as e:
    print(f"Error initializing YouTube API client: {e}")
    youtube = None
# --- Helper Functions ---

def get_video_id(url):
    """Extracts the YouTube video ID from a URL."""
    try:
        # Standard video URL: https://www.youtube.com/watch?v=VIDEO_ID
        if "v=" in url:
            query = urlparse(url).query
            video_id = parse_qs(query)['v'][0]
        # Shortened URL: https://youtu.be/VIDEO_ID
        elif "youtu.be/" in url:
            video_id = urlparse(url).path[1:]
        else:
            return None
        return video_id
    except Exception:
        return None

def fetch_comments(video_id, max_comments=1000):
    """Fetches comments and basic video metadata using the YouTube API."""
    if not youtube:
        return {"error": "API client failed to initialize."}, None
        
    comments = []
    video_data = {}
    next_page_token = None
    
    # 1. Get initial video statistics (likes, views)
    try:
        video_response = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        ).execute()
        
        if not video_response['items']:
            return {"error": "Video not found or is unavailable."}, None
            
        snippet = video_response['items'][0]['snippet']
        stats = video_response['items'][0]['statistics']
        
        video_data = {
            'title': snippet.get('title'),
            'description': snippet.get('description', ''),
            'views': int(stats.get('viewCount', 0)),
            'likes': int(stats.get('likeCount', 0)),
        }
    except Exception as e:
        return {"error": f"Error fetching video data: {e}"}, None

    # 2. Fetch comments in pages
    try:
        while len(comments) < max_comments:
            comment_threads = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=min(50, max_comments - len(comments)),
                pageToken=next_page_token
            ).execute()

            for item in comment_threads.get('items', []):
                comment_snippet = item['snippet']['topLevelComment']['snippet']

                comments.append({
                    'author': comment_snippet.get('authorDisplayName', 'Anonymous'),
                    'comment': comment_snippet.get('textDisplay', '')
                })

                if len(comments) >= max_comments:
                    break

            next_page_token = comment_threads.get('nextPageToken')
            if not next_page_token:
                break
    except Exception as e:
        # This often happens if comments are disabled
        if not comments:
             return {"error": "Comments are disabled or API quota exceeded."}, None
        # If we got some comments before the error, we proceed with what we have
        print(f"Warning: Stopped fetching comments early due to error: {e}")

    return comments, video_data


def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        formatter = TextFormatter()
        return formatter.format_transcript(transcript)
    except Exception as e:
        print(f"Transcript Error: {e}")
        return None

def verify_content_with_ai(transcript_text):
    if not GEMINI_API_KEY:
        return "AI verification unavailable: API key missing."
    if not transcript_text:
        return "AI verification unavailable: No transcript found for this video."
    
    try:
        # Truncate transcript to ~100k chars to fit context bounds safely
        transcript_text = transcript_text[:100000]
        
        prompt = f"""Analyze this YouTube video transcript. 
1. Is the content clickbait? 
2. Is it actually useful and valid? 
3. Is it worth the user's time? 
Keep your response concise, max 3 sentences.

Transcript:
{transcript_text}"""

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return "AI verification failed during analysis."

def verify_content_with_metadata(title, description, top_comments):
    if not GEMINI_API_KEY:
        return "AI verification unavailable: API key missing."
        
    try:
        # Prepare comments
        comments_text = "\n".join([f"- {c['author']}: {c['comment']}" for c in top_comments[:50]])
        
        prompt = f"""This YouTube video does not have a transcript. Based on the Title, Description, and Top Comments, please analyze the video.
1. What is the video likely about?
2. Do the comments suggest the video is clickbait or a waste of time?
3. Is it worth watching?
Keep your response concise, max 3 sentences.

Title: {title}
Description: {description[:500]}...
Top Comments:
{comments_text[:3000]}"""

        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Error (Metadata Fallback): {e}")
        return "AI verification failed during fallback analysis."

# --- VADER Analysis Logic (Adapted from your Colab Code) ---

def analyze_comments(comment_list):
    """Analyzes a list of comments and calculates overall sentiment."""
    positive_count = 0
    negative_count = 0
    
    # Run the VADER analysis logic
    for item in comment_list:
        # Added str() protection, as in the previous fix
        vs = analyzer.polarity_scores(item['comment'])
        
        # Using the standard VADER threshold
        if vs['compound'] >= 0.05:
            positive_count += 1
        elif vs['compound'] <= -0.05:
            negative_count += 1
    
    return positive_count, negative_count

# --- Flask Route: MAIN ENTRY POINT ---
@app.route('/analyze', methods=['GET'])
def get_analysis():
    """Takes URL, fetches data, performs analysis, and returns results."""
    
    # 1. Get the URL from the front-end request
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided."}), 400

    video_id = get_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL format."}), 400

    # 2. Fetch comments and metadata
    comments, video_data = fetch_comments(video_id)
    
    if "error" in comments:
        return jsonify(comments), 500

    total_comments_fetched = len(comments)
    if total_comments_fetched == 0:
        return jsonify({"title": "No Comments Found", "description": "Analysis could not run as no comments were retrieved."}), 200

    # 3. Run Analysis
    positive_count, negative_count = analyze_comments(comments)
    
    total_valenced = positive_count + negative_count
    
    if total_valenced == 0:
        sentiment_pct = 50.0  # Default to neutral 50% if literally zero emotion detected
    else:
        # Method 1: Ratio
        ratio_pct = (positive_count / total_valenced) * 100
        
        # Method 2: Net Sentiment
        net_score = positive_count - negative_count
        net_pct = (net_score / total_comments_fetched) * 100
        net_pct = max(0.0, net_pct) # Floor negative net scores to 0%
        
        # Final Score: Average of both methods
        sentiment_pct = (ratio_pct + net_pct) / 2.0
    
    # 4. Engagement Calculation (Using placeholder logic as before)
    engagement_pct = sentiment_pct * 0.95 + 5
    engagement_pct = min(engagement_pct, 99.9)

    # 5. Fetch Transcript and Verify with AI
    transcript_text = fetch_transcript(video_id)
    if transcript_text:
        ai_verdict = verify_content_with_ai(transcript_text)
    else:
        # Fallback to metadata and comments
        ai_verdict = verify_content_with_metadata(
            title=video_data.get('title', ''),
            description=video_data.get('description', ''),
            top_comments=comments
        )

    # 6. Determine Reception
    if sentiment_pct >= 70:
        reception, title, icon = 'positive', 'Highly Positive Reception', 'fa-smile-beam'
    elif sentiment_pct >= 40:
        reception, title, icon = 'mixed', 'Mixed Audience Opinion', 'fa-meh'
    else:
        reception, title, icon = 'negative', 'Negative Reception', 'fa-frown'
    
    # Get top 10 comments with authors
    top_comments = []
    for i in range(min(50, len(comments))):
        top_comments.append({
            'author': comments[i]['author'],
            'comment': str(comments[i]['comment'])
        })

    # 7. Prepare Final JSON Response
    result = {
        'type': reception,
        'icon': icon,
        'title': title,
        'description': f'Analysis based on {total_comments_fetched} live comments.',
        'sentiment': round(sentiment_pct, 1),
        'engagement': round(engagement_pct, 1),
        'likes': video_data.get('likes', 0),
        'views': video_data.get('views', 0),
        'comments': top_comments,
        'ai_verdict': ai_verdict
    }

    return jsonify(result)

# --- Run Server ---
if __name__ == '__main__':
    app.run(debug=True)