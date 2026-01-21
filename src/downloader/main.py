"""Main module for YouTube Video Downloader."""

import argparse
import os
import shutil
import sys

import yt_dlp
from dotenv import load_dotenv


def is_ffmpeg_available():
    """Check if ffmpeg is installed and available in PATH."""
    return shutil.which("ffmpeg") is not None


def load_config():
    """Load configuration from .env file."""
    load_dotenv()
    download_dir = os.getenv("DOWNLOAD_DIR", "./downloads")
    return {"download_dir": download_dir}


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="YouTube Video Downloader - Download videos with quality selection"
    )
    parser.add_argument("--url", type=str, help="YouTube video URL")
    parser.add_argument(
        "--quality", type=str, help="Video quality (e.g., '720p' or format index)"
    )
    return parser.parse_args()


def get_video_info(url):
    """Extract video information and available formats."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }

    has_ffmpeg = is_ffmpeg_available()
    if not has_ffmpeg:
        print("\nWarning: ffmpeg not found. Install ffmpeg for better quality.\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Collect available heights
            heights = set()
            for f in info.get("formats", []):
                if f.get("vcodec") != "none" and f.get("height"):
                    heights.add(f.get("height"))

            # Create format options
            formats = []
            for height in sorted(heights, reverse=True):
                if has_ffmpeg:
                    format_id = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
                else:
                    format_id = f"best[height<={height}]"

                formats.append({
                    "format_id": format_id,
                    "resolution": f"{height}p",
                    "height": height,
                })

            # Add "best" option at the top
            if formats:
                best_height = formats[0]["height"]
                best_format_id = "bestvideo+bestaudio/best" if has_ffmpeg else "best"
                formats.insert(0, {
                    "format_id": best_format_id,
                    "resolution": f"best ({best_height}p)",
                    "height": best_height + 1,
                })

            return {"title": info.get("title", "video"), "formats": formats}
    except Exception as e:
        raise ValueError(f"Failed to fetch video info: {e}") from e


def select_quality(formats, quality_arg=None):
    """Select video quality interactively or from argument."""
    if not formats:
        raise ValueError("No suitable formats found")

    # If quality specified in CLI
    if quality_arg:
        for fmt in formats:
            if quality_arg.lower() in fmt["resolution"].lower():
                return fmt["format_id"]
        try:
            index = int(quality_arg) - 1
            if 0 <= index < len(formats):
                return formats[index]["format_id"]
        except ValueError:
            pass
        print(f"Quality '{quality_arg}' not found. Available options:")

    # Interactive selection
    print("\nAvailable video qualities:")
    for i, fmt in enumerate(formats, 1):
        print(f"{i}. {fmt['resolution']}")

    while True:
        try:
            choice = input("\nSelect quality (enter number): ").strip()
            index = int(choice) - 1
            if 0 <= index < len(formats):
                return formats[index]["format_id"]
            print(f"Please enter a number between 1 and {len(formats)}")
        except (ValueError, KeyboardInterrupt):
            print("\nInvalid input. Please enter a number.")
            continue


def progress_hook(d):
    """Display download progress."""
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "0%")
        speed = d.get("_speed_str", "N/A")
        eta = d.get("_eta_str", "N/A")
        print(f"\r[download] {percent} at {speed} ETA {eta}", end="")
    elif d["status"] == "finished":
        print(f"\n[download] Download completed: {d['filename']}")


def download_video(url, format_id, download_dir, title):
    """Download video with specified format."""
    os.makedirs(download_dir, exist_ok=True)

    ydl_opts = {
        "format": format_id,
        "outtmpl": os.path.join(download_dir, "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\nDownloading: {title}")
            print(f"Saving to: {download_dir}\n")
            ydl.download([url])
            return True
    except Exception as e:
        print(f"\nError during download: {e}")
        return False


def main():
    """Main entry point for the YouTube downloader."""
    try:
        args = parse_arguments()
        config = load_config()
        download_dir = config["download_dir"]

        url = args.url
        if not url:
            url = input("Enter YouTube video URL: ").strip()

        if not url:
            print("Error: URL is required")
            return 1

        print("\nFetching video information...")
        video_info = get_video_info(url)

        print(f"\nVideo: {video_info['title']}")

        format_id = select_quality(video_info["formats"], args.quality)
        success = download_video(url, format_id, download_dir, video_info["title"])

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
