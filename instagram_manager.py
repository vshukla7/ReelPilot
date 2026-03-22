import os
import random
import time
import moviepy
try:
    import moviepy.editor as mp
    moviepy.editor = mp # Explicit submodule attachment
    moviepy.VideoFileClip = mp.VideoFileClip
    moviepy.AudioFileClip = mp.AudioFileClip
except Exception:
    pass

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, FeedbackRequired
import config

class InstagramManager:
    def __init__(self, username):
        self.username = username
        self.cl = Client()
        self.session_file = os.path.join(config.SESSIONS_DIR, f"{self.username}.json")

    def login(self, password=None):
        """
        Attempts to login with stored session or provided password.
        Returns True on success, False or exception on failure.
        """
        if os.path.exists(self.session_file):
            print(f"Loading session for {self.username}...")
            try:
                self.cl.load_settings(self.session_file)
                # Verify if session is still alive
                self.cl.get_timeline_feed()
                return True
            except (LoginRequired, Exception) as e:
                print(f"Session expired or failed: {e}")
                # Fallback to password login if session failed
                if not password:
                    return False
        
        if password:
            print(f"Logging in {self.username} with password...")
            try:
                self.cl.login(self.username, password)
                self.cl.dump_settings(self.session_file)
                return True
            except Exception as e:
                print(f"Login with password failed: {e}")
                raise e
        return False


    def upload_reel(self, video_path, caption):
        """
        Uploads a video file as a Reel.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        try:
            print(f"Uploading Reel: {video_path}...")
            # For instagrapi, clip_upload is recommended for Reels
            media = self.cl.clip_upload(
                video_path,
                caption=caption
            )
            return media
        except Exception as e:
            print(f"Failed to upload {video_path}: {e}")
            raise e


    def get_video_files(self, folder_path):
        """
        Returns a list of .mp4 files in the folder.
        """
        if not os.path.exists(folder_path):
            return []
        
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".mp4")]

    def upload_one_video(self, folder_path, captions, progress_callback=None, log_callback=None):
        """
        Scans folder, uploads the first available .mp4, and deletes it.
        """
        videos = self.get_video_files(folder_path)
        if not videos:
            if log_callback: log_callback("No .mp4 files found in the selected folder.")
            return False

        if progress_callback: progress_callback(1, 1)
        
        video_path = videos[0]
        # Select random caption if list, else use string
        caption = random.choice(captions) if isinstance(captions, list) else captions
        
        try:
            if log_callback: log_callback(f"Step 1/2: Uploading {os.path.basename(video_path)} to Instagram...")
            media = self.upload_reel(video_path, caption)
            
            # If we get here, upload was successful
            if log_callback: 
                sc = getattr(media, 'code', 'N/A')
                log_callback(f"✅ Success! Uploaded as Reel with code: {sc}")
                log_callback("Step 2/2: Cleaning up local file...")
            
            # Explicitly clear any client internal states if possible
            # Explicitly clear any client internal states if possible
            import gc
            gc.collect()
            time.sleep(2)
            
            # Strategy: Try to RENAME the file first. 
            # If rename works, it means we have access. If not, it's locked.
            temp_name = video_path + ".trash"
            deleted = False
            
            for i in range(12): # Up to 60 seconds of retries
                try:
                    if os.path.exists(video_path):
                        # Try to move it first - this is often more successful on Windows
                        os.replace(video_path, temp_name)
                        # If we reach here, we moved it! Now delete the moved file.
                        os.remove(temp_name)
                        if log_callback: log_callback(f"🗑️ File deleted successfully: {os.path.basename(video_path)}")
                        deleted = True
                        break
                except (PermissionError, OSError):
                    if log_callback: log_callback(f"⏳ File still locked by OS, retrying ({i+1}/12)...")
                    gc.collect()
                    time.sleep(5)
            
            # Also try to delete the .jpg thumbnail instagrapi might have left behind
            thumb_path = video_path + ".jpg"
            if os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                except:
                    pass

            if not deleted:
                if log_callback: log_callback(f"⚠️ OS lock persists. Scheduling hard-delete in background...")
                import subprocess
                # Ping localhost for 15 seconds to create a delay, then force delete the file in a detached cmd
                cmd = f'cmd.exe /c "ping 127.0.0.1 -n 15 > nul & del /F /Q \\"{video_path}\\""'
                subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            
            if progress_callback: progress_callback(1, 1)
            return True
            
        except Exception as e:
            if log_callback: log_callback(f"❌ Error during upload: {str(e)}")
            return False




