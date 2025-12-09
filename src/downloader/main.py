"""Main module for YouTube Video Downloader."""

import argparse
import os
import sys

import yt_dlp
from dotenv import load_dotenv


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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Filter mp4 formats with both video and audio
            formats = []
            for f in info.get("formats", []):
                if (
                    f.get("ext") == "mp4"
                    and f.get("vcodec") != "none"
                    and f.get("acodec") != "none"
                ):
                    formats.append(
                        {
                            "format_id": f["format_id"],
                            "resolution": f.get("resolution", "unknown"),
                            "height": f.get("height", 0),
                            "filesize": f.get("filesize", 0),
                        }
                    )

            # Sort by height (quality) descending
            formats.sort(key=lambda x: x["height"], reverse=True)

            return {"title": info.get("title", "video"), "formats": formats}
    except Exception as e:
        raise ValueError(f"Failed to fetch video info: {e}") from e


def select_quality(formats, quality_arg=None):
    """Select video quality interactively or from argument."""
    if not formats:
        raise ValueError("No suitable formats found")

    # If quality specified in CLI
    if quality_arg:
        # Try to match by resolution (e.g., "720p")
        for fmt in formats:
            if quality_arg.lower() in fmt["resolution"].lower():
                return fmt["format_id"]

        # Try to match by index
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
        size = f"({fmt['filesize'] / (1024**2):.1f} MB)" if fmt["filesize"] else ""
        print(f"{i}. {fmt['resolution']} {size}")

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
    # Ensure download directory exists
    os.makedirs(download_dir, exist_ok=True)

    ydl_opts = {
        "format": format_id,
        "outtmpl": os.path.join(download_dir, "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
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
        # 1. Parse arguments
        args = parse_arguments()

        # 2. Load configuration
        config = load_config()
        download_dir = config["download_dir"]

        # 3. Get URL (from args or input)
        url = args.url
        if not url:
            url = input("Enter YouTube video URL: ").strip()

        if not url:
            print("Error: URL is required")
            return 1

        # 4. Extract video information
        print("\nFetching video information...")
        video_info = get_video_info(url)

        print(f"\nVideo: {video_info['title']}")

        # 5. Select quality
        format_id = select_quality(video_info["formats"], args.quality)

        # 6. Download video
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
